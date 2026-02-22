"use client"

import { useCallback, useEffect, useMemo, useState } from "react"
import { useRouter } from "next/navigation"
import { getResultsList } from "@/lib/api"
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
  BarChart,
  Bar,
} from "recharts"
import Link from "next/link"
import { useAuth } from "@/context/AuthContext"
import Card from "@/components/Card"
import ThemeFontSwitcher from "@/components/ThemeFontSwitcher"

interface ResultItem {
  id: string
  project_name: string
  created_at: string
  score?: number | null
  grade?: string | null
  error_rate?: number | null
  security_grade?: string | number | null
  ssl_grade?: string | null
  ssl_versions?: string[] | null
  wpt_grade?: string | null
  lighthouse_score?: number | null
}

const COLORS = ["#10B981", "#6366F1", "#F59E0B", "#F97316", "#EF4444", "#0EA5E9", "#A855F7"]

export default function DashboardPage() {
  const router = useRouter()
  const { user, token, ready } = useAuth()
  const [results, setResults] = useState<ResultItem[]>([])
  const [counter, setCounter] = useState({
    total: 0,
    avgScore: 0,
    tls13Pct: 0,
    secPassPct: 0,
    wptAvg: 0,
    lhAvg: 0,
  })

  useEffect(() => {
    if (!token) {
      return
    }

    async function load() {
      try {
        const res = await getResultsList({ limit: 25, offset: 0 }, token)
        setResults(res.items as ResultItem[])
      } catch (error) {
        console.error("Failed to load results", error)
      }
    }

    load()
  }, [token])

  useEffect(() => {
    if (ready && !user) {
      router.replace("/login")
    }
  }, [ready, user, router])

  const animateCounter = useCallback((total: number, avg: number, tlsPct: number, secPct: number, wptAvg: number, lhAvg: number) => {
    let t = 0
    let s = 0

    const interval = window.setInterval(() => {
      t += Math.ceil(total / 25)
      s += avg / 25

      setCounter({
        total: t >= total ? total : t,
        avgScore:
          s >= avg ? Math.round(avg) : Math.round(s),
        tls13Pct: tlsPct,
        secPassPct: secPct,
        wptAvg: Math.round(wptAvg) || 0,
        lhAvg: Math.round(lhAvg) || 0,
      })

      if (t >= total) window.clearInterval(interval)
    }, 40)

    return () => window.clearInterval(interval)
  }, [])

  const aggregates = useMemo(() => {
    const gradeCount = { "A+": 0, A: 0, B: 0, C: 0, D: 0, F: 0 }
    const secGradeCount: Record<string, number> = { "A+": 0, A: 0, B: 0, C: 0, D: 0, E: 0, F: 0 }
    const sslGradeCount: Record<string, number> = { "A+": 0, A: 0, B: 0, C: 0, D: 0, E: 0, F: 0 }
    let tls10 = 0
    let tls11 = 0
    let tls12 = 0
    let tls13 = 0
    const wptScoreBuckets: { name: string; value: number }[] = []
    const lhScoreBuckets: { name: string; value: number }[] = []

    let tls13Supported = 0
    let tls12Supported = 0
    let secValidCount = 0
    let secScoreSum = 0
    let wptScoreSum = 0
    let wptCount = 0
    let lhScoreSum = 0
    let lhCount = 0
    let perfScoreSum = 0

    results.forEach((r) => {
      if (typeof r.score === "number") perfScoreSum += r.score
      const grade = r.grade
      if (grade && gradeCount[grade as keyof typeof gradeCount] !== undefined) {
        gradeCount[grade as keyof typeof gradeCount]++
      }

      const secG = r.security_grade
      if (secG !== undefined && secG !== null && secG !== "") {
        const g = String(secG)
        if (secGradeCount[g] !== undefined) secGradeCount[g]++
        // Approximate header coverage for KPI: treat A/A+ as pass.
        if (g.startsWith("A")) {
          secValidCount++
          secScoreSum += 1
        }
      }

      if (r.ssl_versions?.includes("TLS 1.3")) tls13Supported++
      if (r.ssl_versions?.includes("TLS 1.2")) tls12Supported++
      if (r.ssl_versions?.includes("TLS 1.0")) tls10++
      if (r.ssl_versions?.includes("TLS 1.1")) tls11++
      if (r.ssl_versions?.includes("TLS 1.2")) tls12++
      if (r.ssl_versions?.includes("TLS 1.3")) tls13++
      if (r.ssl_grade && sslGradeCount[r.ssl_grade] !== undefined) sslGradeCount[r.ssl_grade]++

      // We don't have WPT score in list payload; bucket by grade only.
      if (r.wpt_grade) {
        const g = r.wpt_grade
        const s = g === "A+" ? 97 : g === "A" ? 93 : g === "B" ? 87 : g === "C" ? 78 : g === "D" ? 70 : 50
        wptScoreSum += s
        wptCount += 1
        if (s >= 90) wptScoreBuckets.push({ name: "90-100", value: 1 })
        else if (s >= 80) wptScoreBuckets.push({ name: "80-89", value: 1 })
        else if (s >= 70) wptScoreBuckets.push({ name: "70-79", value: 1 })
        else if (s >= 60) wptScoreBuckets.push({ name: "60-69", value: 1 })
        else wptScoreBuckets.push({ name: "<60", value: 1 })
      }

      const lhScore = r.lighthouse_score
      if (lhScore !== undefined && lhScore !== null) {
        lhScoreSum += Number(lhScore)
        lhCount += 1
        const s = Number(lhScore)
        if (s >= 90) lhScoreBuckets.push({ name: "90-100", value: 1 })
        else if (s >= 80) lhScoreBuckets.push({ name: "80-89", value: 1 })
        else if (s >= 70) lhScoreBuckets.push({ name: "70-79", value: 1 })
        else if (s >= 60) lhScoreBuckets.push({ name: "60-69", value: 1 })
        else lhScoreBuckets.push({ name: "<60", value: 1 })
      }
    })

    const total = Math.max(results.length, 1)
    const avg = perfScoreSum / total
    const tlsPct = Math.round(((tls13Supported + tls12Supported) / total) * 100)
    const secPct = secValidCount ? Math.round((secScoreSum / Math.max(secValidCount, 1)) * 100) : 0
    const wptAvg = wptCount ? wptScoreSum / wptCount : 0
    const lhAvg = lhCount ? lhScoreSum / lhCount : 0

    const order = ["A", "B", "C", "D", "F"]
    const donutData = order.map((name) => ({ name, value: gradeCount[name as keyof typeof gradeCount] || 0 }))

    const gradeOrder = ["A+", "A", "B", "C", "D", "E", "F"]
    const secDonutData = gradeOrder.map((name) => ({ name, value: secGradeCount[name] || 0 }))
    const sslDonutData = gradeOrder.map((name) => ({ name, value: sslGradeCount[name] || 0 }))

    const tlsCoverage = [
      { version: "TLS 1.0", pct: Math.round((tls10 / total) * 100) },
      { version: "TLS 1.1", pct: Math.round((tls11 / total) * 100) },
      { version: "TLS 1.2", pct: Math.round((tls12 / total) * 100) },
      { version: "TLS 1.3", pct: Math.round((tls13 / total) * 100) },
    ]

    const bucketize = (arr: { name: string; value: number }[]) => {
      const map: Record<string, number> = {}
      arr.forEach((b) => {
        map[b.name] = (map[b.name] || 0) + b.value
      })
      const order = ["90-100", "80-89", "70-79", "60-69", "<60"]
      return order.map((name) => ({ name, value: map[name] || 0 }))
    }

    const wptBuckets = bucketize(wptScoreBuckets)
    const lhBuckets = bucketize(lhScoreBuckets)

    return { gradeCount, secGradeCount, sslGradeCount, donutData, secDonutData, sslDonutData, wptBuckets, lhBuckets, tlsCoverage, total: results.length, avg, tlsPct, secPct, wptAvg, lhAvg }
  }, [results])

  const donutData = aggregates.donutData
  const secDonutData = aggregates.secDonutData
  const sslDonutData = aggregates.sslDonutData
  const wptBuckets = aggregates.wptBuckets
  const lhBuckets = aggregates.lhBuckets
  const tlsCoverage = aggregates.tlsCoverage

  useEffect(() => {
    if (!results.length) return

    const stopAnimation = animateCounter(
      aggregates.total,
      aggregates.avg,
      aggregates.tlsPct,
      aggregates.secPct,
      aggregates.wptAvg,
      aggregates.lhAvg
    )

    setCounter((prev) => ({
      ...prev,
      total: aggregates.total,
      avgScore: Math.round(aggregates.avg) || 0,
      tls13Pct: 0,
      secPassPct: aggregates.secPct,
      wptAvg: Math.round(aggregates.wptAvg) || 0,
      lhAvg: Math.round(aggregates.lhAvg) || 0,
    }))

    return stopAnimation
  }, [results, animateCounter, aggregates])

  /* -------- Trend Data -------- */

  const trendData = results
    .slice(0, 10)
    .reverse()
    .map((r) => ({
      // Use a stable UTC date string to avoid SSR/client locale hydration mismatches.
      date: new Date(r.created_at).toISOString().slice(0, 10),
      score: r.score ?? 0,
      errorRate: r.error_rate ?? 0,
    }))

  useEffect(() => {
    if (!results.length) return
    const stopAnimation = animateCounter(
      aggregates.total,
      aggregates.avg,
      aggregates.tlsPct,
      aggregates.secPct,
      aggregates.wptAvg,
      aggregates.lhAvg
    )

    setCounter((prev) => ({
      ...prev,
      total: aggregates.total,
      avgScore: Math.round(aggregates.avg) || 0,
      tls13Pct: aggregates.tlsPct,
      secPassPct: aggregates.secPct,
      wptAvg: Math.round(aggregates.wptAvg) || 0,
      lhAvg: Math.round(aggregates.lhAvg) || 0,
    }))

    return stopAnimation
  }, [results, animateCounter, aggregates])

  if (!ready || !user) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-sm text-terminal-dim">Preparing your workspace…</div>
      </div>
    )
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
      className="space-y-10 pb-10"
    >
      <div className="flex items-center justify-between gap-4">
        <div className="text-terminal-phosphor text-xl sm:text-2xl font-semibold">Dashboard</div>
        <div className="hidden sm:block">
          <ThemeFontSwitcher />
        </div>
      </div>

      {/* KPI */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-4 sm:gap-6">
        <KPI title="Total Tests" value={counter.total} />
        <KPI title="Average Score" value={counter.avgScore || "N/A"} />
        {/* TLS coverage shown in chart below */}
        <KPI title="Header Coverage" value={`${counter.secPassPct}%`} />
        <KPI title="WPT Avg Score" value={counter.wptAvg ? Math.round(counter.wptAvg) : "N/A"} />
        <KPI title="Lighthouse Perf" value={counter.lhAvg ? Math.round(counter.lhAvg) : "N/A"} />
      </div>

      {/* CHARTS */}
      <div className="border border-terminal-border bg-terminal-surface shadow-terminal p-4 sm:p-6 rounded-md">
        <h2 className="text-lg font-semibold mb-4 text-terminal-phosphor">
          Score & Error Rate Trend
        </h2>

        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={trendData}>
            <defs>
              <linearGradient id="scoreGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#39FF14" stopOpacity={0.55} />
                <stop offset="95%" stopColor="#39FF14" stopOpacity={0} />
              </linearGradient>
            </defs>

            <CartesianGrid strokeDasharray="3 3" stroke="rgba(57,255,20,0.14)" />
            <XAxis dataKey="date" stroke="rgba(234,251,230,0.65)" />
            <YAxis domain={[0, 100]} stroke="rgba(234,251,230,0.65)" />
            <Tooltip
              contentStyle={{
                background: "rgba(10,12,10,0.95)",
                border: "1px solid rgba(26,46,26,1)",
                color: "rgba(234,251,230,0.95)",
              }}
              labelStyle={{ color: "rgba(57,255,20,0.9)" }}
            />

            <Line
              type="monotone"
              dataKey="score"
              stroke="#39FF14"
              strokeWidth={3}
              dot={{ r: 4 }}
              fill="url(#scoreGradient)"
              animationDuration={1200}
            />

            <Line
              type="monotone"
              dataKey="errorRate"
              stroke="#FF0055"
              strokeWidth={2}
              dot={false}
              animationDuration={1200}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 sm:gap-6">
        {/* Score Breakdown */}
        <div className="border border-terminal-border bg-terminal-surface shadow-terminal p-4 sm:p-6 rounded-md">
          <h2 className="text-lg font-semibold mb-4">Score Breakdown</h2>
          <ResponsiveContainer width="100%" height={360}>
            <PieChart>
              <Pie
                data={donutData}
                dataKey="value"
                nameKey="name"
                innerRadius={60}
                outerRadius={110}
                paddingAngle={3}
                labelLine={false}
                label={false}
              >
                {donutData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Legend verticalAlign="bottom" height={36} />
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </div>

        {/* TLS Coverage */}
        <div className="border border-terminal-border bg-terminal-surface shadow-terminal p-4 sm:p-6 rounded-md">
          <h2 className="text-lg font-semibold mb-4">TLS Coverage</h2>
          <ResponsiveContainer width="100%" height={320}>
            <BarChart data={tlsCoverage} margin={{ top: 10, right: 20, bottom: 20, left: 0 }}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="version" />
              <YAxis domain={[0, 100]} tickFormatter={(v) => `${v}%`} />
              <Tooltip formatter={(v: any) => `${v}%`} />
              <Bar dataKey="pct" fill="#6366F1" radius={[6, 6, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 sm:gap-6">
        {/* SECURITY & SSL BREAKDOWN */}
        <div className="border border-terminal-border bg-terminal-surface shadow-terminal p-4 sm:p-6 rounded-md">
          <h2 className="text-lg font-semibold mb-4">Security Header Grades</h2>
          <ResponsiveContainer width="100%" height={320}>
            <PieChart>
              <Pie
                data={secDonutData}
                dataKey="value"
                nameKey="name"
                innerRadius={60}
                outerRadius={110}
                paddingAngle={3}
                labelLine={false}
                label={false}
              >
                {secDonutData.map((entry, index) => (
                  <Cell key={`sec-cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Legend verticalAlign="bottom" height={36} />
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </div>

        <div className="border border-terminal-border bg-terminal-surface shadow-terminal p-4 sm:p-6 rounded-md">
          <h2 className="text-lg font-semibold mb-4">SSL Ratings</h2>
          <ResponsiveContainer width="100%" height={320}>
            <PieChart>
              <Pie
                data={sslDonutData}
                dataKey="value"
                nameKey="name"
                innerRadius={60}
                outerRadius={110}
                paddingAngle={3}
                labelLine={false}
                label={false}
              >
                {sslDonutData.map((entry, index) => (
                  <Cell key={`ssl-cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Legend verticalAlign="bottom" height={36} />
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 sm:gap-6">
        {/* WebPageTest Score Buckets */}
        <div className="border border-terminal-border bg-terminal-surface shadow-terminal p-4 sm:p-6 rounded-md">
          <h2 className="text-lg font-semibold mb-4">WebPageTest Scores</h2>
          <ResponsiveContainer width="100%" height={360}>
            <PieChart>
              <Pie
                data={wptBuckets}
                dataKey="value"
                nameKey="name"
                innerRadius={60}
                outerRadius={110}
                paddingAngle={3}
                labelLine={false}
                label={false}
              >
                {wptBuckets.map((entry, index) => (
                  <Cell key={`wpt-cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Legend verticalAlign="bottom" height={36} />
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </div>

        {/* Lighthouse Performance Buckets */}
        <div className="border border-terminal-border bg-terminal-surface shadow-terminal p-4 sm:p-6 rounded-md">
          <h2 className="text-lg font-semibold mb-4">Lighthouse Performance Scores</h2>
          <ResponsiveContainer width="100%" height={360}>
            <PieChart>
              <Pie
                data={lhBuckets}
                dataKey="value"
                nameKey="name"
                innerRadius={60}
                outerRadius={110}
                paddingAngle={3}
                labelLine={false}
                label={false}
              >
                {lhBuckets.map((entry, index) => (
                  <Cell key={`lh-cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Legend verticalAlign="bottom" height={36} />
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* RECENT ACTIVITY */}
      <div className="border border-terminal-border bg-terminal-surface shadow-terminal p-6 rounded-md">
        <h2 className="text-lg font-semibold mb-4 text-terminal-phosphor">
          Recent Activity
        </h2>

        <div className="space-y-3">
          {results.slice(0, 5).map((r) => (
            <Link
              key={r.id}
              href={`/result/${r.id}`}
              className="block p-3 border border-terminal-border hover:bg-terminal-surface2 transition-none"
            >
              <div className="font-semibold text-terminal-amber">
                {r.project_name}
              </div>
              <div className="text-xs text-terminal-dim">
                {new Date(r.created_at).toISOString().replace("T", " ").slice(0, 19)}
              </div>
            </Link>
          ))}

          {results.length === 0 && (
            <div className="text-terminal-dim text-sm">
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
    <motion.div whileHover={{}} className="border border-terminal-border bg-terminal-surface shadow-terminal p-4 sm:p-6 rounded-md">
      <div className="text-xs uppercase tracking-widest text-terminal-dim mb-3">{title}</div>
      <div className="text-2xl sm:text-3xl font-semibold text-terminal-phosphor">
        {value} <span className="cursor-block" aria-hidden="true" />
      </div>
    </motion.div>
  )
}
