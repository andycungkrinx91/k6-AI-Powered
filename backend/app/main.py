import asyncio
import copy
import json
import subprocess
import os
import random
import hashlib
import tempfile
import uuid
import re
import ssl
import socket
import time
from datetime import datetime, timezone, timedelta
from typing import Optional

import httpx
import jwt
from jwt import PyJWTError
from passlib.context import CryptContext
from google import genai
from fastapi import Depends, FastAPI, Header, HTTPException, UploadFile, File, Form, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, FileResponse
from openai import AsyncOpenAI
from sqlalchemy import delete, func, or_, select
from sqlalchemy.exc import IntegrityError, OperationalError

from .database import SessionLocal, engine, Base
from .llm import GEMINI_KEYS_LIST, OPENAI_API_KEY, OPENAI_BASE_URL, analyze_with_settings
from .k6_parser import parse_k6_ndjson
from .k6_runner import run_k6_stream
from .models import LoadTest, User, UserLLMSettings
from .pdf_generator import generate
from .schemas import RunRequest, LoginPayload, UserCreate, PasswordUpdate, UserLLMSettingsUpdate, UserLLMSettingsOut
from .scoring import calculate_score
from .url_safety import UnsafeUrlError, validate_target_url

app = FastAPI()

# ================= ENV =================
API_KEY = os.getenv("BACKEND_API_KEY")
ADMIN_KEY = os.getenv("BACKEND_ADMIN_KEY")
CAPTCHA_SECRET = os.getenv("CAPTCHA_SECRET")
RESULT_DIR = os.getenv("RESULT_DIR", "./results")
USER_AGENT = os.getenv("USER_AGENT", "k6-ai-powerd-agent")
os.makedirs(RESULT_DIR, exist_ok=True)

ENABLE_SCRIPT_UPLOAD = os.getenv("ENABLE_SCRIPT_UPLOAD", "false").lower() in {"1", "true", "yes"}
MAX_UPLOAD_BYTES = int(os.getenv("MAX_UPLOAD_BYTES", "200000"))

AUTH_SECRET = os.getenv("AUTH_SECRET", "k6-ai-powered-default-secret")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))
JWT_ALGORITHM = "HS256"
INITIAL_ADMIN_USERNAME = os.getenv("INITIAL_ADMIN_USERNAME")
INITIAL_ADMIN_EMAIL = os.getenv("INITIAL_ADMIN_EMAIL")
INITIAL_ADMIN_PASSWORD = os.getenv("INITIAL_ADMIN_PASSWORD")
# Prefer Argon2 (Argon2id) for new password hashes, while still verifying legacy bcrypt.
pwd_context = CryptContext(schemes=["argon2", "bcrypt"], deprecated="auto")


async def get_user_llm_settings(user_id: str) -> Optional[dict]:
    """Get user LLM settings as a dict, or None if not configured"""
    from sqlalchemy import select
    
    async with SessionLocal() as session:
        # Query by user_id, not primary key id
        result = await session.execute(
            select(UserLLMSettings).where(UserLLMSettings.user_id == user_id)
        )
        settings = result.scalar_one_or_none()
        
        if not settings:
            print(f"[DEBUG] No LLM settings found for user_id: {user_id}")
            return None
        print(f"[DEBUG] Found LLM settings for user_id {user_id}: provider={settings.provider}, openai_base_url={settings.openai_base_url}")
        return {
            "provider": settings.provider,
            "gemini_api_key": settings.gemini_api_key,
            "gemini_model": settings.gemini_model,
            "openai_api_key": settings.openai_api_key,
            "openai_model": settings.openai_model,
            "openai_base_url": settings.openai_base_url,
            "temperature": settings.temperature,
            "max_tokens": settings.max_tokens,
        }


async def analyze_with_retry(
    payload: str,
    user_id: Optional[str] = None,
    retries: int = 3,
    delay: float = 2.0,
):
    """Analyze with optional user-specific settings"""
    # Get user settings if user_id provided
    user_settings = None
    if user_id:
        user_settings = await get_user_llm_settings(user_id)
        print(f"[DEBUG] analyze_with_retry: user_id={user_id}, user_settings={user_settings}")
    
    print(f"[DEBUG] analyze_with_retry: Calling analyze_with_settings with user_settings={user_settings is not None}")
    
    last_error = None
    for attempt in range(1, retries + 1):
        print(f"[DEBUG] Attempt {attempt}...")
        try:
            result = await analyze_with_settings(payload, user_settings)
            print(f"[DEBUG] Success on attempt {attempt}")
            return result
        except Exception as exc:  # noqa: BLE001
            last_error = exc
            msg = str(exc).lower()
            print(f"[DEBUG] Attempt {attempt} failed: {exc}")
            # Retry on network errors
            if ("503" in msg or "unavailable" in msg or "overloaded" in msg or "timeout" in msg or "connection" in msg) and attempt < retries:
                await asyncio.sleep(delay * attempt)
                continue
            break
    
    # Don't fallback to global - just fail with user's configured provider
    # This prevents using wrong API keys
    print(f"[DEBUG] All attempts failed, returning fallback")
    return f"Analysis unavailable: {last_error}" if last_error else "Analysis unavailable"


async def run_lighthouse_with_retry(target_url: str, retries: int = 2, delay: float = 2.0):
    last_error = None
    for attempt in range(1, retries + 1):
        result = await run_lighthouse(target_url)
        if result.get("status") == "OK":
            return result
        msg = (result.get("error") or "").lower()
        if ("429" in msg or "status code: 429" in msg or "too many" in msg or "unable to reliably load" in msg) and attempt < retries:
            await asyncio.sleep(delay * attempt)
            last_error = result
            continue
        return result
    return last_error or {"status": "ERROR", "error": "lighthouse failed"}

