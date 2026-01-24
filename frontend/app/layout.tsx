"use client"

import "./global.css"
import { useState } from "react"
import Header from "@/components/Header"
import Sidebar from "@/components/Sidebar"

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  const [collapsed, setCollapsed] = useState(false)
  const [mobileOpen, setMobileOpen] = useState(false)

  return (
    <html lang="en">
      <body className="bg-gray-50 text-gray-900">
        <div className="flex min-h-screen">

          <Sidebar
            collapsed={collapsed}
            mobileOpen={mobileOpen}
            setMobileOpen={setMobileOpen}
          />

          <div
            className={`flex-1 flex flex-col transition-all duration-300 ${
              collapsed ? "lg:ml-20" : "lg:ml-64"
            }`}
          >
            <Header
              collapsed={collapsed}
              setCollapsed={setCollapsed}
              setMobileOpen={setMobileOpen}
            />

            <main className="p-6 md:p-8">
              {children}
            </main>

          </div>

        </div>
      </body>
    </html>
  )
}
