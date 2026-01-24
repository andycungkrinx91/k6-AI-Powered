"use client"

import { useEffect, useState } from "react"
import { getResults } from "@/lib/api"
import { motion } from "framer-motion"
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
  PieChart,
  Pie,
  Cell,
  Legend,
} from "recharts"
import Link from "next/link"

interface ResultItem {
  id: string
  project_name: string
  created_at: string
  result_json?: any
}

const COLORS = ["#10B981", "#6366F1", "#F59E0B", "#F97316", "#EF4444"]

export default function DashboardPage() {
  const [results, setResults] = useState<ResultItem[]>([])
  const [counter, setCounter] = useState({
    total: 0,
    avgScore: 0,
  })

  useEffect(() => {
    async function load() {
      const data = await getResults()
      setResults(data)
    }
    load()
  }, [])

  useEffect(() => {
    if (!results.length) return

    const total = results.length
    const avg =
      results.reduce(
        (acc, r) =>
          acc + (r.result_json?.scorecard?.score ?? 0),
        0
      ) / total

    animateCounter(total, avg)
  }, [results])

  const animateCounter = (total: number, avg: number) => {
    let t = 0
    let s = 0

    const interval = setInterval(() => {
      t += Math.ceil(total / 25)
      s += avg / 25

      setCounter({
        total: t >= total ? total : t,
        avgScore:
          s >= avg ? Math.round(avg) : Math.round(s),
      })

      if (t >= total) clearInterval(interval)
    }, 40)
  }

  /* -------- Trend Data -------- */

  const trendData = results
    .slice(0, 10)
    .reverse()
    .map((r) => ({
      date: new Date(r.created_at).toLocaleDateString(),
      score: r.result_json?.scorecard?.score ?? 0,
      errorRate:
        r.result_json?.metrics?.checks?.error_rate ?? 0,
    }))

  /* -------- Grade Breakdown -------- */

  const gradeCount = {
    A: 0,
    B: 0,
    C: 0,
    D: 0,
    F: 0,
  }

  results.forEach((r) => {
    const grade = r.result_json?.scorecard?.grade
    if (grade && gradeCount[grade as keyof typeof gradeCount] !== undefined) {
      gradeCount[grade as keyof typeof gradeCount]++
    }
  })

  const donutData = Object.entries(gradeCount).map(
    ([grade, value]) => ({
      name: grade,
      value,
    })
  )

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
      className="space-y-10 pb-10"
    >
      {/* HERO */}
      <div className="bg-gradient-to-r from-indigo-600 to-purple-600 text-white rounded-3xl p-8 shadow-xl">
        <h1 className="text-3xl font-bold mb-2">
          Performance Intelligence
        </h1>
        <p className="text-indigo-100">
          SLA scoring & error analytics overview
        </p>
      </div>

      {/* KPI */}
      <div className="grid md:grid-cols-2 gap-6">
        <KPI title="Total Tests" value={counter.total} />
        <KPI
          title="Average Score"
          value={counter.avgScore || "N/A"}
        />
      </div>

      {/* CHARTS */}
      <div className="grid md:grid-cols-2 gap-6">
        {/* Trend Line */}
        <div className="bg-white rounded-2xl shadow p-6">
          <h2 className="text-lg font-semibold mb-4">
            Score & Error Rate Trend
          </h2>

          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={trendData}>
              <defs>
                <linearGradient id="scoreGradient" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#6366F1" stopOpacity={0.8}/>
                  <stop offset="95%" stopColor="#6366F1" stopOpacity={0}/>
                </linearGradient>
              </defs>

              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" />
              <YAxis domain={[0, 100]} />
              <Tooltip />

              <Line
                type="monotone"
                dataKey="score"
                stroke="#6366F1"
                strokeWidth={3}
                dot={{ r: 4 }}
                fill="url(#scoreGradient)"
                animationDuration={1200}
              />

              <Line
                type="monotone"
                dataKey="errorRate"
                stroke="#EF4444"
                strokeWidth={2}
                dot={false}
                animationDuration={1200}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* Donut Chart with Animated Entrance */}
        <div className="bg-white rounded-2xl shadow p-6">
          <h2 className="text-lg font-semibold mb-4">
            Score Breakdown
          </h2>

          <motion.div
            initial={{ opacity: 0, scale: 0.8, rotate: -15 }}
            animate={{ opacity: 1, scale: 1, rotate: 0 }}
            transition={{ duration: 0.8, ease: "easeOut" }}
          >
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={donutData}
                  dataKey="value"
                  nameKey="name"
                  innerRadius={70}
                  outerRadius={110}
                  paddingAngle={4}
                  animationBegin={0}
                  animationDuration={1200}
                  animationEasing="ease-out"
                >
                  {donutData.map((entry, index) => (
                    <Cell
                      key={`cell-${index}`}
                      fill={COLORS[index % COLORS.length]}
                    />
                  ))}
                </Pie>
                <Legend />
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </motion.div>
        </div>
      </div>

      {/* RECENT ACTIVITY */}
      <div className="bg-white rounded-2xl shadow p-6">
        <h2 className="text-lg font-semibold mb-4">
          Recent Activity
        </h2>

        <div className="space-y-3">
          {results.slice(0, 5).map((r) => (
            <Link
              key={r.id}
              href={`/result/${r.id}`}
              className="block p-3 rounded-xl hover:bg-gray-50 transition"
            >
              <div className="font-semibold text-orange-600">
                {r.project_name}
              </div>
              <div className="text-xs text-gray-500">
                {new Date(r.created_at).toLocaleString()}
              </div>
            </Link>
          ))}

          {results.length === 0 && (
            <div className="text-gray-400 text-sm">
              No activity yet.
            </div>
          )}
        </div>
      </div>
    </motion.div>
  )
}

/* ---------------- COMPONENTS ---------------- */

function KPI({ title, value }: { title: string; value: any }) {
  return (
    <motion.div
      whileHover={{ y: -4 }}
      className="bg-white rounded-2xl shadow p-6"
    >
      <div className="text-sm text-gray-500 mb-2">
        {title}
      </div>
      <div className="text-3xl font-bold text-gray-800">
        {value}
      </div>
    </motion.div>
  )
}
