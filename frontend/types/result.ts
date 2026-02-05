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
  security_headers?: Record<string, any>
  security_status?: string
  security_pdf?: string
  ssl?: {
    status?: string
    score?: number
    rating?: string
    findings?: Array<{ id: string; severity: string; message: string }>
    supported_versions?: string[]
    weak_versions?: string[]
    negotiated_ciphers?: string[]
    key_algorithm?: string
    key_size?: number
    expires_in_days?: number
    protocol_score?: number
    key_exchange_score?: number
    cipher_strength_score?: number
    ssllabs_grade?: string
    ssllabs_status?: string
    cert_subject?: string
    cert_issuer?: string
    cert_not_before?: string
    cert_not_after?: string
    cert_san?: string[]
  }
}
