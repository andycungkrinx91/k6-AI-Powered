# K6 AI Performance Intelligence – Backend

Enterprise-grade Load Testing Intelligence Platform powered by:

- FastAPI (Async)
- k6 Execution Engine
- MySQL 8 (Async SQLAlchemy)
- Gemini AI Engineering Analysis
- ReportLab PDF Generator
- Server-Sent Events (SSE) Streaming
- Docker / VM Ready Deployment

---

# 🚀 Core Features

## 🔹 Load Test Builder Mode
- Dynamically generate k6 test from API request
- Stream real-time execution logs (SSE)
- Auto score calculation (SLA-aware)
- AI performance analysis
- Enterprise PDF report

## 🔹 Custom k6 Script Mode
- Optional `.js` file upload mode (disabled by default)
- Max upload size configurable via `MAX_UPLOAD_BYTES`
- Suspicious script detection
- Server-side CAPTCHA validation
- k6 structured exit code handling
- Threshold failure detection (exit code 99 supported)
- Same scoring + AI + PDF pipeline

## 🔹 Security Header Scanner (built-in)
- Async HTTP header scan after k6 run
- Checks: CSP, Permissions-Policy, Referrer-Policy, HSTS, X-Content-Type-Options, X-Frame-Options
- Grades + present/total, recommendations, raw headers snapshot
- Included in result JSON and merged PDF

## 🔹 SSL/TLS Analysis (built-in)
- Runs after header scan, against the same target
- Probes TLS 1.3/1.2 support, flags legacy 1.1/1.0
- Captures negotiated ciphers, key algo/size, cert subject/issuer/SAN/validity
- Sub-scores (protocol / key exchange / cipher strength), letter rating, findings
- Included in result JSON and merged PDF
 - No external SSL Labs dependency; home-grown analyzer aiming for SSL Labs-like detail

## 🔹 WebPageTest (Playwright, built-in)
- Headless Chromium + custom `k6-ai-powerd-agent` User-Agent
- Simulated Fast 3G + CPU throttle, first + repeat view (cache)
- Captures TTFB, DCL, Load, FP, FCP, LCP, CLS, INP
- Resource waterfall (top 40), transfer sizes, elapsed time, TBT, Speed Index heuristic, page weight, total requests
- Auto WPT-style composite score + grade, first/repeat summaries in PDF
- Stored in DB, exposed via API, and rendered in PDF

## 🔹 Lighthouse (built-in)
- Runs headless via Playwright Chromium
- Captures category scores (Performance/Accessibility/Best Practices/SEO/PWA if present)
- Shows key metrics (FCP, LCP, CLS, TBT, TTI, Speed Index)
- Included in API payloads and PDF

## 🔹 AI Analysis (Gemini)
- Multi API key rotation
- Random key selection
- Auto retry (429 / 503)
- 3 retry attempts using different keys

## 🔹 Database
- MySQL 8
- Auto table creation on startup
- Async SQLAlchemy engine
- JSON metric storage

## 🔹 Admin Utilities
- Reset all test data via CLI-only endpoint

---

# 📁 Project Structure

```
backend
├── app
│   ├── database.py
│   ├── gemini.py
│   ├── __init__.py
│   ├── k6_parser.py
│   ├── k6_runner.py
│   ├── main.py
│   ├── models.py
│   ├── pdf_generator.py
│   ├── schemas.py
│   └── scoring.py
├── assets
│   ├── fonts
│   │   ├── Montserrat-Bold.ttf
│   │   └── Montserrat-Regular.ttf
│   ├── logo2.png
│   ├── logo3.png
│   └── logo.png
├── Dockerfile
└── requirements.txt
```

---

# 🔐 Environment Variables

Create `.env` inside backend root.

Example:

```
DATABASE_URL=mysql+aiomysql://k6user:k6password@mysql:3306/k6ai
BACKEND_API_KEY=super_secret_key
BACKEND_ADMIN_KEY=super_secret_admin_key  # required for /api/resetdata via x-admin-key
CAPTCHA_SECRET=your_internal_secret
RESULT_DIR=/app/results
CORS_ORIGINS=http://localhost,http://localhost:3000
USER_AGENT=k6-ai-powerd-agent
LIGHTHOUSE_CHROMIUM_FLAGS=--headless=new --no-sandbox --disable-dev-shm-usage --disable-gpu

# Auth (JWT)
# IMPORTANT: set a long random secret in production.
AUTH_SECRET=change_me_to_a_long_random_secret
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# Initial admin bootstrap (kept in sync on backend startup)
INITIAL_ADMIN_USERNAME=admin
INITIAL_ADMIN_EMAIL=admin@example.com
INITIAL_ADMIN_PASSWORD=change_me

Admin bootstrap behavior:

- On startup, backend ensures an admin user exists for `INITIAL_ADMIN_USERNAME` / `INITIAL_ADMIN_EMAIL`.
- If not found, it creates the admin.
- If found but password differs from env, it rotates the password to match `INITIAL_ADMIN_PASSWORD`.
- If found but role/email differ from env, it updates them.

# Gemini (Multiple Keys Supported)
GEMINI_API_KEYS=key1,key2,key3
# Use an available Gemini model id for your account/region.
# Example: gemini-2.5-flash
GEMINI_MODEL=gemini-2.5-flash
GEMINI_MAX_TOKENS=8192
GEMINI_TEMPERATURE=0.2

# Security / SSRF
ALLOWED_TARGET_PORTS=80,443

# Script upload (dangerous; disabled by default)
ENABLE_SCRIPT_UPLOAD=false
MAX_UPLOAD_BYTES=200000

# Execution limits
K6_TIMEOUT_SECONDS=180

# SLA Thresholds
THRESHOLD_SUCCESS_RATE=0.95
THRESHOLD_ERROR_RATE=0.1
THRESHOLD_P90_MS=1500
```

