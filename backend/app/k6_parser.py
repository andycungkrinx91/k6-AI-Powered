import json
import numpy as np
from collections import defaultdict
from datetime import datetime

def parse_k6_ndjson(raw: str):

    latency_values = []
    timeline_latency = defaultdict(list)
    # http_reqs is a Counter in k6 JSON output; values are cumulative.
    # We store the maximum observed value per second bucket.
    timeline_requests = defaultdict(float)
    timeline_checks = defaultdict(lambda: {"pass": 0, "fail": 0})

    first_ts = None
    last_ts = None

    for line in raw.splitlines():
        if not line.strip():
            continue

        try:
            obj = json.loads(line)
        except:
            continue

        if obj.get("type") != "Point":
            continue

        metric = obj.get("metric")
        data = obj.get("data", {})
        value = data.get("value")
        timestamp = data.get("time")

        if value is None or timestamp is None:
            continue

        value = float(value)

        ts = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))

        # ---- Track real test duration ----
        if not first_ts:
            first_ts = ts
        last_ts = ts

        bucket = ts.replace(microsecond=0).isoformat()

        if metric == "http_req_duration":
            latency_values.append(value)
            timeline_latency[bucket].append(value)

        if metric == "http_reqs":
            # Keep max cumulative count observed in this bucket.
            if value > timeline_requests[bucket]:
                timeline_requests[bucket] = value

        if metric == "checks":
            if value == 1:
                timeline_checks[bucket]["pass"] += 1
            else:
                timeline_checks[bucket]["fail"] += 1

    summary = {}

    # ================= LATENCY =================
    if latency_values:
        arr = np.array(latency_values)
        summary["http_req_duration"] = {
            "avg": round(float(np.mean(arr)), 2),
            "p(95)": round(float(np.percentile(arr, 95)), 2),
            "p(99)": round(float(np.percentile(arr, 99)), 2),
            "min": round(float(np.min(arr)), 2),
            "max": round(float(np.max(arr)), 2),
        }

    # ================= ERROR RATE =================
    total_pass = sum(v["pass"] for v in timeline_checks.values())
    total_fail = sum(v["fail"] for v in timeline_checks.values())
    total_checks = total_pass + total_fail

    error_rate = total_fail / total_checks if total_checks else 0

    summary["checks"] = {
        "passes": total_pass,
        "fails": total_fail,
        "error_rate": round(error_rate, 4)
    }

    # ================= REQUESTS / RPS =================
    total_requests = int(max(timeline_requests.values())) if timeline_requests else 0

    if first_ts and last_ts and last_ts > first_ts:
        duration_seconds = (last_ts - first_ts).total_seconds()
        rps = total_requests / duration_seconds if duration_seconds > 0 else 0
    else:
        duration_seconds = 1
        rps = 0

    summary["http_reqs"] = {
        "count": total_requests,
        "rate": round(rps, 2)
    }

    return {
        "metrics": summary,
        "timeline": {
            "latency": dict(timeline_latency),
            "requests": dict(timeline_requests),
            "checks": dict(timeline_checks),
        }
    }
