"use client"

import { useState } from "react"
import Card from "@/components/Card"
import RunForm from "@/components/RunForm"
import RunScriptUpload from "@/components/RunScriptUpload"

export default function LoadTestPage() {
  const [tab, setTab] = useState<"builder" | "upload">("builder")

  return (
    <Card title="Run Load Test">
      <div className="flex gap-4 mb-6">
        <button
          onClick={() => setTab("builder")}
          className={`px-4 py-2 rounded-xl transition ${
            tab === "builder"
              ? "bg-indigo-600 text-white"
              : "bg-gray-200 hover:bg-gray-300"
          }`}
        >
          Builder Mode
        </button>

        <button
          onClick={() => setTab("upload")}
          className={`px-4 py-2 rounded-xl transition ${
            tab === "upload"
              ? "bg-indigo-600 text-white"
              : "bg-gray-200 hover:bg-gray-300"
          }`}
        >
          Upload k6 Script
        </button>
      </div>

      {tab === "builder" && <RunForm />}
      {tab === "upload" && <RunScriptUpload />}
    </Card>
  )
}
