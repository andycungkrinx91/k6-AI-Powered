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

  const securityStatus = data.security_status || (data.security_headers ? "ready" : "pending")
  const securityHeaders = data.security_headers
  const ssl = data.ssl
  const wpt = data.webpagetest
  const lighthouse = data.lighthouse

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
            Download Report
          </button>
        </div>
      </Card>

      {/* Snapshots removed */}

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

      <Card title="Security Headers">
        <div className="grid md:grid-cols-4 gap-4 mb-4">
          <Stat label="Status" value={securityStatus} />
          <Stat label="Grade" value={securityHeaders?.score ?? securityHeaders?.grade ?? "N/A"} />
          <Stat label="Score" value={securityHeaders?.headers ? `${Object.values(securityHeaders.headers).filter((v) => v === "present").length}/${Object.keys(securityHeaders.headers).length}` : "N/A"} />
          <Stat label="Target" value={securityHeaders?.url ?? data.url} />
        </div>

        {securityStatus !== "ready" && (
          <div className="text-sm text-gray-500">
            Security header scan is still running. Refresh this page after the scan completes.
          </div>
        )}

        {securityStatus === "ready" && securityHeaders?.error && (
          <div className="text-sm text-red-500">Security scan failed: {securityHeaders.error}</div>
        )}

        {securityStatus === "ready" && securityHeaders?.headers && (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left text-gray-500">
                  <th className="py-2 pr-4">Header</th>
                  <th className="py-2">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y">
                {Object.entries(securityHeaders.headers)
                  .slice(0, 12)
                  .map(([key, value]) => (
                    <tr key={key}>
                      <td className="py-2 pr-4 font-medium text-gray-800">{key}</td>
                      <td className="py-2 text-gray-700 break-all">{String(value)}</td>
                    </tr>
                  ))}
              </tbody>
            </table>
          </div>
        )}

        {securityStatus === "ready" && !securityHeaders?.headers && !securityHeaders?.error && (
          <div className="text-sm text-gray-500">No header details available.</div>
        )}
      </Card>

      {ssl && (
        <Card title="SSL / TLS Analysis">
          <div className="grid md:grid-cols-3 gap-4 mb-4">
            <Stat label="Status" value={ssl.status || "N/A"} />
            <Stat label="Rating" value={ssl.rating || ssl.ssllabs_grade || "N/A"} />
            <Stat label="Score" value={ssl.score !== undefined ? String(ssl.score) : "N/A"} />
            <Stat label="Cert Expiry (days)" value={ssl.expires_in_days !== undefined ? String(ssl.expires_in_days) : "N/A"} />
          </div>

          <div className="grid md:grid-cols-3 gap-3 text-sm text-gray-800 mb-4">
            <Stat label="Protocol Score" value={ssl.protocol_score !== undefined ? String(ssl.protocol_score) : "N/A"} />
            <Stat label="Key Exchange Score" value={ssl.key_exchange_score !== undefined ? String(ssl.key_exchange_score) : "N/A"} />
            <Stat label="Cipher Strength Score" value={ssl.cipher_strength_score !== undefined ? String(ssl.cipher_strength_score) : "N/A"} />
          </div>

          <div className="grid md:grid-cols-2 gap-3 text-sm text-gray-800">
            <div>
              <div className="text-gray-500 text-xs uppercase mb-1">Supported Versions</div>
              <div className="bg-gray-50 border border-gray-100 rounded-lg p-3 break-words">
                {ssl.supported_versions?.length ? ssl.supported_versions.join(", ") : "-"}
              </div>
            </div>
            <div>
              <div className="text-gray-500 text-xs uppercase mb-1">Weak Protocols</div>
              <div className="bg-gray-50 border border-gray-100 rounded-lg p-3 break-words">
                {ssl.weak_versions?.length ? ssl.weak_versions.join(", ") : "None"}
              </div>
            </div>
            <div>
              <div className="text-gray-500 text-xs uppercase mb-1">Key</div>
              <div className="bg-gray-50 border border-gray-100 rounded-lg p-3 break-words">
                {(ssl.key_algorithm || "N/A") + (ssl.key_size ? ` ${ssl.key_size} bits` : "")}
              </div>
            </div>
            <div>
              <div className="text-gray-500 text-xs uppercase mb-1">Negotiated Ciphers</div>
              <div className="bg-gray-50 border border-gray-100 rounded-lg p-3 break-words">
                {ssl.negotiated_ciphers?.length ? ssl.negotiated_ciphers.join(", ") : "-"}
              </div>
            </div>
            <div>
              <div className="text-gray-500 text-xs uppercase mb-1">Certificate Subject</div>
              <div className="bg-gray-50 border border-gray-100 rounded-lg p-3 break-words">
                {ssl.cert_subject || "N/A"}
              </div>
            </div>
            <div>
              <div className="text-gray-500 text-xs uppercase mb-1">Certificate Issuer</div>
              <div className="bg-gray-50 border border-gray-100 rounded-lg p-3 break-words">
                {ssl.cert_issuer || "N/A"}
              </div>
            </div>
            <div>
              <div className="text-gray-500 text-xs uppercase mb-1">Valid From</div>
              <div className="bg-gray-50 border border-gray-100 rounded-lg p-3 break-words">
                {ssl.cert_not_before || "N/A"}
              </div>
            </div>
            <div>
              <div className="text-gray-500 text-xs uppercase mb-1">Valid To</div>
              <div className="bg-gray-50 border border-gray-100 rounded-lg p-3 break-words">
                {ssl.cert_not_after || "N/A"}
              </div>
            </div>
            <div>
              <div className="text-gray-500 text-xs uppercase mb-1">SAN (DNS)</div>
              <div className="bg-gray-50 border border-gray-100 rounded-lg p-3 break-words">
                {ssl.cert_san?.length ? ssl.cert_san.join(", ") : "-"}
              </div>
            </div>
            {ssl.ssllabs_grade && (
              <div>
                <div className="text-gray-500 text-xs uppercase mb-1">SSL Labs Grade</div>
                <div className="bg-gray-50 border border-gray-100 rounded-lg p-3 break-words">
                  {ssl.ssllabs_grade} ({ssl.ssllabs_status || "READY"})
                </div>
              </div>
            )}
          </div>

          {ssl.findings?.length ? (
            <div className="mt-4">
              <div className="text-gray-500 text-xs uppercase mb-1">Findings</div>
              <ul className="bg-gray-50 border border-gray-100 rounded-lg divide-y text-sm">
                {ssl.findings.slice(0, 10).map((f: any) => (
                  <li key={f.id} className="p-3">
                    <span className="font-semibold uppercase text-xs mr-2">[{f.severity}]</span>
                    <span className="text-gray-800">{f.message}</span>
                  </li>
                ))}
              </ul>
            </div>
          ) : null}
        </Card>
      )}

      {wpt && Object.keys(wpt).length > 0 && (
        <Card title="WebPageTest (Playwright)">
          <div className="grid md:grid-cols-3 gap-4 mb-4 text-sm">
            <Stat label="Status" value={wpt.status || "N/A"} />
            <Stat label="Agent" value={wpt.agent || "k6-ai-powerd-agent"} />
            <Stat label="Network" value={wpt.settings?.network_profile || "Simulated"} />
            <Stat label="Latency (ms)" value={wpt.settings?.latency_ms !== undefined ? String(wpt.settings.latency_ms) : "N/A"} />
            <Stat label="CPU Throttle" value={wpt.settings?.cpu_throttle !== undefined ? String(wpt.settings.cpu_throttle) : "N/A"} />
            <Stat label="Download (B/s)" value={wpt.settings?.download_bps !== undefined ? String(wpt.settings.download_bps) : "N/A"} />
            <Stat label="WPT Grade" value={wpt.grade || "N/A"} />
            <Stat label="WPT Score" value={wpt.score !== undefined ? String(wpt.score) : "N/A"} />
          </div>

          {wpt.summary && (
            <div className="grid md:grid-cols-3 gap-3 text-sm mb-4">
              <SmallStat title="FCP" value={formatMs(wpt.summary.fcp_ms)} />
              <SmallStat title="LCP" value={formatMs(wpt.summary.lcp_ms)} />
              <SmallStat title="CLS" value={wpt.summary.cls} />
              <SmallStat title="TTFB" value={formatMs(wpt.summary.ttfb_ms)} />
              <SmallStat title="Start Render" value={formatMs(wpt.summary.start_render_ms)} />
              <SmallStat title="Speed Index" value={formatMs(wpt.summary.speed_index_ms)} />
              <SmallStat title="TBT" value={formatMs(wpt.summary.tbt_ms)} />
              <SmallStat title="Page Weight" value={formatKb(wpt.summary.page_weight_kb)} />
              <SmallStat title="Total Requests" value={wpt.summary.total_requests} />
              <SmallStat title="DC Time" value={formatMs(wpt.summary.dc_time_ms)} />
              <SmallStat title="DC Bytes" value={formatKb(wpt.summary.dc_bytes_kb)} />
              <SmallStat title="Total Time" value={formatMs(wpt.summary.total_time_ms)} />
              <SmallStat title="Elapsed" value={formatMs(wpt.summary.elapsed_ms)} />
            </div>
          )}

          <ViewSection label="First View (Cold Cache)" view={wpt.first_view} />
          <ViewSection label="Repeat View (Warm Cache)" view={wpt.repeat_view} />

          {wpt.error && (
            <div className="text-sm text-red-500 mt-2">WebPageTest error: {wpt.error}</div>
          )}
        </Card>
      )}

      {lighthouse && Object.keys(lighthouse).length > 0 && (
        <Card title="Lighthouse">
          <div className="grid md:grid-cols-3 gap-4 mb-4 text-sm">
            <Stat label="Status" value={lighthouse.status || "N/A"} />
            <Stat label="Perf Score" value={lighthouse.score !== undefined ? String(lighthouse.score) : "N/A"} />
            <Stat label="Grade" value={lighthouse.grade || "N/A"} />
          </div>
          {lighthouse.categories && (
            <div className="rounded-2xl border border-gray-100 bg-gray-50 p-4 mb-4">
              <div className="text-xs uppercase text-gray-500 mb-3">Scores</div>
              <div className="grid md:grid-cols-5 gap-3 text-sm">
                <ScoreBox label="Performance" value={lighthouse.categories?.performance} />
                <ScoreBox label="Accessibility" value={lighthouse.categories?.accessibility} />
                <ScoreBox label="Best Practices" value={lighthouse.categories?.best_practices} />
                <ScoreBox label="SEO" value={lighthouse.categories?.seo} />
                <ScoreBox label="PWA" value={lighthouse.categories?.pwa} />
              </div>
            </div>
          )}
          {lighthouse.metrics && (
            <div className="grid md:grid-cols-3 gap-3 text-sm">
              <SmallStat title="FCP" value={lighthouse.metrics["first-contentful-paint"]} />
              <SmallStat title="LCP" value={lighthouse.metrics["largest-contentful-paint"]} />
              <SmallStat title="CLS" value={lighthouse.metrics["cumulative-layout-shift"]} />
              <SmallStat title="TBT" value={lighthouse.metrics["total-blocking-time"]} />
              <SmallStat title="TTI" value={lighthouse.metrics["interactive"]} />
              <SmallStat title="Speed Index" value={lighthouse.metrics["speed-index"]} />
            </div>
          )}
          {lighthouse.error && (
            <div className="text-sm text-red-500 mt-2">Lighthouse error: {lighthouse.error}</div>
          )}
        </Card>
      )}
    </div>
  )
}

