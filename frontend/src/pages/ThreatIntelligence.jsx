import { useState, useEffect, useMemo } from 'react'
import { threatIntelAPI } from '../api/client'
import { GlassCard, KPICard, LoadingSpinner, StatusBadge, EmptyState, SentinelButton, PageHeader, SectionHeader } from '../components/common'
import {
  Globe, ShieldAlert, Server, Activity, MapPin, Clock, Terminal,
  X, RefreshCw, Layers, Cpu, Search
} from 'lucide-react'
import {
  AreaChart, Area, PieChart, Pie, Cell,
  XAxis, YAxis, Tooltip, ResponsiveContainer
} from 'recharts'
import { getThreatColor } from '../lib/utils'

const CHART_COLORS = ['#00F5A0', '#4DB8FF', '#FF4D67', '#F5C451', '#9B6CFF', '#00C98B', '#FF7043', '#20E67A']

export default function ThreatIntelligencePage() {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)
  const [selectedIp, setSelectedIp] = useState(null)
  const [ipModalData, setIpModalData] = useState(null)
  const [ipLoading, setIpLoading] = useState(false)
  const [searchFilter, setSearchFilter] = useState('')

  const loadData = (showSpinner = true) => {
    if (showSpinner) setLoading(true)
    else setRefreshing(true)

    threatIntelAPI.getFullIntel()
      .then((res) => {
        if (res.data?.data) {
          setData(res.data.data)
        }
      })
      .catch(console.error)
      .finally(() => {
        setLoading(false)
        setRefreshing(false)
      })
  }

  useEffect(() => {
    loadData(true)
  }, [])

  // Handle IP selection for Modal inspector
  const handleIpClick = (ip) => {
    if (!ip) return
    setSelectedIp(ip)
    setIpLoading(true)
    threatIntelAPI.getIpDetails(ip)
      .then((res) => {
        setIpModalData(res.data?.data || null)
      })
      .catch((err) => {
        console.error(err)
        setIpModalData(null)
      })
      .finally(() => setIpLoading(false))
  }

  const summary = data?.summary || {}
  const reputationFeed = data?.reputation_feed || []
  const ipActivity = data?.ip_activity || []
  const recentAttacks = data?.recent_attacks || []
  const statistics = data?.statistics || {}

  // Filter reputation feed by search
  const filteredFeed = useMemo(() => {
    if (!searchFilter.trim()) return reputationFeed
    const q = searchFilter.toLowerCase()
    return reputationFeed.filter(item =>
      item.ip.toLowerCase().includes(q) ||
      (item.country && item.country.toLowerCase().includes(q)) ||
      (item.city && item.city.toLowerCase().includes(q)) ||
      (item.isp && item.isp.toLowerCase().includes(q))
    )
  }, [reputationFeed, searchFilter])

  // Filter IP activity by search
  const filteredActivity = useMemo(() => {
    if (!searchFilter.trim()) return ipActivity
    const q = searchFilter.toLowerCase()
    return ipActivity.filter(item =>
      item.ip.toLowerCase().includes(q) ||
      (item.attack_type && item.attack_type.toLowerCase().includes(q)) ||
      (item.protocol && item.protocol.toLowerCase().includes(q))
    )
  }, [ipActivity, searchFilter])

  if (loading) return <LoadingSpinner size="lg" text="Aggregating threat intelligence..." />

  const hasData = summary.total_attacks > 0 || reputationFeed.length > 0

  const customTooltipStyle = {
    background: '#0B1412',
    border: '1px solid rgba(0, 245, 160, 0.2)',
    borderRadius: 8,
    color: '#E8FFF6',
    fontSize: 12,
    fontFamily: 'Inter',
  }

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <PageHeader
        icon={Globe}
        title="Threat Intelligence"
        badge="GLOBAL INTEL"
        subtitle="Honeypot IP reputation index, malicious infrastructure tracking, and geographic telemetry"
        actions={
          <div className="flex items-center gap-2">
            <div className="relative">
              <Search size={13} className="absolute left-3 top-2.5 text-[#607A71]" />
              <input
                type="text"
                value={searchFilter}
                onChange={(e) => setSearchFilter(e.target.value)}
                placeholder="Search IP, country, ISP..."
                className="pl-8 pr-3 py-1.5 rounded-lg bg-[#08110F] border border-[rgba(0,245,160,0.16)] text-xs text-[#E8FFF6] outline-none focus:border-[#00F5A0] w-48 font-mono"
              />
            </div>
            <SentinelButton onClick={() => loadData(false)} disabled={refreshing} variant="secondary" size="sm">
              <RefreshCw size={13} className={refreshing ? 'animate-spin' : ''} />
              <span>{refreshing ? 'Refreshing...' : 'Refresh'}</span>
            </SentinelButton>
          </div>
        }
      />

      {!hasData ? (
        <GlassCard className="p-8">
          <EmptyState preset="intel" />
        </GlassCard>
      ) : (
        <>
          {/* SECTION 1: Summary KPI Cards */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3.5">
            <KPICard label="Total Attacks" value={summary.total_attacks || 0} icon={Activity} color="#00F5A0" />
            <KPICard label="Unique Attacker IPs" value={summary.unique_attacker_ips || 0} icon={Globe} color="#4DB8FF" />
            <KPICard label="High Threat IPs" value={summary.high_threat_ips || 0} icon={ShieldAlert} color="#FF4D67" />
            <KPICard label="Tracked C2 Servers" value={summary.tracked_c2_servers || 0} icon={Server} color="#F5C451" />
          </div>

          {/* SECTION 2: Honeypot IP Reputation Table */}
          <GlassCard className="p-5">
            <div className="flex items-center justify-between mb-4">
              <SectionHeader
                title="Honeypot IP Reputation Index"
                badge={`${filteredFeed.length} IPs`}
                className="mb-0"
              />
            </div>

            <div className="overflow-x-auto">
              <table className="soc-table">
                <thead>
                  <tr>
                    <th>IP Address</th>
                    <th>Country</th>
                    <th>City / Region</th>
                    <th>ISP / Network</th>
                    <th>ASN</th>
                    <th>Attacks</th>
                    <th>Score</th>
                    <th>Status</th>
                    <th>Last Seen</th>
                    <th className="w-16"></th>
                  </tr>
                </thead>
                <tbody>
                  {filteredFeed.length === 0 ? (
                    <tr>
                      <td colSpan={10} className="text-center py-10 text-xs text-[#607A71]">
                        No IP reputation records found matching search query.
                      </td>
                    </tr>
                  ) : (
                    filteredFeed.map((item) => (
                      <tr key={item.ip}>
                        <td>
                          <button
                            onClick={() => handleIpClick(item.ip)}
                            className="font-mono font-semibold text-[#00F5A0] hover:underline cursor-pointer"
                          >
                            {item.ip}
                          </button>
                        </td>
                        <td className="text-[#E8FFF6]">
                          {item.country} <span className="text-[#607A71] text-[10px] font-mono">({item.country_code})</span>
                        </td>
                        <td className="text-[#9BB7AD]">{item.city ? `${item.city}, ${item.region}` : item.region || '—'}</td>
                        <td className="text-[#9BB7AD] max-w-xs truncate">{item.isp || '—'}</td>
                        <td className="font-mono text-[#607A71] text-[11px]">{item.asn || '—'}</td>
                        <td className="font-mono font-semibold text-[#E8FFF6]">{item.attack_count}</td>
                        <td>
                          <span className="font-mono font-bold" style={{ color: getThreatColor(item.threat_score) }}>
                            {item.threat_score}
                          </span>
                        </td>
                        <td>
                          <span className={`px-2 py-0.5 rounded text-[10px] font-mono font-semibold ${
                            item.status === 'Live' ? 'bg-[rgba(32,230,122,0.12)] text-[#20E67A] border border-[rgba(32,230,122,0.3)]' :
                            item.status === 'High Threat' || item.status === 'Active Threat' ? 'bg-[rgba(255,77,103,0.12)] text-[#FF4D67] border border-[rgba(255,77,103,0.3)]' :
                            'bg-[rgba(77,184,255,0.12)] text-[#4DB8FF] border border-[rgba(77,184,255,0.3)]'
                          }`}>
                            {item.status}
                          </span>
                        </td>
                        <td className="text-[#607A71] text-[11px] font-mono">
                          {item.last_seen ? new Date(item.last_seen).toLocaleDateString() : 'Recent'}
                        </td>
                        <td>
                          <button
                            onClick={() => handleIpClick(item.ip)}
                            className="text-[11px] font-medium text-[#00F5A0] hover:underline cursor-pointer"
                          >
                            Inspect
                          </button>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </GlassCard>

          {/* SECTION 3: Attacker Activity Summary */}
          <GlassCard className="p-5">
            <SectionHeader title="Attacker Behavioral Telemetry" badge={`${filteredActivity.length} sources`} />

            <div className="overflow-x-auto">
              <table className="soc-table">
                <thead>
                  <tr>
                    <th>Attacker IP</th>
                    <th>Attacks</th>
                    <th>Protocol</th>
                    <th>Logins (Tried/Granted)</th>
                    <th>Cmds</th>
                    <th>Payloads</th>
                    <th>Stage / Type</th>
                    <th>Score</th>
                    <th>Status</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredActivity.length === 0 ? (
                    <tr>
                      <td colSpan={9} className="text-center py-10 text-xs text-[#607A71]">
                        No activity records captured.
                      </td>
                    </tr>
                  ) : (
                    filteredActivity.map((act) => (
                      <tr key={act.ip}>
                        <td>
                          <button onClick={() => handleIpClick(act.ip)} className="font-mono font-semibold text-[#00F5A0] hover:underline cursor-pointer">
                            {act.ip}
                          </button>
                        </td>
                        <td className="font-mono text-[#E8FFF6]">{act.total_attacks}</td>
                        <td className="font-mono text-[#4DB8FF]">{act.protocol}</td>
                        <td className="font-mono">
                          {act.login_attempts} / <span className={act.successful_logins > 0 ? 'text-[#FF4D67] font-bold' : 'text-[#607A71]'}>{act.successful_logins}</span>
                        </td>
                        <td className="font-mono font-semibold text-[#E8FFF6]">{act.commands_executed}</td>
                        <td className="font-mono">
                          {act.download_attempts > 0 ? (
                            <span className="text-[#FF4D67] font-bold">{act.download_attempts}</span>
                          ) : (
                            <span className="text-[#607A71]">0</span>
                          )}
                        </td>
                        <td className="text-[#9BB7AD]">{act.attack_type}</td>
                        <td>
                          <span className="font-mono font-bold" style={{ color: getThreatColor(act.threat_score) }}>
                            {act.threat_score}
                          </span>
                        </td>
                        <td>
                          <span className={`px-2 py-0.5 rounded text-[10px] font-mono font-semibold ${
                            act.status === 'Live' ? 'bg-[rgba(32,230,122,0.12)] text-[#20E67A]' : 'bg-[rgba(255,255,255,0.06)] text-[#9BB7AD]'
                          }`}>
                            {act.status}
                          </span>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </GlassCard>

          {/* SECTION 4: Distributions & Stats */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {/* By Country */}
            <GlassCard className="p-4">
              <SectionHeader title="Attacks by Country" />
              {(statistics.by_country || []).length === 0 ? (
                <p className="text-xs text-[#607A71] py-8 text-center">No location statistics</p>
              ) : (
                <div className="space-y-2 max-h-56 overflow-y-auto">
                  {statistics.by_country.map((c, i) => (
                    <div key={i} className="space-y-1">
                      <div className="flex justify-between text-xs">
                        <span className="text-[#E8FFF6]">{c.country}</span>
                        <span className="font-mono text-[#00F5A0]">{c.count}</span>
                      </div>
                      <div className="w-full h-1.5 rounded-full bg-[#08110F] overflow-hidden">
                        <div
                          className="h-full rounded-full bg-[#00F5A0]"
                          style={{ width: `${Math.min(100, (c.count / (summary.total_attacks || 1)) * 100)}%` }}
                        />
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </GlassCard>

            {/* By Protocol */}
            <GlassCard className="p-4">
              <SectionHeader title="Protocol Distribution" />
              {(statistics.by_protocol || []).length === 0 ? (
                <p className="text-xs text-[#607A71] py-8 text-center">No protocol statistics</p>
              ) : (
                <ResponsiveContainer width="100%" height={180}>
                  <PieChart>
                    <Pie
                      data={statistics.by_protocol}
                      dataKey="count"
                      nameKey="protocol"
                      cx="50%"
                      cy="50%"
                      innerRadius={40}
                      outerRadius={65}
                      paddingAngle={3}
                    >
                      {statistics.by_protocol.map((_, i) => (
                        <Cell key={i} fill={CHART_COLORS[i % CHART_COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip contentStyle={customTooltipStyle} />
                  </PieChart>
                </ResponsiveContainer>
              )}
            </GlassCard>

            {/* Top Attacker IPs */}
            <GlassCard className="p-4">
              <SectionHeader title="Top Attacker IPs" />
              {(statistics.by_ip || []).length === 0 ? (
                <p className="text-xs text-[#607A71] py-8 text-center">No IP statistics</p>
              ) : (
                <div className="space-y-1.5 max-h-56 overflow-y-auto">
                  {statistics.by_ip.map((ipItem, i) => (
                    <div key={i} className="flex items-center justify-between py-1 border-b border-[rgba(255,255,255,0.04)] text-xs">
                      <button onClick={() => handleIpClick(ipItem.ip)} className="font-mono font-semibold text-[#00F5A0] hover:underline cursor-pointer">
                        {ipItem.ip}
                      </button>
                      <span className="font-mono text-[#9BB7AD]">{ipItem.count} events</span>
                    </div>
                  ))}
                </div>
              )}
            </GlassCard>
          </div>
        </>
      )}

      {/* IP Details Inspector Modal */}
      {selectedIp && (
        <div className="fixed inset-0 bg-[#050908]/80 z-50 flex items-center justify-center p-4 backdrop-blur-xs">
          <div className="w-full max-w-lg rounded-xl bg-[#0B1412] border border-[rgba(0,245,160,0.3)] shadow-2xl p-5 space-y-4">
            <div className="flex items-center justify-between border-b border-[rgba(0,245,160,0.14)] pb-3">
              <div className="flex items-center gap-2">
                <Globe size={16} className="text-[#00F5A0]" />
                <h3 className="text-sm font-bold text-[#E8FFF6] font-mono">
                  IP Threat Profile: {selectedIp}
                </h3>
              </div>
              <button
                onClick={() => { setSelectedIp(null); setIpModalData(null) }}
                className="text-[#607A71] hover:text-[#E8FFF6] cursor-pointer"
              >
                <X size={16} />
              </button>
            </div>

            {ipLoading ? (
              <LoadingSpinner size="md" text="Querying IP threat intelligence..." />
            ) : ipModalData ? (
              <div className="space-y-2.5 text-xs">
                <div className="grid grid-cols-2 gap-2">
                  <div className="p-2.5 rounded bg-[#08110F] border border-[rgba(0,245,160,0.12)]">
                    <span className="text-[10px] text-[#607A71] block font-mono">Country</span>
                    <span className="font-semibold text-[#E8FFF6]">{ipModalData.country || 'Unknown'} ({ipModalData.country_code})</span>
                  </div>
                  <div className="p-2.5 rounded bg-[#08110F] border border-[rgba(0,245,160,0.12)]">
                    <span className="text-[10px] text-[#607A71] block font-mono">City / Region</span>
                    <span className="font-semibold text-[#E8FFF6]">{ipModalData.city || 'Unknown'}, {ipModalData.region}</span>
                  </div>
                  <div className="p-2.5 rounded bg-[#08110F] border border-[rgba(0,245,160,0.12)]">
                    <span className="text-[10px] text-[#607A71] block font-mono">ISP / Network</span>
                    <span className="font-semibold text-[#E8FFF6] truncate block">{ipModalData.isp || 'Unknown'}</span>
                  </div>
                  <div className="p-2.5 rounded bg-[#08110F] border border-[rgba(0,245,160,0.12)]">
                    <span className="text-[10px] text-[#607A71] block font-mono">ASN</span>
                    <span className="font-mono text-[#E8FFF6]">{ipModalData.asn || 'N/A'}</span>
                  </div>
                </div>

                <div className="p-2.5 rounded bg-[#08110F] border border-[rgba(0,245,160,0.12)]">
                  <div className="flex justify-between items-center">
                    <span className="text-[10px] text-[#607A71] font-mono">Threat Score</span>
                    <span className="font-mono font-bold" style={{ color: getThreatColor(ipModalData.threat_score || 0) }}>
                      {ipModalData.threat_score || 0} / 100
                    </span>
                  </div>
                </div>
              </div>
            ) : (
              <p className="text-xs text-[#607A71] py-4 text-center">No enriched intelligence data found for this IP.</p>
            )}

            <div className="pt-2 flex justify-end">
              <SentinelButton
                onClick={() => { setSelectedIp(null); setIpModalData(null) }}
                variant="secondary"
                size="sm"
              >
                Close
              </SentinelButton>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
