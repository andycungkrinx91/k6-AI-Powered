import os
import random
import asyncio
from typing import Optional
from google import genai
from google.genai.errors import APIError

# LLM Provider Configuration (Global/Fallback)
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "gemini").lower()

# Gemini Configuration (Global)
GEMINI_API_KEYS = os.getenv("GEMINI_API_KEYS")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
GEMINI_MAX_TOKENS = int(os.getenv("GEMINI_MAX_TOKENS", "2048"))
GEMINI_TEMPERATURE = float(os.getenv("GEMINI_TEMPERATURE", "0.2"))

# OpenAI / OpenAI-Compatible (vLLM, etc.) Configuration (Global)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL")  # For vLLM, Ollama, etc.
OPENAI_MAX_TOKENS = int(os.getenv("OPENAI_MAX_TOKENS", "2048"))
OPENAI_TEMPERATURE = float(os.getenv("OPENAI_TEMPERATURE", "0.2"))

# Process Gemini Keys
GEMINI_KEYS_LIST = [k.strip() for k in (GEMINI_API_KEYS or "").split(",") if k.strip()]


# Shared Prompt Template
PROMPT_TEMPLATE = """
You are an expert senior performance engineer.

Analyze the following structured JSON payload which may include:
- k6 load metrics (metrics, timeline, scorecard)
- Security headers scan (security_headers)
- SSL/TLS analysis (ssl)
- WebPageTest (Playwright) results (webpagetest: first/repeat, summary, waterfall)
- Lighthouse results (lighthouse: categories, metrics)

Provide concise, enterprise-ready output:
1) Executive summary (link perf/security/UX together)
2) Bottlenecks and root causes (perf, network, frontend, TLS, headers)
3) Risks (SLA, security surface, UX) with severity
4) Prioritized recommendations (short bullets, actionable)
5) Scaling/operational guidance (load profile, headroom)

Rules:
- Be specific; cite key numbers (e.g., p95, LCP, TTFB, CLS, INP, Speed Index, TLS rating, header grade, WPT score, Lighthouse scores)
- Note missing/invalid data explicitly if sections are absent
- Keep tone professional and concise

DATA:
{payload}
"""


def _analyze_with_gemini_key(
    payload: str,
    api_key: str,
    model: str = GEMINI_MODEL,
    temperature: float = GEMINI_TEMPERATURE,
    max_tokens: int = GEMINI_MAX_TOKENS,
) -> str:
    client = genai.Client(api_key=api_key)
    prompt = PROMPT_TEMPLATE.format(payload=payload)

    response = client.models.generate_content(
        model=model,
        contents=prompt,
        config={
            "temperature": temperature,
            "max_output_tokens": max_tokens
        }
    )

    return response.text or ""


async def _analyze_with_openai_compatible(
    payload: str,
    api_key: Optional[str] = None,
    model: str = OPENAI_MODEL,
    base_url: Optional[str] = None,
    temperature: float = OPENAI_TEMPERATURE,
    max_tokens: int = OPENAI_MAX_TOKENS,
) -> str:
    # For vLLM/local providers, use direct HTTP like curl
    import httpx
    
    url = base_url if base_url else "https://api.openai.com/v1"
    
    # Use the key as-is, don't set to empty if None
    key = api_key if api_key else ""
    
    print(f"[DEBUG] _analyze_with_openai_compatible: model={model}, base_url={url}, has_key={'yes' if key else 'no'}")
    
    prompt = PROMPT_TEMPLATE.format(payload=payload)
    
    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json"
    }
    
    payload_data = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": temperature,
        "max_tokens": max_tokens
    }
    
    try:
        print(f"[DEBUG] _analyze_with_openai_compatible: Calling chat/completions...")
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{url.rstrip('/')}/chat/completions",
                headers=headers,
                json=payload_data
            )
            print(f"[DEBUG] _analyze_with_openai_compatible: Response status: {response.status_code}")
            if response.status_code != 200:
                print(f"[DEBUG] _analyze_with_openai_compatible: Error: {response.text[:300]}")
                raise RuntimeError(f"API returned {response.status_code}: {response.text[:200]}")
            
            data = response.json()
            return data["choices"][0]["message"]["content"] or ""
    except Exception as e:
        print(f"[DEBUG] _analyze_with_openai_compatible: Error: {e}")
        raise


