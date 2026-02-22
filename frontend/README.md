# K6 AI Performance Intelligence – Frontend

Modern performance testing dashboard built with:

- Next.js 16 (App Router)
- React 19
- TailwindCSS 4
- Recharts (data visualization)
- TypeScript

Runtime requirements:

- Node.js 24.x (see `frontend/package.json` engines)
- pnpm 9.x

## 🔐 Authentication

- The Next.js app now requires authentication before accessing dashboards or running tests. Use `/login` to authenticate with username/email + password.
- On a fresh install, backend bootstraps an admin account from `INITIAL_ADMIN_*` environment variables.
- Administrators get a dedicated `Users` menu where they can list existing accounts and mint new admin/user credentials with username, email, password, and role.
- All users get a `Profile` page to rotate their password; load test results record the `run_by` identity for auditing.
- Axios-style proxy (`/api/backend`) forwards the JWT and backend API key automatically after you log in.

## 🎛 Theme & Font Switcher

- Default theme: Linux terminal (matrix)
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
- Persisted in localStorage:
  - `k6-theme`
  - `k6-font`
- UI entry point: Sidebar settings (top)

This frontend connects to the FastAPI backend and provides:

- Builder Mode (visual load test creation)
- Custom Script Upload Mode
- Real-time streaming logs (SSE)
- Animated dashboards
- Performance trend charts
- Result history table with filtering, sorting, pagination
- Role-based navigation (admin user management)

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
BACKEND_API_URL=http://backend:8000
BACKEND_API_KEY=your_backend_api_key_here
```

These values are read server-side by `app/api/backend/[...path]/route.ts` and are not exposed to the browser (do not prefix with `NEXT_PUBLIC_`).

VM helper:

- You can manage these values via `scripts/.env` and run `bash scripts/run-frontend-ubuntu.sh`.

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
  -e BACKEND_API_URL=http://backend:8000 \
  -e BACKEND_API_KEY=your_backend_api_key_here \
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

 - Upload .js k6 script (max size enforced by backend config)
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

Authentication flow:

- First page: `/login`
- After login, the dashboard shows a greeting: `Welcome <username>, lets do a great work today!`
- Admin users see an extra menu: `/users` (user directory + create user)
- Profile page: `/profile` (update password)

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
