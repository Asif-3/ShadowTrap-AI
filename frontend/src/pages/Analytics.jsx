import { useState, useEffect } from 'react'
import { analyticsAPI } from '../api/client'
import { GlassCard, LoadingSpinner, EmptyState, PageHeader, SectionHeader } from '../components/common'
import { motion } from 'framer-motion'
import { BarChart3 } from 'lucide-react'
import {
  PieChart, Pie, Cell, ResponsiveContainer, AreaChart, Area,
  XAxis, YAxis, Tooltip
} from 'recharts'

const CHART_PALETTE = ['#00F5A0', '#4DB8FF', '#FF4D67', '#F5C451', '#9B6CFF', '#00C98B', '#FF7043', '#20E67A']

export default function Analytics() {
  const [overview, setOverview] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    analyticsAPI.getStats()
      .then(r => setOverview(r.data.data))
      .catch(console.error)
      .finally(() => setLoading(false))
  }, [])

  if (loading) return <LoadingSpinner size="lg" text="Compiling telemetry analytics..." />

  const hasData = overview && (
    (overview.total_attacks > 0) ||
    (overview.timeline && overview.timeline.some(t => t.count > 0)) ||
    (overview.stage_distribution && overview.stage_distribution.length > 0) ||
    (overview.intent_distribution && overview.intent_distribution.length > 0) ||
    (overview.top_commands && overview.top_commands.length > 0) ||
    (overview.top_countries && overview.top_countries.length > 0)
  )

  const customTooltip = {
    background: '#0B1412',
    border: '1px solid rgba(0, 245, 160, 0.2)',
    borderRadius: 8,
    color: '#E8FFF6',
    fontSize: 12,
    fontFamily: 'Inter',
  }

  const topCommands = overview?.top_commands || []
  const maxCommandCount = Math.max(...topCommands.map(c => c.count || 1), 1)

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <PageHeader
        icon={BarChart3}
        title="Threat Analytics & Telemetry"
        badge="BEHAVIORAL AI"
        subtitle="Comprehensive honeypot telemetry distributions, kill chain stages, and command frequency statistics"
      />

      {!hasData ? (
        <GlassCard className="p-8">
          <EmptyState preset="analytics" />
        </GlassCard>
      ) : (
        <>
          {/* Attack Volume Trend */}
          <GlassCard className="p-5">
            <SectionHeader title="Attack Volume Trend" badge="Timeline" />
            <ResponsiveContainer width="100%" height={240}>
              <AreaChart data={overview?.timeline || []}>
                <defs>
                  <linearGradient id="trendGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#00F5A0" stopOpacity={0.25} />
                    <stop offset="95%" stopColor="#00F5A0" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <XAxis dataKey="date" tick={{ fill: '#9BB7AD', fontSize: 10, fontFamily: 'Inter' }} axisLine={false} tickLine={false} tickFormatter={v => v?.slice(5)} />
                <YAxis tick={{ fill: '#9BB7AD', fontSize: 10, fontFamily: 'Inter' }} axisLine={false} tickLine={false} />
                <Tooltip contentStyle={customTooltip} />
                <Area type="monotone" dataKey="count" stroke="#00F5A0" fill="url(#trendGrad)" strokeWidth={2} />
              </AreaChart>
            </ResponsiveContainer>
          </GlassCard>

          {/* Charts Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
            {/* Attack Stage Distribution */}
            <GlassCard className="p-5">
              <SectionHeader title="Attack Stage Distribution" />
              {(overview?.stage_distribution || []).length === 0 ? (
                <EmptyState preset="analytics" size="sm" title="No stage data yet" description="Attack stages will be visualized once sessions are captured." />
              ) : (
                <>
                  <ResponsiveContainer width="100%" height={200}>
                    <PieChart>
                      <Pie data={overview?.stage_distribution || []} dataKey="count" nameKey="stage" cx="50%" cy="50%"
                        innerRadius={45} outerRadius={75} paddingAngle={3}>
                        {(overview?.stage_distribution || []).map((_, i) => (
                          <Cell key={i} fill={CHART_PALETTE[i % CHART_PALETTE.length]} />
                        ))}
                      </Pie>
                      <Tooltip contentStyle={customTooltip} />
                    </PieChart>
                  </ResponsiveContainer>
                  <div className="flex flex-wrap gap-1.5 mt-2 max-h-24 overflow-y-auto">
                    {(overview?.stage_distribution || []).map((s, i) => (
                      <span 
                        key={i} 
                        className="text-[10px] font-semibold px-2 py-0.5 rounded font-mono"
                        style={{ background: `${CHART_PALETTE[i % 8]}15`, color: CHART_PALETTE[i % 8], border: `1px solid ${CHART_PALETTE[i % 8]}33` }}
                      >
                        {s.stage}: {s.count}
                      </span>
                    ))}
                  </div>
                </>
              )}
            </GlassCard>

            {/* Behavioral Intent Distribution */}
            <GlassCard className="p-5">
              <SectionHeader title="Behavioral Intent Distribution" />
              {(overview?.intent_distribution || []).length === 0 ? (
                <EmptyState preset="analytics" size="sm" title="No intent data yet" description="Behavioral intents will appear once commands are analyzed." />
              ) : (
                <>
                  <ResponsiveContainer width="100%" height={200}>
                    <PieChart>
                      <Pie data={overview?.intent_distribution || []} dataKey="count" nameKey="intent" cx="50%" cy="50%"
                        innerRadius={45} outerRadius={75} paddingAngle={3}>
                        {(overview?.intent_distribution || []).map((_, i) => (
                          <Cell key={i} fill={CHART_PALETTE[(i + 2) % CHART_PALETTE.length]} />
                        ))}
                      </Pie>
                      <Tooltip contentStyle={customTooltip} />
                    </PieChart>
                  </ResponsiveContainer>
                  <div className="flex flex-wrap gap-1.5 mt-2 max-h-24 overflow-y-auto">
                    {(overview?.intent_distribution || []).map((s, i) => (
                      <span 
                        key={i} 
                        className="text-[10px] font-semibold px-2 py-0.5 rounded font-mono"
                        style={{ background: `${CHART_PALETTE[(i + 2) % 8]}15`, color: CHART_PALETTE[(i + 2) % 8], border: `1px solid ${CHART_PALETTE[(i + 2) % 8]}33` }}
                      >
                        {s.intent}: {s.count}
                      </span>
                    ))}
                  </div>
                </>
              )}
            </GlassCard>

            {/* Top Executed Commands */}
            <GlassCard className="p-5">
              <SectionHeader title="Top Executed Commands" badge={`${topCommands.length}`} />
              {topCommands.length === 0 ? (
                <EmptyState preset="analytics" size="sm" title="No commands captured" description="Commands will be ranked once shell sessions are recorded." />
              ) : (
                <div className="space-y-2.5 max-h-64 overflow-y-auto pr-1">
                  {topCommands.slice(0, 8).map((cmdItem, i) => {
                    const pct = Math.max(10, (cmdItem.count / maxCommandCount) * 100)
                    const color = CHART_PALETTE[i % CHART_PALETTE.length]

                    return (
                      <div 
                        key={i} 
                        className="p-2.5 rounded-lg border transition-colors hover:border-[rgba(0,245,160,0.3)] space-y-2"
                        style={{
                          backgroundColor: '#08110F',
                          borderColor: 'rgba(0, 245, 160, 0.12)',
                        }}
                      >
                        <div className="flex items-center justify-between gap-3">
                          <div className="flex items-center gap-2 min-w-0 flex-1">
                            <span className="text-[#00F5A0] font-mono font-bold text-xs select-none">$</span>
                            <span
                              className="font-mono text-xs text-[#E8FFF6] truncate font-medium"
                              title={cmdItem.command}
                            >
                              {cmdItem.command}
                            </span>
                          </div>
                          <span 
                            className="text-[10px] font-mono font-bold px-2 py-0.5 rounded shrink-0"
                            style={{
                              backgroundColor: `${color}18`,
                              color: color,
                              border: `1px solid ${color}35`,
                            }}
                          >
                            {cmdItem.count} {cmdItem.count === 1 ? 'hit' : 'hits'}
                          </span>
                        </div>

                        {/* Progress Bar */}
                        <div className="w-full h-1.5 rounded-full overflow-hidden bg-[#050908] border border-[rgba(255,255,255,0.04)]">
                          <motion.div
                            initial={{ width: 0 }}
                            animate={{ width: `${pct}%` }}
                            transition={{ duration: 0.5, delay: i * 0.04 }}
                            className="h-full rounded-full"
                            style={{ backgroundColor: color }}
                          />
                        </div>
                      </div>
                    )
                  })}
                </div>
              )}
            </GlassCard>

            {/* Top Countries */}
            <GlassCard className="p-5">
              <SectionHeader title="Top Attacker Country Origins" badge={`${(overview?.top_countries || []).length}`} />
              {(overview?.top_countries || []).length === 0 ? (
                <EmptyState preset="analytics" size="sm" title="No geolocation data" description="Country origins will appear once IPs are geolocated." />
              ) : (
                <div className="space-y-2.5 max-h-64 overflow-y-auto pr-1">
                  {(overview?.top_countries || []).slice(0, 8).map((c, i) => {
                    const maxCountryCount = (overview?.top_countries?.[0]?.count) || 1
                    const pct = Math.max(10, (c.count / maxCountryCount) * 100)
                    const color = CHART_PALETTE[i % CHART_PALETTE.length]

                    return (
                      <div 
                        key={i} 
                        className="p-2.5 rounded-lg border transition-colors hover:border-[rgba(0,245,160,0.3)] space-y-2"
                        style={{
                          backgroundColor: '#08110F',
                          borderColor: 'rgba(0, 245, 160, 0.12)',
                        }}
                      >
                        <div className="flex items-center justify-between gap-3">
                          <span className="text-xs font-semibold text-[#E8FFF6] font-sans truncate">{c.country}</span>
                          <span 
                            className="text-[10px] font-mono font-bold px-2 py-0.5 rounded shrink-0"
                            style={{
                              backgroundColor: `${color}18`,
                              color: color,
                              border: `1px solid ${color}35`,
                            }}
                          >
                            {c.count} {c.count === 1 ? 'attack' : 'attacks'}
                          </span>
                        </div>

                        <div className="w-full h-1.5 rounded-full overflow-hidden bg-[#050908] border border-[rgba(255,255,255,0.04)]">
                          <motion.div
                            initial={{ width: 0 }}
                            animate={{ width: `${pct}%` }}
                            transition={{ duration: 0.5, delay: i * 0.04 }}
                            className="h-full rounded-full"
                            style={{ backgroundColor: color }}
                          />
                        </div>
                      </div>
                    )
                  })}
                </div>
              )}
            </GlassCard>
          </div>
        </>
      )}
    </div>
  )
}
