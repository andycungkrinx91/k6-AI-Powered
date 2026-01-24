import http from 'k6/http';
import { Rate } from "k6/metrics";
import { check, sleep } from 'k6';

export const URL = "https://quickpizza.grafana.com/"

export const options = {
  ext: {
    loadimpact: {
      distribution: {
        "amazon:us:ashburn": {
          loadZone: "amazon:us:ashburn",
          percent: 100
        }
      },
      apm: []
    }
  },
  thresholds: {
    success: ["rate>0.95"],
    errors: ["rate<0.1"],
    http_req_duration: ["p(90)<1500"]
  },
  scenarios: {
    Scenario_1: {
      executor: "ramping-vus",
      gracefulStop: "30s",
      stages: [
        { target: 10, duration: "1m" },
        { target: 10, duration: "1m" },
        { target: 20, duration: "1m" },
        { target: 20, duration: "1m" },
        { target: 20, duration: "1m" },
      ],
      gracefulRampDown: "30s",
      exec: "scenario_1"
    }
  }
};

export let errorRate = new Rate("errors");
export let successRate = new Rate("success");

export function scenario_1() {
  let response = http.get(URL);

  let resultSuccess = check(response, {
    "status is 200": (r) => r.status === 200,
  });

  successRate.add(resultSuccess);
  errorRate.add(!resultSuccess);

  sleep(1);
}

export default function () {}
