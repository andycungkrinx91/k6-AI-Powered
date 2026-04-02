"use client"

import { FormEvent, useEffect, useState } from "react"
import { useRouter } from "next/navigation"
import { useAuth } from "@/context/AuthContext"
import { getLLMSettings, testLLMConnection, updateLLMSettings } from "@/lib/api"
import Card from "@/components/Card"

export default function LLMSettingsPage() {
  const { user, token, ready } = useAuth()
  const router = useRouter()

  // LLM Settings state
  const [llmProvider, setLlmProvider] = useState<"gemini" | "openai" | "local">("gemini")
  const [geminiApiKey, setGeminiApiKey] = useState("")
  const [geminiModel, setGeminiModel] = useState("")
  const [openaiApiKey, setOpenaiApiKey] = useState("")
  const [openaiModel, setOpenaiModel] = useState("")
  const [openaiBaseUrl, setOpenaiBaseUrl] = useState("")
  const [temperature, setTemperature] = useState("0.2")
  const [maxTokens, setMaxTokens] = useState("2048")
  const [status, setStatus] = useState<{ type: "success" | "error"; message: string } | null>(null)
  const [loading, setLoading] = useState(false)
  const [testLoading, setTestLoading] = useState(false)
  const [loaded, setLoaded] = useState(false)

  useEffect(() => {
    if (ready && !user) {
      router.replace("/login")
    }
  }, [ready, user, router])

  // Load LLM settings on mount
  useEffect(() => {
    if (token && user && !loaded) {
      getLLMSettings(token)
        .then((settings) => {
          setLlmProvider(settings.provider)
          setGeminiApiKey(settings.gemini_api_key || "")
          setGeminiModel(settings.gemini_model || "")
          setOpenaiApiKey(settings.openai_api_key || "")
          setOpenaiModel(settings.openai_model || "")
          setOpenaiBaseUrl(settings.openai_base_url || "")
          setTemperature(settings.temperature)
          setMaxTokens(settings.max_tokens)
          setLoaded(true)
        })
        .catch(() => {
          setLoaded(true)
        })
    }
  }, [token, user, loaded])

  const buildPayload = () => ({
    provider: llmProvider,
    gemini_api_key: geminiApiKey || null,
    gemini_model: geminiModel || null,
    openai_api_key: openaiApiKey || null,
    openai_model: openaiModel || null,
    openai_base_url: openaiBaseUrl || null,
    temperature,
    max_tokens: maxTokens,
  })

  const getErrorMessage = (error: any, fallback: string) => {
    const raw = error?.message || fallback

    try {
      const parsed = JSON.parse(raw)
      return parsed?.detail || raw
    } catch {
      return raw
    }
  }

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault()

    setLoading(true)
    setStatus(null)

    if (!token) {
      setStatus({ type: "error", message: "Missing authentication token. Please sign in again." })
      setLoading(false)
      return
    }

    try {
      await updateLLMSettings(buildPayload(), token)
      setStatus({ type: "success", message: "LLM settings saved successfully" })
    } catch (error: any) {
      setStatus({ type: "error", message: getErrorMessage(error, "Unable to save LLM settings") })
    } finally {
      setLoading(false)
    }
  }

  const handleTestConnection = async () => {
    setTestLoading(true)
    setStatus(null)

    if (!token) {
      setStatus({ type: "error", message: "Missing authentication token. Please sign in again." })
      setTestLoading(false)
      return
    }

    try {
      const result = await testLLMConnection(buildPayload(), token)
      setStatus({ type: "success", message: result.message || "Connection test successful" })
    } catch (error: any) {
      setStatus({ type: "error", message: getErrorMessage(error, "Connection test failed") })
    } finally {
      setTestLoading(false)
    }
  }

  if (!ready) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-sm text-terminal-dim">Loading...</div>
      </div>
    )
  }

  if (!user) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-sm text-terminal-dim">Redirecting...</div>
      </div>
    )
  }

  return (
    <div className="space-y-8 pb-10 min-h-screen">
      <div>
        <h1 className="text-3xl font-bold text-terminal-white">LLM Settings</h1>
        <p className="text-sm text-terminal-dim mt-1">Configure your AI provider for analysis</p>
      </div>

      <Card title="AI PROVIDER CONFIGURATION">
        <div className="flex items-center justify-between">
          <span className="text-xs text-terminal-dim">select your preferred AI provider</span>
        </div>

        {status && (
          <div
            className={`border px-4 py-3 text-sm ${
              status.type === "success"
                ? "border-terminal-cyan text-terminal-cyan bg-terminal-cyan/10"
                : "border-terminal-magenta text-terminal-magenta bg-terminal-magenta/10"
            }`}
          >
            {status.message}
          </div>
        )}

        <form className="space-y-4" onSubmit={handleSubmit}>
          {/* Provider Selection */}
          <div>
            <label className="text-xs uppercase tracking-wider text-terminal-dim">Provider</label>
            <select
              value={llmProvider}
              onChange={(e) => setLlmProvider(e.target.value as "gemini" | "openai" | "local")}
              className="mt-2 w-full px-4 py-3 text-sm bg-black border border-terminal-border text-terminal-white"
            >
              <option value="gemini">Google Gemini</option>
              <option value="openai">OpenAI (api.openai.com)</option>
              <option value="local">Local / OpenAI-Compatible (vLLM, Ollama)</option>
            </select>
            <div className="text-xs text-terminal-dim mt-1">
              {llmProvider === "gemini" && "Use Google Gemini API for AI analysis"}
              {llmProvider === "openai" && "Use OpenAI's official API (requires billing)"}
              {llmProvider === "local" && "Use local LLM server (vLLM, Ollama, etc.)"}
            </div>
          </div>

          {/* Gemini Settings */}
          {llmProvider === "gemini" && (
            <>
              <div>
                <label className="text-xs uppercase tracking-wider text-terminal-dim">Gemini API Key</label>
                <input
                  type="password"
                  value={geminiApiKey}
                  onChange={(event) => setGeminiApiKey(event.target.value)}
                  placeholder="Enter your Gemini API key"
                  className="mt-2 w-full px-4 py-3 text-sm"
                />
                <div className="text-xs text-terminal-dim mt-1">
                  Get your key from{" "}
                  <a
                    href="https://aistudio.google.com/app/apikey"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-terminal-cyan underline"
                  >
                    Google AI Studio
                  </a>
                </div>
              </div>
              <div>
                <label className="text-xs uppercase tracking-wider text-terminal-dim">Gemini Model (optional)</label>
                <input
                  type="text"
                  value={geminiModel}
                  onChange={(event) => setGeminiModel(event.target.value)}
                  placeholder="gemini-2.5-flash"
                  className="mt-2 w-full px-4 py-3 text-sm"
                />
              </div>
            </>
          )}

          {/* OpenAI Settings */}
          {llmProvider === "openai" && (
            <>
              <div>
                <label className="text-xs uppercase tracking-wider text-terminal-dim">OpenAI API Key</label>
                <input
                  type="password"
                  value={openaiApiKey}
                  onChange={(event) => setOpenaiApiKey(event.target.value)}
                  placeholder="sk-..."
                  className="mt-2 w-full px-4 py-3 text-sm"
                />
                <div className="text-xs text-terminal-dim mt-1">
                  Get your key from{" "}
                  <a
                    href="https://platform.openai.com/api-keys"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-terminal-cyan underline"
                  >
                    OpenAI Platform
                  </a>
                </div>
              </div>
              <div>
                <label className="text-xs uppercase tracking-wider text-terminal-dim">OpenAI Model (optional)</label>
                <input
                  type="text"
                  value={openaiModel}
                  onChange={(event) => setOpenaiModel(event.target.value)}
                  placeholder="gpt-4o"
                  className="mt-2 w-full px-4 py-3 text-sm"
                />
              </div>
            </>
          )}

          {/* Local / OpenAI-Compatible Settings */}
          {llmProvider === "local" && (
            <>
              <div>
                <label className="text-xs uppercase tracking-wider text-terminal-dim">Base URL</label>
                <input
                  type="text"
                  value={openaiBaseUrl}
                  onChange={(event) => setOpenaiBaseUrl(event.target.value)}
                  placeholder="http://localhost:8000/v1"
                  className="mt-2 w-full px-4 py-3 text-sm"
                />
                <div className="text-xs text-terminal-dim mt-1">
                  Enter the base URL for your local LLM server (vLLM, Ollama, etc.)
                </div>
              </div>
              <div>
                <label className="text-xs uppercase tracking-wider text-terminal-dim">Model Name</label>
                <input
                  type="text"
                  value={openaiModel}
                  onChange={(event) => setOpenaiModel(event.target.value)}
                  placeholder="e.g., gpt-4o, llama3, qwen2.5"
                  className="mt-2 w-full px-4 py-3 text-sm"
                />
              </div>
              <div>
                <label className="text-xs uppercase tracking-wider text-terminal-dim">API Key (optional)</label>
                <input
                  type="password"
                  value={openaiApiKey}
                  onChange={(event) => setOpenaiApiKey(event.target.value)}
                  placeholder="Leave empty for no auth"
                  className="mt-2 w-full px-4 py-3 text-sm"
                />
              </div>
            </>
          )}

          {/* Common Settings */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="text-xs uppercase tracking-wider text-terminal-dim">Temperature</label>
              <input
                type="text"
                value={temperature}
                onChange={(event) => setTemperature(event.target.value)}
                placeholder="0.2"
                className="mt-2 w-full px-4 py-3 text-sm"
              />
            </div>
            <div>
              <label className="text-xs uppercase tracking-wider text-terminal-dim">Max Tokens</label>
              <input
                type="text"
                value={maxTokens}
                onChange={(event) => setMaxTokens(event.target.value)}
                placeholder="2048"
                className="mt-2 w-full px-4 py-3 text-sm"
              />
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <button
              type="button"
              onClick={handleTestConnection}
              disabled={loading || testLoading}
              className="w-full px-4 py-3 border border-terminal-cyan text-terminal-cyan bg-transparent text-sm font-semibold uppercase tracking-widest hover:bg-terminal-cyan hover:text-black disabled:opacity-60"
            >
              {testLoading ? "Testing…" : "Test Connect"}
            </button>
            <button
              type="submit"
              disabled={loading || testLoading}
              className="w-full px-4 py-3 border border-terminal-phosphor text-terminal-phosphor bg-transparent text-sm font-semibold uppercase tracking-widest hover:bg-terminal-phosphor hover:text-black disabled:opacity-60"
            >
              {loading ? "Saving…" : "Save Settings"}
            </button>
          </div>
        </form>
      </Card>

      <Card title="ABOUT">
        <div className="text-sm text-terminal-dim space-y-2">
          <p>
            The AI analysis uses your configured LLM provider to analyze k6 load test results,
            security headers, SSL/TLS configuration, WebPageTest data, and Lighthouse metrics.
          </p>
          <p>
            If you don&apos;t configure your own API key, the system will use the global configuration
            set by the administrator.
          </p>
        </div>
      </Card>
    </div>
  )
}
