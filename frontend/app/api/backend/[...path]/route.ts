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
  // Avoid upstream compression to prevent content-encoding mismatches when proxying
  // through Node fetch and edge proxies (e.g. Cloudflare).
  headers.set("accept-encoding", "identity")
  const authorization = req.headers.get("authorization")
  if (authorization && authorization !== "Bearer undefined" && authorization !== "Bearer null") {
    // Standardize casing for downstream services.
    headers.set("Authorization", authorization)
    // Fallback header: helps when intermediaries modify Authorization.
    headers.set("X-App-Authorization", authorization)
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

  let res: Response
  try {
    res = await fetch(backendUrl, init)
  } catch (err) {
    const message = err instanceof Error ? err.message : String(err)
    return new Response(`Backend fetch failed: ${message}`, {
      status: 502,
      headers: {
        "content-type": "text/plain; charset=utf-8",
      },
    })
  }

  // Pass-through status + headers, but avoid leaking hop-by-hop headers.
  const outHeaders = new Headers(res.headers)
  outHeaders.delete("connection")
  outHeaders.delete("transfer-encoding")
  // Node's fetch (undici) transparently decompresses gzip/br/deflate responses.
  // If we forward Content-Encoding unchanged, the browser will try to decode an
  // already-decoded body and fail with ERR_CONTENT_DECODING_FAILED.
  outHeaders.delete("content-encoding")
  outHeaders.delete("content-length")

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
