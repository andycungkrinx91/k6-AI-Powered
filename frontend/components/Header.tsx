"use client"

import Link from "next/link"
import { Menu, CircleUser } from "lucide-react"
import { useAuth } from "@/context/AuthContext"

export default function Header({
  collapsed,
  setCollapsed,
  setMobileOpen,
}: {
  collapsed: boolean
  setCollapsed: (v: boolean) => void
  setMobileOpen: (v: boolean) => void
}) {
  const { user, logout, ready } = useAuth()

  return (
    <header className="h-20 bg-terminal-surface border-b border-terminal-border flex items-center px-4 md:px-6 justify-between gap-4">

      <div className="flex items-center gap-3">
        <button
          onClick={() => setMobileOpen(true)}
          className="p-2 rounded-md hover:bg-terminal-surface2 transition lg:hidden"
        >
          <Menu size={20} />
        </button>

        <button
          onClick={() => setCollapsed(!collapsed)}
          className="p-2 rounded-md hover:bg-terminal-surface2 transition hidden lg:block"
        >
          <Menu size={20} />
        </button>

        {user && (
          <p className="text-sm text-terminal-phosphor font-semibold whitespace-nowrap">
            Welcome {user.username}, lets do a great work today! <span className="cursor-block" aria-hidden="true" />
          </p>
        )}
      </div>

      <div className="flex items-center gap-3">
        {user ? (
          <>
            <Link
              href="/profile"
              className="p-2 rounded-md border border-terminal-border text-terminal-cyan hover:text-terminal-white hover:bg-terminal-surface2"
              aria-label="Profile"
            >
              <CircleUser size={18} />
            </Link>
            <button
              onClick={logout}
              className="px-4 py-2 border border-terminal-phosphor text-terminal-phosphor bg-transparent text-sm font-medium hover:bg-terminal-phosphor hover:text-black"
            >
              Sign out
            </button>
          </>
        ) : ready ? (
          <Link
            href="/login"
            className="px-4 py-2 border border-terminal-phosphor text-terminal-phosphor bg-transparent text-sm font-medium hover:bg-terminal-phosphor hover:text-black"
          >
            Sign in
          </Link>
        ) : null}
      </div>

    </header>
  )
}
