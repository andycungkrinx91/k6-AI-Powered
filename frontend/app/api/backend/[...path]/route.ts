import { NextRequest } from "next/server"

export const runtime = "nodejs"
export const dynamic = "force-dynamic"

const BACKEND_BASE = process.env.BACKEND_API_URL || "http://localhost:8000"
const BACKEND_KEY = process.env.BACKEND_API_KEY || ""

function buildBackendUrl(pathParts: string[], search: string) {
  const path = "/" + pathParts.map(encodeURIComponent).join("/")
  return `${BACKEND_BASE}${path}${search || ""}`
}

async function proxy(req: NextRequest, ctx: { params: Promise<{ path: string[] }> }) {
  const { path } = await ctx.params
  const backendUrl = buildBackendUrl(path, req.nextUrl.search)

  const headers = new Headers()
  headers.set("x-api-key", BACKEND_KEY)
  const authorization = req.headers.get("authorization")
  if (authorization && authorization !== "Bearer undefined" && authorization !== "Bearer null") {
    // Standardize casing for downstream services.
    headers.set("Authorization", authorization)
  }
  const contentType = req.headers.get("content-type")
  if (contentType) headers.set("content-type", contentType)
  const accept = req.headers.get("accept")
  if (accept) headers.set("accept", accept)

  const init: RequestInit = {
    method: req.method,
    headers,
    // Streaming bodies are only allowed on certain methods.
    body: req.method === "GET" || req.method === "HEAD" ? undefined : req.body,
    // Avoid caching for long-running jobs.
    cache: "no-store",
  }

  // Node.js fetch requires duplex when streaming a request body.
  if (init.body) {
    ;(init as any).duplex = "half"
  }

  const res = await fetch(backendUrl, init)

  // Pass-through status + headers, but avoid leaking hop-by-hop headers.
  const outHeaders = new Headers(res.headers)
  outHeaders.delete("connection")
  outHeaders.delete("transfer-encoding")

  return new Response(res.body, {
    status: res.status,
    headers: outHeaders,
  })
}

export async function GET(req: NextRequest, ctx: any) {
  return proxy(req, ctx)
}

export async function POST(req: NextRequest, ctx: any) {
  return proxy(req, ctx)
}

export async function PUT(req: NextRequest, ctx: any) {
  return proxy(req, ctx)
}

export async function PATCH(req: NextRequest, ctx: any) {
  return proxy(req, ctx)
}

export async function DELETE(req: NextRequest, ctx: any) {
  return proxy(req, ctx)
}
