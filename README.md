# 🚀 K6 AI Powered

![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?logo=docker&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688?logo=fastapi&logoColor=white)
![Next.js](https://img.shields.io/badge/Next.js-16-black?logo=next.js&logoColor=white)
![MySQL](https://img.shields.io/badge/MySQL-8.0-4479A1?logo=mysql&logoColor=white)


# 🧠 AI‑Powered Performance Intelligence Platform

> Beautiful. Intelligent. Enterprise‑grade.

K6 AI Powered is a full‑stack performance testing platform that combines **k6 load testing**, **AI analysis (Gemini)**, and a **modern analytics dashboard** into a single production‑ready system.

<table align="center">
  <tr>
    <td align="center"><b>Login Page</b></td>
    <td align="center"><b>Users</b></td>
  </tr>
  <tr>
    <td><a href="https://raw.githubusercontent.com/andycungkrinx91/k6-AI-Powered/master/images/login.png" target="_blank"><img src="https://raw.githubusercontent.com/andycungkrinx91/k6-AI-Powered/master/images/login.png" width="400px"/></a></td>
    <td><a href="https://raw.githubusercontent.com/andycungkrinx91/k6-AI-Powered/master/images/users.png" target="_blank"><img src="https://raw.githubusercontent.com/andycungkrinx91/k6-AI-Powered/master/images/users.png" width="400px"/></a></td>
  </tr>
  <tr>
    <td align="center"><b>Profile</b></td>
    <td align="center"><b>Themes Settings</b></td>
  </tr>
  <tr>
    <td><a href="https://raw.githubusercontent.com/andycungkrinx91/k6-AI-Powered/master/images/profile.png" target="_blank"><img src="https://raw.githubusercontent.com/andycungkrinx91/k6-AI-Powered/master/images/profile.png" width="400px"/></a></td>
    <td><a href="https://raw.githubusercontent.com/andycungkrinx91/k6-AI-Powered/master/images/themes.png" target="_blank"><img src="https://raw.githubusercontent.com/andycungkrinx91/k6-AI-Powered/master/images/themes.png" width="400px"/></a></td>
  </tr>
  <tr>
    <td align="center"><b>Dashboard</b></td>
    <td align="center"><b>Builder Mode</b></td>
  </tr>
  <tr>
    <td><a href="https://raw.githubusercontent.com/andycungkrinx91/k6-AI-Powered/master/images/dashboard-page.png" target="_blank"><img src="https://raw.githubusercontent.com/andycungkrinx91/k6-AI-Powered/master/images/dashboard-page.png" width="400px"/></a></td>
    <td><a href="https://raw.githubusercontent.com/andycungkrinx91/k6-AI-Powered/master/images/builder-mode.png" target="_blank"><img src="https://raw.githubusercontent.com/andycungkrinx91/k6-AI-Powered/master/images/builder-mode.png" width="400px"/></a></td>
  </tr>
  <tr>
    <td align="center"><b>Result Load Test</b></td>
    <td align="center"><b>Upload Custom K6 Script</b></td>
  </tr>
  <tr>
    <td><a href="https://raw.githubusercontent.com/andycungkrinx91/k6-AI-Powered/master/images/load-test-result.png" target="_blank"><img src="https://raw.githubusercontent.com/andycungkrinx91/k6-AI-Powered/master/images/load-test-result.png" width="400px"/></a></td>
    <td><a href="https://raw.githubusercontent.com/andycungkrinx91/k6-AI-Powered/master/images/k6-custom-script.png" target="_blank"><img src="https://raw.githubusercontent.com/andycungkrinx91/k6-AI-Powered/master/images/k6-custom-script.png" width="400px"/></a></td>
  </tr>
  <tr>
    <td align="center"><b>Result History</b></td>
    <td align="center"><b>Report Preview</b></td>
  </tr>
  <tr>
    <td><a href="https://raw.githubusercontent.com/andycungkrinx91/k6-AI-Powered/master/images/result-page.png" target="_blank"><img src="https://raw.githubusercontent.com/andycungkrinx91/k6-AI-Powered/master/images/result-page.png" width="400px"/></a></td>
    <td><a href="https://raw.githubusercontent.com/andycungkrinx91/k6-AI-Powered/master/images/report-preview.png" target="_blank"><img src="https://raw.githubusercontent.com/andycungkrinx91/k6-AI-Powered/master/images/report-preview.png" width="400px"/></a></td>
  </tr>
</table>

---

## ✨ Overview

**K6 AI Powered** is a full‑stack performance testing platform combining:

- ⚡ k6 load testing
- 🧠 AI analysis (Gemini, OpenAI, Local LLM)
- 📊 Advanced dashboards
- 📄 Automated PDF reporting
- 🔐 Secure execution pipeline

It provides both:

- Builder Mode (visual test configuration)
- Script Upload Mode (custom k6 JS execution; optional via backend config)

---
# 🏗 Architecture

Frontend (Next.js)  ⇄  Backend (FastAPI)  ⇄  k6 Engine  ⇄  AI (Gemini/OpenAI/Local LLM)  ⇄  MySQL

---

# 🖥 Tech Stack

## 🔙 Backend (FastAPI)

- FastAPI
- SQLAlchemy (Async)
- MySQL 8
- k6 CLI
- AI Analysis (Google Gemini, OpenAI, Local LLM/vLLM/Ollama)
- ReportLab (PDF generator)
- Docker
- asyncio / subprocess
- SSE Streaming (text/event-stream)

📘 Detailed backend documentation:

➡ **[Backend README](https://github.com/andycungkrinx91/k6-AI-Powered/blob/master/backend/README.md)** <br>
➡ **[API README](https://github.com/andycungkrinx91/k6-AI-Powered/blob/master/backend/API_README.md)**

---

## 🎨 Frontend (Next.js)

- Next.js (App Router)
- React 19
- TypeScript
- TailwindCSS 4
- Recharts
- SSE Streaming
- Animated UI components

UI theme:

- Default look is Linux terminal (matrix)
- Built-in Theme + Font switcher (persisted in localStorage)

Runtime requirements (local dev):

- Node.js 24.x
- pnpm 9.x

📘 Detailed frontend documentation:

➡ **[Frontend README](https://github.com/andycungkrinx91/k6-AI-Powered/blob/master/frontend/README.md)**

---

# 🔥 Core Features

## 1️⃣ Builder Mode
- Dynamic stage configuration
- Real‑time progress + step badges (k6, Security Headers, SSL, WPT, Lighthouse)
- Streaming logs
- AI‑generated analysis with retry on 429/503
- Automated PDF report (performance + security) with formatted AI analysis sections

## 2️⃣ Script Upload Mode
- Upload custom k6 scripts (max size configurable via `MAX_UPLOAD_BYTES`; backend default: 200000 bytes)
- Can be disabled by default (`ENABLE_SCRIPT_UPLOAD=false`)
- Captcha validation (when upload mode is enabled)
- Malware pattern filtering
- Structured exit‑code handling
- Same post-run pipeline: Security Headers, SSL/TLS analysis, WebPageTest (Playwright), Lighthouse

## 3️⃣ Security & TLS Intelligence
- Security Headers: CSP, Permissions-Policy, Referrer-Policy, HSTS, X-Content-Type-Options, X-Frame-Options; grade, recommendations, raw headers; PDF + API
- SSL/TLS Analyzer: TLS 1.3/1.2 detection, legacy flags, negotiated ciphers, key algo/size, cert subject/issuer/SAN/validity, sub-scores and rating; PDF + API

## 4️⃣ Web Performance Scans
- WebPageTest (Playwright): first/repeat view, TTFB/DCL/Load/FP/FCP/LCP/CLS/INP, Speed Index heuristic, TBT, page weight, resource waterfall; WPT-style score/grade; PDF + API + UI cards
- Lighthouse: Performance/Accessibility/Best Practices/SEO/PWA (fallback 0 if missing), key metrics (FCP, LCP, CLS, TBT, TTI, Speed Index); PDF + API + UI cards

## 5️⃣ Dashboard
- Performance trend chart (animated)
- Error rate trend
- Score breakdown donut
- SLA + Security + SSL + WPT + Lighthouse badges in Result History
- Animated KPI counters

## 6️⃣ User LLM Settings (Per-User AI Configuration)
- Users can configure their own AI provider for analysis
- Supported providers:
  - **Google Gemini**: Use your own Gemini API key
  - **OpenAI**: Use your own OpenAI API key (api.openai.com)
  - **Local/OpenAI-Compatible**: Use local LLM servers (vLLM, Ollama, etc.)
- Per-user settings override global configuration
- Settings accessible from LLM Settings menu
- Common options: temperature, max tokens, model selection

## 6️⃣ LLM Context Management
- Automatic timeline data downsampling (max 30 buckets) for large payloads
- max_tokens capping for local LLM providers
- Supports local vLLM servers with context limits up to 18336 tokens

## 7️⃣ Terminal UI (Themes + Fonts)

- Themes:
  - `matrix` (default) – linux green
  - `amber` – mainframe
  - `cyberpunk` – neon
  - `midnight` – dracula
  - `modern-geist` – clean contrast
  - `modern-linear` – sleek indigo
  - `terminal-terminator` – utilitarian red
  - `terminal-arch` – arch blue
- Fonts:
  - `modern` – dev mono
  - `classic` – dense
  - `geometric` – wide
  - `retro` – crt
- Stored in localStorage keys: `k6-theme`, `k6-font`
- Switcher entry point: Sidebar settings (top)

Changelog:

- See `CHANGELOG.md`

## 7️⃣ Authentication (Admin/User)
- Login with username/email + password
- Roles: `admin` (create users) and `user` (run load tests)
- Greeting banner after login
- Profile page for password updates and LLM settings

## 8️⃣ Result Management
- Sortable, paginated table with filtering
- Mobile responsive cards with badge summaries
- PDF download (load/security)
- CLI reset endpoint

## 9️⃣ Identity & Access Control
- Admin + user roles enforced via JWTs (`/api/auth/login` returns an access token after supplying username/email + password)
- Administrators can manage accounts through the new `Users` menu (list + create user with username/email/password/role)
- Every user has a profile page to rotate their password
- Load tests annotate results with the `run_by` id/username for auditing; every request now requires the backend API key plus the Bearer token
- The initial admin account is kept in sync on backend startup using `INITIAL_ADMIN_*` environment variables (create if missing, rotate password/update role+email if different)

---

# 🐳 Deployment

## Backend

Located in:

```
/backend
```

## Frontend

Located in:

```
/frontend
```

Each folder contains its own Dockerfile.

VM (no Docker) backend runner:

```
bash scripts/run-backend-ubuntu.sh
```

VM (no Docker) frontend runner:

```
# Optional: create scripts/.env from template
cp scripts/.env.example scripts/.env

bash scripts/run-frontend-ubuntu.sh
```

---

# ☁️ Cloudflare Tunnel (Optional)

For exposing services behind NAT/firewall without public IP:

## Enable Tunnel

1. Create a Cloudflare Zero Trust tunnel at https://one.dash.cloudflare.com
2. Get the tunnel token
3. Add to `backend/.env`:

```bash
TUNNEL_TOKEN=your_tunnel_token_here
```

4. The `cf-tunnel` service in docker-compose will automatically use it

## Disable Tunnel (Development)

Comment out or remove the `cf-tunnel` service from `docker-compose.yaml`:

```yaml
# cf-tunnel:
#   <<: *default-logging
#   image: cloudflare/cloudflared:latest
#   ...
```

## How It Works

- Uses `cloudflare/cloudflared` container
- Connects to Cloudflare's edge using your tunnel token
- Services are accessible via the tunnel's public URL
- HTTP/2 transport enabled for better compatibility

---

# 🔐 Security Model

- All API requests require the backend API key and a JWT bearing the logged-in identity; load tests record the user who ran them.
- API key protected endpoints
- Server-side script validation
- Captcha protection for upload mode (when enabled)
- Gemini multi-key fallback logic
- No secrets exposed to frontend

---

© Andy Setiyawan 2026 – All Rights Reserved.
Made with ❤️

LinkedIn:
https://www.linkedin.com/in/andy-setiyawan-452396170/