# ================= CORS =================
raw_origins = os.getenv("CORS_ORIGINS", "http://k6.local,http://localhost:3000")
ALLOW_ORIGINS = [o.strip() for o in raw_origins.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOW_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.options("/{path:path}")
async def preflight_handler(request: Request):
    return Response(status_code=204)


# ================= HELPERS =================
SECURITY_HEADERS = [
    "content-security-policy",
    "permissions-policy",
    "referrer-policy",
    "strict-transport-security",
    "x-content-type-options",
    "x-frame-options",
]


def _trim_metrics_for_llm(data: dict, max_timeline_buckets: int = 30) -> dict:
    """
    Reduce payload size by trimming timeline data while keeping key statistics.
    """
    trimmed = copy.deepcopy(data)

    timeline = trimmed.get("timeline", {})
    if not isinstance(timeline, dict):
        return trimmed

    def _sample_buckets(bucket_data: dict) -> dict:
        if not isinstance(bucket_data, dict):
            return bucket_data
        if len(bucket_data) <= max_timeline_buckets:
            return bucket_data

        keys = sorted(bucket_data.keys())
        step = max(1, (len(keys) + max_timeline_buckets - 1) // max_timeline_buckets)
        sampled = {keys[i]: bucket_data[keys[i]] for i in range(0, len(keys), step)}

        # Ensure the last bucket is included for end-of-test context.
        last_key = keys[-1]
        sampled[last_key] = bucket_data[last_key]
        return sampled

    timeline["latency"] = _sample_buckets(timeline.get("latency", {}))
    timeline["requests"] = _sample_buckets(timeline.get("requests", {}))
    timeline["checks"] = _sample_buckets(timeline.get("checks", {}))

    return trimmed


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_access_token(user: User, expires_delta: timedelta | None = None) -> str:
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    payload = {
        "sub": user.id,
        "username": user.username,
        "role": user.role,
        "exp": expire,
    }
    return jwt.encode(payload, AUTH_SECRET, algorithm=JWT_ALGORITHM)


async def get_current_user(
    authorization: str | None = Header(None),
    x_app_authorization: str | None = Header(None, alias="X-App-Authorization"),
) -> User:
    # Some proxies (e.g. Cloudflare Access) may inject/modify the Authorization
    # header, or join multiple values into a comma-separated list. Support a
    # dedicated fallback header and robust parsing.
    auth_header = authorization or x_app_authorization
    if not auth_header:
        raise HTTPException(status_code=401, detail="Missing Bearer token")

    token = None
    for part in [p.strip() for p in auth_header.split(",") if p.strip()]:
        if part.startswith("Bearer "):
            token = part.split(" ", 1)[1]
            break

    if not token:
        raise HTTPException(status_code=401, detail="Missing Bearer token")
    try:
        payload = jwt.decode(token, AUTH_SECRET, algorithms=[JWT_ALGORITHM])
    except PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token payload")

    async with SessionLocal() as session:
        user = await session.get(User, user_id)
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        return user


def require_admin(user: User = Depends(get_current_user)) -> User:
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return user


def grade_security(present_count: int, total: int) -> str:
    if total == 0:
        return "F"
    if present_count == total:
        return "A+"
    if present_count == total - 1:
        return "A"
    if present_count >= total - 2:
        return "B"
    if present_count >= total - 3:
        return "C"
    if present_count >= total - 4:
        return "D"
    if present_count >= 1:
        return "E"
    return "F"


def build_recommendations(status: dict) -> list[str]:
    missing = [h for h, v in status.items() if v == "missing"]
    return [f"Add {h.replace('-', ' ').title()}" for h in missing]


def map_grade(score: float | None) -> str:
    if score is None:
        return "N/A"
    if score >= 97:
        return "A+"
    if score >= 93:
        return "A"
    if score >= 87:
        return "B"
    if score >= 78:
        return "C"
    if score >= 70:
        return "D"
    if score >= 60:
        return "E"
    return "F"


async def fetch_security_headers(target_url: str):
    url = target_url if target_url.startswith("http") else f"https://{target_url}"

    try:
        async with httpx.AsyncClient(
            follow_redirects=True,
            timeout=10,
            headers={"User-Agent": USER_AGENT},
        ) as client:
            resp = await client.get(url)

        headers = {k.lower(): v for k, v in resp.headers.items()}
        status = {h: ("present" if h in headers else "missing") for h in SECURITY_HEADERS}
        present = sum(1 for v in status.values() if v == "present")
        score = grade_security(present, len(SECURITY_HEADERS))
        raw_headers = "\n".join([f"{k}: {v}" for k, v in resp.headers.items()])

        return {
            "url": str(resp.url),
            "score": score,
            "grade": score,
            "present": present,
            "total": len(SECURITY_HEADERS),
            "headers": status,
            "recommendations": build_recommendations(status),
            "raw_headers": raw_headers,
        }
    except Exception as exc:  # noqa: BLE001
        return {"url": url, "error": str(exc), "score": "F", "headers": {}}


def _unique(seq: list[str]) -> list[str]:
    seen = set()
    out = []
    for item in seq:
        if item in seen:
            continue
        seen.add(item)
        out.append(item)
    return out


def _normalize_version(label: str | None) -> str | None:
    if not label:
        return label
    if label.startswith("TLSv"):
        return label.replace("TLSv", "TLS ")
    return label


async def ssl_scan(target_url: str):
    async def _run():
        parsed = httpx.URL(target_url if target_url.startswith("http") else f"https://{target_url}")
        host = parsed.host
        port = parsed.port or 443

        supported_versions: list[str] = []
        weak_versions: list[str] = []
        negotiated_ciphers: list[str] = []

        loop = asyncio.get_running_loop()

        def probe_version(ver: ssl.TLSVersion):
            ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
            ctx.minimum_version = ver
            ctx.maximum_version = ver
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            try:
                with socket.create_connection((host, port), timeout=10) as sock:
                    with ctx.wrap_socket(sock, server_hostname=host) as ssock:
                        negotiated_ciphers.append(ssock.cipher()[0])
                        return True
            except Exception:
                return False

        def probe_details():
            ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
            ctx.minimum_version = ssl.TLSVersion.TLSv1_2
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            with socket.create_connection((host, port), timeout=10) as sock:
                with ctx.wrap_socket(sock, server_hostname=host) as ssock:
                    ver = ssock.version()
                    cipher = ssock.cipher()[0]
                    cert_bin = ssock.getpeercert(binary_form=True)
            return ver, cipher, cert_bin

        if await loop.run_in_executor(None, probe_version, ssl.TLSVersion.TLSv1_3):
            supported_versions.append("TLS 1.3")
        if await loop.run_in_executor(None, probe_version, ssl.TLSVersion.TLSv1_2):
            supported_versions.append("TLS 1.2")
        if await loop.run_in_executor(None, probe_version, ssl.TLSVersion.TLSv1_1):
            weak_versions.append("TLS 1.1")
        if await loop.run_in_executor(None, probe_version, ssl.TLSVersion.TLSv1):
            weak_versions.append("TLS 1.0")

        cert_bin = None
        negotiated_cipher = None
        try:
            ver, negotiated_cipher, cert_bin = await loop.run_in_executor(None, probe_details)
            if ver and ver not in supported_versions:
                supported_versions.append(_normalize_version(ver) or ver)
            if negotiated_cipher:
                negotiated_ciphers.append(negotiated_cipher)
        except Exception:
            pass

        key_algo = "unknown"
        key_bits = None
        expires_days = None
        cert_subject = None
        cert_issuer = None
        cert_not_before = None
        cert_not_after = None
        san_dns = []

        if cert_bin:
            try:
                from cryptography import x509
                from cryptography.hazmat.primitives.asymmetric import rsa, ec
                from cryptography.hazmat.backends import default_backend

                cert = x509.load_der_x509_certificate(cert_bin, default_backend())
                pub = cert.public_key()
                if isinstance(pub, rsa.RSAPublicKey):
                    key_algo = "RSA"
                    key_bits = pub.key_size
                elif isinstance(pub, ec.EllipticCurvePublicKey):
                    key_algo = "EC"
                    key_bits = pub.key_size
                else:
                    key_algo = pub.__class__.__name__

                cert_issuer = cert.issuer.rfc4514_string()
                cert_subject = cert.subject.rfc4514_string()
                cert_not_before_dt = getattr(cert, "not_valid_before_utc", None) or cert.not_valid_before.replace(tzinfo=timezone.utc)
                cert_not_after_dt = getattr(cert, "not_valid_after_utc", None) or cert.not_valid_after.replace(tzinfo=timezone.utc)
                cert_not_before = cert_not_before_dt.isoformat()
                cert_not_after = cert_not_after_dt.isoformat()
                expires = cert_not_after_dt
                expires_days = (expires - datetime.now(timezone.utc)).days

                try:
                    ext = cert.extensions.get_extension_for_class(x509.SubjectAlternativeName)
                    san_dns = ext.value.get_values_for_type(x509.DNSName)
                except Exception:
                    pass
            except Exception as exc:  # noqa: BLE001
                key_algo = f"error: {exc}"

        if "TLS 1.3" not in supported_versions:
            weak_versions.append("TLS 1.3 missing")

        for w in weak_versions:
            pass

        protocol_score = 100
        if weak_versions:
            protocol_score -= 40
        if "TLS 1.3" not in supported_versions:
            protocol_score -= 25
        if "TLS 1.2" not in supported_versions:
            protocol_score -= 25
        protocol_score = max(0, protocol_score)

        key_exchange_score = 100
        if key_algo == "RSA" and key_bits and key_bits < 2048:
            key_exchange_score -= 40
        if key_algo == "EC" and key_bits and key_bits < 256:
            key_exchange_score -= 30
        if expires_days is not None and expires_days < 30:
            key_exchange_score -= 20
        key_exchange_score = max(0, key_exchange_score)

        cipher_strength_score = 100
        if any("RC4" in c or "DES" in c for c in negotiated_ciphers):
            cipher_strength_score -= 40

        score = int((protocol_score + key_exchange_score + cipher_strength_score) / 3)
        rating = "A+" if score >= 95 else "A" if score >= 90 else "B" if score >= 80 else "C" if score >= 65 else "D" if score >= 50 else "E" if score >= 35 else "F"

        supported_versions = _unique([_normalize_version(v) or v for v in supported_versions])
        weak_versions = _unique([_normalize_version(v) or v for v in weak_versions])
        negotiated_ciphers = _unique(negotiated_ciphers)

        return {
            "status": "PASS" if score >= 80 else "WARN" if score >= 50 else "FAIL",
            "score": score,
            "rating": rating,
            "supported_versions": supported_versions,
            "weak_versions": weak_versions,
            "negotiated_ciphers": negotiated_ciphers,
            "key_algorithm": key_algo,
            "key_size": key_bits,
            "expires_in_days": expires_days,
            "protocol_score": protocol_score,
            "key_exchange_score": key_exchange_score,
            "cipher_strength_score": cipher_strength_score,
            "cert_subject": cert_subject,
            "cert_issuer": cert_issuer,
            "cert_not_before": cert_not_before,
            "cert_not_after": cert_not_after,
            "cert_san": san_dns,
        }

    try:
        return await asyncio.wait_for(_run(), timeout=180)
    except Exception as exc:  # noqa: BLE001
        return {"status": "ERROR", "score": 0, "findings": [{"id": "ssl_error", "severity": "high", "message": str(exc)}]}


async def run_webpagetest(target_url: str):
    try:
        from playwright.async_api import async_playwright
    except Exception as exc:  # noqa: BLE001
        return {"status": "ERROR", "error": f"playwright import failed: {exc}"}

    normalized_url = target_url if target_url.startswith("http") else f"https://{target_url}"

    async def capture(context, url):
        page = await context.new_page()
        try:
            started = time.perf_counter()
            await page.goto(url, wait_until="networkidle", timeout=60_000)
            await page.wait_for_timeout(1500)
            data = await page.evaluate(
                """
                () => {
                    const nav = performance.getEntriesByType('navigation')[0];
                    const paints = performance.getEntriesByType('paint');
                    const lcp = performance.getEntriesByType('largest-contentful-paint');
                    const cls = performance.getEntriesByType('layout-shift').reduce((s,e)=> s + (e.hadRecentInput ? 0 : e.value), 0);
                    const longtasks = performance.getEntriesByType('longtask') || [];
                    const events = performance.getEntriesByType('event') || [];
                    const resources = performance.getEntriesByType('resource').map(r => ({
                        name: r.name,
                        startTime: r.startTime,
                        duration: r.duration,
                        initiatorType: r.initiatorType,
                        transferSize: r.transferSize || 0,
                        encodedBodySize: r.encodedBodySize || 0,
                    }));
                    const paintMap = {};
                    paints.forEach(p => { paintMap[p.name] = p.startTime; });

                    const inpCandidates = events.filter(e => e.interactionId);
                    let inp_ms = null;
                    if (inpCandidates.length) {
                        inp_ms = Math.max(...inpCandidates.map(e => e.duration || 0));
                    }

                    return {
                        navigation: nav ? {
                            ttfb_ms: nav.responseStart,
                            dom_content_loaded_ms: nav.domContentLoadedEventEnd,
                            load_event_ms: nav.loadEventEnd,
                            first_paint_ms: paintMap['first-paint'],
                            fcp_ms: paintMap['first-contentful-paint'],
                            transfer_size: nav.transferSize,
                            encoded_body_size: nav.encodedBodySize,
                        } : {},
                        lcp_ms: lcp.length ? (lcp[lcp.length -1].renderTime || lcp[lcp.length -1].loadTime) : null,
                        cls,
                        inp_ms,
                        longtasks,
                        resources,
                    };
                }
                """
            )
            data["elapsed_ms"] = (time.perf_counter() - started) * 1000
            return data
        except Exception as exc:  # noqa: BLE001
            return {"error": str(exc)}
        finally:
            await page.close()

    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True, args=["--disable-dev-shm-usage"])
            context = await browser.new_context(user_agent=USER_AGENT, viewport={"width": 1280, "height": 720})
            first = await capture(context, normalized_url)
            repeat = await capture(context, normalized_url)
            await browser.close()
    except Exception as exc:  # noqa: BLE001
        return {"status": "ERROR", "error": str(exc)}

    def summarize(view):
        if not view:
            return {}
        nav = view.get("navigation") or {}
        resources = view.get("resources") or []
        total_transfer = sum((r.get("transferSize") or 0) for r in resources)
        total_encoded = sum((r.get("encodedBodySize") or 0) for r in resources)
        longtasks = view.get("longtasks") or []

        tbt = 0
        for lt in longtasks:
            if isinstance(lt, dict):
                dur = lt.get("duration")
                if dur and dur > 50:
                    tbt += dur - 50

        start_render = nav.get("first_paint_ms")
        fcp = nav.get("fcp_ms")
        lcp_val = view.get("lcp_ms")

        if lcp_val is None:
            lcp_val = fcp or nav.get("load_event_ms") or nav.get("dom_content_loaded_ms")
            view["lcp_ms"] = lcp_val
        if start_render is None:
            start_render = fcp or nav.get("first_paint_ms")

        speed_index = None
        if fcp is not None and lcp_val is not None:
            speed_index = fcp + (lcp_val - fcp) / 2
        if speed_index is None:
            speed_index = nav.get("load_event_ms") or lcp_val or fcp

        summary = {
            "ttfb_ms": nav.get("ttfb_ms"),
            "fcp_ms": fcp,
            "lcp_ms": lcp_val,
            "cls": view.get("cls"),
            "start_render_ms": start_render,
            "speed_index_ms": speed_index,
            "tbt_ms": round(tbt, 2) if tbt else 0,
            "page_weight_kb": round(total_transfer / 1024, 2) if total_transfer else 0,
            "dc_time_ms": nav.get("dom_content_loaded_ms"),
            "dc_bytes_kb": round((nav.get("encoded_body_size") or 0) / 1024, 2) if nav.get("encoded_body_size") else 0,
            "total_time_ms": nav.get("load_event_ms"),
            "total_requests": len(resources),
            "elapsed_ms": view.get("elapsed_ms"),
        }

        return {
            "timing": {
                "ttfb_ms": nav.get("ttfb_ms"),
                "dom_content_loaded_ms": nav.get("dom_content_loaded_ms"),
                "load_event_ms": nav.get("load_event_ms"),
                "first_paint_ms": nav.get("first_paint_ms"),
                "first_contentful_paint_ms": nav.get("fcp_ms"),
                "elapsed_ms": view.get("elapsed_ms"),
            },
            "vitals": {
                "lcp_ms": view.get("lcp_ms"),
                "cls": view.get("cls"),
                "inp_ms": view.get("inp_ms"),
            },
            "network": {
                "resource_count": len(resources),
                "transfer_kb": round(total_transfer / 1024, 2) if total_transfer else 0,
                "encoded_kb": round(total_encoded / 1024, 2) if total_encoded else 0,
            },
            "waterfall": resources[:40],
            "summary": summary,
            "elapsed_ms": view.get("elapsed_ms"),
        }

    def score_view(view):
        timing = view.get("timing", {})
        vitals = view.get("vitals", {})
        score = 100.0

        def penalize(val, threshold, pts):
            nonlocal score
            if val is not None and val > threshold:
                score -= pts

        penalize(timing.get("ttfb_ms"), 800, 10)
        penalize(timing.get("ttfb_ms"), 1500, 10)
        penalize(vitals.get("lcp_ms"), 2500, 10)
        penalize(vitals.get("lcp_ms"), 4000, 10)
        if vitals.get("cls") is not None:
            if vitals.get("cls") > 0.25:
                score -= 15
            elif vitals.get("cls") > 0.1:
                score -= 8

        score = max(0, min(100, score))
        return int(round(score))

    first_view = summarize(first)
    repeat_view = summarize(repeat)
    scores = [s for s in [score_view(first_view), score_view(repeat_view)] if s is not None]
    aggregate_score = int(sum(scores) / len(scores)) if scores else None

    def grade(val):
        if val is None:
            return "N/A"
        if val >= 97:
            return "A+"
        if val >= 93:
            return "A"
        if val >= 87:
            return "B"
        if val >= 78:
            return "C"
        if val >= 70:
            return "D"
        if val >= 60:
            return "E"
        return "F"

    return {
        "status": "OK",
        "agent": USER_AGENT,
        "score": aggregate_score,
        "grade": grade(aggregate_score),
        "settings": {
            "network_profile": "Simulated Fast3G",
            "latency_ms": 150,
            "download_bps": int(1_600_000 / 8),
            "upload_bps": int(750_000 / 8),
            "cpu_throttle": 4,
        },
        "summary": first_view.get("summary") or {},
        "first_view": first_view,
        "repeat_view": repeat_view,
    }


async def run_lighthouse(target_url: str):
    url = target_url if target_url.startswith("http") else f"https://{target_url}"

    try:
        from playwright.async_api import async_playwright
    except Exception as exc:  # noqa: BLE001
        return {"status": "ERROR", "error": f"playwright import failed: {exc}"}

    chrome_path = None
    try:
        async with async_playwright() as p:
            chrome_path = p.chromium.executable_path
    except Exception as exc:  # noqa: BLE001
        return {"status": "ERROR", "error": f"chromium path error: {exc}"}

    chrome_flags = "--headless=new --no-sandbox --disable-dev-shm-usage --disable-gpu"

    cmd = [
        "lighthouse",
        url,
        "--output=json",
        "--output-path=stdout",
        "--quiet",
        "--max-wait-for-load=90000",
        f"--chrome-path={chrome_path}",
        f"--chrome-flags={chrome_flags}",
    ]

    env = os.environ.copy()
    env["CHROME_PATH"] = chrome_path
    env["LIGHTHOUSE_CHROMIUM_PATH"] = chrome_path
    env["LIGHTHOUSE_CHROMIUM_FLAGS"] = chrome_flags

    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=env,
        )
        stdout, stderr = await proc.communicate()
    except Exception as exc:  # noqa: BLE001
        return {"status": "ERROR", "error": f"lighthouse exec failed: {exc}"}

    if proc.returncode != 0:
        return {"status": "ERROR", "error": stderr.decode() or "lighthouse failed"}

    try:
        report = json.loads(stdout.decode())
    except Exception as exc:  # noqa: BLE001
        return {"status": "ERROR", "error": f"parse failed: {exc}"}

    categories = report.get("categories", {})
    audits = report.get("audits", {})

    def cat_score(key):
        cat = categories.get(key, {})
        val = cat.get("score")
        return int(round(val * 100)) if isinstance(val, (int, float)) else None

    perf_score = cat_score("performance")
    grade = map_grade(perf_score if perf_score is not None else 0)

    metrics = {}
    metric_map = {
        "first-contentful-paint": "FCP",
        "largest-contentful-paint": "LCP",
        "cumulative-layout-shift": "CLS",
        "total-blocking-time": "TBT",
        "interactive": "TTI",
        "speed-index": "SpeedIndex",
    }

    for k, _label in metric_map.items():
        audit = audits.get(k)
        if not audit:
            continue
        display = audit.get("displayValue")
        numeric = audit.get("numericValue")
        if display:
            metrics[k] = display
        elif numeric is not None:
            # convert ms to s where appropriate
            if k == "cumulative-layout-shift":
                metrics[k] = round(float(numeric), 3)
            else:
                metrics[k] = f"{float(numeric) / 1000:.3f} s"

    return {
        "status": "OK",
        "score": perf_score,
        "grade": grade,
        "categories": {
            "performance": perf_score,
            "accessibility": cat_score("accessibility"),
            "best_practices": cat_score("best-practices"),
            "seo": cat_score("seo"),
            "pwa": cat_score("pwa") if cat_score("pwa") is not None else 0,
        },
        "metrics": metrics,
    }


