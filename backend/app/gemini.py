import os
import random
from google import genai
import asyncio
from google.genai.errors import APIError

GEMINI_API_KEYS = os.getenv("GEMINI_API_KEYS")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
GEMINI_MAX_TOKENS = int(os.getenv("GEMINI_MAX_TOKENS", "2048"))
GEMINI_TEMPERATURE = float(os.getenv("GEMINI_TEMPERATURE", "0.2"))

if not GEMINI_API_KEYS:
    raise RuntimeError("GEMINI_API_KEYS not configured")

API_KEYS = [k.strip() for k in GEMINI_API_KEYS.split(",") if k.strip()]

if not API_KEYS:
    raise RuntimeError("No valid Gemini API keys provided")


def _analyze_with_key(payload: str, api_key: str) -> str:
    client = genai.Client(api_key=api_key)

    prompt = f"""
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

    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=prompt,
        config={
            "temperature": GEMINI_TEMPERATURE,
            "max_output_tokens": GEMINI_MAX_TOKENS
        }
    )

    return response.text


async def analyze(payload: str) -> str:

    attempts = 0
    used_keys = set()

    while attempts < 3:

        available_keys = [k for k in API_KEYS if k not in used_keys]
        if not available_keys:
            break

        api_key = random.choice(available_keys)
        used_keys.add(api_key)

        try:
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(
                None,
                _analyze_with_key,
                payload,
                api_key
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
