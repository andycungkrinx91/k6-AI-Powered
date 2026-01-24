export type RunResponse = {
  id: string
  message?: string
}

export interface Scorecard {
  score: number
  grade: string
  risk: string
}

export interface Metrics {
  http_req_duration?: {
    avg: number
    "p(95)": number
    "p(99)": number
  }
  http_reqs?: {
    count: number
  }
  checks?: {
    error_rate: number
  }
}

export interface Timeline {
  latency: Record<string, number[]>
  requests: Record<string, number>
  checks: Record<string, { pass: number; fail: number }>
}

export interface LoadTestResult {
  id: string
  url: string
  created_at: string
  scorecard: Scorecard
  metrics: Metrics
  timeline: Timeline
  analysis: string
  pdf_url: string
}
