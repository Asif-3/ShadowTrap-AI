import { useState, useEffect, useRef } from 'react'
import { llmAPI, attacksAPI } from '../api/client'
import { GlassCard, SentinelButton, PageHeader } from '../components/common'
import { Terminal, Send, Bot, User, AlertTriangle, RefreshCw, ChevronDown, Sparkles } from 'lucide-react'

const SUGGESTIONS = [
  'Summarize the latest attack',
  'What MITRE techniques were used?',
  'Recommend incident response containment steps',
  'Extract all IOCs and malicious IPs',
]

export default function SecurityCopilotPage() {
  const [messages, setMessages] = useState([
    {
      sender: 'bot',
      text: 'Hello, SOC Analyst. I am your AI Cyber Security Copilot powered by Qwen3-0.6B (Local llama.cpp). Ask me to analyze honeypot attacks, summarize command logs, or recommend incident response steps based on real telemetry.\n\nTry clicking one of the suggested prompts below or ask your own question.'
    }
  ])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [sessions, setSessions] = useState([])
  const [selectedSession, setSelectedSession] = useState('')
  const [showSessionPicker, setShowSessionPicker] = useState(false)
  const [retryData, setRetryData] = useState(null)
  const chatEndRef = useRef(null)

  // Load available attack sessions
  useEffect(() => {
    attacksAPI.getRecent(20)
      .then(res => {
        const data = res.data?.data || []
        setSessions(Array.isArray(data) ? data : [])
      })
      .catch(() => setSessions([]))
  }, [])

  // Auto-scroll to bottom of chat
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const handleSend = async (overrideText = null) => {
    const userText = (overrideText || input).trim()
    if (!userText || loading) return

    const userMsg = { sender: 'user', text: userText }
    setMessages((prev) => [...prev, userMsg])
    setInput('')
    setLoading(true)
    setRetryData(null)

    try {
      const res = await llmAPI.explain(userText, selectedSession || null)
      const data = res.data?.data || {}

      let botText = ''
      if (typeof data === 'string') {
        botText = data
      } else if (data.explanation) {
        botText = data.explanation
      } else if (data.attack_summary || data.risk_analysis) {
        const parts = [
          data.attack_summary && `**Summary:** ${data.attack_summary}`,
          data.risk_analysis && `**Risk:** ${data.risk_analysis}`,
          data.behavior_explanation && `**Behavior:** ${data.behavior_explanation}`,
          data.recommendations && `**Recommendations:** ${data.recommendations}`,
          data.future_risk && `**Future Risk:** ${data.future_risk}`,
        ].filter(Boolean)
        botText = parts.join('\n\n')
      }

      if (!botText) {
        botText = 'The AI model returned an empty response. This may happen if the model is still loading. Please try again in a moment.'
        setRetryData(userText)
      }

      const isFallback = data.is_fallback === true
      setMessages((prev) => [...prev, {
        sender: 'bot',
        text: botText,
        isFallback,
      }])
    } catch (err) {
      console.error('Copilot error:', err)
      const errorMsg = err.response?.data?.error || err.message || 'Unknown error'
      setRetryData(userText)
      setMessages((prev) => [
        ...prev,
        {
          sender: 'bot',
          text: `⚠️ AI request failed: ${errorMsg}\n\nThe model may be loading or temporarily unavailable. Click retry or try again shortly.`,
          isError: true,
        }
      ])
    } finally {
      setLoading(false)
    }
  }

  const handleRetry = () => {
    if (retryData) {
      handleSend(retryData)
    }
  }

  return (
    <div className="space-y-5">
      {/* Page Header */}
      <PageHeader
        icon={Terminal}
        title="AI Security Copilot"
        badge="QWEN-0.6B"
        subtitle="Local LLM-powered incident investigation, threat explanation, and defense recommendations"
        actions={
          <div className="flex items-center gap-2">
            {/* Session Selector */}
            <div className="relative">
              <button
                onClick={() => setShowSessionPicker(!showSessionPicker)}
                className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-[#0B1412] border border-[rgba(0,245,160,0.2)] text-xs text-[#9BB7AD] hover:border-[#00F5A0] transition cursor-pointer"
              >
                <Sparkles size={13} className="text-[#00F5A0]" />
                <span className="font-mono">
                  {selectedSession ? `Session: ${selectedSession.slice(0, 12)}` : 'Auto (Latest Session)'}
                </span>
                <ChevronDown size={13} />
              </button>

              {showSessionPicker && (
                <div className="absolute top-full right-0 mt-1 w-64 max-h-56 overflow-y-auto rounded-lg bg-[#0B1412] border border-[rgba(0,245,160,0.25)] shadow-xl z-50 p-1">
                  <button
                    onClick={() => { setSelectedSession(''); setShowSessionPicker(false) }}
                    className="w-full text-left px-3 py-2 text-xs rounded hover:bg-[rgba(255,255,255,0.05)] text-[#00F5A0] font-sans font-medium transition cursor-pointer"
                  >
                    Auto (Latest Session)
                  </button>
                  {sessions.map((s) => (
                    <button
                      key={s.session_id}
                      onClick={() => { setSelectedSession(s.session_id); setShowSessionPicker(false) }}
                      className="w-full text-left px-3 py-2 text-xs rounded hover:bg-[rgba(255,255,255,0.05)] text-[#E8FFF6] border-t border-[rgba(255,255,255,0.04)] transition cursor-pointer"
                    >
                      <span className="font-mono text-[#00F5A0] text-[11px] block">{s.session_id}</span>
                      <span className="text-[10px] text-[#607A71] block font-mono">{s.src_ip} • Score: {s.threat_score || '—'}</span>
                    </button>
                  ))}
                </div>
              )}
            </div>

            {retryData && (
              <SentinelButton onClick={handleRetry} variant="secondary" size="sm">
                <RefreshCw size={12} /> Retry
              </SentinelButton>
            )}
          </div>
        }
      />

      {/* Chat Container */}
      <GlassCard className="h-[600px] flex flex-col justify-between p-4 sm:p-5">
        {/* Chat Message Stream */}
        <div className="flex-1 overflow-y-auto space-y-4 pr-1">
          {messages.map((m, i) => (
            <div
              key={i}
              className={`flex gap-3 text-xs ${m.sender === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              {m.sender === 'bot' && (
                <div className={`w-7 h-7 rounded-lg flex items-center justify-center shrink-0 border ${
                  m.isError
                    ? 'bg-[rgba(255,77,103,0.12)] text-[#FF4D67] border-[rgba(255,77,103,0.3)]'
                    : m.isFallback
                    ? 'bg-[rgba(245,196,81,0.12)] text-[#F5C451] border-[rgba(245,196,81,0.3)]'
                    : 'bg-[rgba(0,245,160,0.12)] text-[#00F5A0] border-[rgba(0,245,160,0.25)]'
                }`}>
                  {m.isError ? <AlertTriangle size={15} /> : <Bot size={15} />}
                </div>
              )}

              <div
                className={`max-w-[85%] sm:max-w-[75%] p-3.5 rounded-lg whitespace-pre-line leading-relaxed font-sans text-xs ${
                  m.sender === 'user'
                    ? 'bg-[#00F5A0] text-[#050908] font-semibold'
                    : m.isError
                    ? 'bg-[rgba(255,77,103,0.08)] border border-[rgba(255,77,103,0.3)] text-[#E8FFF6]'
                    : m.isFallback
                    ? 'bg-[rgba(245,196,81,0.08)] border border-[rgba(245,196,81,0.3)] text-[#E8FFF6]'
                    : 'bg-[#08110F] border border-[rgba(0,245,160,0.14)] text-[#E8FFF6]'
                }`}
              >
                {m.text}
                {m.isFallback && (
                  <p className="text-[10px] mt-2 text-[#F5C451] font-mono">⚡ Rule-based analysis (local AI model offline)</p>
                )}
              </div>

              {m.sender === 'user' && (
                <div className="w-7 h-7 rounded-lg bg-[#0F1A17] text-[#00F5A0] border border-[rgba(0,245,160,0.2)] flex items-center justify-center shrink-0">
                  <User size={15} />
                </div>
              )}
            </div>
          ))}

          {loading && (
            <div className="flex gap-3 items-center text-xs text-[#9BB7AD]">
              <div className="w-7 h-7 rounded-lg bg-[rgba(0,245,160,0.12)] text-[#00F5A0] flex items-center justify-center shrink-0 border border-[rgba(0,245,160,0.2)]">
                <Bot size={15} className="animate-pulse" />
              </div>
              <div className="flex items-center gap-2 font-mono text-[11px]">
                <span className="w-1.5 h-1.5 rounded-full bg-[#00F5A0] animate-pulse" />
                <span>Qwen3-0.6B is analyzing threat telemetry...</span>
              </div>
            </div>
          )}

          <div ref={chatEndRef} />
        </div>

        {/* Prompt Suggestions */}
        <div className="pt-3 pb-2 flex flex-wrap gap-1.5 border-t border-[rgba(0,245,160,0.1)]">
          {SUGGESTIONS.map((s, idx) => (
            <button
              key={idx}
              onClick={() => handleSend(s)}
              disabled={loading}
              className="text-[11px] px-2.5 py-1 rounded bg-[#08110F] text-[#9BB7AD] hover:text-[#00F5A0] border border-[rgba(255,255,255,0.06)] hover:border-[rgba(0,245,160,0.25)] transition cursor-pointer font-sans"
            >
              {s}
            </button>
          ))}
        </div>

        {/* Input Composer */}
        <div className="pt-2 flex items-center gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSend()}
            placeholder="Ask Copilot to explain an attack, summarize threat indicators, or recommend IR steps..."
            className="st-input text-xs"
          />
          <SentinelButton onClick={() => handleSend()} disabled={loading} size="md">
            <Send size={13} />
          </SentinelButton>
        </div>
      </GlassCard>
    </div>
  )
}
