import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import { dashboardAPI } from '../api/client'
import { useRealTimeAttacks } from '../hooks/useRealTimeAttacks'
import { GlassCard, KPICard, PageHeader, SectionHeader, ThreatMeter, LoadingSpinner, StatusBadge, EmptyState } from '../components/common'
import WorldAttackMap from '../components/dashboard/WorldAttackMap'
import ThreatHeatmap from '../components/dashboard/ThreatHeatmap'
import BehaviorClusterViz from '../components/dashboard/BehaviorClusterViz'
import ModelPerformance from '../components/dashboard/ModelPerformance'
import { Shield, Radio, AlertTriangle, Activity, Play, ArrowRight, Eye, Workflow, LayoutDashboard } from 'lucide-react'
import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts'
import { getThreatColor, getThreatLevel } from '../lib/utils'

export default function Dashboard() {
  const [widgets, setWidgets] = useState(null)
  const [loading, setLoading] = useState(true)
  const navigate = useNavigate()

  const { attacks: realTimeAttacks, dashboardStats, isNewAttack, refreshCount } = useRealTimeAttacks()

  const fetchWidgets = () => {
    dashboardAPI.getWidgets()
      .then((res) => setWidgets(res.data.data))
      .catch(console.error)
      .finally(() => setLoading(false))
  }

  useEffect(() => {
    fetchWidgets()
  }, [refreshCount, realTimeAttacks.length])

  if (loading) return <LoadingSpinner size="lg" text="Loading SOC dashboard..." />
  if (!widgets) return <p className="text-sm text-[#607A71]">Failed to load dashboard data</p>

  const { stats, recent_attacks, attack_timeline, attack_locations, heatmap_data, behavior_clusters, model_performance, model_metrics } = widgets

  // Merge real-time stats with API stats
  const liveStats = {
    total_attacks: dashboardStats?.total_attacks ?? stats.total_attacks,
    today_attacks: dashboardStats?.today_attacks ?? stats.today_attacks,
    high_risk_attacks: dashboardStats?.high_risk_attacks ?? stats.high_risk_attacks,
    live_sessions: dashboardStats?.live_sessions ?? stats.live_sessions,
    avg_threat_score: dashboardStats?.avg_threat_score ?? stats.avg_threat_score,
  }

  // Merge real-time attacks with API attacks, deduplicated by session_id
  const mergeAttacks = () => {
    const map = new Map()
    if (recent_attacks) {
      recent_attacks.forEach((a) => map.set(a.session_id, a))
    }
    realTimeAttacks.forEach((a) => map.set(a.session_id, a))
    return Array.from(map.values())
      .sort((a, b) => new Date(b.created_at || b.start_time || 0) - new Date(a.created_at || a.start_time || 0))
      .slice(0, 10)
  }

  const displayAttacks = mergeAttacks()
  const hasAttacks = liveStats.total_attacks > 0 || displayAttacks?.length > 0

  const pipelineSteps = [
    { title: '1. Decoy Trap', status: 'Active', desc: 'Attacker visits corporate site decoy', icon: Eye, color: '#00F5A0' },
    { title: '2. Silent Telemetry', status: 'Logging', desc: 'Fingerprinting & DevTools detection', icon: Activity, color: '#4DB8FF' },
    { title: '3. Cowrie Honeypot', status: 'Live', desc: 'SSH/Telnet command capture sandbox', icon: Radio, color: '#F5C451' },
    { title: '4. AI Analysis', status: 'Analyzing', desc: 'Threat scoring & MITRE ATT&CK mapping', icon: Shield, color: '#9B6CFF' }
  ]

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <PageHeader
        icon={LayoutDashboard}
        title="SOC Dashboard"
        subtitle="Autonomous deception honeypot • Real-time threat intelligence • AI behavioral analytics"
        actions={
          <button
            onClick={() => navigate('/sentinel/live-sessions')}
            className="btn-primary text-xs font-semibold"
          >
            <Play size={13} /> Launch Simulator <ArrowRight size={13} />
          </button>
        }
      />

      {/* Deception Pipeline */}
      <div
        className="sentinel-card p-5"
        style={{ backgroundColor: '#08110F' }}
      >
        <div className="flex items-center justify-between mb-3.5">
          <div className="flex items-center gap-2">
            <Workflow size={15} className="text-[#00F5A0]" />
            <span className="text-[11px] font-semibold text-[#E8FFF6] tracking-wider uppercase font-sans">
              Deception Pipeline
            </span>
          </div>
          <span className="text-[10px] font-semibold text-[#20E67A] flex items-center gap-1.5 font-mono tracking-wider">
            <span className="live-dot-sm" /> OPERATIONAL
          </span>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {pipelineSteps.map((step, idx) => (
            <motion.div
              key={idx}
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: idx * 0.08 }}
              className="p-3.5 rounded-lg space-y-2 border"
              style={{
                backgroundColor: '#0B1412',
                borderColor: 'rgba(0, 245, 160, 0.12)',
              }}
            >
              <div className="flex items-center justify-between">
                <step.icon size={16} style={{ color: step.color }} />
                <span
                  className="text-[9px] font-semibold px-2 py-0.5 rounded font-mono"
                  style={{
                    color: step.color,
                    backgroundColor: `${step.color}14`,
                    border: `1px solid ${step.color}30`,
                  }}
                >
                  {step.status.toUpperCase()}
                </span>
              </div>
              <p className="text-xs font-semibold text-[#E8FFF6] font-sans">{step.title}</p>
              <p className="text-[11px] text-[#9BB7AD] leading-snug font-sans">{step.desc}</p>
            </motion.div>
          ))}
        </div>
      </div>

      {/* KPI Cards — Matching 4-col grid */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <KPICard label="Total Attacks" value={liveStats.total_attacks} icon={Shield} color="#00F5A0" delay={0} />
        <KPICard label="Today's Attacks" value={liveStats.today_attacks} icon={Activity} color="#4DB8FF" delay={0.04} />
        <KPICard label="High Risk" value={liveStats.high_risk_attacks} icon={AlertTriangle} color="#FF4D67" delay={0.08} />
        <KPICard label="Live Sessions" value={liveStats.live_sessions} icon={Radio} color="#20E67A" delay={0.12} />
      </div>

      {/* Data-dependent sections */}
      {!hasAttacks ? (
        <GlassCard className="p-6">
          <EmptyState preset="dashboard" size="lg">
            <button
              onClick={() => navigate('/sentinel/live-sessions')}
              className="btn-primary text-xs mt-2"
            >
              <Play size={14} /> Launch Attack Simulator
            </button>
          </EmptyState>
        </GlassCard>
      ) : (
        <>
          {/* Row 1: Attack Map (2 cols) + Threat Gauge (1 col) — Perfectly Aligned */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-5 items-stretch">
            <GlassCard className="lg:col-span-2 p-5 flex flex-col justify-between h-full">
              <SectionHeader title="Global Attack Origins" badge="LIVE" />
              <WorldAttackMap locations={attack_locations || []} />
            </GlassCard>

            <GlassCard className="flex flex-col justify-between p-5 h-full">
              <SectionHeader title="Threat Index" />
              <div className="flex-1 flex flex-col items-center justify-center my-2">
                <ThreatMeter score={Math.round(liveStats.avg_threat_score)} size={130} />
                <p className="text-sm font-semibold mt-3 font-sans" style={{ color: getThreatColor(liveStats.avg_threat_score) }}>
                  {getThreatLevel(liveStats.avg_threat_score)} Risk Level
                </p>
              </div>
              <div className="w-full pt-3 border-t border-[rgba(0,245,160,0.1)] flex justify-between text-[11px] font-mono text-[#9BB7AD]">
                <span>SOC EVALUATION</span>
                <span className="text-[#00F5A0] font-semibold">ACTIVE</span>
              </div>
            </GlassCard>
          </div>

          {/* Row 2: Timeline (2 cols) + Heatmap (1 col) — Perfectly Aligned */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-5 items-stretch">
            <GlassCard className="lg:col-span-2 p-5 flex flex-col justify-between h-full">
              <SectionHeader title="Attack Volume Timeline" badge="30 Days" />
              <ResponsiveContainer width="100%" height={210}>
                <AreaChart data={attack_timeline}>
                  <defs>
                    <linearGradient id="timelineGrad" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#00F5A0" stopOpacity={0.25} />
                      <stop offset="95%" stopColor="#00F5A0" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <XAxis dataKey="date" tick={{ fill: '#9BB7AD', fontSize: 10, fontFamily: 'Inter' }} axisLine={false} tickLine={false} tickFormatter={(v) => v?.slice(5)} />
                  <YAxis tick={{ fill: '#9BB7AD', fontSize: 10, fontFamily: 'Inter' }} axisLine={false} tickLine={false} />
                  <Tooltip contentStyle={{ background: '#0B1412', border: '1px solid rgba(0, 245, 160, 0.2)', borderRadius: 8, color: '#E8FFF6', fontSize: 12, fontFamily: 'Inter' }} />
                  <Area type="monotone" dataKey="count" stroke="#00F5A0" fill="url(#timelineGrad)" strokeWidth={2} />
                </AreaChart>
              </ResponsiveContainer>
            </GlassCard>

            <ThreatHeatmap heatData={heatmap_data} />
          </div>

          {/* Row 3: Behavior Cluster (1 col) + Model Performance (1 col) */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-5 items-stretch">
            <BehaviorClusterViz clusters={behavior_clusters || []} />
            <ModelPerformance performanceData={model_performance || []} currentMetrics={model_metrics} />
          </div>

          {/* Row 4: Recent Attacks Table */}
          <GlassCard className="p-5">
            <div className="flex items-center justify-between mb-4">
              <SectionHeader
                title="Recent Attack Sessions"
                badge={`${displayAttacks.length}`}
                className="mb-0"
              />
              <button
                onClick={() => navigate('/sentinel/attacks')}
                className="text-xs font-medium text-[#00F5A0] hover:underline cursor-pointer font-sans"
              >
                View All →
              </button>
            </div>

            <div className="overflow-x-auto">
              <table className="soc-table">
                <thead>
                  <tr>
                    <th>Session ID</th>
                    <th>Source IP</th>
                    <th>Stage</th>
                    <th>Intent</th>
                    <th>Threat</th>
                    <th>Cmds</th>
                    <th>Status</th>
                  </tr>
                </thead>
                <tbody>
                  {displayAttacks.map((atk, i) => (
                    <motion.tr
                      key={atk.session_id}
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      transition={{ delay: i * 0.03 }}
                      className={`cursor-pointer ${isNewAttack(atk.session_id) ? 'bg-[rgba(0,245,160,0.04)]' : ''}`}
                      onClick={() => navigate(`/sentinel/attacks/${atk.session_id}`)}
                    >
                      <td>
                        <code className="font-semibold text-[#00F5A0] font-mono text-[11px]">{atk.session_id}</code>
                      </td>
                      <td className="font-mono text-[11px]">{atk.src_ip}</td>
                      <td className="text-[#9BB7AD] font-sans">{atk.attack_stage || '—'}</td>
                      <td className="text-[#9BB7AD] font-sans">{atk.intent || '—'}</td>
                      <td>
                        <span className="font-bold font-mono" style={{ color: getThreatColor(atk.threat_score) }}>
                          {atk.threat_score}
                        </span>
                      </td>
                      <td className="text-[#9BB7AD] font-mono">{atk.command_count}</td>
                      <td><StatusBadge status={atk.status} /></td>
                    </motion.tr>
                  ))}
                </tbody>
              </table>
            </div>
          </GlassCard>
        </>
      )}
    </div>
  )
}
