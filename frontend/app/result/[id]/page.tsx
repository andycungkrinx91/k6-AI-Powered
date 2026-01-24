"use client"

import { useEffect, useState } from "react"
import { useParams } from "next/navigation"
import { getResult, downloadResult } from "@/lib/api"
import ChartCard from "@/components/ChartCard"
import ResultTable from "@/components/ResultTable"
import Card from "@/components/Card"

export default function ResultDetail() {
  const params = useParams()
  const id = params?.id as string

  const [data, setData] = useState<any>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!id) return

    async function fetchData() {
      try {
        const res = await getResult(id)
        setData(res)
      } catch (err) {
        console.error(err)
      } finally {
        setLoading(false)
      }
    }

    fetchData()
  }, [id])

  if (loading) return <div>Loading...</div>

  if (!data) return <div>No result found</div>

  return (
    <div className="space-y-6">

      <Card title={`Load Test Result — ${data.project_name}`}>
        <div className="flex justify-between items-center">
          <div>
            <div className="text-orange-600 font-semibold">
              {data.project_name}
            </div>
            <div className="text-purple-600 text-sm">
              {data.url}
            </div>
          </div>

          <button
            onClick={() => downloadResult(id)}
            className="bg-indigo-600 text-white px-4 py-2 rounded-lg hover:bg-indigo-700"
          >
            Download PDF
          </button>
        </div>
      </Card>

      <ResultTable metrics={data.metrics} />

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <ChartCard
          title="Latency Trend"
          data={data.timeline?.latency}
        />
        <ChartCard
          title="Throughput"
          data={data.timeline?.requests}
        />
      </div>
    </div>
  )
}
