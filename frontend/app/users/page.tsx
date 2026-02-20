"use client"

import { FormEvent, useEffect, useState } from "react"
import { useRouter } from "next/navigation"
import { createUser, fetchUsers } from "@/lib/api"
import { useAuth } from "@/context/AuthContext"

type UserRow = {
  id: string
  username: string
  email: string
  role: "admin" | "user"
  created_at: string | null
}

export default function UsersPage() {
  const { user, token, ready, isAdmin } = useAuth()
  const router = useRouter()
  const [users, setUsers] = useState<UserRow[]>([])
  const [loading, setLoading] = useState(false)
  const [status, setStatus] = useState<{ type: "success" | "error"; message: string } | null>(null)
  const [form, setForm] = useState({ username: "", email: "", password: "", role: "user" })
  const [creating, setCreating] = useState(false)

  useEffect(() => {
    if (ready && !user) {
      router.replace("/login")
    }
  }, [ready, user, router])

  useEffect(() => {
    if (ready && user && !isAdmin) {
      router.replace("/")
    }
  }, [ready, user, isAdmin, router])

  useEffect(() => {
    if (!ready || !isAdmin) return
    if (!token) return

    let cancelled = false
    setLoading(true)
    fetchUsers(token)
      .then((data) => {
        if (!cancelled) {
          setUsers(data)
        }
      })
      .catch((error) => {
        setStatus({ type: "error", message: error?.message || "Unable to load users" })
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })

    return () => {
      cancelled = true
    }
  }, [ready, token, isAdmin])

  if (!ready || !user || !isAdmin) {
    return null
  }

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault()
    if (!token) return
    setCreating(true)
    setStatus(null)

    try {
      await createUser({
        username: form.username,
        email: form.email,
        password: form.password,
        role: form.role as "admin" | "user",
      }, token)
      setStatus({ type: "success", message: "User created" })
      setForm({ username: "", email: "", password: "", role: "user" })
      const refreshed = await fetchUsers(token)
      setUsers(refreshed)
    } catch (error: any) {
      setStatus({ type: "error", message: error?.message || "Could not create user" })
    } finally {
      setCreating(false)
    }
  }

  return (
    <div className="space-y-6 pb-10">
      <div className="border border-terminal-border bg-terminal-surface shadow-terminal p-8">
        <div className="flex flex-col gap-2">
          <p className="text-xs uppercase tracking-[0.3em] text-terminal-dim">Administrator</p>
          <h1 className="text-2xl font-semibold text-terminal-phosphor">Manage user accounts</h1>
          <p className="text-sm text-terminal-dim">
            Create administrator or load test users that can authenticate into the dashboard.
          </p>
        </div>

        <form onSubmit={handleSubmit} className="mt-6 grid gap-4 md:grid-cols-2">
          <div>
            <label className="text-xs uppercase tracking-wide text-terminal-dim">Username</label>
            <input
              value={form.username}
              onChange={(event) => setForm((prev) => ({ ...prev, username: event.target.value }))}
              className="mt-2 w-full px-4 py-3 text-sm"
              placeholder="andy"
              required
            />
          </div>

          <div>
            <label className="text-xs uppercase tracking-wide text-terminal-dim">Email</label>
            <input
              type="email"
              value={form.email}
              onChange={(event) => setForm((prev) => ({ ...prev, email: event.target.value }))}
              className="mt-2 w-full px-4 py-3 text-sm"
              placeholder="andy@example.com"
              required
            />
          </div>

          <div>
            <label className="text-xs uppercase tracking-wide text-terminal-dim">Password</label>
            <input
              type="password"
              value={form.password}
              onChange={(event) => setForm((prev) => ({ ...prev, password: event.target.value }))}
              className="mt-2 w-full px-4 py-3 text-sm"
              placeholder="strong password"
              required
            />
          </div>

          <div>
            <label className="text-xs uppercase tracking-wide text-terminal-dim">Role</label>
            <select
              value={form.role}
              onChange={(event) => setForm((prev) => ({ ...prev, role: event.target.value }))}
              className="mt-2 w-full px-4 py-3 text-sm"
            >
              <option value="user">Load Test User</option>
              <option value="admin">Administrator</option>
            </select>
          </div>

          <div className="md:col-span-2">
            <button
              type="submit"
              disabled={creating}
              className="w-full px-4 py-3 border border-terminal-phosphor text-terminal-phosphor bg-transparent text-sm font-semibold uppercase tracking-widest hover:bg-terminal-phosphor hover:text-black disabled:opacity-60"
            >
              {creating ? "Creating…" : "Create user"}
            </button>
          </div>
        </form>

        {status && (
          <p
            className={`mt-4 text-sm ${
              status.type === "success" ? "text-terminal-cyan" : "text-terminal-magenta"
            }`}
          >
            {status.message}
          </p>
        )}
      </div>

      <div className="border border-terminal-border bg-terminal-surface shadow-terminal p-8">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold text-terminal-phosphor">User directory</h2>
          <span className="text-xs text-terminal-dim">Showing {users.length} items</span>
        </div>

        <div className="mt-4 overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-terminal-surface2 border-b border-terminal-border sticky top-0">
              <tr className="text-left text-terminal-dim uppercase text-xs tracking-wider">
                <th className="px-6 py-4">User ID</th>
                <th className="px-6 py-4">Username</th>
                <th className="px-6 py-4">Email</th>
                <th className="px-6 py-4">Role</th>
                <th className="px-6 py-4">Created</th>
              </tr>
            </thead>
            <tbody className="divide-y">
              {loading ? (
                <tr>
                  <td colSpan={5} className="px-6 py-4 text-center text-terminal-dim">
                    Loading users…
                  </td>
                </tr>
              ) : users.length === 0 ? (
                <tr>
                  <td colSpan={5} className="px-6 py-4 text-center text-terminal-dim">
                    No users yet.
                  </td>
                </tr>
              ) : (
                users.map((row) => (
                  <tr key={row.id} className="hover:bg-terminal-surface2 transition-none">
                    <td className="px-6 py-4 font-mono text-xs text-terminal-dim break-all">{row.id}</td>
                    <td className="px-6 py-4 font-semibold text-terminal-cyan">{row.username}</td>
                    <td className="px-6 py-4 text-terminal-white break-all">{row.email}</td>
                    <td className="px-6 py-4">
                      <span className={`px-3 py-1 border text-xs font-semibold ${row.role === "admin" ? "border-terminal-phosphor text-terminal-phosphor" : "border-terminal-border text-terminal-white"}`}>
                        {row.role === "admin" ? "Admin" : "User"}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-terminal-dim text-xs">
                      {row.created_at
                        ? new Date(row.created_at)
                            .toISOString()
                            .replace("T", " ")
                            .slice(0, 19)
                        : "-"}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
