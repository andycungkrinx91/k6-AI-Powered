"use client"

import { FormEvent, useEffect, useState } from "react"
import { useRouter } from "next/navigation"
import { useAuth } from "@/context/AuthContext"
import { updatePassword } from "@/lib/api"
import Card from "@/components/Card"

export default function ProfilePage() {
  const { user, token, ready } = useAuth()
  const router = useRouter()
  const [currentPassword, setCurrentPassword] = useState("")
  const [newPassword, setNewPassword] = useState("")
  const [confirmPassword, setConfirmPassword] = useState("")
  const [status, setStatus] = useState<{ type: "success" | "error"; message: string } | null>(null)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if (ready && !user) {
      router.replace("/login")
    }
  }, [ready, user, router])

  if (!ready || !user || !token) {
    return null
  }

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault()
    if (newPassword !== confirmPassword) {
      setStatus({ type: "error", message: "New passwords must match" })
      return
    }

    setLoading(true)
    setStatus(null)

    try {
      await updatePassword({ current_password: currentPassword, new_password: newPassword }, token)
      setStatus({ type: "success", message: "Password updated successfully" })
      setCurrentPassword("")
      setNewPassword("")
      setConfirmPassword("")
    } catch (error: any) {
      setStatus({ type: "error", message: error?.message || "Unable to update password" })
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-8 pb-10 min-h-screen">
      <Card title="PROFILE">
        <div className="text-xs text-terminal-dim">user</div>
        <div className="flex flex-col gap-2 mt-3">
          <div className="text-2xl font-semibold text-terminal-white">{user.username}</div>
          <div className="text-sm text-terminal-dim break-all">{user.email}</div>
          <div className="text-xs font-semibold inline-flex items-center gap-2 px-3 py-1 border border-terminal-border text-terminal-cyan w-max">
            {user.role === "admin" ? "Administrator" : "Standard user"}
          </div>
        </div>
      </Card>

      <Card title="UPDATE PASSWORD">
        <div className="flex items-center justify-between">
          <span className="text-xs text-terminal-dim">protected area</span>
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
          <div>
            <label className="text-xs uppercase tracking-wider text-terminal-dim">Current password</label>
            <input
              type="password"
              value={currentPassword}
              onChange={(event) => setCurrentPassword(event.target.value)}
              className="mt-2 w-full px-4 py-3 text-sm"
            />
          </div>

          <div>
            <label className="text-xs uppercase tracking-wider text-terminal-dim">New password</label>
            <input
              type="password"
              value={newPassword}
              onChange={(event) => setNewPassword(event.target.value)}
              className="mt-2 w-full px-4 py-3 text-sm"
            />
          </div>

          <div>
            <label className="text-xs uppercase tracking-wider text-terminal-dim">Confirm password</label>
            <input
              type="password"
              value={confirmPassword}
              onChange={(event) => setConfirmPassword(event.target.value)}
              className="mt-2 w-full px-4 py-3 text-sm"
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full px-4 py-3 border border-terminal-phosphor text-terminal-phosphor bg-transparent text-sm font-semibold uppercase tracking-widest hover:bg-terminal-phosphor hover:text-black disabled:opacity-60"
          >
            {loading ? "Updating…" : "Save changes"}
          </button>
        </form>
      </Card>
    </div>
  )
}
