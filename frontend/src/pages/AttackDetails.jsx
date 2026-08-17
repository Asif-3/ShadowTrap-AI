import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { attacksAPI } from '../api/client'
import { GlassCard, ThreatMeter, SentinelButton, LoadingSpinner, SectionHeader } from '../components/common'
import { motion } from 'framer-motion'
import { ArrowLeft, Play, Brain, Shield, Target, Crosshair, Zap, UserCheck, Terminal } from 'lucide-react'
import { getThreatColor, getStageColor } from '../lib/utils'

export default function AttackDetails() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [attack, setAttack] = useState(null)
  const [analysis, setAnalysis] = useState(null)
  const [loading, setLoading] = useState(true)
  const [analyzing, setAnalyzing] = useState(false)
  const [llmLoading, setLlmLoading] = useState(false)

  useEffect(() => {
    attacksAPI.getAttackById(id)
      .then(res => {
        const data = res.data.data
        setAttack(data)
        if (data?.ai_analysis) setAnalysis(data.ai_analysis)
      })
      .catch(console.error)
      .finally(() => setLoading(false))
  }, [id])

  // Poll for LLM / Copilot results when analysis is in progress
  useEffect(() => {
    let interval;
    let pollCount = 0;
    const maxPolls = 20; // 60 seconds max

    const isGenerating = llmLoading || (
      attack && (
        (attack.ai_analysis && attack.ai_analysis.status === 'generating') ||
        (attack.llm && attack.llm.attack_summary &&
          (attack.llm.attack_summary.includes('in progress') || attack.llm.attack_summary.includes('generating')))
      )
    );

    if (isGenerating) {
      interval = setInterval(() => {
        pollCount++;
        if (pollCount >= maxPolls) {
          setLlmLoading(false);
          clearInterval(interval);
          return;
        }
        attacksAPI.getAttackById(id)
          .then(res => {
            const updated = res.data.data;
            setAttack(updated);
            if (updated?.ai_analysis || (updated?.llm && !updated.llm.attack_summary?.includes('generating'))) {
              setAnalysis(updated?.ai_analysis || updated);
              setLlmLoading(false);
              clearInterval(interval);
            }
          })
          .catch(console.error);
      }, 3000);
    }
    return () => clearInterval(interval);
  }, [llmLoading, attack?.ai_analysis, attack?.llm?.attack_summary, id]);

  const runAnalysis = async () => {
    setAnalyzing(true)
    setLlmLoading(true)
    try {
      const res = await attacksAPI.analyzeAttack(id)
      if (res.data?.data?.ai_analysis) {
        setAnalysis(res.data.data.ai_analysis)
      }
      const updated = await attacksAPI.getAttackById(id)
      setAttack(updated.data.data)
      if (updated.data?.data?.ai_analysis) {
        setAnalysis(updated.data.data.ai_analysis)
        setLlmLoading(false)
      }
    } catch (err) {
      console.error(err)
      setLlmLoading(false)
    } finally {
      setAnalyzing(false)
    }
  }

  if (loading) return <LoadingSpinner size="lg" text="Loading attack dossier..." />
  if (!attack) return <p className="text-xs text-[#FF4D67]">Attack session not found</p>

  const persona = analysis?.persona || attack.persona || {}
  const stage = analysis?.stage || attack.attack_stage || {}
  const intent = analysis?.intent || attack.intent || {}
  const prediction = analysis?.prediction || attack.prediction || {}
  const llm = analysis?.llm || attack.llm || {}
  const mitre = analysis?.mitre || attack.mitre || {}

  const aiAnalysis = attack?.ai_analysis || analysis?.ai_analysis || (typeof analysis === 'object' && analysis?.threat_level ? analysis : null) || {}

  const hasQwenAnalysis = Boolean(
    aiAnalysis && (
      aiAnalysis.threat_level ||
      aiAnalysis.likely_next_move ||
      aiAnalysis.reasoning ||
      aiAnalysis.attacker_behavior ||
      aiAnalysis.recommended_action ||
      aiAnalysis.recommended_defensive_action ||
      aiAnalysis.observed_facts?.length > 0
    )
  )

  const hasLlmAnalysis = Boolean(
    llm && llm.attack_summary &&
    !llm.attack_summary.includes('in progress') &&
    !llm.attack_summary.includes('generating')
  )

  return (
    <div className="space-y-5">
      {/* Header Bar */}
      <div className="flex items-center justify-between flex-wrap gap-4 pb-4 border-b border-[rgba(0,245,160,0.14)]">
        <div className="flex items-center gap-3">
          <button 
            onClick={() => navigate(-1)} 
            className="p-2 rounded-lg hover:bg-[rgba(255,255,255,0.05)] text-[#9BB7AD] hover:text-[#E8FFF6] transition cursor-pointer border border-[rgba(0,245,160,0.14)]"
          >
            <ArrowLeft size={16} />
          </button>
          <div>
            <h1 className="text-xl font-bold flex items-center gap-2 text-[#E8FFF6] font-sans">
              Forensic Session <code className="text-[#00F5A0] font-mono text-base">{attack.session_id}</code>
            </h1>
            <p className="text-xs text-[#9BB7AD] mt-0.5 font-mono">
              IP: {attack.src_ip} • {attack.command_count} commands captured • {attack.duration?.toFixed(1)}s duration
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <SentinelButton onClick={runAnalysis} disabled={analyzing} size="sm">
            <Brain size={14} />
            {analyzing ? 'Analyzing...' : 'Run AI Analysis'}
          </SentinelButton>
          <SentinelButton 
            variant="secondary" 
            size="sm" 
            onClick={() => navigate(`/sentinel/replay/${attack.session_id}`)}
          >
            <Play size={14} /> Replay
          </SentinelButton>
        </div>
      </div>

      {/* Overview Cards Row */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <GlassCard className="text-center flex flex-col items-center justify-center p-4">
          <ThreatMeter score={attack.threat_score || 0} size={90} />
          <p className="text-xs text-[#9BB7AD] mt-2 font-medium font-sans">Threat Score</p>
        </GlassCard>

        <GlassCard className="p-4 flex flex-col justify-between">
          <div className="flex items-center gap-2">
            <Target size={15} className="text-[#00F5A0]" />
            <span className="text-xs font-medium text-[#9BB7AD]">Attack Stage</span>
          </div>
          <div>
            <p className="text-base font-bold font-sans" style={{ color: getStageColor(typeof attack.attack_stage === 'string' ? attack.attack_stage : stage.stage) }}>
              {(typeof attack.attack_stage === 'string' ? attack.attack_stage : stage.stage) || 'Pending Analysis'}
            </p>
            {stage.confidence && <p className="text-[11px] text-[#607A71] mt-0.5 font-mono">Confidence: {stage.confidence}%</p>}
          </div>
        </GlassCard>

        <GlassCard className="p-4 flex flex-col justify-between">
          <div className="flex items-center gap-2">
            <Crosshair size={15} className="text-[#FF4D67]" />
            <span className="text-xs font-medium text-[#9BB7AD]">Inferred Intent</span>
          </div>
          <div>
            <p className="text-base font-bold text-[#FF4D67] font-sans">
              {(typeof attack.intent === 'string' ? attack.intent : intent.intent) || 'Pending Analysis'}
            </p>
            {intent.confidence && <p className="text-[11px] text-[#607A71] mt-0.5 font-mono">Confidence: {intent.confidence}%</p>}
          </div>
        </GlassCard>

        <GlassCard className="p-4 flex flex-col justify-between">
          <div className="flex items-center gap-2">
            <Zap size={15} className="text-[#F5C451]" />
            <span className="text-xs font-medium text-[#9BB7AD]">Predicted Next Move</span>
          </div>
          <div>
            <p className="text-base font-bold text-[#F5C451] font-sans">
              {prediction.predicted_stage || aiAnalysis.likely_next_move || 'Pending'}
            </p>
            {prediction.confidence && <p className="text-[11px] text-[#607A71] mt-0.5 font-mono">Confidence: {prediction.confidence}%</p>}
          </div>
        </GlassCard>
      </div>

      {/* Persona + Captured Commands */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
        {/* Attacker Persona Card */}
        <GlassCard className="p-5">
          <SectionHeader title="Attacker Persona" />
          <div className="space-y-2.5">
            {[
              { label: 'Skill Level', value: persona.skill_level || '—' },
              { label: 'Attack Style', value: persona.attack_style || '—' },
              { label: 'Likely Goal', value: persona.likely_goal || '—' },
              { label: 'Risk Rating', value: persona.risk || '—' },
              { label: 'Threat Level', value: persona.threat_level ? `${persona.threat_level}/10` : '—' },
              { label: 'Confidence', value: persona.confidence ? `${persona.confidence}%` : '—' },
            ].map((item, i) => (
              <div key={i} className="flex justify-between items-center py-1.5 border-b border-[rgba(255,255,255,0.05)] text-xs">
                <span className="text-[#9BB7AD] font-sans">{item.label}</span>
                <span className="font-semibold text-[#E8FFF6] font-mono">{item.value}</span>
              </div>
            ))}
          </div>
          {persona.behavioral_traits?.length > 0 && (
            <div className="mt-4 pt-3 border-t border-[rgba(0,245,160,0.12)]">
              <p className="text-xs font-semibold text-[#9BB7AD] mb-2 font-sans">Behavioral Traits</p>
              {persona.behavioral_traits.map((t, i) => (
                <p key={i} className="text-[11px] py-0.5 text-[#E8FFF6] font-mono">• {t}</p>
              ))}
            </div>
          )}
        </GlassCard>

        {/* Command Timeline Card */}
        <GlassCard className="lg:col-span-2 p-5">
          <SectionHeader title="Captured Command Stream" badge={`${attack.commands?.length || 0} cmds`} />
          <div className="terminal-card p-4 max-h-80 overflow-y-auto space-y-1.5 font-mono text-xs">
            {attack.commands?.map((cmd, i) => (
              <motion.div
                key={i}
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: i * 0.02 }}
                className="flex items-center justify-between py-1 border-b border-[rgba(255,255,255,0.04)]"
              >
                <div className="flex items-center gap-2">
                  <span className="text-[#00F5A0] font-bold select-none">$</span>
                  <span className="text-[#E8FFF6]">{cmd}</span>
                </div>
                {attack.timestamps?.[i] && (
                  <span className="text-[10px] text-[#607A71] ml-3 shrink-0">
                    {attack.timestamps[i]?.slice(11, 19)}
                  </span>
                )}
              </motion.div>
            ))}
          </div>
        </GlassCard>
      </div>

      {/* MITRE Mapping + AI Threat Analysis */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
        {/* MITRE Mapping */}
        {mitre.techniques?.length > 0 && (
          <GlassCard className="p-5">
            <SectionHeader 
              title="MITRE ATT&CK Mapping" 
              badge={`${mitre.coverage_score || 0}% coverage`} 
            />
            <div className="space-y-2 max-h-80 overflow-y-auto">
              {mitre.techniques.map((t, i) => (
                <div 
                  key={i} 
                  className="flex items-center gap-3 p-3 rounded-lg border"
                  style={{
                    backgroundColor: '#08110F',
                    borderColor: 'rgba(0, 245, 160, 0.14)',
                  }}
                >
                  <code className="text-xs font-bold text-[#00F5A0] font-mono px-2 py-0.5 rounded bg-[rgba(0,245,160,0.1)]">
                    {t.id}
                  </code>
                  <div>
                    <p className="text-xs font-semibold text-[#E8FFF6] font-sans">{t.name}</p>
                    <p className="text-[10px] text-[#9BB7AD] font-sans">{t.tactic}</p>
                  </div>
                </div>
              ))}
            </div>
          </GlassCard>
        )}

        {/* AI Threat Analysis Panel */}
        <GlassCard className={`p-5 ${!mitre.techniques?.length ? 'lg:col-span-2' : ''}`}>
          <div className="flex items-center justify-between mb-4">
            <SectionHeader title="AI Threat Analysis" className="mb-0" />
            {llmLoading && (
              <span className="text-[10px] font-mono font-semibold px-2 py-0.5 rounded bg-[rgba(0,245,160,0.1)] text-[#00F5A0] animate-pulse">
                Generating...
              </span>
            )}
          </div>

          {llmLoading && !hasQwenAnalysis && !hasLlmAnalysis ? (
            <div className="flex flex-col items-center justify-center py-10 space-y-3">
              <LoadingSpinner size="md" text="Qwen AI Copilot is synthesizing threat intelligence..." />
            </div>
          ) : hasQwenAnalysis ? (
            <div className="space-y-4 max-h-96 overflow-y-auto pr-1">
              {/* Badges Bar */}
              <div className="flex flex-wrap items-center gap-2 pb-3 border-b border-[rgba(0,245,160,0.12)] text-xs">
                {aiAnalysis.threat_level && (
                  <span className={`px-2 py-0.5 rounded font-mono font-bold text-[10px] ${
                    aiAnalysis.threat_level === 'CRITICAL' ? 'bg-red-500/20 text-[#FF4D67] border border-red-500/30' :
                    aiAnalysis.threat_level === 'HIGH' ? 'bg-orange-500/20 text-[#FF7043] border border-orange-500/30' :
                    aiAnalysis.threat_level === 'MEDIUM' ? 'bg-yellow-500/20 text-[#F5C451] border border-yellow-500/30' :
                    'bg-blue-500/20 text-[#4DB8FF] border border-blue-500/30'
                  }`}>
                    {aiAnalysis.threat_level}
                  </span>
                )}
                {typeof aiAnalysis.risk_score === 'number' && (
                  <span className="px-2 py-0.5 rounded bg-[#08110F] text-[#9BB7AD] font-mono text-[10px] border border-[rgba(255,255,255,0.06)]">
                    Risk: {aiAnalysis.risk_score}/100
                  </span>
                )}
                {typeof aiAnalysis.confidence === 'number' && (
                  <span className="px-2 py-0.5 rounded bg-[#08110F] text-[#9BB7AD] font-mono text-[10px] border border-[rgba(255,255,255,0.06)]">
                    Conf: {Math.round(aiAnalysis.confidence > 1 ? aiAnalysis.confidence : aiAnalysis.confidence * 100)}%
                  </span>
                )}
                <span className="px-2 py-0.5 rounded bg-[rgba(0,245,160,0.1)] text-[#00F5A0] font-sans font-medium text-[10px] ml-auto">
                  {aiAnalysis.source === 'qwen_llm' ? '🤖 Qwen3-0.6B Local AI' : 'Deterministic Analysis'}
                </span>
              </div>

              {/* Attacker Behavior */}
              {aiAnalysis.attacker_behavior && (
                <div>
                  <p className="text-xs font-semibold text-[#00F5A0] mb-1 font-sans">Attacker Behavior</p>
                  <p className="text-xs text-[#9BB7AD] leading-relaxed font-sans">{aiAnalysis.attacker_behavior}</p>
                </div>
              )}

              {/* Likely Next Move */}
              {aiAnalysis.likely_next_move && (
                <div className="p-3 rounded-lg bg-[rgba(245,196,81,0.08)] border border-[rgba(245,196,81,0.25)]">
                  <p className="text-xs font-semibold text-[#F5C451] mb-1 flex items-center gap-1.5 font-sans">
                    <Zap size={13} /> Likely Next Move
                  </p>
                  <p className="text-xs font-medium text-[#E8FFF6] font-sans">{aiAnalysis.likely_next_move}</p>
                </div>
              )}

              {/* Recommended Defensive Action */}
              {(aiAnalysis.recommended_action || aiAnalysis.recommended_defensive_action) && (
                <div className="p-3 rounded-lg bg-[rgba(32,230,122,0.08)] border border-[rgba(32,230,122,0.25)]">
                  <p className="text-xs font-semibold text-[#20E67A] mb-1 flex items-center gap-1.5 font-sans">
                    <Shield size={13} /> Recommended Defensive Action
                  </p>
                  <p className="text-xs text-[#E8FFF6] leading-relaxed font-sans">
                    {aiAnalysis.recommended_action || aiAnalysis.recommended_defensive_action}
                  </p>
                </div>
              )}
            </div>
          ) : hasLlmAnalysis ? (
            <div className="space-y-3.5 max-h-80 overflow-y-auto">
              {[
                { title: 'Incident Summary', content: llm.attack_summary, color: '#00F5A0' },
                { title: 'Risk Analysis', content: llm.risk_analysis, color: '#FF4D67' },
                { title: 'Behavior Explanation', content: llm.behavior_explanation, color: '#4DB8FF' },
                { title: 'Threat Intelligence', content: llm.threat_explanation, color: '#F5C451' },
                { title: 'Recommendations', content: llm.recommendations, color: '#20E67A' },
              ].map((section, i) => section.content && (
                <div key={i}>
                  <p className="text-xs font-semibold mb-0.5 font-sans" style={{ color: section.color }}>{section.title}</p>
                  <p className="text-xs leading-relaxed text-[#9BB7AD] font-sans">{section.content}</p>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-8">
              <p className="text-xs text-[#607A71] font-sans">Click "Run AI Analysis" to generate threat intelligence</p>
            </div>
          )}
        </GlassCard>
      </div>
    </div>
  )
}