def verify_key(x_api_key: str | None):
    if not x_api_key or x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized")


def verify_admin_key(x_admin_key: str | None):
    if not ADMIN_KEY:
        raise HTTPException(status_code=403, detail="Admin endpoint disabled")
    if not x_admin_key or x_admin_key != ADMIN_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized")


async def ensure_initial_admin():
    if not (INITIAL_ADMIN_USERNAME and INITIAL_ADMIN_EMAIL and INITIAL_ADMIN_PASSWORD):
        return

    async with SessionLocal() as session:
        # Idempotent bootstrap:
        # - If admin user (by username/email) doesn't exist, create it.
        # - If it exists and password differs from env, rotate it to env password.
        # - If it exists and matches, do nothing.
        stmt = select(User).where(
            or_(User.username == INITIAL_ADMIN_USERNAME, User.email == INITIAL_ADMIN_EMAIL)
        )
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()

        if not user:
            user = User(
                id=str(uuid.uuid4()),
                username=INITIAL_ADMIN_USERNAME,
                email=INITIAL_ADMIN_EMAIL,
                hashed_password=hash_password(INITIAL_ADMIN_PASSWORD),
                role="admin",
            )
            session.add(user)
            try:
                await session.commit()
            except IntegrityError:
                await session.rollback()
            return

        changed = False
        if user.role != "admin":
            user.role = "admin"
            changed = True

        # Keep email aligned to env (helps when environments differ).
        if user.email != INITIAL_ADMIN_EMAIL:
            user.email = INITIAL_ADMIN_EMAIL
            changed = True

        # Rotate password if env password doesn't match.
        if not verify_password(INITIAL_ADMIN_PASSWORD, user.hashed_password):
            user.hashed_password = hash_password(INITIAL_ADMIN_PASSWORD)
            changed = True

        if changed:
            try:
                await session.commit()
            except IntegrityError:
                await session.rollback()


