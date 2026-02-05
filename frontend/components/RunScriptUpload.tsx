"use client"

import { useState, useEffect } from "react"
import { useRouter } from "next/navigation"

export default function RunScriptUpload() {
  const router = useRouter()

  const [projectName, setProjectName] = useState("")
  const [file, setFile] = useState<File | null>(null)

  const [captchaQuestion, setCaptchaQuestion] = useState("")
  const [captchaAnswer, setCaptchaAnswer] = useState("")
  const [captchaToken, setCaptchaToken] = useState("")
  const [captchaTimestamp, setCaptchaTimestamp] = useState<number | null>(null)

  const [loading, setLoading] = useState(false)
  const [logs, setLogs] = useState<string[]>([])
  const [showModal, setShowModal] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [steps, setSteps] = useState<Record<string, "pending" | "running" | "done" | "skip">>({
    load: "pending",
    security_headers: "pending",
    ssl: "pending",
    wpt: "pending",
    lighthouse: "pending",
  })

  const API_BASE =
    process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"
  const API_KEY = process.env.NEXT_PUBLIC_API_KEY

  useEffect(() => {
    fetch(`${API_BASE}/api/captcha`)
      .then((res) => res.json())
      .then((data) => {
        setCaptchaQuestion(data.question)
        setCaptchaToken(data.token)
        setCaptchaTimestamp(data.timestamp)
      })
  }, [API_BASE])

  const handleCloseModal = () => {
    setShowModal(false)
    setLogs([])
    setLoading(false)
  }

  const handleRun = async () => {
    setError(null)

    if (!projectName.trim()) {
      setError("Project name is required")
      return
    }

    if (!file) {
      setError("Please upload a .js file")
      return
    }

    if (!captchaAnswer || !captchaToken || !captchaTimestamp) {
      setError("Please solve captcha")
      return
    }

    setLoading(true)
    setLogs([])
    setShowModal(true)
    setSteps({
      load: "running",
      security_headers: "pending",
      ssl: "pending",
      wpt: "pending",
      lighthouse: "pending",
    })

    const formData = new FormData()
    formData.append("project_name", projectName)
    formData.append("file", file)
    formData.append("captcha_answer", captchaAnswer)
    formData.append("captcha_token", captchaToken)
    formData.append("captcha_timestamp", String(captchaTimestamp))

    try {
      const response = await fetch(`${API_BASE}/api/runjs`, {
        method: "POST",
        headers: {
          "x-api-key": API_KEY || ""
        },
        body: formData
      })

      if (!response.ok) {
        const text = await response.text()
        setError(text)
        setLoading(false)
        return
      }

      const reader = response.body?.getReader()
      const decoder = new TextDecoder()

      if (!reader) throw new Error("No stream")

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        const chunk = decoder.decode(value)
        const lines = chunk.split("\n")

        lines.forEach((line) => {
          if (!line.startsWith("data: ")) return

          const message = line.replace("data: ", "").trim()

          // ✅ ONLY real backend failure markers
          if (message.startsWith("ERROR:")) {
            setError(message.replace("ERROR:", "").trim())
            setLoading(false)
          }

          if (message === "__FAILED__") {
            setError("k6 execution failed")
            setLoading(false)
          }

          if (message.startsWith("RUN_ID:")) {
            const id = message.replace("RUN_ID:", "")
            router.push(`/result/${id}`)
          }

          if (message.startsWith("PROGRESS:")) {
            const parts = message.split(":")
            if (parts.length >= 3) {
              const key = parts[1]
              const status = parts[2]
              setSteps((prev) => ({
                ...prev,
                [key]: status === "start" ? "running" : status === "done" ? "done" : status === "skip" ? "skip" : prev[key],
              }))
            }
            return
          }

          if (!message.startsWith("__")) {
            setLogs(prev => [...prev, message])
          }
        })
      }

    } catch (err) {
      setError("Execution failed")
      setLoading(false)
    }
  }

  return (
    <div className="space-y-6 relative">

      {/* Error Alert */}
      {error && (
        <div className="bg-red-500 text-white px-4 py-2 rounded-xl text-sm">
          {error}
        </div>
      )}

      {/* Project Name */}
      <div>
        <label className="block text-sm font-medium mb-2">
          Project Name
        </label>
        <input
          value={projectName}
          onChange={(e) => setProjectName(e.target.value)}
          className="w-full border rounded-xl px-4 py-2"
        />
      </div>

      {/* File Upload */}
      <div>
        <label className="block text-sm font-medium mb-2">
          Upload k6 Script (.js)
        </label>
        <input
          type="file"
          accept=".js"
          onChange={(e) =>
            setFile(e.target.files ? e.target.files[0] : null)
          }
          className="w-full border rounded-xl px-4 py-2"
        />
      </div>

      {/* Captcha */}
      <div>
        <label className="block text-sm font-medium mb-2">
          Solve: {captchaQuestion}
        </label>
        <input
          type="number"
          value={captchaAnswer}
          onChange={(e) => setCaptchaAnswer(e.target.value)}
          className="w-full border rounded-xl px-4 py-2"
        />
      </div>

      <button
        onClick={handleRun}
        disabled={loading}
        className={`px-6 py-3 rounded-xl text-white transition ${
          loading
            ? "bg-gray-400 cursor-not-allowed"
            : "bg-indigo-600 hover:bg-indigo-700"
        }`}
      >
        {loading ? "Running..." : "Run Script"}
      </button>

      {/* Running Modal */}
      {showModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white w-[600px] max-h-[520px] rounded-2xl p-6 shadow-xl flex flex-col relative">

            {!loading && (
              <button
                onClick={handleCloseModal}
                className="absolute top-4 right-4 text-gray-500 hover:text-red-500 text-lg font-bold"
              >
                ✕
              </button>
            )}

            <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
              Running Custom Script
              {loading && (
                <span className="w-2 h-2 bg-indigo-600 rounded-full animate-ping" />
              )}
            </h2>

            {loading && (
              <div className="w-full bg-gray-200 rounded-full h-3 mb-4 overflow-hidden">
                <div className="h-full bg-indigo-600 animate-pulse w-1/2" />
              </div>
            )}

            <div className="grid grid-cols-2 gap-2 mb-4 text-xs">
              {[
                { key: "load", label: "k6 Execution" },
                { key: "security_headers", label: "Security Headers" },
                { key: "ssl", label: "SSL Scan" },
                { key: "wpt", label: "WebPageTest" },
                { key: "lighthouse", label: "Lighthouse" },
              ].map((step) => (
                <div key={step.key} className="flex items-center gap-2">
                  <span
                    className={`w-2 h-2 rounded-full ${
                      steps[step.key] === "done"
                        ? "bg-green-500"
                        : steps[step.key] === "running"
                        ? "bg-yellow-400 animate-pulse"
                        : steps[step.key] === "skip"
                        ? "bg-gray-400"
                        : "bg-gray-300"
                    }`}
                  />
                  <span className="text-gray-700">{step.label}</span>
                </div>
              ))}
            </div>

            <div className="bg-black text-green-400 font-mono text-xs p-4 rounded-lg overflow-y-auto flex-1">
              {logs.map((log, i) => (
                <div key={i}>{log}</div>
              ))}
            </div>

          </div>
        </div>
      )}

    </div>
  )
}
