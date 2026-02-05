# Changelog

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

