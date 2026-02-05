# K6 AI Performance Intelligence – Frontend

Modern performance testing dashboard built with:

- Next.js 16 (App Router)
- React 19
- TailwindCSS 4
- Recharts (data visualization)
- TypeScript

This frontend connects to the FastAPI backend and provides:

- Builder Mode (visual load test creation)
- Custom Script Upload Mode
- Real-time streaming logs (SSE)
- Animated dashboards
- Performance trend charts
- Result history table with filtering, sorting, pagination

---

# 📁 Project Structure

```
frontend/
├── app
│   ├── global.css
│   ├── layout.tsx
│   ├── load-test
│   │   └── page.tsx
│   ├── page.tsx
│   └── result
│       ├── [id]
│       │   └── page.tsx
│       └── page.tsx
├── components
│   ├── Card.tsx
│   ├── ChartCard.tsx
│   ├── Header.tsx
│   ├── Modal.tsx
│   ├── ResultTable.tsx
│   ├── RunForm.tsx
│   ├── RunScriptUpload.tsx
│   └── Sidebar.tsx
├── Dockerfile
├── lib
│   └── api.ts
├── next.config.js
├── next-env.d.ts
├── package.json
├── pnpm-lock.yaml
├── postcss.config.js
├── README.md
├── tailwind.config.js
├── tsconfig.json
└── types
    └── result.ts
```

---

# ⚙️ Environment Variables

Create `.env`:

```
NEXT_PUBLIC_API_URL=http://backend.local:8000
NEXT_PUBLIC_API_KEY=your_secret_key
```

These values are exposed to the browser.

---

# 🚀 Development

Install dependencies:

```
pnpm install
```

Run dev server:

```
pnpm dev
```

Server runs on:

```
http://localhost:3000
```

---

# 🐳 Docker

Build:

```
docker build -t k6ai-frontend .
```

Run:

```
docker run -p 3000:3000 \
  -e NEXT_PUBLIC_API_URL=http://backend.local:8000 \
  -e NEXT_PUBLIC_API_KEY=your_secret_key \
  k6ai-frontend
```

Make sure backend is accessible from container.

---

# 🧠 Features

## 1️⃣ Builder Mode

- Dynamic stages
- Real-time progress
- Streaming logs
- Animated progress bar
- Step badges for Security Headers, SSL/TLS, WebPageTest (Playwright), Lighthouse
- Success & error toast
- Auto redirect to result page

## 2️⃣ Script Upload Mode

- Upload .js k6 script (max 2MB)
- Backend captcha validation
- Streaming execution logs
- Structured error detection
- Shows post-run steps (Security/SSL/WPT/Lighthouse)

## 3️⃣ Dashboard

- Performance trend line (animated)
- Error rate trend
- Score breakdown donut
- Animated KPI counters
- TLS 1.3 coverage & security-header coverage KPIs
- Security Header grade donut
- SSL rating donut
- Result History badges for Security, SSL, WPT, Lighthouse scores

## 4️⃣ Result Table

- Column sorting
- Filter by ID or Project Name
- Pagination
- Sticky header
- Mobile responsive
- Row expand animation
- SLA Grade badge
- Performance score display
- Security Headers section with grade/score and header statuses
- SSL/TLS section with rating, sub-scores, protocols, ciphers, cert details, findings
- WebPageTest (Playwright) section with first/repeat view metrics, waterfall, score/grade
- Lighthouse section with category scores and key metrics

---

# 📊 Data Flow

Frontend → Backend `/api/run` or `/api/runjs`

Backend streams SSE logs → frontend updates progress UI

When finished:

```
RUN_ID:xxxxx
```

Frontend auto redirects to:

```
/result/{id}
```

---

# 📱 Mobile Support

- Responsive layout
- Collapsible sidebar
- Swipe-friendly pagination
- Sticky search bar

---

# 🔐 Security Model

- API key required on all requests
- Script validation handled server-side
- Captcha required for custom script execution
- No sensitive keys stored in frontend

---

# 📌 Production Notes

- Use domain-based routing instead of localhost
- Ensure CORS configured correctly in backend
- Always use HTTPS in production
- Do not expose private API keys

---

# 👤 Author

© Andy Setiyawan 2026 – All Rights Reserved.
Made with ❤️

LinkedIn:
https://www.linkedin.com/in/andy-setiyawan-452396170/

---

End of Frontend README
