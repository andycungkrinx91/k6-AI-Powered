"use client"

import { useEffect, useState } from "react"
import { useRouter } from "next/navigation"
import Card from "@/components/Card"
import RunForm from "@/components/RunForm"
import RunScriptUpload from "@/components/RunScriptUpload"
import { useAuth } from "@/context/AuthContext"

export default function LoadTestPage() {
  const router = useRouter()
  const { user, ready } = useAuth()
  const [tab, setTab] = useState<"builder" | "upload">("builder")

  useEffect(() => {
    if (ready && !user) {
      router.replace("/login")
    }
  }, [ready, user, router])

  if (!ready || !user) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-sm text-terminal-dim">Securing the studio…</div>
      </div>
    )
  }

    return (
      <Card title="Run Load Test">
      <div className="flex border-b border-terminal-border mb-6">
        <button
          onClick={() => setTab("builder")}
          className={`px-6 py-3 text-sm font-medium relative rounded-t-md ${
            tab === "builder"
              ? "text-terminal-phosphor"
              : "text-terminal-dim hover:text-terminal-white"
          }`}
        >
          Builder Mode
          {tab === "builder" && (
            <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-terminal-phosphor" />
          )}
        </button>

        <button
          onClick={() => setTab("upload")}
          className={`px-6 py-3 text-sm font-medium relative rounded-t-md ${
            tab === "upload"
              ? "text-terminal-phosphor"
              : "text-terminal-dim hover:text-terminal-white"
          }`}
        >
          Upload k6 Script
          {tab === "upload" && (
            <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-terminal-phosphor" />
          )}
        </button>
      </div>

      {tab === "builder" && <RunForm />}
      {tab === "upload" && <RunScriptUpload />}
    </Card>
  )
}
