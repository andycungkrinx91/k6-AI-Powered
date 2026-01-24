"use client"

import { Menu } from "lucide-react"

export default function Header({
  collapsed,
  setCollapsed,
  setMobileOpen,
}: {
  collapsed: boolean
  setCollapsed: (v: boolean) => void
  setMobileOpen: (v: boolean) => void
}) {
  return (
    <header className="h-16 bg-white border-b border-gray-100 flex items-center px-4 md:px-6 justify-between">

      {/* Mobile Menu Button */}
      <button
        onClick={() => setMobileOpen(true)}
        className="p-2 rounded-lg hover:bg-gray-100 transition lg:hidden"
      >
        <Menu size={20} />
      </button>

      {/* Desktop Collapse Button */}
      <button
        onClick={() => setCollapsed(!collapsed)}
        className="p-2 rounded-lg hover:bg-gray-100 transition hidden lg:block"
      >
        <Menu size={20} />
      </button>

      <div className="text-sm text-gray-500">
        K6 AI Performance Dashboard
      </div>

    </header>
  )
}