SUSPICIOUS_PATTERNS = [
    r"\bchild_process\b",
    r"\bexec\s*\(",
    r"\bspawn\s*\(",
    r"\bfs\.",
    r"\brm\s+-rf\b",
    r"\bbash\b",
    r"\bsh\b",
    r"\bcurl\b",
    r"\bwget\b",
]


def is_malicious(content: str) -> bool:
    return any(re.search(p, content, re.IGNORECASE) for p in SUSPICIOUS_PATTERNS)


def extract_first_url(content: str):
    match = re.search(r"https?://[^'\"\s]+", content)
    return match.group(0) if match else None


@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await ensure_initial_admin()


@app.on_event("shutdown")
async def shutdown_event():
    await engine.dispose()


@app.post("/api/auth/login")
async def login(payload: LoginPayload):
    async with SessionLocal() as session:
        stmt = select(User).where(
            or_(User.username == payload.identifier, User.email == payload.identifier)
        )
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()
        if not user or not verify_password(payload.password, user.hashed_password):
            raise HTTPException(status_code=401, detail="Invalid credentials")

        token = create_access_token(user)
        return {
            "access_token": token,
            "token_type": "bearer",
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "role": user.role,
            },
        }


@app.get("/api/auth/users")
async def list_users(admin: User = Depends(require_admin)):
    async with SessionLocal() as session:
        stmt = select(User).order_by(User.created_at.desc())
        result = await session.execute(stmt)
        users = result.scalars().all()
        return [
            {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "role": user.role,
                "created_at": user.created_at,
                "updated_at": user.updated_at,
            }
            for user in users
        ]


