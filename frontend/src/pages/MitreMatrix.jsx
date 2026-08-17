import { useState, useEffect } from 'react'
import { GlassCard, LoadingSpinner, EmptyState, PageHeader, SectionHeader } from '../components/common'
import { Cpu, Info, ShieldCheck } from 'lucide-react'
import { analyticsAPI } from '../api/client'

export default function MitreMatrixPage() {
  const [mitreData, setMitreData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [selectedTech, setSelectedTech] = useState(null)

  useEffect(() => {
    analyticsAPI.getStats()
      .then((res) => {
        const data = res.data.data
        const stageMap = {}
        if (data?.stage_distribution) {
          data.stage_distribution.forEach(item => {
            stageMap[item.stage] = item.count
          })
        }
        setMitreData(stageMap)
      })
      .catch(console.error)
      .finally(() => setLoading(false))
  }, [])

  if (loading) return <LoadingSpinner size="lg" text="Mapping MITRE ATT&CK telemetry..." />

  const TACTICS = [
    { name: 'Reconnaissance', key: 'Reconnaissance' },
    { name: 'Initial Access', key: 'Initial Access' },
    { name: 'Execution', key: 'Execution' },
    { name: 'Persistence', key: 'Persistence' },
    { name: 'Privilege Escalation', key: 'Privilege Escalation' },
    { name: 'Defense Evasion', key: 'Defense Evasion' },
    { name: 'Credential Access', key: 'Credential Discovery' },
    { name: 'Discovery', key: 'Discovery' },
    { name: 'Command & Control', key: 'Command And Control' },
    { name: 'Exfiltration', key: 'Exfiltration' },
  ]

  const TECHNIQUE_MAP = {
    'Reconnaissance': [{ id: 'T1595', name: 'Active Scanning' }],
    'Initial Access': [{ id: 'T1078', name: 'Valid Accounts' }],
    'Execution': [{ id: 'T1059', name: 'Command & Scripting Interpreter' }],
    'Persistence': [{ id: 'T1053', name: 'Scheduled Task/Job' }],
    'Privilege Escalation': [{ id: 'T1548', name: 'Abuse Elevation Control' }],
    'Defense Evasion': [{ id: 'T1070', name: 'Indicator Removal' }],
    'Credential Access': [{ id: 'T1003', name: 'OS Credential Dumping' }],
    'Discovery': [{ id: 'T1033', name: 'System Owner Discovery' }, { id: 'T1049', name: 'System Network Discovery' }],
    'Command & Control': [{ id: 'T1105', name: 'Ingress Tool Transfer' }],
    'Exfiltration': [{ id: 'T1041', name: 'Exfiltration Over C2' }],
  }

  const totalDetections = Object.values(mitreData || {}).reduce((a, b) => a + b, 0)

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <PageHeader
        icon={Cpu}
        title="MITRE ATT&CK Matrix"
        badge={`${totalDetections} detections`}
        subtitle="Tactics, Techniques, and Procedures (TTPs) mapped automatically to real-time honeypot captures"
      />

      {totalDetections === 0 ? (
        <GlassCard className="p-8">
          <EmptyState preset="mitre" />
        </GlassCard>
      ) : (
        <>
          {/* Horizontal Scrolling Matrix Grid */}
          <div className="overflow-x-auto pb-2">
            <div className="flex gap-2.5 min-w-[1100px]">
              {TACTICS.map((tactic) => {
                const count = mitreData?.[tactic.key] || 0
                const techniques = TECHNIQUE_MAP[tactic.name] || []

                return (
                  <div key={tactic.name} className="flex-1 min-w-[120px] space-y-2">
                    {/* Tactic Column Header */}
                    <div 
                      className="p-3 rounded-lg border text-center"
                      style={{
                        backgroundColor: '#08110F',
                        borderColor: count > 0 ? 'rgba(0, 245, 160, 0.25)' : 'rgba(255, 255, 255, 0.06)',
                      }}
                    >
                      <p className="text-[11px] font-bold text-[#E8FFF6] truncate font-sans">{tactic.name}</p>
                      <p className="text-[10px] font-mono font-semibold mt-0.5" style={{ color: count > 0 ? '#00F5A0' : '#607A71' }}>
                        {count} hits
                      </p>
                    </div>

                    {/* Techniques in this Tactic */}
                    <div className="space-y-1.5">
                      {techniques.map((tech) => (
                        <button
                          key={tech.id}
                          onClick={() => setSelectedTech({ ...tech, count, tacticName: tactic.name })}
                          className={`w-full text-left p-2.5 rounded-lg transition-all cursor-pointer space-y-1 block border ${
                            count > 0
                              ? 'bg-[#0B1412] border-[rgba(0,245,160,0.2)] hover:border-[#00F5A0]'
                              : 'bg-[#08110F] border-[rgba(255,255,255,0.04)] opacity-40 hover:opacity-70'
                          }`}
                        >
                          <div className="flex items-center justify-between text-[10px]">
                            <span className="font-mono font-bold text-[#00F5A0]">{tech.id}</span>
                            <span className="font-mono font-semibold text-[#9BB7AD]">{count}×</span>
                          </div>
                          <p className="text-[11px] font-medium text-[#E8FFF6] leading-tight font-sans truncate">{tech.name}</p>
                        </button>
                      ))}
                    </div>
                  </div>
                )
              })}
            </div>
          </div>

          {/* Technique Detail Inspector */}
          {selectedTech && (
            <GlassCard className="p-4">
              <div className="flex items-center justify-between border-b border-[rgba(0,245,160,0.12)] pb-2.5 mb-2.5">
                <div className="flex items-center gap-2">
                  <ShieldCheck className="text-[#00F5A0]" size={16} />
                  <h3 className="text-xs font-bold text-[#E8FFF6] font-sans">
                    Technique Analysis: <code className="text-[#00F5A0] font-mono">{selectedTech.id}</code> — {selectedTech.name}
                  </h3>
                </div>
                <button 
                  onClick={() => setSelectedTech(null)} 
                  className="text-xs text-[#607A71] hover:text-[#E8FFF6] cursor-pointer"
                >
                  Close
                </button>
              </div>
              <p className="text-xs text-[#9BB7AD] font-sans">
                Observed in honeypot telemetry: <strong className="text-[#00F5A0] font-mono">{selectedTech.count} times</strong>
                {selectedTech.tacticName && <> under the <span className="text-[#E8FFF6] font-semibold">{selectedTech.tacticName}</span> tactic category</>}.
              </p>
            </GlassCard>
          )}
        </>
      )}
    </div>
  )
}
