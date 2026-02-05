"use client"

import { useState } from "react"
import { useRouter } from "next/navigation"

interface Stage {
  duration: string
  target: number
}

export default function RunForm() {
  const router = useRouter()

  const [projectName, setProjectName] = useState("")
  const [url, setUrl] = useState("")
  const [stages, setStages] = useState<Stage[]>([
    { duration: "", target: 0 },
  ])

  const [errors, setErrors] = useState<any>({})
  const [loading, setLoading] = useState(false)
  const [logs, setLogs] = useState<string[]>([])
  const [showModal, setShowModal] = useState(false)
  const [progress, setProgress] = useState(0)
  const [steps, setSteps] = useState<Record<string, "pending" | "running" | "done" | "skip">>({
    load: "pending",
    security_headers: "pending",
    ssl: "pending",
    wpt: "pending",
    lighthouse: "pending",
  })

  const stepWeights: Record<string, number> = {
    security_headers: 82,
    ssl: 88,
    wpt: 94,
    lighthouse: 98,
  }

  const [toast, setToast] = useState<{
    type: "success" | "error"
    message: string
  } | null>(null)

  const API_BASE =
    process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"
  const API_KEY = process.env.NEXT_PUBLIC_API_KEY

  const parseDurationToSeconds = (duration: string) => {
    if (duration.endsWith("s"))
      return parseInt(duration.replace("s", ""))
    if (duration.endsWith("m"))
      return parseInt(duration.replace("m", "")) * 60
    return 0
  }

  const validate = () => {
    const newErrors: any = {}

    if (!projectName.trim())
      newErrors.projectName = "Project name is required"

    if (!url.trim())
      newErrors.url = "Target URL is required"

    if (!stages.length)
      newErrors.stages = "At least one stage required"

    stages.forEach((stage, index) => {
      if (!stage.duration)
        newErrors[`duration-${index}`] = "Required"
      if (!stage.target)
        newErrors[`target-${index}`] = "Required"
    })

    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  const handleSubmit = async () => {
    if (!validate()) return

      setLoading(true)
      setLogs([])
      setShowModal(true)
      setProgress(0)
      setSteps({
        load: "running",
        security_headers: "pending",
        ssl: "pending",
        wpt: "pending",
        lighthouse: "pending",
      })

    const totalSeconds = stages.reduce(
      (acc, stage) =>
        acc + parseDurationToSeconds(stage.duration),
      0
    )

    let elapsed = 0

    try {
      const response = await fetch(`${API_BASE}/api/run`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "x-api-key": API_KEY || "",
        },
        body: JSON.stringify({
          project_name: projectName,
          url,
          stages,
        }),
      })

      if (!response.body) throw new Error("No stream")

      const reader = response.body.getReader()
      const decoder = new TextDecoder()

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        const chunk = decoder.decode(value)
        const lines = chunk.split("\n")

        lines.forEach((line) => {
          if (!line.startsWith("data: ")) return

          const message = line.replace("data: ", "").trim()

          // Real backend error only
          if (message.startsWith("ERROR:")) {
            setToast({
              type: "error",
              message: message.replace("ERROR:", "").trim(),
            })
          }

          // Progress update
          if (message.includes("running")) {
            elapsed += 1
            const percent = Math.min(
              Math.floor((elapsed / totalSeconds) * 100),
              80
            )
            setProgress(percent)
            setLogs((prev) => [...prev, message])
          }

          // Step markers from backend
          if (message.startsWith("PROGRESS:")) {
            const parts = message.split(":")
            // PROGRESS:security_headers:start
            if (parts.length >= 3) {
              const key = parts[1]
              const status = parts[2]
              setSteps((prev) => ({
                ...prev,
                [key]: status === "start" ? "running" : status === "done" ? "done" : status === "skip" ? "skip" : prev[key],
              }))
              if (status === "done" || status === "skip") {
                const weight = stepWeights[key]
                if (weight) {
                  setProgress((p) => Math.max(p, Math.min(weight, 99)))
                }
              }
            }
            return
          }

          // Success
          if (message.startsWith("RUN_ID:")) {
            const id = message.replace("RUN_ID:", "")
            setProgress(100)
            setSteps((prev) => ({ ...prev, load: "done", security_headers: prev.security_headers === "pending" ? "done" : prev.security_headers, ssl: prev.ssl === "pending" ? "done" : prev.ssl, wpt: prev.wpt === "pending" ? "done" : prev.wpt, lighthouse: prev.lighthouse === "pending" ? "done" : prev.lighthouse }))

            setToast({
              type: "success",
              message: "Test completed 🎉",
            })

            setTimeout(() => {
              setShowModal(false)
              router.push(`/result/${id}`)
            }, 1000)
          }
        })
      }
    } catch (err) {
      setToast({
        type: "error",
        message: "Failed to run test",
      })
      setShowModal(false)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-6 relative">

      {/* TOAST */}
      {toast && (
        <div
          className={`fixed top-6 right-6 px-5 py-3 rounded-xl shadow-lg text-sm font-medium animate-slide-in z-50 ${
            toast.type === "error"
              ? "bg-red-500 text-white"
              : "bg-green-600 text-white"
          }`}
        >
          {toast.message}
        </div>
      )}

      {/* PROJECT NAME */}
      <div>
        <label className="block text-sm font-medium mb-2">
          Project Name
        </label>
        <input
          value={projectName}
          onChange={(e) => setProjectName(e.target.value)}
          placeholder="Ecommerce Load Test"
          className={`w-full border rounded-xl px-4 py-2 focus:ring-2 focus:ring-indigo-500 ${
            errors.projectName ? "border-red-500" : ""
          }`}
        />
        {errors.projectName && (
          <p className="text-red-500 text-xs mt-1">
            {errors.projectName}
          </p>
        )}
      </div>

      {/* URL */}
      <div>
        <label className="block text-sm font-medium mb-2">
          Target URL
        </label>
        <input
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          placeholder="https://example.com"
          className={`w-full border rounded-xl px-4 py-2 focus:ring-2 focus:ring-indigo-500 ${
            errors.url ? "border-red-500" : ""
          }`}
        />
        {errors.url && (
          <p className="text-red-500 text-xs mt-1">
            {errors.url}
          </p>
        )}
      </div>

      {/* STAGES */}
      <div>
        <label className="block text-sm font-medium mb-3">
          Load Stages
        </label>

        {stages.map((stage, index) => (
          <div key={index} className="mb-3">
            <div className="flex gap-4 items-center">
              <input
                value={stage.duration}
                placeholder="Duration (ex: 30s, 1m)"
                onChange={(e) => {
                  const updated = [...stages]
                  updated[index].duration = e.target.value
                  setStages(updated)
                }}
                className={`border rounded-xl px-4 py-2 w-1/2 ${
                  errors[`duration-${index}`] ? "border-red-500" : ""
                }`}
              />

              <input
                type="number"
                value={stage.target || ""}
                placeholder="Target VUs"
                onChange={(e) => {
                  const updated = [...stages]
                  updated[index].target = Number(e.target.value)
                  setStages(updated)
                }}
                className={`border rounded-xl px-4 py-2 w-1/2 ${
                  errors[`target-${index}`] ? "border-red-500" : ""
                }`}
              />

              {stages.length > 1 && (
                <button
                  type="button"
                  onClick={() =>
                    setStages(stages.filter((_, i) => i !== index))
                  }
                  className="text-red-500 text-lg px-2"
                >
                  ×
                </button>
              )}
            </div>

            {(errors[`duration-${index}`] ||
              errors[`target-${index}`]) && (
              <p className="text-red-500 text-xs mt-1">
                Duration and target required
              </p>
            )}
          </div>
        ))}

        <button
          type="button"
          onClick={() =>
            setStages([...stages, { duration: "", target: 0 }])
          }
          className="text-indigo-600 text-sm font-medium hover:underline"
        >
          + Add Stage
        </button>
      </div>

      {/* SUBMIT */}
      <button
        onClick={handleSubmit}
        disabled={loading}
        className={`px-6 py-3 rounded-xl text-white font-medium transition ${
          loading
            ? "bg-gray-400 cursor-not-allowed"
            : "bg-indigo-600 hover:bg-indigo-700"
        }`}
      >
        {loading ? "Running..." : "Run Load Test"}
      </button>

      {/* STREAM MODAL */}
      {showModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white w-[600px] max-h-[520px] rounded-2xl p-6 shadow-xl flex flex-col">
            <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
              Running Load Test...
              {loading && (
                <span className="w-2 h-2 bg-indigo-600 rounded-full animate-ping" />
              )}
            </h2>

            <div className="w-full bg-gray-200 rounded-full h-3 mb-2 overflow-hidden">
              <div
                className={`h-full bg-indigo-600 transition-all duration-500 ${
                  loading ? "animate-subtle-pulse" : ""
                }`}
                style={{ width: `${progress}%` }}
              />
            </div>

            <div className="text-sm text-gray-600 mb-4">
              {progress}% Complete
            </div>

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