⚠️ Never commit `.env` to version control.

---

# 🔑 Authentication & Access Control

- **JWT login**: `POST /api/auth/login` accepts `{ identifier, password }` (username or email) and returns `access_token` + user payload.
- **Role-aware APIs**: Each request now requires **both** the backend API key (`x-api-key`) and a `Bearer` token in the `Authorization` header; tokens are valid for `ACCESS_TOKEN_EXPIRE_MINUTES`.
- **Administrator**: Can seed the first admin via `INITIAL_ADMIN_*` env vars, list accounts (`GET /api/auth/users`), and create new admins/users (`POST /api/auth/users`).
- **Normal users**: Can only run load tests, upload scripts (if enabled), and view their personal results.
- **Profile**: Users update their password via `PUT /api/profile/password`.
- **Auditing**: Every saved load test now stores `user_id`/`username` and exposes `run_by` inside the result JSON for easier filtering.

# 🐳 Run with Docker

## Build

```
docker build -t k6-ai-backend .
```

## Run

```
docker run -d \
  --name k6-ai-backend \
  -p 8000:8000 \
  --env-file .env \
  k6-ai-backend
```

Backend available at:

```
http://localhost:8000
```

---

# 🐳 Docker Compose (MySQL + Backend)

```
version: "3.9"

services:
  mysql:
    image: mysql:8
    environment:
      MYSQL_ROOT_PASSWORD: rootPassword
      MYSQL_DATABASE: k6ai
      MYSQL_USER: k6user
      MYSQL_PASSWORD: k6password
    ports:
      - "3306:3306"

  backend:
    build: .
    env_file: .env
    volumes:
      - ./results:/app/results
    depends_on:
      - mysql
    ports:
      - "8000:8000"
```

Use a dedicated host results folder and map it to the same path as `RESULT_DIR` inside the container (example above assumes `RESULT_DIR=/app/results`).

Run:

```
docker compose up -d --build
```

---

# 🛠 Local Development

```
pip install -r requirements.txt
python -m playwright install --with-deps chromium
# Optional (only needed if you enable/require Lighthouse scans on this machine)
npm install -g lighthouse
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Authentication:

- Login endpoint: `POST /api/auth/login` (username/email + password)
- Use the returned Bearer token for API calls: `Authorization: Bearer <token>`
- Admin-only user management:
  - `GET /api/auth/users`
  - `POST /api/auth/users`

VM (no Docker):

```
bash scripts/run-backend-ubuntu.sh
```

Frontend (VM, no Docker):

```
cp scripts/.env.example scripts/.env
bash scripts/run-frontend-ubuntu.sh
```

---

# 📡 API Endpoints

## ▶ Run Builder Mode

POST `/api/run`

---

## ▶ Run Custom JS Script

POST `/api/runjs`

Note: disabled by default (`ENABLE_SCRIPT_UPLOAD=false`); upload size limit is configurable via `MAX_UPLOAD_BYTES`.

Requires:
- project_name
- file (.js)
- captcha_answer
- captcha_token
- captcha_timestamp

---

## ▶ Get Result

GET `/api/result/{run_id}`

---

## ▶ List Results

GET `/api/result/list`

---

## ▶ Download PDF

GET `/api/download/{run_id}`

---

## ▶ Reset All Data (CLI Only)

POST `/api/resetdata`

⚠️ This endpoint:
- Deletes all database records
- Does not remove files on disk
- Requires `BACKEND_ADMIN_KEY` via `x-admin-key`

---

# 🧠 AI Multi-Key Logic

- Keys loaded from `GEMINI_API_KEYS`
- Random key chosen per request
- If Gemini returns:
  - 429 (rate limit)
  - 503 (service unavailable)
- Backend retries up to 3 times
- Each retry uses a different key

---

# ⚙️ Scoring System

Scoring is dynamic via `.env`:

- SUCCESS_RATE >= THRESHOLD_SUCCESS_RATE
- ERROR_RATE <= THRESHOLD_ERROR_RATE
- P90 <= THRESHOLD_P90_MS

Grades:
- A (Excellent)
- B (Good)
- C (Needs Improvement)
- F (Fail)

Exit code 99 (threshold failure) is treated as valid execution.

---

# 🔐 Security Model

- API Key required on all endpoints
- Server-side CAPTCHA validation
- Suspicious JS script detection
- Script upload disabled by default (`ENABLE_SCRIPT_UPLOAD=false`)
- Max upload size configurable via `MAX_UPLOAD_BYTES`
- Structured exit code handling
- Execution timeout protection
- SSE streaming isolation

---

# 📊 PDF Report Includes

- Cover page with project name
- SLA scoring
- Latency trends
- Error trends
- Scorecard breakdown
- Executive AI analysis
- Risk assessment
- Optimization guidance

---

# 🏭 Production Notes

- Use NGINX reverse proxy
- Bind FastAPI to `0.0.0.0`
- Store results in persistent volume
- Protect `/api/resetdata`
- Use dedicated VM for heavy k6 execution
- Avoid running arbitrary scripts without sandboxing in public environments

---

# 👤 Author

© Andy Setiyawan 2026 – All Rights Reserved.
Made with ❤️

LinkedIn:
https://www.linkedin.com/in/andy-setiyawan-452396170/
