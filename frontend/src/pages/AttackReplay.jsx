import { useState, useEffect, useRef } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { replayAPI, attacksAPI } from '../api/client'
import { GlassCard, SentinelButton, LoadingSpinner, PageHeader, EmptyState, SectionHeader } from '../components/common'
import { motion, AnimatePresence } from 'framer-motion'
import { Play, Pause, SkipForward, RotateCcw, ArrowLeft, Terminal } from 'lucide-react'

export default function AttackReplay() {
  const { sessionId } = useParams()
  const navigate = useNavigate()
  const [replay, setReplay] = useState([])
  const [attacks, setAttacks] = useState([])
  const [selectedSession, setSelectedSession] = useState(sessionId || '')
  const [currentStep, setCurrentStep] = useState(-1)
  const [playing, setPlaying] = useState(false)
  const [speed, setSpeed] = useState(1)
  const [loading, setLoading] = useState(true)
  const terminalRef = useRef(null)
  const timerRef = useRef(null)

  // Load attack list if no session specified
  useEffect(() => {
    if (!sessionId) {
      attacksAPI.getAttacks({ limit: 24 })
        .then(res => { setAttacks(res.data.data.items || []); setLoading(false) })
        .catch(() => setLoading(false))
    }
  }, [sessionId])

  // Load replay data
  useEffect(() => {
    if (selectedSession) {
      setLoading(true)
      replayAPI.getReplay(selectedSession)
        .then(res => { setReplay(res.data.data || []); setCurrentStep(-1); setPlaying(false) })
        .catch(console.error)
        .finally(() => setLoading(false))
    }
  }, [selectedSession])

  // Playback engine
  useEffect(() => {
    if (playing && currentStep < replay.length - 1) {
      const nextStep = replay[currentStep + 1]
      const delay = Math.max(200, (nextStep?.delay || 1.5) * 1000 / speed)
      timerRef.current = setTimeout(() => setCurrentStep(s => s + 1), delay)
    } else if (currentStep >= replay.length - 1) {
      setPlaying(false)
    }
    return () => clearTimeout(timerRef.current)
  }, [playing, currentStep, replay, speed])

  // Auto-scroll terminal
  useEffect(() => {
    if (terminalRef.current) {
      terminalRef.current.scrollTop = terminalRef.current.scrollHeight
    }
  }, [currentStep])

  const togglePlay = () => {
    if (currentStep >= replay.length - 1) setCurrentStep(-1)
    setPlaying(!playing)
  }

  const reset = () => { setPlaying(false); setCurrentStep(-1) }
  const skipNext = () => { if (currentStep < replay.length - 1) setCurrentStep(s => s + 1) }

  // Session selector view
  if (!selectedSession && !sessionId) {
    return (
      <div className="space-y-6">
        <PageHeader
          icon={Terminal}
          title="Attack Session Replay"
          subtitle="Select a recorded honeypot session to execute real-time command chronology playback"
        />

        {loading ? <LoadingSpinner text="Loading sessions..." /> : attacks.length === 0 ? (
          <GlassCard className="p-6">
            <EmptyState preset="replay" />
          </GlassCard>
        ) : (
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {attacks.map((atk) => (
              <GlassCard 
                key={atk.session_id} 
                className="cursor-pointer sentinel-card-hover p-4" 
                onClick={() => setSelectedSession(atk.session_id)}
              >
                <div className="flex items-center justify-between">
                  <code className="text-xs font-semibold text-[#00F5A0] font-mono">{atk.session_id}</code>
                  <span className="text-[10px] font-mono text-[#9BB7AD]">{atk.command_count} cmds</span>
                </div>
                <p className="text-[11px] text-[#607A71] mt-1 font-mono">{atk.src_ip} • {atk.attack_stage || 'Unknown'}</p>
              </GlassCard>
            ))}
          </div>
        )}
      </div>
    )
  }

  return (
    <div className="space-y-5">
      {/* Top Bar */}
      <div className="flex items-center justify-between flex-wrap gap-4 pb-4 border-b border-[rgba(0,245,160,0.14)]">
        <div className="flex items-center gap-3">
          <button 
            onClick={() => sessionId ? navigate(-1) : setSelectedSession('')} 
            className="p-2 rounded-lg hover:bg-[rgba(255,255,255,0.05)] text-[#9BB7AD] hover:text-[#E8FFF6] transition cursor-pointer border border-[rgba(0,245,160,0.14)]"
          >
            <ArrowLeft size={16} />
          </button>
          <div>
            <h1 className="text-xl font-bold text-[#E8FFF6] flex items-center gap-2 font-sans">
              <Terminal size={18} className="text-[#00F5A0]" /> Command Sequence Replay
            </h1>
            <p className="text-xs text-[#9BB7AD] mt-0.5 font-mono">
              Session: <code className="text-[#00F5A0] font-bold">{selectedSession}</code>
            </p>
          </div>
        </div>
      </div>

      {loading ? <LoadingSpinner text="Loading replay stream..." /> : (
        <>
          {/* Controls Bar */}
          <GlassCard className="flex items-center justify-between flex-wrap gap-4 p-4">
            <div className="flex items-center gap-2">
              <SentinelButton onClick={togglePlay} size="sm">
                {playing ? <Pause size={14} /> : <Play size={14} />}
                {playing ? 'Pause' : 'Play'}
              </SentinelButton>
              <SentinelButton onClick={skipNext} variant="secondary" size="sm" title="Step forward">
                <SkipForward size={14} />
              </SentinelButton>
              <SentinelButton onClick={reset} variant="secondary" size="sm" title="Reset timeline">
                <RotateCcw size={14} />
              </SentinelButton>
            </div>

            {/* Playback Speed */}
            <div className="flex items-center gap-2">
              <span className="text-xs font-medium text-[#9BB7AD] font-sans">Speed:</span>
              {[0.5, 1, 2, 4].map(s => (
                <button 
                  key={s} 
                  onClick={() => setSpeed(s)}
                  className={`px-2 py-1 rounded text-xs font-mono font-semibold transition cursor-pointer ${
                    speed === s
                      ? 'bg-[rgba(0,245,160,0.12)] text-[#00F5A0] border border-[rgba(0,245,160,0.3)]'
                      : 'text-[#607A71] hover:text-[#E8FFF6] hover:bg-[rgba(255,255,255,0.04)] border border-transparent'
                  }`}
                >
                  {s}x
                </button>
              ))}
            </div>

            <div className="text-xs font-mono font-semibold text-[#00F5A0] bg-[rgba(0,245,160,0.08)] px-2.5 py-1 rounded border border-[rgba(0,245,160,0.2)]">
              Step {Math.max(0, currentStep + 1)} / {replay.length}
            </div>
          </GlassCard>

          {/* Progress Bar */}
          <div className="h-1.5 rounded-full overflow-hidden bg-[#08110F] border border-[rgba(0,245,160,0.14)]">
            <motion.div
              className="h-full rounded-full bg-[#00F5A0]"
              animate={{ width: `${replay.length ? ((currentStep + 1) / replay.length) * 100 : 0}%` }}
              transition={{ duration: 0.2 }}
            />
          </div>

          {/* Terminal Console */}
          <div 
            ref={terminalRef} 
            className="terminal-card p-4 min-h-[360px] max-h-[460px] overflow-y-auto font-mono text-xs shadow-xl"
          >
            <div className="mb-3 border-b border-[rgba(0,245,160,0.14)] pb-2 flex items-center justify-between text-[11px]">
              <span className="text-[#00F5A0] font-bold">[SHADOWTRAP://SANDBOX_REPLAY]</span>
              <span className="text-[#607A71]">SANDBOX TELEMETRY LOG</span>
            </div>

            <AnimatePresence>
              {replay.slice(0, currentStep + 1).map((step, i) => (
                <motion.div
                  key={i}
                  initial={{ opacity: 0, x: -10 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ duration: 0.15 }}
                  className="py-1 flex items-center justify-between border-b border-[rgba(255,255,255,0.03)]"
                >
                  <div className="flex items-center gap-2">
                    <span className="text-[#00F5A0] font-bold select-none">root@honeypot:~$</span>
                    <span className="text-[#E8FFF6]">{step.command}</span>
                  </div>
                  {step.timestamp && (
                    <span className="text-[10px] text-[#607A71] shrink-0 font-mono">
                      {step.timestamp?.slice(11, 19)}
                    </span>
                  )}
                </motion.div>
              ))}
            </AnimatePresence>

            {/* Prompt Line */}
            {currentStep < replay.length - 1 && (
              <div className="py-1 flex items-center gap-2">
                <span className="text-[#00F5A0] font-bold select-none">root@honeypot:~$</span>
                <span className="inline-block w-2 h-4 animate-pulse bg-[#00F5A0]" />
              </div>
            )}
          </div>

          {/* Steps Timeline Badges */}
          <GlassCard className="p-4">
            <SectionHeader title="Executed Command Sequence" badge={`${replay.length} steps`} />
            <div className="flex flex-wrap gap-1.5 max-h-36 overflow-y-auto">
              {replay.map((step, i) => (
                <button
                  key={i}
                  onClick={() => { setCurrentStep(i); setPlaying(false) }}
                  className={`px-2.5 py-1 rounded text-[11px] font-mono transition truncate max-w-[180px] cursor-pointer border ${
                    i <= currentStep
                      ? 'bg-[rgba(0,245,160,0.12)] text-[#00F5A0] border-[rgba(0,245,160,0.3)] font-semibold'
                      : 'bg-[#08110F] text-[#607A71] hover:text-[#E8FFF6] border-[rgba(255,255,255,0.06)]'
                  }`}
                >
                  {step.command}
                </button>
              ))}
            </div>
          </GlassCard>
        </>
      )}
    </div>
  )
}
