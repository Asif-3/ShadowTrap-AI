import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { Eye, ShieldAlert, Monitor, Terminal, Activity, RefreshCw } from 'lucide-react'
import { GlassCard, KPICard, PageHeader, SectionHeader, LoadingSpinner, SentinelButton, EmptyState } from '../components/common'

export default function TrapVisitors() {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [selectedVisitor, setSelectedVisitor] = useState(null)

  const fetchVisitors = async () => {
    setLoading(true)
    try {
      const token = localStorage.getItem('shadowtrap_token')
      const res = await fetch('/api/trap/visitors', {
        headers: { Authorization: `Bearer ${token}` }
      })
      if (res.ok) {
        const result = await res.json()
        setData(result.data)
      }
    } catch (err) {
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchVisitors()
  }, [])

  if (loading) return <LoadingSpinner size="lg" text="Loading decoy telemetry..." />

  const stats = data?.stats || { total_events: 0, unique_ips: 0, fingerprints: 0, devtools_detected: 0, form_submissions: 0 }
  const visitors = data?.visitors || []

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <PageHeader
        icon={Eye}
        title="Decoy Trap Visitors"
        badge="TELEMETRY"
        subtitle="Real-time telemetry and browser fingerprints captured silently from the TechNova decoy site"
        actions={
          <SentinelButton onClick={fetchVisitors} variant="secondary" size="sm">
            <RefreshCw size={13} className={loading ? 'animate-spin' : ''} />
            <span>Refresh</span>
          </SentinelButton>
        }
      />

      {/* KPI Stat Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3.5">
        <KPICard label="Total Trap Events" value={stats.total_events} icon={Activity} color="#00F5A0" delay={0} />
        <KPICard label="Unique Visitor IPs" value={stats.unique_ips} icon={Eye} color="#4DB8FF" delay={0.03} />
        <KPICard label="Fingerprints" value={stats.fingerprints} icon={Monitor} color="#9B6CFF" delay={0.06} />
        <KPICard label="DevTools Probes" value={stats.devtools_detected} icon={Terminal} color="#FF4D67" delay={0.09} />
        <KPICard label="Form Submissions" value={stats.form_submissions} icon={ShieldAlert} color="#F5C451" delay={0.12} />
      </div>

      {/* Main Table & Inspector Split */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
        {/* Visitors Log Table */}
        <GlassCard className="lg:col-span-2 p-5">
          <SectionHeader title="Recorded Trap Activity Stream" badge={`${visitors.length} events`} />

          <div className="overflow-x-auto">
            <table className="soc-table">
              <thead>
                <tr>
                  <th>Timestamp</th>
                  <th>IP Address</th>
                  <th>Event Type</th>
                  <th>User Agent</th>
                  <th className="w-16"></th>
                </tr>
              </thead>
              <tbody>
                {visitors.length === 0 ? (
                  <tr>
                    <td colSpan={5} className="py-10 text-center text-[#607A71] text-xs">
                      No trap activity logged yet. Visit <a href="/" target="_blank" className="text-[#00F5A0] font-semibold underline">the decoy site</a> to trigger telemetry.
                    </td>
                  </tr>
                ) : (
                  visitors.map((v, i) => {
                    const client = v.client_data || {}
                    const isDevTools = v.event_type === 'devtools_detected'
                    const isForm = v.event_type === 'form_submission'
                    const isSelected = selectedVisitor === v

                    return (
                      <motion.tr
                        key={i}
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        transition={{ delay: i * 0.015 }}
                        onClick={() => setSelectedVisitor(v)}
                        className={`cursor-pointer ${isSelected ? 'bg-[rgba(0,245,160,0.06)]' : ''}`}
                      >
                        <td className="font-mono text-[11px] text-[#607A71]">
                          {v.received_at ? new Date(v.received_at).toLocaleTimeString() : 'N/A'}
                        </td>
                        <td className="font-mono font-semibold text-[11px] text-[#00F5A0]">
                          {v.visitor_ip}
                        </td>
                        <td>
                          <span
                            className={`px-2 py-0.5 rounded text-[10px] font-mono font-semibold ${
                              isDevTools
                                ? 'bg-[rgba(255,77,103,0.12)] text-[#FF4D67] border border-[rgba(255,77,103,0.25)]'
                                : isForm
                                ? 'bg-[rgba(245,196,81,0.12)] text-[#F5C451] border border-[rgba(245,196,81,0.25)]'
                                : 'bg-[rgba(0,245,160,0.1)] text-[#00F5A0] border border-[rgba(0,245,160,0.2)]'
                            }`}
                          >
                            {v.event_type}
                          </span>
                        </td>
                        <td className="text-[#9BB7AD] text-xs max-w-[180px] truncate font-sans">
                          {v.user_agent || client.userAgent || '—'}
                        </td>
                        <td>
                          <button
                            onClick={(e) => {
                              e.stopPropagation()
                              setSelectedVisitor(v)
                            }}
                            className="text-[11px] font-medium text-[#00F5A0] hover:underline cursor-pointer"
                          >
                            Inspect
                          </button>
                        </td>
                      </motion.tr>
                    )
                  })
                )}
              </tbody>
            </table>
          </div>
        </GlassCard>

        {/* Selected Visitor Fingerprint Inspector */}
        <GlassCard className="p-5 space-y-4 h-fit sticky top-20">
          <SectionHeader title="Visitor Inspector" />

          {!selectedVisitor ? (
            <div className="py-12 text-center text-xs text-[#607A71]">
              Click any trap record from the stream to inspect browser fingerprints and device telemetry.
            </div>
          ) : (
            <div className="space-y-3 text-xs">
              <div className="p-3 rounded-lg bg-[#08110F] border border-[rgba(0,245,160,0.14)]">
                <span className="text-[10px] font-semibold uppercase text-[#607A71] block font-mono">Visitor IP</span>
                <span className="font-mono font-bold text-sm text-[#00F5A0] mt-0.5 block">{selectedVisitor.visitor_ip}</span>
              </div>

              <div className="space-y-2">
                <div className="flex justify-between py-1.5 border-b border-[rgba(255,255,255,0.04)]">
                  <span className="text-[#607A71]">Event Type</span>
                  <span className="font-semibold text-[#E8FFF6] font-mono">{selectedVisitor.event_type}</span>
                </div>

                <div className="flex justify-between py-1.5 border-b border-[rgba(255,255,255,0.04)]">
                  <span className="text-[#607A71]">Screen Resolution</span>
                  <span className="font-mono text-[#E8FFF6]">
                    {selectedVisitor.client_data?.screenWidth} × {selectedVisitor.client_data?.screenHeight}
                  </span>
                </div>

                <div className="flex justify-between py-1.5 border-b border-[rgba(255,255,255,0.04)]">
                  <span className="text-[#607A71]">Timezone</span>
                  <span className="font-medium text-[#E8FFF6]">{selectedVisitor.client_data?.timezone || 'N/A'}</span>
                </div>

                <div className="flex justify-between py-1.5 border-b border-[rgba(255,255,255,0.04)]">
                  <span className="text-[#607A71]">Language</span>
                  <span className="text-[#E8FFF6]">{selectedVisitor.client_data?.language || 'N/A'}</span>
                </div>

                <div className="flex justify-between py-1.5 border-b border-[rgba(255,255,255,0.04)]">
                  <span className="text-[#607A71]">Canvas Hash</span>
                  <span className="font-mono text-[10px] text-[#00F5A0] truncate max-w-[140px]">
                    {selectedVisitor.client_data?.canvasHash || 'N/A'}
                  </span>
                </div>

                <div className="flex justify-between py-1.5 border-b border-[rgba(255,255,255,0.04)]">
                  <span className="text-[#607A71]">WebGL Renderer</span>
                  <span className="text-[10px] text-[#9BB7AD] truncate max-w-[140px]">
                    {selectedVisitor.client_data?.webglRenderer || 'N/A'}
                  </span>
                </div>
              </div>

              {selectedVisitor.client_data?.formData && (
                <div className="p-3 rounded-lg bg-[rgba(245,196,81,0.08)] border border-[rgba(245,196,81,0.25)] text-[#E8FFF6]">
                  <span className="text-[10px] font-semibold uppercase text-[#F5C451] block mb-1 font-mono">Captured Form Data</span>
                  <pre className="text-[11px] font-mono whitespace-pre-wrap text-[#F5C451]">
                    {JSON.stringify(selectedVisitor.client_data.formData, null, 2)}
                  </pre>
                </div>
              )}

              <div className="pt-1">
                <span className="text-[10px] font-semibold uppercase text-[#607A71] block mb-1 font-mono">User Agent</span>
                <p className="text-[11px] font-mono p-2 rounded bg-[#08110F] border border-[rgba(0,245,160,0.1)] break-all text-[#9BB7AD]">
                  {selectedVisitor.user_agent || selectedVisitor.client_data?.userAgent || 'N/A'}
                </p>
              </div>
            </div>
          )}
        </GlassCard>
      </div>
    </div>
  )
}