async def analyze_with_settings(payload: str, user_settings: Optional[dict] = None) -> str:
    """
    Analyze payload using user settings if provided, otherwise fall back to global config.
    
    Args:
        payload: The JSON data to analyze
        user_settings: Optional dict with user LLM settings:
            - provider: "gemini" | "openai" | "local"
            - gemini_api_key: str (for Gemini)
            - gemini_model: str (optional)
            - openai_api_key: str (for OpenAI)
            - openai_model: str (optional)
            - openai_base_url: str (for local/other OpenAI-compatible)
            - temperature: float
            - max_tokens: int
    """
    # Determine provider
    provider = None
    if user_settings and user_settings.get("provider"):
        provider = user_settings["provider"]
        print(f"[DEBUG] Using provider from user_settings: {provider}")
    else:
        provider = LLM_PROVIDER
        print(f"[DEBUG] Using default LLM_PROVIDER: {LLM_PROVIDER}")
    
    print(f"[DEBUG] Final provider: {provider}, user_settings: {user_settings}")
    
    # Get common settings
    if user_settings:
        temperature = float(user_settings.get("temperature", GEMINI_TEMPERATURE))
        max_tokens = int(user_settings.get("max_tokens", GEMINI_MAX_TOKENS))
    else:
        temperature = GEMINI_TEMPERATURE
        max_tokens = GEMINI_MAX_TOKENS
    
    # Process based on provider
    if provider == "openai":
        # OpenAI (uses OpenAI API - requires api.openai.com)
        api_key = None
        model = OPENAI_MODEL
        base_url = None
        
        if user_settings:
            api_key = user_settings.get("openai_api_key") or OPENAI_API_KEY
            model = user_settings.get("openai_model") or OPENAI_MODEL
        
        if not api_key:
            api_key = OPENAI_API_KEY
        
        return await _analyze_with_openai_compatible(
            payload=payload,
            api_key=api_key,
            model=model,
            base_url=base_url,
            temperature=temperature,
            max_tokens=max_tokens,
        )
    
    elif provider == "local":
        # Local/OpenAI-compatible (vLLM, Ollama, etc.)
        api_key = None
        model = OPENAI_MODEL
        base_url = None
        
        if user_settings:
            api_key = user_settings.get("openai_api_key") or "no-key-required"
            model = user_settings.get("openai_model") or "gpt-4o"
            base_url = user_settings.get("openai_base_url") or OPENAI_BASE_URL
        
        if not base_url and OPENAI_BASE_URL:
            base_url = OPENAI_BASE_URL
        
        print(f"[DEBUG] local: api_key={'***' if api_key and api_key != 'no-key-required' else 'None'}, model={model}, base_url={base_url}")
        
        if not base_url:
            raise RuntimeError("OpenAI base URL not configured for local LLM")
        
        # For local vLLM - use the actual key from user settings
        if user_settings and user_settings.get("openai_api_key"):
            api_key = user_settings["openai_api_key"]
        
        try:
            result = await _analyze_with_openai_compatible(
                payload=payload,
                api_key=api_key,
                model=model,
                base_url=base_url,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            print(f"[DEBUG] local: Success!")
            return result
        except Exception as e:
            print(f"[DEBUG] local: Error - {e}")
            raise
    
    else:
        # Default to Gemini
        # Use user-provided key if available, otherwise use global keys
        if user_settings and user_settings.get("gemini_api_key"):
            api_keys = [user_settings["gemini_api_key"]]
            model = user_settings.get("gemini_model") or GEMINI_MODEL
        elif GEMINI_KEYS_LIST:
            api_keys = GEMINI_KEYS_LIST
            model = GEMINI_MODEL
        else:
            raise RuntimeError("GEMINI_API_KEYS not configured")
        
        attempts = 0
        used_keys = set()
        
        while attempts < 3:
            available_keys = [k for k in api_keys if k not in used_keys]
            if not available_keys:
                break
            
            api_key = random.choice(available_keys)
            used_keys.add(api_key)
            
            try:
                loop = asyncio.get_event_loop()
                return await loop.run_in_executor(
                    None,
                    _analyze_with_gemini_key,
                    payload,
                    api_key,
                    model,
                    temperature,
                    max_tokens
                )
            
            except APIError as e:
                status = getattr(e, "status_code", None)
                # Retry only on rate limit / service unavailable
                if status in [429, 503]:
                    attempts += 1
                    continue
                raise
            
            except Exception:
                attempts += 1
                continue
        
        raise RuntimeError("Gemini API unavailable after retries")


# Keep backward compatibility - analyze() uses global config
async def analyze(payload: str) -> str:
    """Legacy function - uses global configuration only"""
    return await analyze_with_settings(payload, None)
