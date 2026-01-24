"use client"

type Props = {
  metrics: any
}

export default function ResultTable({ metrics }: Props) {
  if (!metrics) return null

  const http = metrics.http_req_duration || {}
  const checks = metrics.checks || {}
  const reqs = metrics.http_reqs || {}

  return (
    <div className="bg-white p-6 rounded-xl shadow">
      <h3 className="text-lg font-semibold mb-4">
        Performance Metrics
      </h3>

      <table className="w-full text-sm">
        <tbody className="divide-y">
          <tr className="py-2">
            <td className="py-2 font-medium">Average (ms)</td>
            <td>{http.avg ?? "N/A"}</td>
          </tr>

          <tr>
            <td className="py-2 font-medium">P95 (ms)</td>
            <td>{http["p(95)"] ?? "N/A"}</td>
          </tr>

          <tr>
            <td className="py-2 font-medium">P99 (ms)</td>
            <td>{http["p(99)"] ?? "N/A"}</td>
          </tr>

          <tr>
            <td className="py-2 font-medium">Total Requests</td>
            <td>{reqs.count ?? "N/A"}</td>
          </tr>

          <tr>
            <td className="py-2 font-medium">Error Rate</td>
            <td>
              {checks.error_rate !== undefined
                ? `${(checks.error_rate * 100).toFixed(2)}%`
                : "N/A"}
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  )
}
