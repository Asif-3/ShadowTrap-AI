import { useState, useEffect } from 'react'
import { reportsAPI, attacksAPI } from '../api/client'
import { GlassCard, SentinelButton, LoadingSpinner, StatusBadge, PageHeader, SectionHeader, EmptyState } from '../components/common'
import {
  FileText,
  Download,
  FileCode,
  CheckCircle2,
  RefreshCw,
  Send,
  AlertCircle,
  Shield,
  FileCheck,
  Terminal,
  Sparkles,
  ChevronDown,
  Check,
} from 'lucide-react'

export default function ReportsPage() {
  const [attacks, setAttacks] = useState([])
  const [selectedSession, setSelectedSession] = useState('')
  const [format, setFormat] = useState('pdf')
  const [sendTelegram, setSendTelegram] = useState(false)
  const [loading, setLoading] = useState(true)
  const [generating, setGenerating] = useState(false)
  const [lastDownloadedFile, setLastDownloadedFile] = useState(null)
  const [notification, setNotification] = useState(null)

  const showNotification = (msg, type = 'success') => {
    setNotification({ msg, type })
    setTimeout(() => setNotification(null), 4500)
  }

  // Load all available sessions
  const loadData = () => {
    setLoading(true)
    attacksAPI
      .getAttacks({ per_page: 50 })
      .then((atkRes) => {
        const atkList = atkRes?.data?.data?.items || atkRes?.data?.data || []
        setAttacks(atkList)
        if (atkList.length > 0) {
          const currentValid = atkList.some((a) => a.session_id === selectedSession)
          if (!selectedSession || !currentValid) {
            setSelectedSession(atkList[0].session_id)
          }
        }
      })
      .catch((err) => {
        console.error('Failed to load attacks:', err)
        showNotification('Failed to fetch attack sessions', 'error')
      })
      .finally(() => setLoading(false))
  }

  useEffect(() => {
    loadData()
  }, [])

  // Download Trigger
  const triggerBrowserFileDownload = (blobData, fileName, mimeType) => {
    const blob = blobData instanceof Blob ? blobData : new Blob([blobData], { type: mimeType })
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.style.display = 'none'
    a.href = url
    a.download = fileName
    document.body.appendChild(a)
    a.click()
    setTimeout(() => {
      if (a.parentNode) a.parentNode.removeChild(a)
      setTimeout(() => window.URL.revokeObjectURL(url), 60000)
    }, 1000)
  }

  const handleGenerateAndDownload = async () => {
    if (!selectedSession) {
      showNotification('Please select a target attack session first.', 'error')
      return
    }

    setGenerating(true)
    try {
      // 1. Generate Report on Backend
      const genRes = await reportsAPI.generateReport({
        session_id: selectedSession,
        format,
        send_telegram: sendTelegram,
      })

      const newReport = genRes?.data?.data
      const repId = newReport?._id || newReport?.filename || selectedSession
      const fileName = newReport?.filename || `ShadowTrap_Report_${selectedSession}.${format}`

      // 2. Direct Browser Download
      try {
        const dlRes = await reportsAPI.downloadReport(repId)
        if (dlRes.data && dlRes.data.type === 'application/json') {
          const errText = await dlRes.data.text()
          let errJson = {}
          try {
            errJson = JSON.parse(errText)
          } catch (e) {}
          throw new Error(errJson.error || 'Server error downloading report file.')
        }

        const mimeMap = { pdf: 'application/pdf', html: 'text/html', json: 'application/json' }
        const contentType =
          dlRes.headers?.['content-type'] || mimeMap[format] || 'application/octet-stream'
        triggerBrowserFileDownload(dlRes.data, fileName, contentType)

        setLastDownloadedFile({
          filename: fileName,
          format: format.toUpperCase(),
          sessionId: selectedSession,
          timestamp: new Date().toLocaleTimeString(),
        })

        showNotification(
          `Report compiled and downloaded successfully${sendTelegram ? ' & dispatched to Telegram' : ''}!`,
          'success'
        )
      } catch (dlErr) {
        console.warn('Blob download fallback triggered:', dlErr)
        const token = localStorage.getItem('shadowtrap_token')
        const directUrl = `/api/reports/download/${repId}?token=${encodeURIComponent(token || '')}`
        const a = document.createElement('a')
        a.style.display = 'none'
        a.href = directUrl
        a.download = fileName
        document.body.appendChild(a)
        a.click()
        setTimeout(() => {
          if (a.parentNode) a.parentNode.removeChild(a)
        }, 1500)

        setLastDownloadedFile({
          filename: fileName,
          format: format.toUpperCase(),
          sessionId: selectedSession,
          timestamp: new Date().toLocaleTimeString(),
        })

        showNotification('Report compiled! Direct browser download initiated.', 'success')
      }
    } catch (err) {
      console.error('Report generation failed:', err)
      showNotification(err.response?.data?.error || 'Failed to generate incident report.', 'error')
    } finally {
      setGenerating(false)
    }
  }

  if (loading) return <LoadingSpinner size="lg" text="Loading report engine..." />

  const hasAttacks = attacks.length > 0
  const currentSessionData = attacks.find((a) => a.session_id === selectedSession)

  const formatOptions = [
    {
      id: 'pdf',
      name: 'PDF Dossier',
      badge: 'FORENSIC PDF',
      description: 'Multi-page formal SOC dossier for stakeholders and compliance.',
      icon: FileText,
    },
    {
      id: 'html',
      name: 'HTML Interactive',
      badge: 'INTERACTIVE',
      description: 'Self-contained SOC dashboard with sticky navigation & filters.',
      icon: FileCheck,
    },
    {
      id: 'json',
      name: 'Raw JSON',
      badge: 'SIEM EXPORT',
      description: 'Standardized 22-section canonical forensic schema for SIEM.',
      icon: FileCode,
    },
  ]

  const getButtonLabel = () => {
    if (generating) return 'Compiling Report...'
    if (format === 'pdf') return 'Generate PDF Report'
    if (format === 'html') return 'Generate HTML Report'
    if (format === 'json') return 'Export JSON'
    return 'Generate Report'
  }

  return (
    <div className="space-y-6">
      {/* Toast Notification */}
      {notification && (
        <div
          className={`p-3.5 rounded-lg border flex items-center justify-between text-xs font-medium shadow-md ${
            notification.type === 'success'
              ? 'bg-[rgba(32,230,122,0.1)] border-[rgba(32,230,122,0.3)] text-[#20E67A]'
              : 'bg-[rgba(255,77,103,0.1)] border-[rgba(255,77,103,0.3)] text-[#FF4D67]'
          }`}
        >
          <div className="flex items-center gap-2">
            {notification.type === 'success' ? <CheckCircle2 size={15} /> : <AlertCircle size={15} />}
            <span>{notification.msg}</span>
          </div>
          <button
            onClick={() => setNotification(null)}
            className="text-xs opacity-70 hover:opacity-100 cursor-pointer px-1"
          >
            ✕
          </button>
        </div>
      )}

      {/* Page Header */}
      <PageHeader
        icon={FileText}
        title="Incident Investigation Reports"
        subtitle="Generate and export forensic investigation reports for SIEM, SOC, and compliance"
        actions={
          <SentinelButton onClick={loadData} variant="secondary" size="sm">
            <RefreshCw size={13} className={loading ? 'animate-spin' : ''} />
            <span>Refresh</span>
          </SentinelButton>
        }
      />

      {!hasAttacks ? (
        <GlassCard className="p-8">
          <EmptyState preset="reports" />
        </GlassCard>
      ) : (
        <>
          {/* SECTION 01: ATTACK SESSION SELECTION */}
          <GlassCard className="p-5 space-y-4">
            <div className="flex items-center gap-2">
              <span className="text-xs font-bold font-mono text-[#00F5A0]">01</span>
              <SectionHeader title="Select Attack Session" className="mb-0" />
            </div>

            <div className="space-y-3">
              <div>
                <select
                  value={selectedSession}
                  onChange={(e) => setSelectedSession(e.target.value)}
                  className="st-input font-mono text-xs sm:text-sm"
                >
                  {attacks.map((a) => (
                    <option key={a.session_id} value={a.session_id}>
                      {a.session_id} — {a.src_ip} ({a.attack_stage || 'Discovery'})
                    </option>
                  ))}
                </select>
              </div>

              {/* Information Meta Blocks */}
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 pt-1">
                <div className="p-3 rounded-lg bg-[#08110F] border border-[rgba(0,245,160,0.12)]">
                  <span className="text-[10px] font-semibold uppercase text-[#607A71] block font-mono">
                    Source IP
                  </span>
                  <span className="text-sm font-bold font-mono text-[#E8FFF6] mt-0.5 block truncate">
                    {currentSessionData?.src_ip || '127.0.0.1'}
                  </span>
                </div>

                <div className="p-3 rounded-lg bg-[#08110F] border border-[rgba(0,245,160,0.12)]">
                  <span className="text-[10px] font-semibold uppercase text-[#607A71] block font-mono">
                    Threat Level
                  </span>
                  <div className="mt-1">
                    <StatusBadge
                      status={
                        currentSessionData?.threat_level ||
                        currentSessionData?.attack_stage ||
                        'medium'
                      }
                    />
                  </div>
                </div>

                <div className="p-3 rounded-lg bg-[#08110F] border border-[rgba(0,245,160,0.12)]">
                  <span className="text-[10px] font-semibold uppercase text-[#607A71] block font-mono">
                    Attack Stage
                  </span>
                  <span className="text-xs font-semibold text-[#9BB7AD] mt-1 flex items-center gap-1.5 font-sans">
                    <span className="live-dot-sm" />
                    {currentSessionData?.attack_stage || 'Discovery'}
                  </span>
                </div>
              </div>
            </div>
          </GlassCard>

          {/* SECTION 02: EXPORT FORMAT SELECTION */}
          <div className="space-y-3">
            <div className="flex items-center gap-2">
              <span className="text-xs font-bold font-mono text-[#00F5A0]">02</span>
              <SectionHeader title="Choose Export Format" className="mb-0" />
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
              {formatOptions.map((opt) => {
                const Icon = opt.icon
                const isSelected = format === opt.id
                return (
                  <button
                    key={opt.id}
                    type="button"
                    onClick={() => setFormat(opt.id)}
                    className={`p-4 rounded-lg text-left transition-all cursor-pointer flex flex-col justify-between min-h-[140px] border ${
                      isSelected
                        ? 'bg-[rgba(0,245,160,0.06)] border-[#00F5A0] shadow-sm'
                        : 'bg-[#0B1412] border-[rgba(0,245,160,0.12)] hover:border-[rgba(0,245,160,0.25)]'
                    }`}
                  >
                    <div className="flex items-start justify-between w-full mb-2">
                      <div
                        className={`w-8 h-8 rounded-lg flex items-center justify-center border ${
                          isSelected
                            ? 'bg-[rgba(0,245,160,0.14)] border-[#00F5A0] text-[#00F5A0]'
                            : 'bg-[#08110F] border-[rgba(0,245,160,0.12)] text-[#9BB7AD]'
                        }`}
                      >
                        <Icon size={16} />
                      </div>

                      <span
                        className={`text-[9px] font-semibold uppercase px-2 py-0.5 rounded font-mono ${
                          isSelected
                            ? 'bg-[rgba(0,245,160,0.14)] text-[#00F5A0]'
                            : 'bg-[#08110F] text-[#607A71]'
                        }`}
                      >
                        {opt.badge}
                      </span>
                    </div>

                    <div className="space-y-1">
                      <h3
                        className={`text-sm font-bold font-sans ${
                          isSelected ? 'text-[#00F5A0]' : 'text-[#E8FFF6]'
                        }`}
                      >
                        {opt.name}
                      </h3>
                      <p className="text-xs text-[#607A71] leading-relaxed font-sans">
                        {opt.description}
                      </p>
                    </div>
                  </button>
                )
              })}
            </div>
          </div>

          {/* SECTION 03: REPORT CONTENT INCLUDED */}
          <div className="space-y-3">
            <div className="flex items-center gap-2">
              <span className="text-xs font-bold font-mono text-[#00F5A0]">03</span>
              <SectionHeader title="Forensic Sections Included" className="mb-0" />
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
              <div className="p-4 rounded-lg bg-[#0B1412] border border-[rgba(0,245,160,0.12)] flex flex-col justify-between min-h-[120px]">
                <div className="flex items-center justify-between mb-1">
                  <Shield size={16} className="text-[#00F5A0]" />
                  <span className="text-[10px] font-mono text-[#20E67A] flex items-center gap-1">
                    <Check size={11} /> 22 Sections
                  </span>
                </div>
                <div>
                  <h4 className="text-xs font-bold text-[#E8FFF6] font-sans">MITRE ATT&CK Matrix</h4>
                  <p className="text-[11px] text-[#607A71] mt-0.5">Tactics, techniques, and mapped behavioral confidence.</p>
                </div>
              </div>

              <div className="p-4 rounded-lg bg-[#0B1412] border border-[rgba(0,245,160,0.12)] flex flex-col justify-between min-h-[120px]">
                <div className="flex items-center justify-between mb-1">
                  <Terminal size={16} className="text-[#00F5A0]" />
                  <span className="text-[10px] font-mono text-[#20E67A] flex items-center gap-1">
                    <Check size={11} /> Captured
                  </span>
                </div>
                <div>
                  <h4 className="text-xs font-bold text-[#E8FFF6] font-sans">Command Chronology</h4>
                  <p className="text-[11px] text-[#607A71] mt-0.5">Complete command sequence, timestamps, and sandbox outputs.</p>
                </div>
              </div>

              <div className="p-4 rounded-lg bg-[#0B1412] border border-[rgba(0,245,160,0.12)] flex flex-col justify-between min-h-[120px]">
                <div className="flex items-center justify-between mb-1">
                  <Sparkles size={16} className="text-[#00F5A0]" />
                  <span className="text-[10px] font-mono text-[#20E67A] flex items-center gap-1">
                    <Check size={11} /> AI Powered
                  </span>
                </div>
                <div>
                  <h4 className="text-xs font-bold text-[#E8FFF6] font-sans">AI Threat & Persona Analysis</h4>
                  <p className="text-[11px] text-[#607A71] mt-0.5">Automated threat reasoning, actor persona, and response steps.</p>
                </div>
              </div>
            </div>
          </div>

          {/* SECTION 04: ACTION FOOTER */}
          <GlassCard className="p-5">
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
              {/* Telegram Switch */}
              <div
                onClick={() => setSendTelegram(!sendTelegram)}
                className="flex items-center gap-3 cursor-pointer select-none"
              >
                <div
                  className={`w-9 h-5 rounded-full p-0.5 transition-colors border flex items-center ${
                    sendTelegram
                      ? 'bg-[rgba(0,245,160,0.2)] border-[#00F5A0] justify-end'
                      : 'bg-[#08110F] border-[rgba(255,255,255,0.1)] justify-start'
                  }`}
                >
                  <div
                    className={`w-3.5 h-3.5 rounded-full transition-transform ${
                      sendTelegram ? 'bg-[#00F5A0]' : 'bg-[#607A71]'
                    }`}
                  />
                </div>

                <div className="flex items-center gap-2">
                  <Send size={14} className={sendTelegram ? 'text-[#00F5A0]' : 'text-[#607A71]'} />
                  <div>
                    <span className="text-xs font-semibold text-[#E8FFF6] block">
                      Send report to Telegram
                    </span>
                    <span className="text-[10px] text-[#607A71] block">
                      Forward generated dossier to configured SOC Telegram channel
                    </span>
                  </div>
                </div>
              </div>

              {/* Generate Button */}
              <SentinelButton
                onClick={handleGenerateAndDownload}
                disabled={generating || !selectedSession}
                size="md"
                className="w-full sm:w-auto"
              >
                {generating ? <RefreshCw size={14} className="animate-spin" /> : <Download size={14} />}
                <span>{getButtonLabel()}</span>
              </SentinelButton>
            </div>

            {/* Download Status */}
            {lastDownloadedFile && (
              <div className="mt-3.5 pt-3.5 border-t border-[rgba(0,245,160,0.12)] flex items-center justify-between text-xs text-[#20E67A]">
                <div className="flex items-center gap-2 font-mono truncate">
                  <CheckCircle2 size={14} className="shrink-0" />
                  <span className="truncate">
                    Generated: <strong>{lastDownloadedFile.filename}</strong> at {lastDownloadedFile.timestamp}
                  </span>
                </div>
                <span className="text-[10px] font-bold uppercase px-2 py-0.5 rounded bg-[rgba(32,230,122,0.1)] border border-[rgba(32,230,122,0.3)] font-mono">
                  {lastDownloadedFile.format} READY
                </span>
              </div>
            )}
          </GlassCard>
        </>
      )}
    </div>
  )
}
