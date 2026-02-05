import asyncio
import json
import os
import uuid


USER_AGENT = os.getenv("USER_AGENT", "k6-ai-powerd-agent")

K6_TEMPLATE = """
import http from 'k6/http';
import { Rate } from "k6/metrics";
import { check } from 'k6';

export const URL = "%s";
export const USER_AGENT = "%s";

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
    run_id = str(uuid.uuid4())
    script_path = f"/tmp/{run_id}.js"
    json_output = f"/tmp/{run_id}.json"

    with open(script_path, "w") as f:
        f.write(K6_TEMPLATE % (url, USER_AGENT, json.dumps(stages)))

    proc = await asyncio.create_subprocess_exec(
        "k6",
        "run",
        "--out",
        f"json={json_output}",
        script_path,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT
    )

    while True:
        line = await proc.stdout.readline()
        if not line:
            break
        yield line.decode()

    await proc.wait()
    yield "__JSON_PATH__:" + json_output
