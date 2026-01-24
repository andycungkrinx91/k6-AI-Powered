const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"
const API_KEY = process.env.NEXT_PUBLIC_API_KEY

async function request(path: string, options: RequestInit = {}) {
  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      "x-api-key": API_KEY || "",
      ...(options.headers || {}),
    },
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
      "x-api-key": API_KEY || "",
    },
    body: JSON.stringify(payload),
  })

  return res
}

// ================= RESULTS =================
export async function getResults() {
  return request("/api/result/list")
}

export async function getResult(id: string) {
  return request(`/api/result/${id}`)
}

export async function downloadResult(id: string) {
  const response = await fetch(
    `${API_BASE}/api/download/${id}`,
    {
      headers: {
        "x-api-key": process.env.NEXT_PUBLIC_API_KEY || ""
      }
    }
  )

  const blob = await response.blob()
  const url = window.URL.createObjectURL(blob)

  const a = document.createElement("a")
  a.href = url
  a.download = `${id}.pdf`
  document.body.appendChild(a)
  a.click()
  a.remove()

  window.URL.revokeObjectURL(url)
}