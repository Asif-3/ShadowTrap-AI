import { useState, useEffect } from 'react'
import { attacksAPI } from '../api/client'
import { useRealTimeAttacks } from '../hooks/useRealTimeAttacks'
import { GlassCard, PageHeader, SectionHeader, StatusBadge, LoadingSpinner, SentinelButton, AttackSimulator, EmptyState } from '../components/common'
import { motion } from 'framer-motion'
import { useNavigate } from 'react-router-dom'
import { Radio, RefreshCw, Zap } from 'lucide-react'
import { getThreatColor } from '../lib/utils'

export default function LiveSessions() {
  const [attacks, setAttacks] = useState([])
  const [loading, setLoading] = useState(true)
  const navigate = useNavigate()
  const { refreshCount } = useRealTimeAttacks()

  const fetchLive = () => {
    setLoading(true)
    attacksAPI.getRecent(30)
      .then(res => setAttacks(res.data.data))
      .catch(console.error)
      .finally(() => setLoading(false))
  }

  useEffect(() => { fetchLive() }, [refreshCount])

  const handleSimulatedAttackEvent = (eventData) => {
    setAttacks(prev => {
      const existingIdx = prev.findIndex(a => a.session_id === eventData.sessionId)
      if (existingIdx >= 0) {
        const updated = [...prev]
        updated[existingIdx] = {
          ...updated[existingIdx],
          command_count: (updated[existingIdx].command_count || 1) + 1,
          threat_score: eventData.score,
          attack_stage: eventData.stage,
          intent: eventData.intent,
          status: 'active',
          is_live: true
        }
        return updated
      } else {
        const newAttack = {
          session_id: eventData.sessionId,
          src_ip: eventData.srcIp,
          protocol: eventData.protocol,
          dst_port: eventData.protocol === 'SSH' ? 22 : eventData.protocol === 'HTTP' ? 80 : 23,
          threat_score: eventData.score,
          attack_stage: eventData.stage,
          intent: eventData.intent,
          command_count: 1,
          status: 'active',
          is_live: true,
          created_at: eventData.timestamp
        }
        return [newAttack, ...prev]
      }
    })
  }

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <PageHeader
        icon={Radio}
        title="Live Attack Sessions"
        subtitle="Real-time honeypot session monitoring & interactive attack simulation"
        actions={
          <SentinelButton onClick={fetchLive} variant="secondary" size="sm">
            <RefreshCw size={14} /> Refresh
          </SentinelButton>
        }
      />

      {/* Attack Simulator */}
      <AttackSimulator onAttackEvent={handleSimulatedAttackEvent} />

      {/* Active Sessions */}
      <div>
        <SectionHeader
          title="Recent Honeypot Sessions"
          badge={String(attacks.length)}
        />

        {loading ? <LoadingSpinner text="Loading sessions..." /> : attacks.length === 0 ? (
          <GlassCard className="p-5">
            <EmptyState preset="sessions" size="md" />
          </GlassCard>
        ) : (
          <div className="grid gap-3">
            {attacks.map((atk, i) => (
              <motion.div
                key={atk.session_id}
                initial={{ opacity: 0, y: 6 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.02 }}
                onClick={() => navigate(`/sentinel/attacks/${atk.session_id}`)}
                className="sentinel-card sentinel-card-hover p-4 cursor-pointer"
              >
                <div className="flex items-center justify-between flex-wrap gap-3">
                  <div className="flex items-center gap-3 min-w-0">
                    <div
                      className="w-2 h-2 rounded-full shrink-0"
                      style={{
                        background: atk.is_live ? '#20E67A' : '#607A71',
                        boxShadow: atk.is_live ? '0 0 8px rgba(32,230,122,0.6)' : 'none'
                      }}
                    />
                    <div className="min-w-0">
                      <code className="text-xs font-semibold text-[#00F5A0] font-mono">{atk.session_id}</code>
                      <p className="text-[11px] text-[#9BB7AD] mt-0.5 font-mono truncate">
                        {atk.src_ip} • {atk.protocol?.toUpperCase()} • :{atk.dst_port}
                      </p>
                    </div>
                  </div>

                  <div className="flex items-center gap-5">
                    <div className="text-right">
                      <span className="text-sm font-bold font-mono" style={{ color: getThreatColor(atk.threat_score) }}>
                        {atk.threat_score}
                      </span>
                      <p className="text-[10px] text-[#607A71] font-sans">Threat</p>
                    </div>
                    <div className="text-right">
                      <span className="text-sm font-semibold text-[#E8FFF6] font-mono">{atk.command_count}</span>
                      <p className="text-[10px] text-[#607A71] font-sans">Cmds</p>
                    </div>
                    <StatusBadge status={atk.status} />
                  </div>
                </div>

                {atk.attack_stage && (
                  <div className="flex flex-wrap gap-2 mt-3 pt-2.5 border-t border-[rgba(0,245,160,0.1)]">
                    <span className="text-[10px] font-semibold px-2 py-0.5 rounded bg-[rgba(0,245,160,0.1)] text-[#00F5A0] border border-[rgba(0,245,160,0.22)]">
                      {atk.attack_stage}
                    </span>
                    {atk.intent && (
                      <span className="text-[10px] font-semibold px-2 py-0.5 rounded bg-[rgba(255,77,103,0.1)] text-[#FF4D67] border border-[rgba(255,77,103,0.25)]">
                        {atk.intent}
                      </span>
                    )}
                  </div>
                )}
              </motion.div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
