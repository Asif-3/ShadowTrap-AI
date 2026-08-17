import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../../context/AuthContext'
import { useRealTimeAttacks } from '../../hooks/useRealTimeAttacks'
import CommandPalette from '../common/CommandPalette'
import NotificationCenter from '../common/NotificationCenter'
import {
  Bell, Search, LogOut, Eye, Menu, Wifi, Clock
} from 'lucide-react'

export default function Topbar({ onMenuClick }) {
  const { user, logout } = useAuth()
  const navigate = useNavigate()

  const [cmdOpen, setCmdOpen] = useState(false)
  const [notifOpen, setNotifOpen] = useState(false)
  const [trapCount, setTrapCount] = useState(0)
  const [currentTime, setCurrentTime] = useState(new Date())

  // Real-time alerts from Socket.IO
  const { alerts, dismissAlert } = useRealTimeAttacks()

  // Update clock every second
  useEffect(() => {
    const timer = setInterval(() => setCurrentTime(new Date()), 1000)
    return () => clearInterval(timer)
  }, [])

  // Periodically fetch trap visitor count
  useEffect(() => {
    const fetchTrapCount = async () => {
      try {
        const token = localStorage.getItem('shadowtrap_token')
        if (!token) return
        const res = await fetch('/api/trap/visitors', {
          headers: { Authorization: `Bearer ${token}` }
        })
        if (res.ok) {
          const data = await res.json()
          setTrapCount(data.data?.stats?.unique_ips || 0)
        }
      } catch { /* silent */ }
    }
    fetchTrapCount()
    const interval = setInterval(fetchTrapCount, 30000)
    return () => clearInterval(interval)
  }, [])

  const timeStr = currentTime.toLocaleTimeString('en-US', { hour12: false })

  return (
    <>
      <header
        className="h-16 sticky top-0 z-20 px-4 sm:px-6 flex items-center justify-between select-none"
        style={{
          backgroundColor: '#08110F',
          borderBottom: '1px solid rgba(0, 245, 160, 0.14)',
          boxShadow: '0 2px 12px rgba(0, 0, 0, 0.4)',
        }}
      >
        {/* Mobile Menu Toggle */}
        <button
          onClick={onMenuClick}
          aria-label="Open navigation menu"
          className="lg:hidden p-2 rounded-lg hover:bg-[rgba(255,255,255,0.05)] text-[#9BB7AD] hover:text-[#E8FFF6] cursor-pointer mr-2"
        >
          <Menu size={18} />
        </button>

        {/* Left Section — Clock & Global Search */}
        <div className="flex items-center gap-3 flex-1 min-w-0">
          {/* UTC/Local SOC Clock */}
          <div 
            className="hidden sm:flex items-center gap-1.5 px-2.5 py-1 rounded-md shrink-0 border"
            style={{
              backgroundColor: '#050908',
              borderColor: 'rgba(0, 245, 160, 0.15)',
            }}
          >
            <Clock size={12} className="text-[#00F5A0]" />
            <span className="text-[11px] text-[#E8FFF6] font-mono font-medium tracking-wider">
              {timeStr}
            </span>
          </div>

          {/* Search / Command Palette Trigger */}
          <button
            onClick={() => setCmdOpen(true)}
            className="flex items-center justify-between gap-2 px-3 py-1.5 rounded-lg text-xs text-[#9BB7AD] hover:text-[#E8FFF6] hover:border-[rgba(0,245,160,0.3)] transition-all cursor-pointer w-44 sm:w-60 shrink-0 border"
            style={{
              backgroundColor: '#0B1412',
              borderColor: 'rgba(0, 245, 160, 0.16)',
            }}
          >
            <div className="flex items-center gap-2 truncate">
              <Search size={13} className="text-[#00F5A0] shrink-0" />
              <span className="truncate font-sans text-xs">Search commands & IPs...</span>
            </div>
            <kbd className="px-1.5 py-0.5 rounded text-[10px] bg-[#050908] border border-[rgba(255,255,255,0.1)] font-mono text-[#00F5A0] shrink-0">
              ⌘K
            </kbd>
          </button>
        </div>

        {/* Right Section — Live Status & Controls */}
        <div className="flex items-center gap-2 sm:gap-3 shrink-0">
          {/* Connection Status */}
          <div 
            className="hidden md:flex items-center gap-1.5 px-2.5 py-1 rounded-md border"
            style={{
              backgroundColor: 'rgba(32, 230, 122, 0.08)',
              borderColor: 'rgba(32, 230, 122, 0.25)',
            }}
          >
            <Wifi size={12} className="text-[#20E67A]" />
            <span className="text-[11px] tracking-wider text-[#20E67A] font-mono font-semibold">
              CONNECTED
            </span>
          </div>

          {/* Trap Visitors Counter */}
          <button
            onClick={() => navigate('/sentinel/trap-visitors')}
            className="flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-semibold transition cursor-pointer border"
            style={{
              backgroundColor: 'rgba(0, 245, 160, 0.08)',
              borderColor: 'rgba(0, 245, 160, 0.22)',
              color: '#00F5A0',
            }}
          >
            <Eye size={13} className="text-[#00F5A0]" />
            <span className="font-mono">{trapCount}</span>
            <span className="text-[10px] tracking-wider font-mono hidden sm:inline">TRAPPED</span>
            <span className="live-dot-sm" />
          </button>

          {/* Notification Center */}
          <button
            onClick={() => setNotifOpen(true)}
            aria-label="Open notifications"
            className="p-2 rounded-lg hover:bg-[rgba(255,255,255,0.05)] text-[#9BB7AD] hover:text-[#E8FFF6] relative cursor-pointer transition-colors"
          >
            <Bell size={16} />
            {alerts.length > 0 && (
              <span className="absolute top-1 right-1 min-w-[15px] h-3.5 rounded-full bg-[#FF4D67] text-white text-[8px] font-bold flex items-center justify-center px-1 font-mono">
                {alerts.length > 99 ? '99+' : alerts.length}
              </span>
            )}
          </button>

          <div className="w-px h-5 bg-[rgba(255,255,255,0.08)]" />

          {/* User Profile & Logout */}
          <div className="flex items-center gap-2">
            <button
              onClick={() => navigate('/sentinel/profile')}
              className="flex items-center gap-2 text-xs text-[#E8FFF6] hover:text-[#00F5A0] cursor-pointer transition-colors"
            >
              <div
                className="w-7 h-7 rounded-md flex items-center justify-center font-bold text-[#00F5A0] border font-mono text-[11px]"
                style={{
                  backgroundColor: 'rgba(0, 245, 160, 0.12)',
                  borderColor: 'rgba(0, 245, 160, 0.3)',
                }}
              >
                {user?.name?.[0]?.toUpperCase() || 'A'}
              </div>
              <span className="hidden lg:inline font-medium text-[#E8FFF6] font-sans">
                {user?.name || 'SOC Analyst'}
              </span>
            </button>

            <button
              onClick={logout}
              title="Logout from Sentinel"
              aria-label="Logout"
              className="p-1.5 text-[#607A71] hover:text-[#FF4D67] transition-colors cursor-pointer rounded-md hover:bg-[rgba(255,77,103,0.1)]"
            >
              <LogOut size={15} />
            </button>
          </div>
        </div>
      </header>

      {/* Modals */}
      <CommandPalette open={cmdOpen} onOpenChange={setCmdOpen} />
      <NotificationCenter
        open={notifOpen}
        onClose={() => setNotifOpen(false)}
        alerts={alerts}
        onDismiss={dismissAlert}
      />
    </>
  )
}
