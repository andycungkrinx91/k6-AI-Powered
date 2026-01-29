from fastapi import FastAPI, Header, HTTPException, UploadFile, File, Form, Request, Response
from fastapi.responses import StreamingResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from .schemas import RunRequest
from sqlalchemy import select, delete
from .k6_parser import parse_k6_ndjson
from .scoring import calculate_score
from .gemini import analyze
from .database import SessionLocal, engine, Base
from .models import LoadTest

import uuid
import os
import json
import tempfile
import re
import random
import hashlib
import time

# ================= ENV =================
IS_VERCEL = os.getenv("VERCEL") == "1"

API_KEY = os.getenv("BACKEND_API_KEY")
CAPTCHA_SECRET = os.getenv("CAPTCHA_SECRET")

RESULT_DIR = (
    tempfile.gettempdir()
    if IS_VERCEL
    else os.getenv("RESULT_DIR", "./results")
)

if not IS_VERCEL:
    os.makedirs(RESULT_DIR, exist_ok=True)

# ================= APP =================
app = FastAPI()

# ================= CORS =================
@app.options("/{path:path}")
async def preflight_handler(request: Request):
    return Response(status_code=204)
raw_origins = os.getenv("CORS_ORIGINS", "")
ALLOW_ORIGINS = [
    origin.strip()
    for origin in raw_origins.split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOW_ORIGINS or ["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ================= HEALTH =================
@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "platform": "vercel" if IS_VERCEL else "server"
    }

# ================= AUTO CREATE TABLE =================
@app.on_event("startup")
async def startup():
    if IS_VERCEL:
        return
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

# ================= SCRIPT SECURITY =================
SUSPICIOUS_PATTERNS = [
    r"\bchild_process\b",
    r"\bexec\s*\(",
    r"\bspawn\s*\(",
    r"\bfs\.",
    r"\brm\s+-rf\b",
    r"\bbash\b",
    r"\bsh\b",
    r"\bcurl\b",
    r"\bwget\b"
]

def is_malicious(content: str) -> bool:
    for pattern in SUSPICIOUS_PATTERNS:
        if re.search(pattern, content, re.IGNORECASE):
            return True
    return False

# ================= RUN TEST (SSE) =================
@app.post("/api/run")
async def run_test(req: RunRequest, x_api_key: str = Header(...)):

    verify_key(x_api_key)

    if IS_VERCEL:
        raise HTTPException(
            status_code=503,
            detail="k6 execution is disabled on Vercel"
        )

    # 🔥 lazy imports (KEEP FEATURE)
    from .k6_runner import run_k6_stream
    from .pdf_generator import generate

    async def event_stream():
        run_id = str(uuid.uuid4())
        json_path = None

        async for line in run_k6_stream(
            str(req.url),
            [s.dict() for s in req.stages]
        ):
            if line.startswith("__JSON_PATH__:"):
                json_path = line.replace("__JSON_PATH__:", "").strip()
            else:
                yield f"data: {line}\n\n"

        raw_ndjson = ""
        if json_path and os.path.exists(json_path):
            with open(json_path) as f:
                raw_ndjson = f.read()

        parsed = parse_k6_ndjson(raw_ndjson)
        parsed["scorecard"] = calculate_score(parsed.get("metrics", {}))

        analysis = await analyze(json.dumps(parsed))

        pdf_path = os.path.join(RESULT_DIR, f"{run_id}.pdf")

        generate(
            pdf_path,
            req.project_name,
            str(req.url),
            json.dumps(parsed),
            analysis
        )

        async with SessionLocal() as session:
            session.add(LoadTest(
                id=run_id,
                project_name=req.project_name,
                url=str(req.url),
                status="finished",
                result_json=parsed,
                analysis=analysis,
                pdf_path=pdf_path
            ))
            await session.commit()

        yield "data: __FINISHED__\n\n"
        yield f"data: RUN_ID:{run_id}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")

# ================= RUN CUSTOM JS (SSE) =================
@app.post("/api/runjs")
async def run_js(
    project_name: str = Form(...),
    file: UploadFile = File(...),
    captcha_answer: int = Form(...),
    captcha_token: str = Form(...),
    captcha_timestamp: int = Form(...),
    x_api_key: str = Header(...)
):

    verify_key(x_api_key)

    if IS_VERCEL:
        raise HTTPException(
            status_code=503,
            detail="Custom k6 execution disabled on Vercel"
        )

    if not validate_captcha(captcha_answer, captcha_token, captcha_timestamp):
        raise HTTPException(status_code=400, detail="Invalid captcha")

    decoded = (await file.read()).decode("utf-8", errors="ignore")

    if is_malicious(decoded):
        raise HTTPException(status_code=400, detail="Suspicious script detected")

    import subprocess  # 🔥 lazy import

    async def event_stream():
        run_id = str(uuid.uuid4())

        with tempfile.TemporaryDirectory() as tmpdir:
            script_path = os.path.join(tmpdir, "script.js")
            result_json_path = os.path.join(tmpdir, "result.json")

            with open(script_path, "w") as f:
                f.write(decoded)

            process = subprocess.Popen(
                ["k6", "run", script_path, "--out", f"json={result_json_path}"],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True
            )

            for line in iter(process.stdout.readline, ""):
                yield f"data: {line.strip()}\n\n"

            process.wait()

        yield "data: __FINISHED__\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")

# ================= CAPTCHA =================
@app.get("/api/captcha")
async def generate_captcha():
    a, b = random.randint(1, 20), random.randint(1, 20)
    ts = int(time.time())
    token = hashlib.sha256(f"{a+b}:{ts}:{CAPTCHA_SECRET}".encode()).hexdigest()
    return {"question": f"{a} + {b}", "timestamp": ts, "token": token}

def validate_captcha(answer: int, token: str, timestamp: int):
    if int(time.time()) - timestamp > 300:
        return False
    expected = hashlib.sha256(f"{answer}:{timestamp}:{CAPTCHA_SECRET}".encode()).hexdigest()
    return expected == token

# ================= RESET =================
@app.post("/api/resetdata")
async def reset_data(x_api_key: str = Header(...)):

    verify_key(x_api_key)

    async with SessionLocal() as session:
        result = await session.execute(select(LoadTest))
        for r in result.scalars():
            if r.pdf_path and os.path.exists(r.pdf_path):
                try:
                    os.remove(r.pdf_path)
                except Exception:
                    pass

        await session.execute(delete(LoadTest))
        await session.commit()

    return {"status": "ok"}
