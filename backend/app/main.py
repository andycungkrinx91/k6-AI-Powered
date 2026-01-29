from fastapi import FastAPI, Header, HTTPException, UploadFile, File, Form
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
from . import models
from fastapi.responses import FileResponse
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

# ================= HEALTH CHECK ===================
@app.get("/api/health")
def health_check():
    return {"status": "Okay"}

# ================= CORS =================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

API_KEY = os.getenv("BACKEND_API_KEY")
RESULT_DIR = os.getenv("RESULT_DIR", "./results")
CAPTCHA_SECRET = os.getenv("CAPTCHA_SECRET")
os.makedirs(RESULT_DIR, exist_ok=True)

# ================= AUTO CREATE TABLE =================
@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

# ================= AUTH =================
def verify_key(x_api_key: str):
    if x_api_key != API_KEY:
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
    for pattern in SUSPICIOUS_PATTERNS:
        if re.search(pattern, content, re.IGNORECASE):
            print("Blocked by pattern:", pattern)
            return True
    return False

# ================= VERCEL CONFIG ===================
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)


# ================= RUN TEST (SSE) =================
@app.post("/api/run")
async def run_test(req: RunRequest, x_api_key: str = Header(...)):

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

        # Read k6 output
        if json_path and os.path.exists(json_path):
            with open(json_path) as f:
                raw_ndjson = f.read()
        else:
            raw_ndjson = ""

        parsed_metrics = parse_k6_ndjson(raw_ndjson)

        metrics = parsed_metrics.get("metrics", {})
        scorecard = calculate_score(metrics)
        parsed_metrics["scorecard"] = scorecard

        structured_json = json.dumps(parsed_metrics)

        analysis = await analyze(structured_json)

        pdf_filename = f"{run_id}.pdf"
        pdf_path = os.path.join(RESULT_DIR, pdf_filename)

        generate(
            pdf_path,
            req.project_name,
            str(req.url),
            structured_json,
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

        yield f"data: __FINISHED__\n\n"
        yield f"data: RUN_ID:{run_id}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")

# ================= LIST RESULTS =================
@app.get("/api/result/list")
async def list_results(x_api_key: str = Header(...)):

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
async def get_result(run_id: str, x_api_key: str = Header(...)):

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
async def download(run_id: str, x_api_key: str = Header(...)):

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
    x_api_key: str = Header(...)
):

    verify_key(x_api_key)
    if not validate_captcha(captcha_answer, captcha_token, captcha_timestamp):
        raise HTTPException(status_code=400, detail="Invalid captcha")

    if not file.filename.endswith(".js"):
        raise HTTPException(status_code=400, detail="Only .js files allowed")

    content = await file.read()

    if len(content) > 2 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File too large (max 2MB)")

    decoded = content.decode("utf-8", errors="ignore")

    if is_malicious(decoded):
        print("BLOCKED SCRIPT CONTENT:")
        raise HTTPException(status_code=400, detail="Suspicious script detected")

    async def event_stream():

        run_id = str(uuid.uuid4())

        with tempfile.TemporaryDirectory() as tmpdir:

            script_path = os.path.join(tmpdir, "script.js")
            result_json_path = os.path.join(tmpdir, "result.json")

            with open(script_path, "w") as f:
                f.write(decoded)

            process = subprocess.Popen(
                [
                    "k6",
                    "run",
                    script_path,
                    "--out",
                    f"json={result_json_path}"
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True
            )

            for line in iter(process.stdout.readline, ""):
                yield f"data: {line.strip()}\n\n"

            try:
                process.wait(timeout=600)
            except subprocess.TimeoutExpired:
                process.kill()
                yield "data: ERROR: Execution timeout\n\n"

                async with SessionLocal() as session:
                    session.add(LoadTest(
                        id=run_id,
                        project_name=project_name,
                        url="Custom Script",
                        status="failed",
                        result_json={},
                        analysis="Execution timeout",
                        pdf_path=""
                    ))
                    await session.commit()

                yield "data: __FAILED__\n\n"
                return

            exit_code = process.returncode

            # ---- Structured Exit Code Handling ----

            if exit_code not in [0, 99]:

                error_message = f"k6 execution failed with exit code {exit_code}"

                yield f"data: ERROR: {error_message}\n\n"

                async with SessionLocal() as session:
                    session.add(LoadTest(
                        id=run_id,
                        project_name=project_name,
                        url="Custom Script",
                        status="failed",
                        result_json={},
                        analysis=error_message,
                        pdf_path=""
                    ))
                    await session.commit()

                yield "data: __FAILED__\n\n"
                return

            # Threshold failure (99) is valid execution
            if not os.path.exists(result_json_path):
                yield "data: ERROR: k6 did not produce output\n\n"
                yield "data: __FAILED__\n\n"
                return

            with open(result_json_path) as f:
                raw_ndjson = f.read()

        # ---- NORMAL PIPELINE CONTINUES ----
        parsed_metrics = parse_k6_ndjson(raw_ndjson)

        metrics = parsed_metrics.get("metrics", {})
        #print("METRICS:", metrics)
        scorecard = calculate_score(metrics)
        #print("PARSED METRICS:", parsed_metrics.keys())
        parsed_metrics["scorecard"] = scorecard

        structured_json = json.dumps(parsed_metrics)

        analysis = await analyze(structured_json)

        pdf_filename = f"{run_id}.pdf"
        pdf_path = os.path.join(RESULT_DIR, pdf_filename)

        generate(
            pdf_path,
            project_name,
            "Custom Script",
            structured_json,
            analysis
        )

        async with SessionLocal() as session:
            session.add(LoadTest(
                id=run_id,
                project_name=project_name,
                url="Custom Script",
                status="finished",
                result_json=parsed_metrics,
                analysis=analysis,
                pdf_path=pdf_path
            ))
            await session.commit()

        yield "data: __FINISHED__\n\n"
        yield f"data: RUN_ID:{run_id}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")

# ================= SIMPLE CAPTCHA =================
@app.get("/api/captcha")
async def generate_captcha():
    a = random.randint(1, 20)
    b = random.randint(1, 20)
    result = a + b
    timestamp = int(time.time())

    token_raw = f"{result}:{timestamp}:{CAPTCHA_SECRET}"
    token = hashlib.sha256(token_raw.encode()).hexdigest()

    return {
        "question": f"{a} + {b}",
        "timestamp": timestamp,
        "token": token
    }


def validate_captcha(answer: int, token: str, timestamp: int):
    # expire captcha after 5 minutes
    if int(time.time()) - int(timestamp) > 300:
        return False

    expected_raw = f"{answer}:{timestamp}:{CAPTCHA_SECRET}"
    expected_token = hashlib.sha256(expected_raw.encode()).hexdigest()

    return expected_token == token

# ================= RESET DATA =================
@app.post("/api/resetdata")
async def reset_data(x_api_key: str = Header(...)):

    verify_key(x_api_key)

    async with SessionLocal() as session:

        # Get all pdf paths first
        result = await session.execute(select(LoadTest))
        records = result.scalars().all()

        for r in records:
            if r.pdf_path and os.path.exists(r.pdf_path):
                try:
                    os.remove(r.pdf_path)
                except Exception:
                    pass

        # Delete DB rows
        await session.execute(delete(LoadTest))
        await session.commit()

    return {"status": "All data reset successfully"}