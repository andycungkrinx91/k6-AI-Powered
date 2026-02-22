"use client"

import { useMemo } from "react"
import { useRouter } from "next/navigation"
import { useAuth } from "@/context/AuthContext"

export default function NotFound() {
  const router = useRouter()
  const { ready, user } = useAuth()

  const target = useMemo(() => {
    if (!ready) return null
    return user ? "/" : "/login"
  }, [ready, user])

  return (
    <div className="min-h-screen bg-terminal-bg text-terminal-white flex items-center justify-center p-6">
      <div className="w-full max-w-xl border border-terminal-border bg-terminal-surface shadow-terminal p-6 sm:p-10">
        <div className="text-terminal-dim text-xs tracking-widest uppercase">[ 404 ]</div>
        <div className="mt-2 text-2xl sm:text-3xl font-semibold text-terminal-phosphor">page not found</div>
        <div className="mt-3 text-sm text-terminal-dim leading-relaxed">
          The route you requested does not exist.
        </div>

        <div className="mt-8 flex items-center gap-3">
          <button
            type="button"
            onClick={() => {
              if (!target) return
              router.replace(target)
            }}
            className="px-5 py-2.5 border border-terminal-phosphor text-terminal-phosphor hover:bg-terminal-phosphor hover:text-black"
            disabled={!target}
          >
            {target ? "[ GO HOME ]" : "[ LOADING ]"}
          </button>
          <div className="text-xs text-terminal-dim">
            {target === "/" ? "redirects to dashboard" : target === "/login" ? "redirects to login" : "checking session…"}
          </div>
        </div>
      </div>
    </div>
  )
}