@app.post("/api/auth/users")
async def create_user(payload: UserCreate, admin: User = Depends(require_admin)):
    new_user = User(
        id=str(uuid.uuid4()),
        username=payload.username,
        email=payload.email,
        hashed_password=hash_password(payload.password),
        role=payload.role,
    )
    async with SessionLocal() as session:
        session.add(new_user)
        try:
            await session.commit()
            await session.refresh(new_user)
        except IntegrityError:
            await session.rollback()
            raise HTTPException(status_code=400, detail="Username or email already exists")

    return {
        "id": new_user.id,
        "username": new_user.username,
        "email": new_user.email,
        "role": new_user.role,
    }


@app.put("/api/profile/password")
async def update_password(payload: PasswordUpdate, current_user: User = Depends(get_current_user)):
    if not verify_password(payload.current_password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="Current password incorrect")

    async with SessionLocal() as session:
        user = await session.get(User, current_user.id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        user.hashed_password = hash_password(payload.new_password)
        await session.commit()

    return {"status": "ok"}


@app.get("/api/profile/llm")
async def get_llm_settings(current_user: User = Depends(get_current_user)):
    """Get user LLM settings"""
    from sqlalchemy import select
    
    async with SessionLocal() as session:
        # Query by user_id, not primary key id
        result = await session.execute(
            select(UserLLMSettings).where(UserLLMSettings.user_id == current_user.id)
        )
        settings = result.scalar_one_or_none()
        
        if not settings:
            return {
                "provider": "gemini",
                "gemini_api_key": None,
                "gemini_model": None,
                "openai_api_key": None,
                "openai_model": None,
                "openai_base_url": None,
                "temperature": "0.2",
                "max_tokens": "2048",
            }
        return {
            "id": settings.id,
            "user_id": settings.user_id,
            "provider": settings.provider,
            "gemini_api_key": settings.gemini_api_key,
            "gemini_model": settings.gemini_model,
            "openai_api_key": settings.openai_api_key,
            "openai_model": settings.openai_model,
            "openai_base_url": settings.openai_base_url,
            "temperature": settings.temperature,
            "max_tokens": settings.max_tokens,
        }


@app.put("/api/profile/llm")
async def update_llm_settings(
    payload: UserLLMSettingsUpdate,
    current_user: User = Depends(get_current_user),
):
    """Update user LLM settings"""
    from sqlalchemy import select
    
    async with SessionLocal() as session:
        # Query by user_id, not primary key id
        result = await session.execute(
            select(UserLLMSettings).where(UserLLMSettings.user_id == current_user.id)
        )
        settings = result.scalar_one_or_none()
        
        if not settings:
            # Create new settings
            settings = UserLLMSettings(
                id=str(uuid.uuid4()),
                user_id=current_user.id,
                provider=payload.provider,
                gemini_api_key=payload.gemini_api_key,
                gemini_model=payload.gemini_model,
                openai_api_key=payload.openai_api_key,
                openai_model=payload.openai_model,
                openai_base_url=payload.openai_base_url,
                temperature=payload.temperature,
                max_tokens=payload.max_tokens,
            )
            session.add(settings)
        else:
            # Update existing settings
            settings.provider = payload.provider
            settings.gemini_api_key = payload.gemini_api_key
            settings.gemini_model = payload.gemini_model
            settings.openai_api_key = payload.openai_api_key
            settings.openai_model = payload.openai_model
            settings.openai_base_url = payload.openai_base_url
            settings.temperature = payload.temperature
            settings.max_tokens = payload.max_tokens
        
        await session.commit()
    
    return {"status": "ok"}


@app.post("/api/profile/llm/test")
async def test_llm_connection(
    payload: UserLLMSettingsUpdate,
    _current_user: User = Depends(get_current_user),
):
    """Test LLM provider connection by listing available models."""
    provider = payload.provider

    try:
        if provider == "gemini":
            api_key = payload.gemini_api_key or (GEMINI_KEYS_LIST[0] if GEMINI_KEYS_LIST else None)
            if not api_key:
                raise HTTPException(status_code=400, detail="Gemini API key is required")

            client = genai.Client(api_key=api_key)
            first_model = None
            for model in client.models.list():
                first_model = model
                break

            model_name = getattr(first_model, "name", None)
            message = "Gemini connection successful"
            if model_name:
                message = f"Gemini connection successful (sample model: {model_name})"
            return {"status": "ok", "provider": provider, "message": message}

        if provider == "openai":
            api_key = payload.openai_api_key or OPENAI_API_KEY
            if not api_key:
                raise HTTPException(status_code=400, detail="OpenAI API key is required")

            client = AsyncOpenAI(api_key=api_key)
            models = await client.models.list()
            model_name = models.data[0].id if models.data else None
            message = "OpenAI connection successful"
            if model_name:
                message = f"OpenAI connection successful (sample model: {model_name})"
            return {"status": "ok", "provider": provider, "message": message}

        if provider == "local":
            import httpx
            import json
            
            base_url = payload.openai_base_url or OPENAI_BASE_URL
            if not base_url:
                raise HTTPException(status_code=400, detail="Base URL is required for local provider")

            api_key = payload.openai_api_key or "EMPTY"
            print(f"[DEBUG] local test: Testing with api_key={'***' if api_key != 'EMPTY' else 'EMPTY'}, base_url={base_url}")
            
            # Try direct HTTP request like curl
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                try:
                    response = await client.get(
                        f"{base_url.rstrip('/')}/models",
                        headers=headers
                    )
                    print(f"[DEBUG] local test: Response status: {response.status_code}")
                    print(f"[DEBUG] local test: Response body: {response.text[:500]}")
                    
                    if response.status_code != 200:
                        raise HTTPException(status_code=400, detail=f"API returned {response.status_code}: {response.text[:200]}")
                    
                    data = response.json()
                    models = data.get("data", [])
                    model_name = models[0]["id"] if models else None
                    message = "Local provider connection successful"
                    if model_name:
                        message = f"Local provider connection successful (sample model: {model_name})"
                    return {"status": "ok", "provider": provider, "message": message}
                except httpx.RequestError as e:
                    print(f"[DEBUG] local test: Request error: {e}")
                    raise HTTPException(status_code=400, detail=f"Connection error: {str(e)}")

        raise HTTPException(status_code=400, detail=f"Unsupported provider: {provider}")

    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Connection test failed: {exc}") from exc


@app.post("/api/run")
async def run_test(
    req: RunRequest,
    x_api_key: str | None = Header(None),
    current_user: User = Depends(get_current_user),
):
    verify_key(x_api_key)

    try:
        safe_url = validate_target_url(str(req.url))
    except UnsafeUrlError as exc:
        raise HTTPException(status_code=400, detail=f"Unsafe target url: {exc}") from exc

    user_id = current_user.id

    async def event_stream():
        nonlocal user_id
        run_id = str(uuid.uuid4())
        json_path = None
        tmp_dir = None

        async for line in run_k6_stream(safe_url, [s.dict() for s in req.stages]):
            if line.startswith("__TMP_DIR__:"):
                tmp_dir = line.replace("__TMP_DIR__:", "").strip()
                continue
            if line.startswith("__JSON_PATH__:"):
                json_path = line.replace("__JSON_PATH__:", "").strip()
            else:
                yield f"data: {line}\n\n"

        raw_ndjson = ""
        if json_path and os.path.exists(json_path):
            with open(json_path) as f:
                raw_ndjson = f.read()

        # Best-effort cleanup of temp artifacts.
        try:
            if json_path and os.path.exists(json_path):
                os.remove(json_path)
        except Exception:
            pass

        try:
            if tmp_dir and os.path.isdir(tmp_dir):
                for name in os.listdir(tmp_dir):
                    path = os.path.join(tmp_dir, name)
                    try:
                        os.remove(path)
                    except Exception:
                        pass
                os.rmdir(tmp_dir)
        except Exception:
            pass

        parsed_metrics = parse_k6_ndjson(raw_ndjson)
        parsed_metrics["scorecard"] = calculate_score(parsed_metrics.get("metrics", {}))
        parsed_metrics["run_by"] = {
            "id": current_user.id,
            "username": current_user.username,
            "role": current_user.role,
        }

        # Security headers
        yield "data: PROGRESS:security_headers:start\n\n"
        security_headers = await fetch_security_headers(safe_url)
        parsed_metrics["security_headers"] = security_headers
        parsed_metrics["security_status"] = "ready" if "error" not in security_headers else "error"
        yield "data: PROGRESS:security_headers:done\n\n"

        # SSL scan
        yield "data: PROGRESS:ssl:start\n\n"
        ssl_result = await ssl_scan(safe_url)
        parsed_metrics["ssl"] = ssl_result
        yield "data: PROGRESS:ssl:done\n\n"

        # WebPageTest (Playwright)
        yield "data: PROGRESS:wpt:start\n\n"
        wpt_result = await run_webpagetest(safe_url)
        parsed_metrics["webpagetest"] = wpt_result
        yield "data: PROGRESS:wpt:done\n\n"

        # Lighthouse
        yield "data: PROGRESS:lighthouse:start\n\n"
        lighthouse_result = await run_lighthouse_with_retry(safe_url)
        parsed_metrics["lighthouse"] = lighthouse_result
        yield "data: PROGRESS:lighthouse:done\n\n"

        trimmed_metrics = _trim_metrics_for_llm(parsed_metrics, max_timeline_buckets=30)
        analysis = await analyze_with_retry(json.dumps(trimmed_metrics), user_id)

        pdf_path = os.path.join(RESULT_DIR, f"{run_id}-load.pdf")
        generate(pdf_path, req.project_name, safe_url, json.dumps(parsed_metrics), analysis)

        parsed_metrics["security_pdf_path"] = pdf_path

        async with SessionLocal() as session:
            session.add(
                LoadTest(
                    id=run_id,
                    project_name=req.project_name,
                    url=safe_url,
                    status="finished",
                    result_json=parsed_metrics,
                    analysis=analysis,
                    pdf_path=pdf_path,
                    user_id=current_user.id,
                    username=current_user.username,
                )
            )
            await session.commit()

        yield "data: __FINISHED__\n\n"
        yield f"data: RUN_ID:{run_id}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@app.post("/api/runjs")
async def run_js(
    project_name: str = Form(...),
    file: UploadFile = File(...),
    captcha_answer: int = Form(...),
    captcha_token: str = Form(...),
    captcha_timestamp: int = Form(...),
    x_api_key: str | None = Header(None),
    current_user: User = Depends(get_current_user),
):
    verify_key(x_api_key)

    if not ENABLE_SCRIPT_UPLOAD:
        raise HTTPException(status_code=403, detail="Script upload disabled")

    if not validate_captcha(captcha_answer, captcha_token, captcha_timestamp):
        raise HTTPException(status_code=400, detail="Invalid captcha")

    user_id = current_user.id

    async def event_stream():
        nonlocal user_id
        run_id = str(uuid.uuid4())
        target_url = extract_first_url(decoded)
        safe_target_url = None
        if target_url:
            try:
                safe_target_url = validate_target_url(target_url)
            except UnsafeUrlError:
                safe_target_url = None

        with tempfile.TemporaryDirectory() as tmpdir:
            script_path = os.path.join(tmpdir, "script.js")
            result_json_path = os.path.join(tmpdir, "result.json")

            with open(script_path, "w") as f:
                f.write(decoded)

            proc = await asyncio.create_subprocess_exec(
                "k6",
                "run",
                script_path,
                "--out",
                f"json={result_json_path}",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
            )

            assert proc.stdout is not None
            while True:
                line = await proc.stdout.readline()
                if not line:
                    break
                yield f"data: {line.decode(errors='ignore').strip()}\n\n"

            await proc.wait()

            raw_ndjson = ""
            if os.path.exists(result_json_path):
                with open(result_json_path) as f:
                    raw_ndjson = f.read()

        parsed_metrics = parse_k6_ndjson(raw_ndjson)
        parsed_metrics["scorecard"] = calculate_score(parsed_metrics.get("metrics", {}))
        parsed_metrics["run_by"] = {
            "id": current_user.id,
            "username": current_user.username,
            "role": current_user.role,
        }

        if not safe_target_url:
            parsed_metrics["security_status"] = "error"
            parsed_metrics["security_headers"] = {"error": "target url missing or unsafe"}
            parsed_metrics["ssl"] = {"status": "ERROR", "score": 0, "findings": [{"id": "no_target", "severity": "high", "message": "Target URL missing or unsafe"}]}
            parsed_metrics["webpagetest"] = {"status": "ERROR", "error": "Target URL missing or unsafe"}
            parsed_metrics["lighthouse"] = {"status": "ERROR", "error": "Target URL missing or unsafe"}
            yield "data: PROGRESS:security_headers:skip\n\n"
            yield "data: PROGRESS:ssl:skip\n\n"
            yield "data: PROGRESS:wpt:skip\n\n"
            yield "data: PROGRESS:lighthouse:skip\n\n"
        else:
            yield "data: PROGRESS:security_headers:start\n\n"
            security_headers = await fetch_security_headers(safe_target_url)
            parsed_metrics["security_headers"] = security_headers
            parsed_metrics["security_status"] = "ready" if "error" not in security_headers else "error"
            yield "data: PROGRESS:security_headers:done\n\n"

            yield "data: PROGRESS:ssl:start\n\n"
            ssl_result = await ssl_scan(safe_target_url)
            parsed_metrics["ssl"] = ssl_result
            yield "data: PROGRESS:ssl:done\n\n"

            yield "data: PROGRESS:wpt:start\n\n"
            wpt_result = await run_webpagetest(safe_target_url)
            parsed_metrics["webpagetest"] = wpt_result
            yield "data: PROGRESS:wpt:done\n\n"

            yield "data: PROGRESS:lighthouse:start\n\n"
            lighthouse_result = await run_lighthouse_with_retry(safe_target_url)
            parsed_metrics["lighthouse"] = lighthouse_result
            yield "data: PROGRESS:lighthouse:done\n\n"

        analysis = await analyze_with_retry(json.dumps(parsed_metrics), user_id)

        pdf_path = os.path.join(RESULT_DIR, f"{run_id}-load.pdf")
        generate(pdf_path, project_name, safe_target_url or "unknown", json.dumps(parsed_metrics), analysis)
        parsed_metrics["security_pdf_path"] = pdf_path

        async with SessionLocal() as session:
            session.add(
                LoadTest(
                    id=run_id,
                    project_name=project_name,
                    url=safe_target_url or "unknown",
                    status="finished",
                    result_json=parsed_metrics,
                    analysis=analysis,
                    pdf_path=pdf_path,
                    user_id=current_user.id,
                    username=current_user.username,
                )
            )
            await session.commit()

        yield "data: __FINISHED__\n\n"
        yield f"data: RUN_ID:{run_id}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@app.get("/api/result/list")
async def list_results(
    limit: int = 50,
    offset: int = 0,
    q: str | None = None,
    include_json: bool = False,
    x_api_key: str | None = Header(None),
    current_user: User = Depends(get_current_user),
):
    verify_key(x_api_key)

    limit = max(1, min(limit, 100))
    offset = max(0, offset)

    async with SessionLocal() as session:
        base = select(LoadTest)
        if current_user.role != "admin":
            base = base.where(LoadTest.user_id == current_user.id)
        if q:
            term = q.strip()
            if term:
                base = base.where(or_(LoadTest.id.contains(term), LoadTest.project_name.contains(term)))

        # Total count (for pagination)
        total_stmt = select(func.count()).select_from(base.subquery())
        total = int((await session.execute(total_stmt)).scalar() or 0)

        try:
            stmt = base.order_by(LoadTest.created_at.desc()).limit(limit).offset(offset)
            result = await session.execute(stmt)
            slice_tests = result.scalars().all()
        except OperationalError:
            fallback_limit = min(limit, 50)
            stmt = base.order_by(LoadTest.created_at.desc()).limit(fallback_limit).offset(offset)
            result = await session.execute(stmt)
            slice_tests = result.scalars().all()

        def summarize(t: LoadTest):
            payload = t.result_json or {}
            scorecard = payload.get("scorecard") or {}
            metrics = payload.get("metrics") or {}
            checks = metrics.get("checks") or {}

            security = payload.get("security_headers") or {}
            ssl_payload = payload.get("ssl") or {}
            wpt = payload.get("webpagetest") or {}
            lh = payload.get("lighthouse") or {}

            item = {
                "id": t.id,
                "project_name": t.project_name,
                "url": t.url,
                "status": t.status,
                "created_at": t.created_at,
                "run_by": payload.get("run_by") or {"id": t.user_id, "username": t.username},
                "score": scorecard.get("score"),
                "grade": scorecard.get("grade"),
                "error_rate": (checks.get("error_rate") if isinstance(checks, dict) else None),
                "security_grade": security.get("grade") or security.get("score"),
                "ssl_grade": ssl_payload.get("rating") or ssl_payload.get("ssllabs_grade"),
                "ssl_versions": ssl_payload.get("supported_versions") if isinstance(ssl_payload, dict) else None,
                "wpt_grade": wpt.get("grade"),
                "lighthouse_score": lh.get("score")
                if isinstance(lh, dict)
                else None,
            }

            # Support older lighthouse payload shape (categories.performance)
            if item["lighthouse_score"] is None and isinstance(lh, dict):
                cats = lh.get("categories") or {}
                item["lighthouse_score"] = cats.get("performance")

            if include_json:
                item["result_json"] = payload
            return item

        return {
            "items": [summarize(t) for t in slice_tests],
            "total": total,
            "limit": limit,
            "offset": offset,
            "q": q or "",
        }


@app.get("/api/result/{run_id}")
async def get_result(
    run_id: str,
    x_api_key: str | None = Header(None),
    current_user: User = Depends(get_current_user),
):
    verify_key(x_api_key)

    async with SessionLocal() as session:
        result = await session.get(LoadTest, run_id)
        if not result:
            raise HTTPException(status_code=404)

        if current_user.role != "admin" and result.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Forbidden")

        payload = result.result_json or {}
        return {
            "id": result.id,
            "project_name": result.project_name,
            "url": result.url,
            "analysis": result.analysis,
            "pdf": f"/api/download/{run_id}",
            "security_pdf": f"/api/download/{run_id}/security" if payload.get("security_pdf_path") else None,
            "metrics": payload.get("metrics", {}),
            "timeline": payload.get("timeline", {}),
            "scorecard": payload.get("scorecard", {}),
            "security_headers": payload.get("security_headers", {}),
            "security_status": payload.get("security_status", "pending"),
            "ssl": payload.get("ssl", {}),
            "webpagetest": payload.get("webpagetest", {}),
            "lighthouse": payload.get("lighthouse", {}),
            "run_by": payload.get("run_by") or {"id": result.user_id, "username": result.username},
        }


@app.get("/api/download/{run_id}")
async def download(
    run_id: str,
    x_api_key: str | None = Header(None),
    current_user: User = Depends(get_current_user),
):
    verify_key(x_api_key)

    async with SessionLocal() as session:
        result = await session.get(LoadTest, run_id)
        if not result:
            raise HTTPException(status_code=404)

        if current_user.role != "admin" and result.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Forbidden")

        # Check if PDF file exists before attempting to serve
        if not result.pdf_path or not os.path.exists(result.pdf_path):
            raise HTTPException(status_code=404, detail="PDF file not found")

        return FileResponse(
            path=result.pdf_path,
            media_type="application/pdf",
            filename=f"{run_id}.pdf",
            headers={"Content-Disposition": f'attachment; filename="{run_id}.pdf"'},
        )


@app.get("/api/download/{run_id}/security")
async def download_security(
    run_id: str,
    x_api_key: str | None = Header(None),
    current_user: User = Depends(get_current_user),
):
    verify_key(x_api_key)

    async with SessionLocal() as session:
        result = await session.get(LoadTest, run_id)
        if not result:
            raise HTTPException(status_code=404)

        if current_user.role != "admin" and result.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Forbidden")

        payload = result.result_json or {}
        pdf_path = payload.get("security_pdf_path")
        if not pdf_path or not os.path.exists(pdf_path):
            raise HTTPException(status_code=404)

        return FileResponse(
            path=pdf_path,
            media_type="application/pdf",
            filename=f"{run_id}-security.pdf",
            headers={"Content-Disposition": f'attachment; filename="{run_id}-security.pdf"'},
        )


@app.get("/api/captcha")
async def generate_captcha():
    a = random.randint(1, 20)
    b = random.randint(1, 20)
    ts = int(time.time())
    token = hashlib.sha256(f"{a+b}:{ts}:{CAPTCHA_SECRET}".encode()).hexdigest()
    return {"question": f"{a} + {b}", "timestamp": ts, "token": token}


def validate_captcha(answer: int, token: str, timestamp: int):
    if int(time.time()) - timestamp > 300:
        return False
    expected = hashlib.sha256(f"{answer}:{timestamp}:{CAPTCHA_SECRET}".encode()).hexdigest()
    return expected == token


@app.post("/api/resetdata")
async def reset_data(x_admin_key: str | None = Header(None)):
    verify_admin_key(x_admin_key)

    async with SessionLocal() as session:
        await session.execute(delete(LoadTest))
        await session.commit()

    return {"status": "ok"}
