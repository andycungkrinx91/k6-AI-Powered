"use client"

import Link from "next/link"
import { usePathname } from "next/navigation"
import { useEffect } from "react"
import {
  LayoutDashboard,
  Play,
  BarChart,
  Heart,
} from "lucide-react"

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

  // 🔥 Auto close mobile sidebar on route change
  useEffect(() => {
    setMobileOpen(false)
  }, [pathname, setMobileOpen])

  const linkClass = (path: string) =>
    `flex items-center gap-3 px-4 py-2 rounded-xl transition ${
      pathname === path
        ? "bg-indigo-50 text-indigo-600 font-medium"
        : "hover:bg-gray-100 text-gray-700"
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
          fixed top-0 left-0 h-full bg-white border-r border-gray-100 p-4 z-50
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
          <div className="mb-10 flex items-center justify-center">
            {!collapsed ? (
              <h1 className="text-xl font-bold">K6 AI Powered</h1>
            ) : (
              <span className="text-xl font-bold">K6 AI</span>
            )}
          </div>

          <nav className="space-y-2">
            <Link href="/" className={linkClass("/")}>
              <LayoutDashboard size={20} />
              {!collapsed && <span>Dashboard</span>}
            </Link>

            <Link href="/load-test" className={linkClass("/load-test")}>
              <Play size={20} />
              {!collapsed && <span>Run Test</span>}
            </Link>

            <Link href="/result" className={linkClass("/result")}>
              <BarChart size={20} />
              {!collapsed && <span>Results</span>}
            </Link>
          </nav>
        </div>

        {/* COPYRIGHT */}
        {!collapsed && (
          <div className="text-xs text-gray-400 border-t border-gray-100 pt-4 space-y-1">
            <div>
              © 2026{" "}
              <a
                href="https://www.linkedin.com/in/andy-setiyawan-452396170/"
                target="_blank"
                rel="noopener noreferrer"
                className="text-indigo-600 hover:underline font-medium"
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
