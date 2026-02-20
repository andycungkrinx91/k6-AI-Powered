"use client"

import Link from "next/link"
import { usePathname } from "next/navigation"
import { useEffect, useMemo } from "react"
import {
  LayoutDashboard,
  Play,
  BarChart,
  Heart,
  User,
  Users,
} from "lucide-react"
import { useAuth } from "@/context/AuthContext"
import ThemeFontSwitcher from "@/components/ThemeFontSwitcher"

export default function Sidebar({
  collapsed,
  mobileOpen,
  setMobileOpen,
}: {
  collapsed: boolean
  mobileOpen: boolean
  setMobileOpen: (v: boolean) => void
}) {
  const pathname = usePathname()
  const { user } = useAuth()

  // 🔥 Auto close mobile sidebar on route change
  useEffect(() => {
    setMobileOpen(false)
  }, [pathname, setMobileOpen])

  const navLinks = useMemo(() => {
    const base = [
      { href: "/", label: "Dashboard", icon: LayoutDashboard },
      { href: "/load-test", label: "Run Test", icon: Play },
      { href: "/result", label: "Results", icon: BarChart },
    ]

    if (user) {
      base.push({ href: "/profile", label: "Profile", icon: User })
    }

    if (user?.role === "admin") {
      base.push({ href: "/users", label: "Users", icon: Users })
    }

    return base
  }, [user])

  const linkClass = (path: string) =>
    `flex items-center gap-3 px-4 py-2 rounded-md transition ${
      pathname === path
        ? "bg-terminal-phosphor/15 text-terminal-phosphor font-medium"
        : "hover:bg-terminal-surface2 text-terminal-white"
    }`

  return (
    <>
      {/* Mobile Overlay */}
      <div
        className={`fixed inset-0 bg-black/40 z-40 transition-opacity duration-300 lg:hidden ${
          mobileOpen ? "opacity-100 visible" : "opacity-0 invisible"
        }`}
        onClick={() => setMobileOpen(false)}
      />

      <aside
        className={`
          fixed top-0 left-0 h-full bg-terminal-surface border-r border-terminal-border p-4 z-50
          flex flex-col justify-between
          transform transition-all duration-300 ease-in-out

          ${collapsed ? "lg:w-20" : "lg:w-64"}

          ${
            mobileOpen
              ? "translate-x-0 w-64"
              : "-translate-x-full w-64"
          }

          lg:translate-x-0
        `}
      >
        {/* TOP */}
        <div>
          <div className="mb-6 flex items-center justify-center">
            {!collapsed ? (
              <h1 className="text-xl font-bold text-terminal-phosphor">K6 AI Powered</h1>
            ) : (
              <span className="text-xl font-bold text-terminal-phosphor">K6 AI</span>
            )}
          </div>

          {!collapsed && (
            <div className="mb-6 flex items-center justify-between border border-terminal-border bg-terminal-bg px-3 py-2 rounded-md">
              <div className="text-[11px] uppercase tracking-widest text-terminal-dim">settings</div>
              <ThemeFontSwitcher compact />
            </div>
          )}

          <nav className="space-y-2">
            {navLinks.map((link) => (
              <Link key={link.href} href={link.href} className={linkClass(link.href)}>
                <link.icon size={20} />
                {!collapsed && <span>{link.label}</span>}
              </Link>
            ))}
          </nav>
        </div>

        {/* COPYRIGHT */}
        {!collapsed && (
          <div className="text-xs text-terminal-dim border-t border-terminal-border pt-4 space-y-1">
            <div>
              © 2026{" "}
              <a
                href="https://www.linkedin.com/in/andy-setiyawan-452396170/"
                target="_blank"
                rel="noopener noreferrer"
                className="text-terminal-cyan hover:underline font-medium"
              >
                Andy Setiyawan
              </a>
            </div>

            <div>All Rights Reserved.</div>

            <div className="flex items-center gap-1">
              Made with
              <Heart
                size={12}
                className="text-red-500 animate-heart-pulse"
              />
            </div>
          </div>
        )}
      </aside>
    </>
  )
}
