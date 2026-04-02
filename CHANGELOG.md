# Changelog

All notable changes to this project will be documented in this file.

The format is based on Keep a Changelog, and this project follows Semantic Versioning.

## [0.4.0] - 2026-04-02

### Added
- **Docker Compose MySQL Healthcheck**: Backend now waits for MySQL to be healthy before starting, preventing connection errors on initial startup
- **LLM Context Management**: Automatic payload trimming and max_tokens capping for local LLM providers with limited context windows
  - Timeline data downsampled to max 30 buckets before sending to LLM
  - max_tokens capped at 6000 for local providers to prevent context overflow

### Changed
- **PDF AI Engineering Analysis**: Improved formatting for numbered sections
  - Section headers (1) Executive Summary, 2) Bottlenecks, etc.) now use Montserrat-Bold 14pt for better visibility
  - Risks section (3) now displays as bullet points instead of tables
- Documentation updated: README files and .env.example with latest features

## [0.3.0] - 2026-03-18

### Added
- **Per-user LLM Settings**: Users can configure their own AI provider and API keys
  - Supported providers: Google Gemini, OpenAI (api.openai.com), Local/OpenAI-Compatible (vLLM, Ollama)
  - New API endpoints: `GET /api/profile/llm`, `PUT /api/profile/llm`
  - New database table: `user_llm_settings`
  - Frontend UI in dedicated LLM Settings page for easy configuration
  - User settings override global configuration when provided
  - Fallback to global env config if user doesn't set their own
- **Dockerfile**: Updated to use Node.js 22.x (required for Lighthouse 13.x)

### Changed
- LLM module refactored to support per-user settings with backward compatibility
- Both `/api/run` and `/api/runjs` endpoints now use user's LLM settings if configured
- PDF generator now handles None/empty analysis gracefully and strips HTML tags from LLM output

## [0.2.0] - 2026-02-21

### Added
- JWT authentication with 2 roles: `admin` and `user`.
- Admin bootstrap via `INITIAL_ADMIN_*` env vars (create if missing; update role/email; rotate password if changed).
- Admin-only Users management page (list + create users).
- Result attribution fields (`run_by` id/username) and access control (users see only their own runs; admins see all).
- Terminal-style UI revamp with theme + font switcher (themes: `matrix`, `amber`, `cyberpunk`, `midnight`; fonts: `modern`, `classic`, `geometric`, `retro`).
- Ubuntu VM runners for no-Docker setup (`scripts/run-backend-ubuntu.sh`, `scripts/run-frontend-ubuntu.sh`) using `scripts/.env`.

### Changed
- Frontend navigation and styling updated to terminal theme across dashboard, load test, results, users, and profile.
- Builder vs upload mode navigation updated to tab-style menu.

### Fixed
- Docker Compose networking issues for MySQL by using service-name addressing (no `localhost` inside containers).
- Frontend proxy header forwarding stabilized for `Authorization` bearer token.
- Hydration mismatch issues by separating root server layout from client app shell.

## [0.1.0] - 2026-02-05
- Add progress step indicators (Security Headers, SSL/TLS, WebPageTest, Lighthouse) to builder and upload flows.
- Integrate Lighthouse with Playwright Chromium; capture performance categories and key metrics.
- Expand WebPageTest (Playwright) to include first/repeat view summaries: TTFB, DCL, Load, FP/FCP/LCP, CLS, INP, TBT, Speed Index heuristic, page weight, total requests, elapsed, waterfall.
- Add WPT composite score/grade; surface in UI and PDF.
- Add security header and SSL/TLS scans to runs; store in DB, expose via API, render in PDF.
- Dashboard and Result History now show Sec/SSL/WPT/Lighthouse badges.
- Add pagination params to results API for faster dashboard loads.
- Retry Gemini analysis on 503/overload; graceful fallback message.
- PDF table alignment improvements for security/SSL/WPT/Lighthouse sections.
