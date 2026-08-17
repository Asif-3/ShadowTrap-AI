import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { attacksAPI } from '../api/client'
import { useRealTimeAttacks } from '../hooks/useRealTimeAttacks'
import { GlassCard, PageHeader, StatusBadge, LoadingSpinner } from '../components/common'
import { motion } from 'framer-motion'
import { Shield, Search, Play, ChevronLeft, ChevronRight, Trash2 } from 'lucide-react'
import { getThreatColor } from '../lib/utils'

export default function Attacks() {
  const [attacks, setAttacks] = useState({ items: [], total: 0, pages: 1 })
  const [loading, setLoading] = useState(true)
  const [page, setPage] = useState(1)
  const [ipFilter, setIpFilter] = useState('')
  const [stageFilter, setStageFilter] = useState('')
  const [intentFilter, setIntentFilter] = useState('')
  const [minScore, setMinScore] = useState('')
  const [selectedAttacks, setSelectedAttacks] = useState([])
  const [deleting, setDeleting] = useState(false)
  const navigate = useNavigate()
  const { refreshCount } = useRealTimeAttacks()

  const fetchAttacks = () => {
    setLoading(true)
    const filters = {}
    if (ipFilter) filters.ip = ipFilter
    if (stageFilter) filters.stage = stageFilter
    if (intentFilter) filters.intent = intentFilter
    if (minScore) filters.min_score = minScore

    attacksAPI.getAttacks({ page, limit: 15, ...filters })
      .then(res => setAttacks(res.data.data))
      .catch(console.error)
      .finally(() => setLoading(false))
  }

  useEffect(() => { fetchAttacks() }, [page, stageFilter, intentFilter, minScore, refreshCount])

  const stages = [
    'Reconnaissance', 'Discovery', 'Credential Discovery', 'Payload Download',
    'Privilege Escalation', 'Persistence', 'Defense Evasion', 'Command And Control',
    'Data Collection', 'Exfiltration'
  ]

  const intents = [
    'Reconnaissance', 'Credential Theft', 'Data Theft',
    'Persistence', 'Malware Deployment', 'Privilege Escalation'
  ]

  const handleSelect = (id, e) => {
    e.stopPropagation()
    setSelectedAttacks(prev => 
      prev.includes(id) ? prev.filter(x => x !== id) : [...prev, id]
    )
  }

  const handleSelectAll = (e) => {
    if (e.target.checked) {
      setSelectedAttacks(attacks.items.map(a => a.session_id))
    } else {
      setSelectedAttacks([])
    }
  }

  const handleBulkDelete = async () => {
    if (!selectedAttacks.length || deleting) return
    if (!window.confirm(`Delete ${selectedAttacks.length} attack sessions?`)) return
    
    setDeleting(true)
    try {
      await attacksAPI.deleteAttacks(selectedAttacks)
      setSelectedAttacks([])
      fetchAttacks()
    } catch (err) {
      console.error(err)
      alert("Failed to delete sessions")
    } finally {
      setDeleting(false)
    }
  }

  return (
    <div className="space-y-5">
      <PageHeader
        icon={Shield}
        title="Attack Sessions"
        badge={`${attacks.total} total`}
        subtitle="All captured honeypot attack sessions with threat analysis"
      />

      {/* Filter Bar */}
      <GlassCard className="flex flex-wrap items-center gap-3 p-4">
        <div className="flex items-center gap-2 px-3 py-2 rounded-lg flex-1 min-w-[180px] bg-[#08110F] border border-[rgba(0,245,160,0.16)]">
          <Search size={14} className="text-[#607A71] shrink-0" />
          <input
            type="text"
            placeholder="Search by IP..."
            value={ipFilter}
            onChange={(e) => setIpFilter(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && fetchAttacks()}
            className="bg-transparent text-xs outline-none w-full text-[#E8FFF6] font-mono placeholder:text-[#607A71] border-0 p-0"
          />
        </div>

        <select
          value={stageFilter}
          onChange={(e) => { setStageFilter(e.target.value); setPage(1) }}
          className="px-3 py-2 rounded-lg text-xs"
        >
          <option value="">All Stages</option>
          {stages.map(s => <option key={s} value={s}>{s}</option>)}
        </select>

        <select
          value={intentFilter}
          onChange={(e) => { setIntentFilter(e.target.value); setPage(1) }}
          className="px-3 py-2 rounded-lg text-xs"
        >
          <option value="">All Intents</option>
          {intents.map(i => <option key={i} value={i}>{i}</option>)}
        </select>

        <select
          value={minScore}
          onChange={(e) => { setMinScore(e.target.value); setPage(1) }}
          className="px-3 py-2 rounded-lg text-xs"
        >
          <option value="">All Scores</option>
          <option value="80">Critical (80+)</option>
          <option value="60">High (60+)</option>
          <option value="35">Medium (35+)</option>
        </select>

        {(ipFilter || stageFilter || intentFilter || minScore) && (
          <button
            onClick={() => { setIpFilter(''); setStageFilter(''); setIntentFilter(''); setMinScore(''); setPage(1) }}
            className="btn-ghost text-xs text-[#FF4D67]"
          >
            Clear Filters
          </button>
        )}

        {selectedAttacks.length > 0 && (
          <button
            onClick={handleBulkDelete}
            disabled={deleting}
            className="btn-danger text-xs ml-auto"
          >
            <Trash2 size={13} />
            {deleting ? 'Deleting...' : `Delete (${selectedAttacks.length})`}
          </button>
        )}
      </GlassCard>

      {/* Attack Table */}
      <GlassCard className="p-0 overflow-hidden">
        {loading ? <div className="p-5"><LoadingSpinner text="Loading attacks..." /></div> : (
          <>
            <div className="overflow-x-auto">
              <table className="soc-table">
                <thead>
                  <tr>
                    <th className="w-10">
                      <input 
                        type="checkbox" 
                        className="accent-[#00F5A0] cursor-pointer"
                        checked={attacks.items?.length > 0 && selectedAttacks.length === attacks.items.length}
                        onChange={handleSelectAll}
                      />
                    </th>
                    <th>Session ID</th>
                    <th>Source IP</th>
                    <th>Cmds</th>
                    <th>Duration</th>
                    <th>Stage</th>
                    <th>Intent</th>
                    <th>Score</th>
                    <th>Status</th>
                    <th className="w-12"></th>
                  </tr>
                </thead>
                <tbody>
                  {attacks.items?.length === 0 && (
                    <tr>
                      <td colSpan={10} className="text-center py-10 text-xs text-[#607A71]">
                        No attack sessions match your filters.
                      </td>
                    </tr>
                  )}
                  {attacks.items?.map((atk, i) => (
                    <motion.tr
                      key={atk.session_id}
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      transition={{ delay: i * 0.02 }}
                      className="cursor-pointer"
                      onClick={() => navigate(`/sentinel/attacks/${atk.session_id}`)}
                    >
                      <td onClick={e => e.stopPropagation()}>
                        <input 
                          type="checkbox" 
                          className="accent-[#00F5A0] cursor-pointer"
                          checked={selectedAttacks.includes(atk.session_id)}
                          onChange={(e) => handleSelect(atk.session_id, e)}
                        />
                      </td>
                      <td>
                        <code className="text-[11px] font-semibold text-[#00F5A0] font-mono">{atk.session_id}</code>
                      </td>
                      <td className="font-mono text-[11px]">{atk.src_ip}</td>
                      <td className="text-[#9BB7AD] font-mono">{atk.command_count}</td>
                      <td className="text-[#9BB7AD] font-mono">{atk.duration?.toFixed(1)}s</td>
                      <td>
                        <span className="text-[10px] font-semibold px-2 py-0.5 rounded bg-[rgba(0,245,160,0.1)] text-[#00F5A0] border border-[rgba(0,245,160,0.22)]">
                          {atk.attack_stage || '—'}
                        </span>
                      </td>
                      <td>
                        <span className="text-[10px] font-semibold px-2 py-0.5 rounded bg-[rgba(255,77,103,0.1)] text-[#FF4D67] border border-[rgba(255,77,103,0.25)]">
                          {atk.intent || '—'}
                        </span>
                      </td>
                      <td>
                        <span className="text-xs font-bold font-mono" style={{ color: getThreatColor(atk.threat_score) }}>
                          {atk.threat_score}
                        </span>
                      </td>
                      <td><StatusBadge status={atk.status} /></td>
                      <td onClick={(e) => e.stopPropagation()}>
                        <button
                          onClick={() => navigate(`/sentinel/replay/${atk.session_id}`)}
                          className="p-1.5 rounded-md hover:bg-[rgba(0,245,160,0.1)] text-[#00F5A0] cursor-pointer transition"
                          title="Replay Attack"
                        >
                          <Play size={13} />
                        </button>
                      </td>
                    </motion.tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Pagination */}
            {attacks.pages > 1 && (
              <div className="flex items-center justify-between px-5 py-3 border-t border-[rgba(0,245,160,0.1)]">
                <span className="text-xs text-[#607A71] font-sans">
                  Page {attacks.page} of {attacks.pages} • {attacks.total} sessions
                </span>
                <div className="flex items-center gap-1.5">
                  <button
                    disabled={page <= 1}
                    onClick={() => setPage(p => Math.max(1, p - 1))}
                    className="p-1.5 rounded-md hover:bg-[rgba(255,255,255,0.04)] disabled:opacity-30 cursor-pointer text-[#9BB7AD]"
                  >
                    <ChevronLeft size={15} />
                  </button>
                  <button
                    disabled={page >= attacks.pages}
                    onClick={() => setPage(p => Math.min(attacks.pages, p + 1))}
                    className="p-1.5 rounded-md hover:bg-[rgba(255,255,255,0.04)] disabled:opacity-30 cursor-pointer text-[#9BB7AD]"
                  >
                    <ChevronRight size={15} />
                  </button>
                </div>
              </div>
            )}
          </>
        )}
      </GlassCard>
    </div>
  )
}
