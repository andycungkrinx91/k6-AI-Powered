"use client"

import { useState } from "react"
import { usePathname } from "next/navigation"
import Header from "@/components/Header"
import Sidebar from "@/components/Sidebar"

export default function AppShell({ children }: { children: React.ReactNode }) {
  const [collapsed, setCollapsed] = useState(false)
  const [mobileOpen, setMobileOpen] = useState(false)
  const pathname = usePathname()
  const isAuthScreen = pathname === "/login"

  // Keep unknown routes (404) clean: render as full-screen without chrome.
  const isKnownAppRoute =
    pathname === "/" ||
    pathname === "/load-test" ||
    pathname === "/users" ||
    pathname === "/profile" ||
    pathname.startsWith("/llm") ||
    pathname.startsWith("/result")
  const isFullScreen = isAuthScreen || !isKnownAppRoute

  if (isFullScreen) {
    return <main className="min-h-screen">{children}</main>
  }

  return (
    <div className="flex min-h-screen">
      <Sidebar
        collapsed={collapsed}
        mobileOpen={mobileOpen}
        setMobileOpen={setMobileOpen}
      />

      <div
        className={`flex-1 min-w-0 flex flex-col transition-all duration-300 ${
          collapsed ? "lg:ml-20" : "lg:ml-64"
        }`}
      >
        <Header
          collapsed={collapsed}
          setCollapsed={setCollapsed}
          setMobileOpen={setMobileOpen}
        />

        <main className="p-4 sm:p-6 md:p-8 min-w-0">{children}</main>
      </div>
    </div>
  )
}
