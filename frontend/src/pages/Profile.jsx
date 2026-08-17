import { useState } from 'react'
import { useAuth } from '../context/AuthContext'
import { authAPI } from '../api/client'
import { GlassCard, SentinelButton, PageHeader, SectionHeader } from '../components/common'
import { User, Lock, Save, CheckCircle2, Shield } from 'lucide-react'

export default function Profile() {
  const { user } = useAuth()
  const [currentPassword, setCurrentPassword] = useState('')
  const [newPassword, setNewPassword] = useState('')
  const [message, setMessage] = useState('')
  const [error, setError] = useState('')

  const handleChangePassword = async (e) => {
    e.preventDefault()
    setMessage(''); setError('')
    try {
      await authAPI.changePassword(currentPassword, newPassword)
      setMessage('Password changed successfully')
      setCurrentPassword(''); setNewPassword('')
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to change password')
    }
  }

  return (
    <div className="space-y-6 max-w-2xl">
      {/* Page Header */}
      <PageHeader
        icon={User}
        title="Analyst Profile"
        subtitle="Manage your SOC credentials, security role permissions, and active session authentication"
      />

      {/* Profile Overview Card */}
      <GlassCard className="p-5">
        <div className="flex items-center gap-4">
          <div 
            className="w-14 h-14 rounded-xl flex items-center justify-center text-xl font-bold font-mono border"
            style={{
              backgroundColor: 'rgba(0, 245, 160, 0.12)',
              borderColor: 'rgba(0, 245, 160, 0.35)',
              color: '#00F5A0',
            }}
          >
            {user?.name?.charAt(0)?.toUpperCase() || 'A'}
          </div>
          <div className="space-y-1">
            <p className="text-base font-bold text-[#E8FFF6] font-sans">{user?.name || 'SOC Analyst'}</p>
            <p className="text-xs text-[#9BB7AD] font-mono">{user?.email || 'analyst@shadowtrap.local'}</p>
            <span className="text-[10px] font-semibold px-2 py-0.5 rounded bg-[rgba(0,245,160,0.1)] text-[#00F5A0] border border-[rgba(0,245,160,0.25)] font-mono uppercase inline-block mt-1">
              {user?.role || 'Security Analyst'}
            </span>
          </div>
        </div>
      </GlassCard>

      {/* Change Password Card */}
      <GlassCard className="p-5">
        <SectionHeader title="Authentication Security" />
        <form onSubmit={handleChangePassword} className="space-y-4">
          <div>
            <label className="text-xs font-medium text-[#9BB7AD] block mb-1.5 font-sans">
              Current Password
            </label>
            <input
              type="password"
              value={currentPassword}
              onChange={(e) => setCurrentPassword(e.target.value)}
              placeholder="••••••••••••"
              className="st-input text-xs"
              required
            />
          </div>

          <div>
            <label className="text-xs font-medium text-[#9BB7AD] block mb-1.5 font-sans">
              New Secure Password
            </label>
            <input
              type="password"
              value={newPassword}
              onChange={(e) => setNewPassword(e.target.value)}
              placeholder="••••••••••••"
              className="st-input text-xs"
              required
            />
          </div>

          {error && <p className="text-xs text-[#FF4D67] font-sans">{error}</p>}
          {message && (
            <p className="text-xs text-[#20E67A] font-sans flex items-center gap-1">
              <CheckCircle2 size={14} /> {message}
            </p>
          )}

          <SentinelButton type="submit" size="md">
            <Save size={14} /> Update Password
          </SentinelButton>
        </form>
      </GlassCard>
    </div>
  )
}
