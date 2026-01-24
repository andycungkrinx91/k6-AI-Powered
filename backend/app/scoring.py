import os

SUCCESS_RATE_THRESHOLD = float(os.getenv("THRESHOLD_SUCCESS_RATE", 0.95))
ERROR_RATE_THRESHOLD = float(os.getenv("THRESHOLD_ERROR_RATE", 0.1))
P90_THRESHOLD_MS = float(os.getenv("THRESHOLD_P90_MS", 1500))


def calculate_score(metrics: dict):

    duration = metrics.get("http_req_duration", {})
    checks = metrics.get("checks", {})

    # Support both standard k6 metric and parsed checks metric
    error_rate = None
    success_rate = None

    # built-in http_req_failed exists
    if "http_req_failed" in metrics:
        error_rate = metrics["http_req_failed"].get("rate")
        success_rate = 1 - error_rate if error_rate is not None else None

    # using checks metric
    elif "checks" in metrics:
        error_rate = checks.get("error_rate")
        if error_rate is not None:
            success_rate = 1 - error_rate

    p90 = duration.get("p(90)") or duration.get("p(95)")

    if p90 is None or error_rate is None or success_rate is None:
        return {
            "p90": None,
            "error_rate": None,
            "grade": "N/A",
            "score": None,
            "risk": "Unknown"
        }

    score = 100

    # Threshold-based scoring using ENV values
    if success_rate < SUCCESS_RATE_THRESHOLD:
        score -= (SUCCESS_RATE_THRESHOLD - success_rate) * 100

    if error_rate > ERROR_RATE_THRESHOLD:
        score -= (error_rate - ERROR_RATE_THRESHOLD) * 100

    if p90 > P90_THRESHOLD_MS:
        score -= min((p90 - P90_THRESHOLD_MS) / 50, 40)

    score = max(0, round(score, 2))

    if score >= 90:
        grade = "A"
        risk = "Low"
    elif score >= 75:
        grade = "B"
        risk = "Moderate"
    elif score >= 60:
        grade = "C"
        risk = "Elevated"
    else:
        grade = "F"
        risk = "High"

    return {
        "p90": p90,
        "error_rate": error_rate,
        "success_rate": success_rate,
        "grade": grade,
        "score": score,
        "risk": risk
    }

