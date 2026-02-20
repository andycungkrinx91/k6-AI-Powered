# K6 AI Powered - Backend

FastAPI service that runs k6 load tests, performs security/TLS checks, optionally runs WebPageTest (Playwright) + Lighthouse, and stores results in MySQL.

## Runtime Requirements

- Python 3.11+
- MySQL 8.0+
- k6 installed on the host/container
- Playwright Chromium (required if WebPageTest is enabled)
- Lighthouse (optional; only needed when Lighthouse scans are enabled)

## Configuration

The backend reads configuration from environment variables (see `backend/.env.example`).

Important auth-related variables:

- `BACKEND_API_KEY`: required for most API requests (`x-api-key`)
- `AUTH_SECRET`: JWT signing secret
- `INITIAL_ADMIN_USERNAME`, `INITIAL_ADMIN_EMAIL`, `INITIAL_ADMIN_PASSWORD`: admin bootstrap user (kept in sync on startup)

Admin bootstrap behavior:

- If the admin user is not found by username/email, it is created.
- If found but role/email/password differ from env, backend updates them to match env.

## Local Development (No Docker)

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Install Playwright browser deps + Chromium (if you use WPT/Playwright)
python -m playwright install --with-deps chromium

uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Ubuntu VM helper:

```bash
bash scripts/run-backend-ubuntu.sh
```

## Docker Compose

- `docker-compose.yaml` loads backend environment from `backend/.env`.
- In Docker networking, MySQL must be addressed by the service name `mysql` (not `localhost`).
