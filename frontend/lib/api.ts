const API_BASE = "/api/backend"

async function request(path: string, options: RequestInit = {}) {
  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {}),
    },
    cache: "no-store",
  })

  if (!res.ok) {
    throw new Error("API Error")
  }

  return res.json()
}

// ================= RUN =================
export async function runTest(payload: any) {
  const res = await fetch(`${API_BASE}/api/run`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
    cache: "no-store",
  })

  return res
}

// ================= RESULTS =================
export async function getResults(limit = 100, offset = 0) {
  return request(`/api/result/list?limit=${limit}&offset=${offset}`)
}

export async function getResult(id: string) {
  return request(`/api/result/${id}`)
}

export async function downloadResult(id: string, variant: "load" | "security" = "load") {
  const path =
    variant === "security"
      ? `${API_BASE}/api/download/${id}/security`
      : `${API_BASE}/api/download/${id}`

  const response = await fetch(path, { cache: "no-store" })

  const blob = await response.blob()
  const url = window.URL.createObjectURL(blob)

  const a = document.createElement("a")
  a.href = url
  a.download = variant === "security" ? `${id}-security.pdf` : `${id}.pdf`
  document.body.appendChild(a)
  a.click()
  a.remove()

  window.URL.revokeObjectURL(url)
}