function Stat({ label, value }: { label: string; value: any }) {
  return (
    <div className="bg-gray-50 rounded-xl p-4 border border-gray-100">
      <div className="text-xs uppercase text-gray-500 tracking-wide">{label}</div>
      <div className="text-lg font-semibold text-gray-800 mt-1">{value ?? "N/A"}</div>
    </div>
  )
}

function ViewSection({ label, view }: { label: string; view: any }) {
  if (!view || Object.keys(view).length === 0) return null

  const timing = view.timing || {}
  const vitals = view.vitals || {}
  const network = view.network || {}
  const waterfall = view.waterfall || []

  return (
    <div className="border border-gray-100 rounded-2xl p-4 mb-4 bg-gray-50">
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-2 mb-3">
        <div className="text-sm font-semibold text-gray-800">{label}</div>
        <div className="flex flex-wrap gap-2 text-xs text-gray-600">
          <Badge label="TTFB" value={timing.ttfb_ms} suffix="ms" />
          <Badge label="DCL" value={timing.dom_content_loaded_ms} suffix="ms" />
          <Badge label="Load" value={timing.load_event_ms} suffix="ms" />
          <Badge label="FCP" value={timing.first_contentful_paint_ms} suffix="ms" />
          <Badge label="LCP" value={vitals.lcp_ms} suffix="ms" />
          <Badge label="CLS" value={vitals.cls} />
          <Badge label="INP" value={vitals.inp_ms} suffix="ms" />
          <Badge label="Elapsed" value={timing.elapsed_ms} suffix="ms" />
        </div>
      </div>

      <div className="grid md:grid-cols-3 gap-3 text-sm mb-3">
        <SmallStat title="Resources" value={network.resource_count} />
        <SmallStat title="Transfer (KB)" value={network.transfer_kb} />
        <SmallStat title="Encoded (KB)" value={network.encoded_kb} />
      </div>

      {waterfall.length > 0 && (
        <div className="overflow-x-auto text-sm">
          <table className="w-full min-w-[640px]">
            <thead>
              <tr className="text-left text-gray-500 text-xs uppercase">
                <th className="py-2 pr-3">Resource</th>
                <th className="py-2 pr-3">Initiator</th>
                <th className="py-2 pr-3">Start (ms)</th>
                <th className="py-2 pr-3">Duration (ms)</th>
                <th className="py-2">Transfer (KB)</th>
              </tr>
            </thead>
            <tbody className="divide-y">
              {waterfall.slice(0, 12).map((r: any, idx: number) => (
                <tr key={`${r.name}-${idx}`}>
                  <td className="py-2 pr-3 text-gray-800 break-all max-w-[320px]">{r.name}</td>
                  <td className="py-2 pr-3 text-gray-700">{r.initiatorType || "-"}</td>
                  <td className="py-2 pr-3 text-gray-700">{typeof r.startTime === "number" ? r.startTime.toFixed(2) : "-"}</td>
                  <td className="py-2 pr-3 text-gray-700">{typeof r.duration === "number" ? r.duration.toFixed(2) : "-"}</td>
                  <td className="py-2 text-gray-700">{typeof r.transferSize === "number" ? (r.transferSize / 1024).toFixed(2) : "0.00"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}

function Badge({ label, value, suffix }: { label: string; value: any; suffix?: string }) {
  if (value === undefined || value === null || value === "") return null
  return (
    <span className="px-2 py-1 rounded-full bg-white border text-gray-700 shadow-sm">
      <span className="font-semibold mr-1 text-gray-900">{label}</span>
      <span className="text-gray-700">
        {typeof value === "number" ? value.toFixed(2) : String(value)}{suffix ? ` ${suffix}` : ""}
      </span>
    </span>
  )
}

function SmallStat({ title, value }: { title: string; value: any }) {
  return (
    <div className="bg-white border border-gray-100 rounded-lg p-3">
      <div className="text-xs uppercase text-gray-500">{title}</div>
      <div className="text-base font-semibold text-gray-800 mt-1">{value ?? "N/A"}</div>
    </div>
  )
}

function formatMs(val: any) {
  if (val === undefined || val === null || Number.isNaN(val)) return "N/A"
  return `${Number(val).toFixed(3)}s`
}

function formatKb(val: any) {
  if (val === undefined || val === null || Number.isNaN(val)) return "N/A"
  return `${Number(val).toFixed(2)} KB`
}

function ScoreBox({ label, value }: { label: string; value: any }) {
  return (
    <div className="bg-white border border-gray-100 rounded-xl p-4 text-center shadow-sm">
      <div className="text-xs uppercase text-gray-500 mb-2">{label}</div>
      <div className="text-2xl font-bold text-gray-900">{value ?? "N/A"}</div>
    </div>
  )
}
