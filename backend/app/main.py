from fastapi import FastAPI, Header, HTTPException, UploadFile, File, Form, Request, Response
from fastapi.responses import StreamingResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from .schemas import RunRequest
from sqlalchemy import select, delete
from .k6_runner import run_k6_stream
from .k6_parser import parse_k6_ndjson
from .scoring import calculate_score
from .gemini import analyze
from .pdf_generator import generate
from .database import SessionLocal, engine, Base
from .models import LoadTest
import uuid
import os
import json
import tempfile
import subprocess
import re
import random
import hashlib
import time

app = FastAPI()

# ================= CORS (FROM .env) =================
raw_origins = os.getenv("CORS_ORIGINS", "http://k6.local,http://localhost:3000")
ALLOW_ORIGINS = [o.strip() for o in raw_origins.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOW_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ================= OPTIONS (PRE-FLIGHT) =================
@app.options("/{path:path}")
async def preflight_handler(request: Request):
    return Response(status_code=204)

API_KEY = os.getenv("BACKEND_API_KEY")
CAPTCHA_SECRET = os.getenv("CAPTCHA_SECRET")
RESULT_DIR = os.getenv("RESULT_DIR", "./results")
os.makedirs(RESULT_DIR, exist_ok=True)

# ================= AUTO CREATE TABLE =================
@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

# ================= AUTH =================
def verify_key(x_api_key: str | None):
    if not x_api_key or x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized")

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
    return any(re.search(p, content, re.IGNORECASE) for p in SUSPICIOUS_PATTERNS)

# ================= RUN TEST (SSE) =================
@app.post("/api/run")
async def run_test(
    req: RunRequest,
    x_api_key: str | None = Header(None)
):
    verify_key(x_api_key)

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

        parsed_metrics = parse_k6_ndjson(raw_ndjson)
        parsed_metrics["scorecard"] = calculate_score(
            parsed_metrics.get("metrics", {})
        )

        analysis = await analyze(json.dumps(parsed_metrics))

        pdf_path = os.path.join(RESULT_DIR, f"{run_id}.pdf")
        generate(
            pdf_path,
            req.project_name,
            str(req.url),
            json.dumps(parsed_metrics),
            analysis
        )

        async with SessionLocal() as session:
            session.add(LoadTest(
                id=run_id,
                project_name=req.project_name,
                url=str(req.url),
                status="finished",
                result_json=parsed_metrics,
                analysis=analysis,
                pdf_path=pdf_path
            ))
            await session.commit()

        yield "data: __FINISHED__\n\n"
        yield f"data: RUN_ID:{run_id}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")

# ================= LIST RESULTS =================
@app.get("/api/result/list")
async def list_results(x_api_key: str | None = Header(None)):
    verify_key(x_api_key)

    async with SessionLocal() as session:
        result = await session.execute(
            select(LoadTest).order_by(LoadTest.created_at.desc())
        )
        tests = result.scalars().all()

        return [
            {
                "id": t.id,
                "project_name": t.project_name,
                "url": t.url,
                "status": t.status,
                "created_at": t.created_at,
                "result_json": t.result_json
            }
            for t in tests
        ]

# ================= GET RESULT =================
@app.get("/api/result/{run_id}")
async def get_result(
    run_id: str,
    x_api_key: str | None = Header(None)
):
    verify_key(x_api_key)

    async with SessionLocal() as session:
        result = await session.get(LoadTest, run_id)
        if not result:
            raise HTTPException(status_code=404)

        return {
            "id": result.id,
            "project_name": result.project_name,
            "url": result.url,
            "analysis": result.analysis,
            "pdf": f"/api/download/{run_id}",
            "metrics": result.result_json.get("metrics", {}),
            "timeline": result.result_json.get("timeline", {}),
            "scorecard": result.result_json.get("scorecard", {})
        }

# ================= DOWNLOAD PDF =================
@app.get("/api/download/{run_id}")
async def download(
    run_id: str,
    x_api_key: str | None = Header(None)
):
    verify_key(x_api_key)

    async with SessionLocal() as session:
        result = await session.get(LoadTest, run_id)
        if not result:
            raise HTTPException(status_code=404)

        return FileResponse(
            path=result.pdf_path,
            media_type="application/pdf",
            filename=f"{run_id}.pdf",
            headers={
                "Content-Disposition": f'attachment; filename="{run_id}.pdf"'
            }
        )

# ================= RUN CUSTOM JS SCRIPT (SSE) =================
@app.post("/api/runjs")
async def run_js(
    project_name: str = Form(...),
    file: UploadFile = File(...),
    captcha_answer: int = Form(...),
    captcha_token: str = Form(...),
    captcha_timestamp: int = Form(...),
    x_api_key: str | None = Header(None)
):
    verify_key(x_api_key)

    if not validate_captcha(captcha_answer, captcha_token, captcha_timestamp):
        raise HTTPException(status_code=400, detail="Invalid captcha")

    decoded = (await file.read()).decode("utf-8", errors="ignore")
    if is_malicious(decoded):
        raise HTTPException(status_code=400, detail="Suspicious script detected")

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
        yield f"data: RUN_ID:{run_id}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")

# ================= CAPTCHA =================
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
    expected = hashlib.sha256(
        f"{answer}:{timestamp}:{CAPTCHA_SECRET}".encode()
    ).hexdigest()
    return expected == token

# ================= RESET DATA =================
@app.post("/api/resetdata")
async def reset_data(x_api_key: str | None = Header(None)):
    verify_key(x_api_key)

    async with SessionLocal() as session:
        await session.execute(delete(LoadTest))
        await session.commit()

    return {"status": "ok"}
