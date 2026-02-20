const API_BASE = "/api/backend"

async function request(path: string, options: RequestInit = {}, token?: string) {
  const headers = new Headers({
    "Content-Type": "application/json",
    ...(options.headers || {}),
  })

  if (token) {
    if (token !== "undefined" && token !== "null") {
      headers.set("Authorization", `Bearer ${token}`)
    }
  }

  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers,
    cache: "no-store",
  })

  if (!res.ok) {
    const message = await res.text()
    throw new Error(message || "API Error")
  }

  return res.json()
}

export type LoginPayload = {
  identifier: string
  password: string
}

export async function login(payload: LoginPayload) {
  const res = await fetch(`${API_BASE}/api/auth/login`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
    cache: "no-store",
  })

  if (!res.ok) {
    const message = await res.text()
    throw new Error(message || "Authentication failed")
  }

  return res.json()
}

export async function fetchUsers(token: string) {
  return request("/api/auth/users", {}, token)
}

export async function createUser(payload: { username: string; email: string; password: string; role: "admin" | "user" }, token: string) {
  return request(
    "/api/auth/users",
    {
      method: "POST",
      body: JSON.stringify(payload),
    },
    token
  )
}

export async function updatePassword(payload: { current_password: string; new_password: string }, token: string) {
  return request(
    "/api/profile/password",
    {
      method: "PUT",
      body: JSON.stringify(payload),
    },
    token
  )
}

// ================= RESULTS =================
export async function getResults(limit = 100, offset = 0, token?: string) {
  return request(`/api/result/list?limit=${limit}&offset=${offset}`, {}, token)
}

export async function getResult(id: string, token?: string) {
  return request(`/api/result/${id}`, {}, token)
}

export async function downloadResult(id: string, token?: string, variant: "load" | "security" = "load") {
  const path =
    variant === "security"
      ? `${API_BASE}/api/download/${id}/security`
      : `${API_BASE}/api/download/${id}`

  const headers: Record<string, string> = {}
  if (token) {
    if (token !== "undefined" && token !== "null") {
      headers.Authorization = `Bearer ${token}`
    }
  }

  const response = await fetch(path, { cache: "no-store", headers })

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
