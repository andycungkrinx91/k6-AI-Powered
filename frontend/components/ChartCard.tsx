"use client"

import { useEffect, useRef, useState } from "react"
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
} from "recharts"
import Card from "./Card"

export default function ChartCard({
  title,
  data,
}: {
  title: string
  data: any
}) {
  const containerRef = useRef<HTMLDivElement | null>(null)
  const [size, setSize] = useState({ width: 0, height: 0 })

  useEffect(() => {
    const node = containerRef.current
    if (!node) return

    const update = () => {
      const rect = node.getBoundingClientRect()
      setSize({ width: rect.width, height: rect.height })
    }

    update()
    const observer = new ResizeObserver(update)
    observer.observe(node)
    return () => observer.disconnect()
  }, [])

  if (!data) return null

  const entries = Object.entries(data)
  if (!entries.length) return null

  const ready = size.width > 10 && size.height > 10

  const chartData = entries.map(([key, value]) => ({
    time: key,
    value:
      typeof value === "number"
        ? value
        : Array.isArray(value)
        ? value.reduce((a: number, b: number) => a + b, 0) /
          (value.length || 1)
        : 0,
  }))

  return (
    <Card title={title}>
      <div
        ref={containerRef}
        className="w-full h-64 min-w-0"
        style={{ minWidth: 0, minHeight: 256 }}
      >
        {ready ? (
          <ResponsiveContainer width="100%" height="100%" minWidth={1} minHeight={1}>
              <LineChart data={chartData}>
                <XAxis dataKey="time" hide />
                <YAxis stroke="rgba(234,251,230,0.65)" />
                <Tooltip
                  contentStyle={{
                    background: "rgba(10,12,10,0.95)",
                    border: "1px solid rgba(26,46,26,1)",
                    color: "rgba(234,251,230,0.95)",
                  }}
                />
                <Line
                  type="monotone"
                  dataKey="value"
                  stroke="#00FFFF"
                  strokeWidth={2}
                />
              </LineChart>
            </ResponsiveContainer>
          ) : (
          <div className="w-full h-full flex items-center justify-center text-xs text-terminal-dim">
            Loading chart…
          </div>
        )}
      </div>
    </Card>
  )
}
