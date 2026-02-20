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
    <div className="bg-terminal-surface border border-terminal-border shadow-terminal p-6 rounded-md">
      <h3 className="text-lg font-semibold mb-4 text-terminal-phosphor">
        Performance Metrics
      </h3>

      <div className="overflow-x-auto">
        <table className="w-full text-sm min-w-[360px]">
          <tbody className="divide-y divide-terminal-border">
            <tr className="py-2">
              <td className="py-2 font-medium">Average (ms)</td>
              <td className="break-words">{http.avg ?? "N/A"}</td>
            </tr>

            <tr>
              <td className="py-2 font-medium">P95 (ms)</td>
              <td className="break-words">{http["p(95)"] ?? "N/A"}</td>
            </tr>

            <tr>
              <td className="py-2 font-medium">P99 (ms)</td>
              <td className="break-words">{http["p(99)"] ?? "N/A"}</td>
            </tr>

            <tr>
              <td className="py-2 font-medium">Total Requests</td>
              <td className="break-words">{reqs.count ?? "N/A"}</td>
            </tr>

            <tr>
              <td className="py-2 font-medium">Error Rate</td>
              <td className="break-words">
                {checks.error_rate !== undefined
                  ? `${(checks.error_rate * 100).toFixed(2)}%`
                  : "N/A"}
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  )
}
