import asyncio
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
from datetime import datetime, timezone

import httpx
from fastapi import FastAPI, Header, HTTPException, UploadFile, File, Form, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, FileResponse
from sqlalchemy import select, delete
from sqlalchemy.exc import OperationalError

from .database import SessionLocal, engine, Base
from .gemini import analyze
from .k6_parser import parse_k6_ndjson
from .k6_runner import run_k6_stream
from .models import LoadTest
from .pdf_generator import generate
from .schemas import RunRequest
from .scoring import calculate_score

app = FastAPI()

# ================= ENV =================
API_KEY = os.getenv("BACKEND_API_KEY")
CAPTCHA_SECRET = os.getenv("CAPTCHA_SECRET")
RESULT_DIR = os.getenv("RESULT_DIR", "./results")
USER_AGENT = os.getenv("USER_AGENT", "k6-ai-powerd-agent")
os.makedirs(RESULT_DIR, exist_ok=True)


async def analyze_with_retry(payload: str, retries: int = 3, delay: float = 2.0):
    last_error = None
    for attempt in range(1, retries + 1):
        try:
            return await analyze(payload)
        except Exception as exc:  # noqa: BLE001
            last_error = exc
            msg = str(exc).lower()
            if ("503" in msg or "unavailable" in msg or "overloaded" in msg) and attempt < retries:
                await asyncio.sleep(delay * attempt)
                continue
            break
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


@app.on_event("shutdown")
async def shutdown_event():
    await engine.dispose()


