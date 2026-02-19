import asyncio
import json
import os
import tempfile
import uuid


USER_AGENT = os.getenv("USER_AGENT", "k6-ai-powerd-agent")

K6_TEMPLATE = """
import http from 'k6/http';
import { Rate } from "k6/metrics";
import { check } from 'k6';

export const URL = %s;
export const USER_AGENT = %s;

export const options = {
  thresholds: {
    success: ["rate>0.95"],
    errors: ["rate<0.1"],
    http_req_duration: ["p(90)<15000"]
  },
  scenarios: {
    Scenario_1: {
      executor: "ramping-vus",
      gracefulStop: "30s",
      stages: %s,
      gracefulRampDown: "30s",
      exec: "scenario_1"
    }
  }
};

export let errorRate = new Rate("errors");
export let successRate = new Rate("success");

export function scenario_1() {
  let response = http.get(URL, { headers: { "User-Agent": USER_AGENT } });

  let resultSuccess = check(response, {
    "status is 200": (r) => r.status == 200,
  });

  successRate.add(resultSuccess);
  errorRate.add(!resultSuccess);
}
"""

async def run_k6_stream(url, stages):
    timeout_s = int(os.getenv("K6_TIMEOUT_SECONDS", "180"))

    # IMPORTANT: do not use TemporaryDirectory here.
    # The caller reads the NDJSON file *after* this generator finishes,
    # so we need the output file to persist until the caller cleans it up.
    tmpdir = tempfile.mkdtemp(prefix="k6-ai-")
    run_id = str(uuid.uuid4())
    script_path = os.path.join(tmpdir, f"{run_id}.js")
    json_output = os.path.join(tmpdir, f"{run_id}.json")

    # Use JSON encoding to avoid quote-breaking in JS.
    url_js = json.dumps(url)
    ua_js = json.dumps(USER_AGENT)
    stages_js = json.dumps(stages)

    with open(script_path, "w") as f:
        f.write(K6_TEMPLATE % (url_js, ua_js, stages_js))

    proc = await asyncio.create_subprocess_exec(
        "k6",
        "run",
        "--out",
        f"json={json_output}",
        script_path,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
    )

    assert proc.stdout is not None
    while True:
        line = await proc.stdout.readline()
        if not line:
            break
        yield line.decode(errors="ignore")

    try:
        await asyncio.wait_for(proc.wait(), timeout=timeout_s)
    except asyncio.TimeoutError:
        proc.kill()
        yield f"K6_TIMEOUT after {timeout_s}s\n"

    yield "__TMP_DIR__:" + tmpdir
    yield "__JSON_PATH__:" + json_output
