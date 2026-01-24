"use client"

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
  if (!data) return null

  const chartData = Object.keys(data).map((key) => ({
    time: key,
    value:
      typeof data[key] === "number"
        ? data[key]
        : Array.isArray(data[key])
        ? data[key].reduce((a: number, b: number) => a + b, 0) /
          data[key].length
        : 0,
  }))

  return (
    <Card title={title}>
      <div style={{ width: "100%", height: 250 }}>
        <ResponsiveContainer>
          <LineChart data={chartData}>
            <XAxis dataKey="time" hide />
            <YAxis />
            <Tooltip />
            <Line
              type="monotone"
              dataKey="value"
              stroke="#6366f1"
              strokeWidth={2}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </Card>
  )
}