@app.post("/api/run")
async def run_test(req: RunRequest, x_api_key: str | None = Header(None)):
    verify_key(x_api_key)

    async def event_stream():
        run_id = str(uuid.uuid4())
        json_path = None

        async for line in run_k6_stream(str(req.url), [s.dict() for s in req.stages]):
            if line.startswith("__JSON_PATH__:"):
                json_path = line.replace("__JSON_PATH__:", "").strip()
            else:
                yield f"data: {line}\n\n"

        raw_ndjson = ""
        if json_path and os.path.exists(json_path):
            with open(json_path) as f:
                raw_ndjson = f.read()

        parsed_metrics = parse_k6_ndjson(raw_ndjson)
        parsed_metrics["scorecard"] = calculate_score(parsed_metrics.get("metrics", {}))

        # Security headers
        yield "data: PROGRESS:security_headers:start\n\n"
        security_headers = await fetch_security_headers(str(req.url))
        parsed_metrics["security_headers"] = security_headers
        parsed_metrics["security_status"] = "ready" if "error" not in security_headers else "error"
        yield "data: PROGRESS:security_headers:done\n\n"

        # SSL scan
        yield "data: PROGRESS:ssl:start\n\n"
        ssl_result = await ssl_scan(str(req.url))
        parsed_metrics["ssl"] = ssl_result
        yield "data: PROGRESS:ssl:done\n\n"

        # WebPageTest (Playwright)
        yield "data: PROGRESS:wpt:start\n\n"
        wpt_result = await run_webpagetest(str(req.url))
        parsed_metrics["webpagetest"] = wpt_result
        yield "data: PROGRESS:wpt:done\n\n"

        # Lighthouse
        yield "data: PROGRESS:lighthouse:start\n\n"
        lighthouse_result = await run_lighthouse_with_retry(str(req.url))
        parsed_metrics["lighthouse"] = lighthouse_result
        yield "data: PROGRESS:lighthouse:done\n\n"

        analysis = await analyze_with_retry(json.dumps(parsed_metrics))

        pdf_path = os.path.join(RESULT_DIR, f"{run_id}-load.pdf")
        generate(pdf_path, req.project_name, str(req.url), json.dumps(parsed_metrics), analysis)

        parsed_metrics["security_pdf_path"] = pdf_path

        async with SessionLocal() as session:
            session.add(
                LoadTest(
                    id=run_id,
                    project_name=req.project_name,
                    url=str(req.url),
                    status="finished",
                    result_json=parsed_metrics,
                    analysis=analysis,
                    pdf_path=pdf_path,
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
):
    verify_key(x_api_key)

    if not validate_captcha(captcha_answer, captcha_token, captcha_timestamp):
        raise HTTPException(status_code=400, detail="Invalid captcha")

    decoded = (await file.read()).decode("utf-8", errors="ignore")
    if is_malicious(decoded):
        raise HTTPException(status_code=400, detail="Suspicious script detected")

    async def event_stream():
        run_id = str(uuid.uuid4())
        target_url = extract_first_url(decoded)

        with tempfile.TemporaryDirectory() as tmpdir:
            script_path = os.path.join(tmpdir, "script.js")
            result_json_path = os.path.join(tmpdir, "result.json")

            with open(script_path, "w") as f:
                f.write(decoded)

            process = subprocess.Popen(
                ["k6", "run", script_path, "--out", f"json={result_json_path}"],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
            )

            for line in iter(process.stdout.readline, ""):
                yield f"data: {line.strip()}\n\n"

            process.wait()

            raw_ndjson = ""
            if os.path.exists(result_json_path):
                with open(result_json_path) as f:
                    raw_ndjson = f.read()

        parsed_metrics = parse_k6_ndjson(raw_ndjson)
        parsed_metrics["scorecard"] = calculate_score(parsed_metrics.get("metrics", {}))

        if not target_url:
            parsed_metrics["security_status"] = "error"
            parsed_metrics["security_headers"] = {"error": "target url not detected"}
            parsed_metrics["ssl"] = {"status": "ERROR", "score": 0, "findings": [{"id": "no_target", "severity": "high", "message": "Target URL not detected"}]}
            parsed_metrics["webpagetest"] = {"status": "ERROR", "error": "Target URL not detected"}
            parsed_metrics["lighthouse"] = {"status": "ERROR", "error": "Target URL not detected"}
            yield "data: PROGRESS:security_headers:skip\n\n"
            yield "data: PROGRESS:ssl:skip\n\n"
            yield "data: PROGRESS:wpt:skip\n\n"
            yield "data: PROGRESS:lighthouse:skip\n\n"
        else:
            yield "data: PROGRESS:security_headers:start\n\n"
            security_headers = await fetch_security_headers(target_url)
            parsed_metrics["security_headers"] = security_headers
            parsed_metrics["security_status"] = "ready" if "error" not in security_headers else "error"
            yield "data: PROGRESS:security_headers:done\n\n"

            yield "data: PROGRESS:ssl:start\n\n"
            ssl_result = await ssl_scan(target_url)
            parsed_metrics["ssl"] = ssl_result
            yield "data: PROGRESS:ssl:done\n\n"

            yield "data: PROGRESS:wpt:start\n\n"
            wpt_result = await run_webpagetest(target_url)
            parsed_metrics["webpagetest"] = wpt_result
            yield "data: PROGRESS:wpt:done\n\n"

            yield "data: PROGRESS:lighthouse:start\n\n"
            lighthouse_result = await run_lighthouse_with_retry(target_url)
            parsed_metrics["lighthouse"] = lighthouse_result
            yield "data: PROGRESS:lighthouse:done\n\n"

        analysis = await analyze_with_retry(json.dumps(parsed_metrics))

        pdf_path = os.path.join(RESULT_DIR, f"{run_id}-load.pdf")
        generate(pdf_path, project_name, target_url or "unknown", json.dumps(parsed_metrics), analysis)
        parsed_metrics["security_pdf_path"] = pdf_path

        async with SessionLocal() as session:
            session.add(
                LoadTest(
                    id=run_id,
                    project_name=project_name,
                    url=target_url or "unknown",
                    status="finished",
                    result_json=parsed_metrics,
                    analysis=analysis,
                    pdf_path=pdf_path,
                )
            )
            await session.commit()

        yield "data: __FINISHED__\n\n"
        yield f"data: RUN_ID:{run_id}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@app.get("/api/result/list")
async def list_results(limit: int = 50, offset: int = 0, x_api_key: str | None = Header(None)):
    verify_key(x_api_key)

    limit = max(1, min(limit, 100))
    offset = max(0, offset)

    async with SessionLocal() as session:
        try:
            stmt = (
                select(LoadTest)
                .order_by(LoadTest.created_at.desc())
                .limit(limit)
                .offset(offset)
            )
            result = await session.execute(stmt)
            slice_tests = result.scalars().all()
        except OperationalError:
            fallback_limit = min(limit, 50)
            stmt = select(LoadTest).limit(fallback_limit).offset(offset)
            result = await session.execute(stmt)
            slice_tests = result.scalars().all()
        return [
            {
                "id": t.id,
                "project_name": t.project_name,
                "url": t.url,
                "status": t.status,
                "created_at": t.created_at,
                "result_json": t.result_json,
            }
            for t in slice_tests
        ]


@app.get("/api/result/{run_id}")
async def get_result(run_id: str, x_api_key: str | None = Header(None)):
    verify_key(x_api_key)

    async with SessionLocal() as session:
        result = await session.get(LoadTest, run_id)
        if not result:
            raise HTTPException(status_code=404)

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
        }


@app.get("/api/download/{run_id}")
async def download(run_id: str, x_api_key: str | None = Header(None)):
    verify_key(x_api_key)

    async with SessionLocal() as session:
        result = await session.get(LoadTest, run_id)
        if not result:
            raise HTTPException(status_code=404)

        return FileResponse(
            path=result.pdf_path,
            media_type="application/pdf",
            filename=f"{run_id}.pdf",
            headers={"Content-Disposition": f'attachment; filename="{run_id}.pdf"'},
        )


@app.get("/api/download/{run_id}/security")
async def download_security(run_id: str, x_api_key: str | None = Header(None)):
    verify_key(x_api_key)

    async with SessionLocal() as session:
        result = await session.get(LoadTest, run_id)
        if not result:
            raise HTTPException(status_code=404)

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
async def reset_data(x_api_key: str | None = Header(None)):
    verify_key(x_api_key)

    async with SessionLocal() as session:
        await session.execute(delete(LoadTest))
        await session.commit()

    return {"status": "ok"}
