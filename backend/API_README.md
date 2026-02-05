# Backend API – Curl Payload Test Guide (2026)

Base variables used in examples:

```
API_KEY=your_secret_key
BASE=http://backend.local:8000
```

---

# 1️⃣ Builder Mode – Run Load Test

## Endpoint
```
POST /api/run
```

## Curl Test

```bash
curl -X POST $BASE/api/run \
  -H "Content-Type: application/json" \
  -H "x-api-key: $API_KEY" \
  -N \
  -d '{
    "project_name": "QuickPizza Test",
    "url": "https://quickpizza.grafana.com/",
    "stages": [
      { "duration": "30s", "target": 10 },
      { "duration": "1m",  "target": 20 }
    ]
  }'
```

### Notes
- `-N` is required for SSE streaming
- You will receive real-time k6 logs
- Final output will contain:

```
data: __FINISHED__
data: RUN_ID:xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
```

The result JSON (and PDF) also includes:
- `security_headers`: grade, score (present/total), recommendations, raw headers
- `ssl`: rating, score, protocol/key-exchange/cipher sub-scores, supported/weak versions, negotiated ciphers, certificate subject/issuer/SAN/validity, findings

---

# 2️⃣ Upload Mode – Run Custom k6 Script

## Step 1: Get Captcha

```bash
curl $BASE/api/captcha
```

Example response:

```json
{
  "question": "4 + 7 = ?",
  "token": "abc123",
  "timestamp": 1700000000
}
```

Solve manually (example: 11)

---

## Step 2: Upload Script

```bash
curl -X POST $BASE/api/runjs \
  -H "x-api-key: $API_KEY" \
  -N \
  -F "project_name=Custom Script Test" \
  -F "file=@./k6-test.js" \
  -F "captcha_answer=11" \
  -F "captcha_token=abc123" \
  -F "captcha_timestamp=1700000000"
```

### Expected Behavior

- Exit code `0` → Success
- Exit code `99` → Threshold failed (still valid execution)
- Exit code `255` → Syntax/structure error

If success:

```
data: __FINISHED__
data: RUN_ID:xxxxxxxx
```

---

# 3️⃣ List All Results

```bash
curl -X GET $BASE/api/result/list \
  -H "x-api-key: $API_KEY"
```

---

# 4️⃣ Get Single Result

```bash
curl -X GET $BASE/api/result/RUN_ID_HERE \
  -H "x-api-key: $API_KEY"
```

---

# 5️⃣ Download PDF Report

```bash
curl -X GET $BASE/api/download/RUN_ID_HERE \
  -H "x-api-key: $API_KEY" \
  --output report.pdf
```

---

# 6️⃣ Reset All Data (Manual CLI Only)

⚠ This deletes database records and generated PDFs.

```bash
curl -X POST $BASE/api/resetdata \
  -H "x-api-key: $API_KEY"
```

---

End of API test documentation.
