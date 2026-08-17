import { useState, useEffect } from 'react'
import { settingsAPI } from '../api/client'
import { GlassCard, SentinelButton, LoadingSpinner, PageHeader, SectionHeader } from '../components/common'
import { Settings as SettingsIcon, Save, CheckCircle2 } from 'lucide-react'

export default function Settings() {
  const [settings, setSettings] = useState({})
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [saved, setSaved] = useState(false)

  useEffect(() => {
    settingsAPI.get()
      .then(res => {
        const map = {}
        res.data.data.forEach(s => { map[s.key] = s.value })
        setSettings(map)
      })
      .catch(console.error)
      .finally(() => setLoading(false))
  }, [])

  const handleSave = async () => {
    setSaving(true)
    try {
      await settingsAPI.update(settings)
      setSaved(true)
      setTimeout(() => setSaved(false), 3000)
    } catch (err) { 
      console.error(err) 
    } finally { 
      setSaving(false) 
    }
  }

  const updateSetting = (key, value) => setSettings(prev => ({ ...prev, [key]: value }))

  if (loading) return <LoadingSpinner size="lg" text="Loading platform settings..." />

  return (
    <div className="space-y-6 max-w-3xl">
      {/* Page Header */}
      <PageHeader
        icon={SettingsIcon}
        title="Platform Configuration"
        subtitle="Manage honeypot sandbox paths, AI model endpoints, alert scoring thresholds, and report preferences"
      />

      {/* Honeypot Configuration */}
      <GlassCard className="p-5 space-y-4">
        <SectionHeader title="Honeypot Sandbox Configuration" />
        <div>
          <label className="text-xs font-medium text-[#9BB7AD] block mb-1.5 font-sans">
            Cowrie Log Path
          </label>
          <input
            type="text"
            value={settings.cowrie_log_path || ''}
            onChange={(e) => updateSetting('cowrie_log_path', e.target.value)}
            placeholder="/var/log/cowrie/cowrie.json"
            className="st-input font-mono text-xs"
          />
          <span className="text-[11px] text-[#607A71] mt-1 block">
            Absolute or relative file path to Cowrie JSON telemetry output
          </span>
        </div>
      </GlassCard>

      {/* AI Configuration */}
      <GlassCard className="p-5 space-y-4">
        <SectionHeader title="AI Engine & Copilot Parameters" />
        <div className="space-y-3.5">
          <div>
            <label className="text-xs font-medium text-[#9BB7AD] block mb-1.5 font-sans">
              Local LLM Model Identifier / Path
            </label>
            <input
              type="text"
              value={settings.hf_model || ''}
              onChange={(e) => updateSetting('hf_model', e.target.value)}
              placeholder="Qwen/Qwen2.5-0.5B-Instruct"
              className="st-input font-mono text-xs"
            />
          </div>

          <div>
            <label className="text-xs font-medium text-[#9BB7AD] block mb-1.5 font-sans">
              High Risk Alert Threshold Score (0 - 100)
            </label>
            <input
              type="number"
              min="1"
              max="100"
              value={settings.alert_threshold || '70'}
              onChange={(e) => updateSetting('alert_threshold', e.target.value)}
              className="st-input font-mono text-xs w-32"
            />
          </div>

          {/* Auto Analyze Toggle */}
          <div className="flex items-center justify-between p-3.5 rounded-lg bg-[#08110F] border border-[rgba(0,245,160,0.12)]">
            <div>
              <p className="text-xs font-semibold text-[#E8FFF6] font-sans">Autonomous Session Analysis</p>
              <p className="text-[11px] text-[#607A71] font-sans">Automatically run AI inference on incoming attacker sessions</p>
            </div>
            <button
              type="button"
              onClick={() => updateSetting('auto_analyze', settings.auto_analyze === 'true' ? 'false' : 'true')}
              className={`w-10 h-5.5 rounded-full p-0.5 transition-colors border flex items-center cursor-pointer ${
                settings.auto_analyze === 'true'
                  ? 'bg-[rgba(0,245,160,0.2)] border-[#00F5A0] justify-end'
                  : 'bg-[#0B1412] border-[rgba(255,255,255,0.1)] justify-start'
              }`}
            >
              <div
                className={`w-4 h-4 rounded-full transition-transform ${
                  settings.auto_analyze === 'true' ? 'bg-[#00F5A0]' : 'bg-[#607A71]'
                }`}
              />
            </button>
          </div>

          <div>
            <label className="text-xs font-medium text-[#9BB7AD] block mb-1.5 font-sans">
              Default Forensic Report Export Format
            </label>
            <select
              value={settings.report_format || 'pdf'}
              onChange={(e) => updateSetting('report_format', e.target.value)}
              className="st-input font-sans text-xs"
            >
              <option value="pdf">PDF Forensic Dossier</option>
              <option value="html">Interactive HTML Report</option>
              <option value="json">Structured Raw JSON</option>
            </select>
          </div>
        </div>
      </GlassCard>

      {/* Save Action Bar */}
      <div className="flex items-center gap-3 pt-2">
        <SentinelButton onClick={handleSave} disabled={saving} size="md">
          <Save size={14} /> {saving ? 'Saving...' : 'Save Changes'}
        </SentinelButton>
        {saved && (
          <span className="text-xs font-medium text-[#20E67A] flex items-center gap-1.5 font-sans">
            <CheckCircle2 size={15} /> Platform configuration updated successfully
          </span>
        )}
      </div>
    </div>
  )
}
