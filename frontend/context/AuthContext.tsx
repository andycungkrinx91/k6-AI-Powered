"use client"

import { useRouter } from "next/navigation"
import { createContext, useContext, useEffect, useState } from "react"
import { login as loginRequest, LoginPayload } from "@/lib/api"
import { AuthUser } from "@/types/auth"

const STORAGE_KEY = "k6-ai-auth"

type StoredSession = {
  user?: AuthUser | null
  token?: string | null
}

function readSession(): StoredSession | null {
  if (typeof window === "undefined") return null
  const raw = window.localStorage.getItem(STORAGE_KEY)
  if (!raw) return null
  try {
    return JSON.parse(raw)
  } catch (error) {
    console.warn("Failed to parse auth payload", error)
    return null
  }
}

type AuthContextValue = {
  user: AuthUser | null
  token: string | null
  ready: boolean
  isAdmin: boolean
  login: (payload: LoginPayload) => Promise<AuthUser>
  logout: () => void
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined)

function persistSession(token: string | null, user: AuthUser | null) {
  if (typeof window === "undefined") return
  if (token && user) {
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify({ token, user }))
    return
  }
  window.localStorage.removeItem(STORAGE_KEY)
}

export function AuthProvider({ children }: { children: React.ReactNode }) {
  // IMPORTANT: keep initial render deterministic for SSR hydration.
  // Load any persisted session only after mount.
  const [user, setUser] = useState<AuthUser | null>(null)
  const [token, setToken] = useState<string | null>(null)
  const [ready, setReady] = useState(false)
  const router = useRouter()

  useEffect(() => {
    const cached = readSession()
    setUser(cached?.user ?? null)
    setToken(cached?.token ?? null)
    setReady(true)
  }, [])

  const login = async (payload: LoginPayload) => {
    const payloadData = await loginRequest(payload)
    setUser(payloadData.user)
    setToken(payloadData.access_token)
    persistSession(payloadData.access_token, payloadData.user)
    return payloadData.user
  }

  const logout = () => {
    setUser(null)
    setToken(null)
    persistSession(null, null)
    router.push("/login")
  }

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        ready,
        isAdmin: !!user && user.role === "admin",
        login,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error("useAuth must be used within AuthProvider")
  }
  return context
}
