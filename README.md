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
- 🧠 AI analysis (Gemini)
- 📊 Advanced dashboards
- 📄 Automated PDF reporting
- 🔐 Secure execution pipeline

It provides both:

- Builder Mode (visual test configuration)
- Script Upload Mode (custom k6 JS execution)

---
# 🏗 Architecture

Frontend (Next.js)  ⇄  Backend (FastAPI)  ⇄  k6 Engine  ⇄  Gemini AI  ⇄  MySQL

---

# 🖥 Tech Stack

## 🔙 Backend (FastAPI)

- FastAPI
- SQLAlchemy (Async)
- MySQL 8
- k6 CLI
- Google Gemini API
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
- TailwindCSS
- Recharts
- SSE Streaming
- Animated UI components

📘 Detailed frontend documentation:

➡ **[Frontend README](https://github.com/andycungkrinx91/k6-AI-Powered/blob/master/frontend/README.md)**

---

# 🔥 Core Features

## 1️⃣ Builder Mode
- Dynamic stage configuration
- Real‑time progress
- Streaming logs
- AI‑generated analysis
- Automated PDF report

## 2️⃣ Script Upload Mode
- Upload custom k6 scripts (≤ 2MB)
- Captcha validation
- Malware pattern filtering
- Structured exit‑code handling
- Secure execution sandbox

## 3️⃣ AI Analysis Engine
- Multi‑key Gemini support
- Random key selection
- Automatic retry on 429 / 503
- Enterprise structured output

## 4️⃣ Dashboard
- Performance trend chart (animated)
- Error rate trend
- Score breakdown donut
- SLA Grade badge
- Animated KPI counters

## 5️⃣ Result Management
- Sortable table
- Pagination
- Mobile responsive
- PDF download
- CLI reset endpoint

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

---

# 🔐 Security Model

- API key protected endpoints
- Server‑side script validation
- Captcha protection for upload mode
- Gemini multi‑key fallback logic
- No secrets exposed to frontend

---

© Andy Setiyawan 2026 – All Rights Reserved.
Made with ❤️

LinkedIn:
https://www.linkedin.com/in/andy-setiyawan-452396170/

