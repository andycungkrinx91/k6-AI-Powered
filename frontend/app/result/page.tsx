"use client"

export const dynamic = "force-dynamic"

import { useEffect, useState } from "react"
import { getResults } from "@/lib/api"
import Link from "next/link"
import { motion, AnimatePresence } from "framer-motion"

interface ResultItem {
  id: string
  project_name: string
  url: string
  status: string
  created_at: string
  result_json?: any
}

const ITEMS_PER_PAGE = 8

export default function ResultPage() {
  const [results, setResults] = useState<ResultItem[]>([])
  const [search, setSearch] = useState("")
  const [page, setPage] = useState(1)

  useEffect(() => {
    async function load() {
      const data = await getResults()
      setResults(data)
    }
    load()
  }, [])

  const filtered = results.filter(
    (r) =>
      r.id.toLowerCase().includes(search.toLowerCase()) ||
      r.project_name.toLowerCase().includes(search.toLowerCase())
  )

  const totalPages = Math.ceil(filtered.length / ITEMS_PER_PAGE)

  const paginatedResults = filtered.slice(
    (page - 1) * ITEMS_PER_PAGE,
    page * ITEMS_PER_PAGE
  )

  const nextPage = () => {
    if (page < totalPages) setPage((p) => p + 1)
  }

  const prevPage = () => {
    if (page > 1) setPage((p) => p - 1)
  }

  const getGradeBadge = (grade: string) => {
    if (!grade) return <span className="text-gray-400">N/A</span>

    const colors: any = {
      A: "bg-green-100 text-green-700",
      B: "bg-blue-100 text-blue-700",
      C: "bg-yellow-100 text-yellow-700",
      D: "bg-orange-100 text-orange-700",
      F: "bg-red-100 text-red-700",
    }

    return (
      <span
        className={`px-3 py-1 text-xs rounded-full font-semibold ${colors[grade]}`}
      >
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
      <h1 className="text-2xl font-semibold">Result History</h1>

      {/* Sticky Mobile Search */}
      <div className="md:static sticky top-0 z-10 bg-gray-50 py-3">
        <input
          type="text"
          placeholder="Search by Run ID or Project Name"
          value={search}
          onChange={(e) => {
            setSearch(e.target.value)
            setPage(1)
          }}
          className="w-full border rounded-xl px-4 py-3 text-sm shadow-sm focus:ring-2 focus:ring-indigo-500"
        />
      </div>

      {/* DESKTOP TABLE */}
      <div className="hidden md:block bg-white rounded-2xl shadow">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 border-b sticky top-0">
            <tr className="text-left text-gray-600 uppercase text-xs tracking-wider">
              <th className="px-6 py-4">Run ID</th>
              <th className="px-6 py-4">Project</th>
              <th className="px-6 py-4">Score</th>
              <th className="px-6 py-4">SLA</th>
              <th className="px-6 py-4">Created</th>
              <th className="px-6 py-4 text-right">Action</th>
            </tr>
          </thead>

          <tbody className="divide-y">
            <AnimatePresence>
              {paginatedResults.map((r) => {
                const score = r.result_json?.scorecard?.score ?? "N/A"
                const grade = r.result_json?.scorecard?.grade ?? null

                return (
                  <motion.tr
                    key={r.id}
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0 }}
                    transition={{ duration: 0.25 }}
                    className="hover:bg-gray-50"
                  >
                    <td className="px-6 py-4 font-mono text-xs">{r.id}</td>
                    <td className="px-6 py-4 font-semibold text-orange-600">
                      {r.project_name}
                    </td>
                    <td className="px-6 py-4 font-semibold">{score}</td>
                    <td className="px-6 py-4">{getGradeBadge(grade)}</td>
                    <td className="px-6 py-4 text-xs text-gray-500">
                      {new Date(r.created_at).toLocaleString()}
                    </td>
                    <td className="px-6 py-4 text-right">
                      <Link
                        href={`/result/${r.id}`}
                        className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 text-xs"
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
          {paginatedResults.map((r) => {
            const score = r.result_json?.scorecard?.score ?? "N/A"
            const grade = r.result_json?.scorecard?.grade ?? null

            return (
              <motion.div
                key={r.id}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.25 }}
                className="bg-white rounded-2xl shadow p-4 space-y-3"
              >
                <div className="text-xs font-mono break-all text-gray-500">
                  {r.id}
                </div>

                <div className="font-semibold text-lg text-orange-600">
                  {r.project_name}
                </div>

                <div className="flex justify-between text-sm">
                  <span>Score</span>
                  <span className="font-semibold">{score}</span>
                </div>

                <div className="flex justify-between text-sm">
                  <span>SLA</span>
                  {getGradeBadge(grade)}
                </div>

                <div className="text-xs text-gray-400">
                  {new Date(r.created_at).toLocaleString()}
                </div>

                <Link
                  href={`/result/${r.id}`}
                  className="block text-center bg-indigo-600 text-white py-2 rounded-lg text-sm"
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
            className="px-4 py-2 bg-gray-200 rounded-lg disabled:opacity-40"
          >
            Prev
          </button>

          <span className="text-sm font-medium">
            Page {page} / {totalPages}
          </span>

          <button
            onClick={nextPage}
            disabled={page === totalPages}
            className="px-4 py-2 bg-gray-200 rounded-lg disabled:opacity-40"
          >
            Next
          </button>
        </div>
      )}
    </motion.div>
  )
}
