"use client"

export const dynamic = "force-dynamic"

import { useEffect, useState } from "react"
import { useRouter } from "next/navigation"
import { getResultsList } from "@/lib/api"
import Link from "next/link"
import { motion, AnimatePresence } from "framer-motion"
import { useAuth } from "@/context/AuthContext"

interface ResultItem {
  id: string
  project_name: string
  url: string
  status: string
  created_at: string
  score?: number | null
  grade?: string | null
  error_rate?: number | null
  security_grade?: string | number | null
  ssl_grade?: string | null
  wpt_grade?: string | null
  lighthouse_score?: number | null
  run_by?: {
    id?: string
    username?: string
  }
}

const ITEMS_PER_PAGE = 8

export default function ResultPage() {
  const router = useRouter()
  const { user, token, ready } = useAuth()
  const [results, setResults] = useState<ResultItem[]>([])
  const [search, setSearch] = useState("")
  const [page, setPage] = useState(1)
  const [total, setTotal] = useState(0)

  useEffect(() => {
    if (!token) {
      return
    }

    async function load() {
      try {
        const res = await getResultsList(
          {
            limit: ITEMS_PER_PAGE,
            offset: (page - 1) * ITEMS_PER_PAGE,
            q: search || undefined,
          },
          token
        )
        setResults(res.items as ResultItem[])
        setTotal(res.total || 0)
      } catch (error) {
        console.error("Failed to load results", error)
      }
    }

    load()
  }, [token, page, search])

  useEffect(() => {
    if (ready && !user) {
      router.replace("/login")
    }
  }, [ready, user, router])

    if (!ready || !user) {
      return (
        <div className="min-h-screen flex items-center justify-center">
          <div className="text-sm text-terminal-dim">Preparing results…</div>
        </div>
      )
    }

  const totalPages = Math.max(1, Math.ceil(total / ITEMS_PER_PAGE))

  const nextPage = () => {
    if (page < totalPages) setPage((p) => p + 1)
  }

  const prevPage = () => {
    if (page > 1) setPage((p) => p - 1)
  }

  const getBadge = (val: any) => {
    if (val === undefined || val === null || val === "") {
      return <span className="px-2 py-1 text-xs text-gray-400">N/A</span>
    }

    const str = String(val)
    let grade = str

    if (/^\d+$/.test(str)) {
      const num = Number(str)
      if (num >= 97) grade = "A+"
      else if (num >= 93) grade = "A"
      else if (num >= 87) grade = "B"
      else if (num >= 78) grade = "C"
      else if (num >= 70) grade = "D"
      else grade = "F"
    }

    const leading = grade.charAt(0)
    const colors: Record<string, string> = {
      A: "bg-green-100 text-green-700",
      B: "bg-blue-100 text-blue-700",
      C: "bg-yellow-100 text-yellow-700",
      D: "bg-orange-100 text-orange-700",
      E: "bg-orange-200 text-orange-800",
      F: "bg-red-100 text-red-700",
    }

    const color = colors[leading] || "bg-gray-100 text-gray-700"

    return (
      <span className={`px-3 py-1 text-xs rounded-full font-semibold ${color}`}>
        {grade}
      </span>
    )
  }

  return (
    <motion.div
      initial={{ opacity: 0, x: 30 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ duration: 0.4 }}
      className="space-y-6 pb-10"
    >
      <h1 className="text-2xl font-semibold text-terminal-phosphor">Result History</h1>

      {/* Sticky Mobile Search */}
      <div className="md:static sticky top-0 z-10 bg-terminal-bg py-3">
        <input
          type="text"
          placeholder="Search by Run ID or Project Name"
          value={search}
          onChange={(e) => {
            setSearch(e.target.value)
            setPage(1)
          }}
          className="w-full px-4 py-3 text-sm"
        />
      </div>

      {/* DESKTOP TABLE */}
      <div className="hidden md:block border border-terminal-border bg-terminal-surface shadow-terminal">
        <table className="w-full text-sm">
          <thead className="bg-terminal-surface2 border-b border-terminal-border sticky top-0">
            <tr className="text-left text-terminal-dim uppercase text-xs tracking-wider">
              <th className="px-6 py-4">Run ID</th>
              <th className="px-6 py-4">Project</th>
              <th className="px-6 py-4">SLA</th>
              <th className="px-6 py-4">Sec</th>
              <th className="px-6 py-4">SSL</th>
              <th className="px-6 py-4">WPT</th>
              <th className="px-6 py-4">LH</th>
              <th className="px-6 py-4">Run By</th>
              <th className="px-6 py-4">Created</th>
              <th className="px-6 py-4 text-right">Action</th>
            </tr>
          </thead>

          <tbody className="divide-y">
            <AnimatePresence>
            {results.map((r) => {
                const grade = r.grade ?? null
                const secGrade = r.security_grade ?? "N/A"
                const sslGrade = r.ssl_grade ?? "N/A"
                const wptGrade = r.wpt_grade ?? "N/A"
                const lhScore = r.lighthouse_score ?? "N/A"
                const runBy = r.run_by || { username: "system" }

              return (
                <motion.tr
                    key={r.id}
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0 }}
                    transition={{ duration: 0.25 }}
                  className="hover:bg-terminal-surface2"
                >
                    <td className="px-6 py-4 font-mono text-xs">{r.id}</td>
                    <td className="px-6 py-4 font-semibold text-terminal-amber">
                      {r.project_name}
                    </td>
                    <td className="px-6 py-4">{getBadge(grade)}</td>
                    <td className="px-6 py-4 text-xs">{getBadge(secGrade)}</td>
                    <td className="px-6 py-4 text-xs">{getBadge(sslGrade)}</td>
                    <td className="px-6 py-4 text-xs">{getBadge(wptGrade)}</td>
                    <td className="px-6 py-4 text-xs">{getBadge(lhScore)}</td>
                    <td className="px-6 py-4 text-xs text-terminal-dim">{runBy.username}</td>
                    <td className="px-6 py-4 text-xs text-terminal-dim">
                      {new Date(r.created_at).toISOString().replace("T", " ").slice(0, 19)}
                    </td>
                    <td className="px-6 py-4 text-right">
                      <Link
                        href={`/result/${r.id}`}
                        className="px-4 py-2 border border-terminal-phosphor text-terminal-phosphor hover:bg-terminal-phosphor hover:text-black text-xs"
                      >
                        View
                      </Link>
                    </td>
                  </motion.tr>
                )
              })}
            </AnimatePresence>
          </tbody>
        </table>
      </div>

      {/* MOBILE CARD VIEW with Swipe */}
      <div className="md:hidden overflow-hidden">
        <motion.div
          key={page}
          drag="x"
          dragConstraints={{ left: 0, right: 0 }}
          onDragEnd={(e, info) => {
            if (info.offset.x < -50) nextPage()
            if (info.offset.x > 50) prevPage()
          }}
          initial={{ x: 100, opacity: 0 }}
          animate={{ x: 0, opacity: 1 }}
          exit={{ x: -100, opacity: 0 }}
          transition={{ duration: 0.3 }}
          className="space-y-4"
        >
          {results.map((r) => {
            const grade = r.grade ?? null
            const secGrade = r.security_grade ?? "N/A"
            const sslGrade = r.ssl_grade ?? "N/A"
            const wptGrade = r.wpt_grade ?? "N/A"
            const lhScore = r.lighthouse_score ?? "N/A"
            const runBy = r.run_by || { username: "system" }

            return (
              <motion.div
                key={r.id}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.25 }}
                className="border border-terminal-border bg-terminal-surface shadow-terminal p-4 space-y-3"
              >
                <div className="text-xs font-mono break-all text-terminal-dim">
                  {r.id}
                </div>

                <div className="font-semibold text-lg text-terminal-amber">
                  {r.project_name}
                </div>

                <div className="text-xs text-terminal-dim">
                  Run by {runBy.username}
                </div>

                <div className="flex justify-between text-sm">
                  <span>SLA</span>
                  {getBadge(grade)}
                </div>

                <div className="grid grid-cols-2 gap-2 text-[11px] text-terminal-dim">
                  <LabelValue label="Sec" value={getBadge(secGrade)} />
                  <LabelValue label="SSL" value={getBadge(sslGrade)} />
                  <LabelValue label="WPT" value={getBadge(wptGrade)} />
                  <LabelValue label="LH" value={getBadge(lhScore)} />
                </div>

                <div className="text-xs text-terminal-dim">
                  {new Date(r.created_at).toISOString().replace("T", " ").slice(0, 19)}
                </div>

                <Link
                  href={`/result/${r.id}`}
                  className="block text-center border border-terminal-phosphor text-terminal-phosphor py-2 rounded-md text-sm hover:bg-terminal-phosphor hover:text-black"
                >
                  View Result
                </Link>
              </motion.div>
            )
          })}
        </motion.div>
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex justify-center gap-4 pt-4">
          <button
            onClick={prevPage}
            disabled={page === 1}
            className="px-4 py-2 border border-terminal-border rounded-md disabled:opacity-40 hover:bg-terminal-surface2"
          >
            Prev
          </button>

          <span className="text-sm font-medium">
            Page {page} / {totalPages}
          </span>

          <button
            onClick={nextPage}
            disabled={page === totalPages}
            className="px-4 py-2 border border-terminal-border rounded-md disabled:opacity-40 hover:bg-terminal-surface2"
          >
            Next
          </button>
        </div>
      )}
    </motion.div>
  )
}

function LabelValue({ label, value }: { label: string; value: any }) {
  return (
    <div className="flex items-center justify-between bg-gray-50 border border-gray-100 rounded-lg px-2 py-1">
      <span className="text-gray-500">{label}</span>
      <span className="font-semibold text-gray-800">{value ?? "N/A"}</span>
    </div>
  )
}
