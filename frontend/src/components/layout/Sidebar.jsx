import { NavLink, useLocation } from 'react-router-dom'
import { motion } from 'framer-motion'
import {
  LayoutDashboard, Radio, Shield, PlayCircle,
  FileText, BarChart3, Settings, ChevronLeft,
  ChevronRight, Fingerprint, Network, Cpu, Terminal, Users, Globe, Eye
} from 'lucide-react'

const navGroups = [
  {
    title: 'Operations',
    items: [
      { path: '/sentinel', icon: LayoutDashboard, label: 'SOC Dashboard' },
      { path: '/sentinel/live-sessions', icon: Radio, label: 'Live Sessions' },
      { path: '/sentinel/attacks', icon: Shield, label: 'Attacks' },
      { path: '/sentinel/replay', icon: PlayCircle, label: 'Attack Replay' },
    ]
  },
  {
    title: 'Intelligence',
    items: [
      { path: '/sentinel/trap-visitors', icon: Eye, label: 'Trap Visitors' },
      { path: '/sentinel/knowledge-graph', icon: Network, label: 'Knowledge Graph' },
      { path: '/sentinel/mitre-matrix', icon: Cpu, label: 'MITRE ATT&CK' },
      { path: '/sentinel/threat-intel', icon: Globe, label: 'Threat Intel' },
    ]
  },
  {
    title: 'Analysis',
    items: [
      { path: '/sentinel/copilot', icon: Terminal, label: 'AI Security Copilot' },
      { path: '/sentinel/reports', icon: FileText, label: 'Reports' },
      { path: '/sentinel/analytics', icon: BarChart3, label: 'Analytics' },
    ]
  },
  {
    title: 'Management',
    items: [
      { path: '/sentinel/users', icon: Users, label: 'User Management' },
      { path: '/sentinel/settings', icon: Settings, label: 'Settings' },
    ]
  }
]

export default function Sidebar({ collapsed, onToggle }) {
  const location = useLocation()

  return (
    <motion.aside
      animate={{ width: collapsed ? 72 : 248 }}
      transition={{ duration: 0.2, ease: 'easeInOut' }}
      className="h-full flex flex-col border-r select-none shrink-0 overflow-hidden"
      style={{
        backgroundColor: '#08110F',
        borderColor: 'rgba(0, 245, 160, 0.14)',
      }}
    >
      {/* Brand Header */}
      <div 
        className="h-16 flex items-center px-4 gap-3 border-b shrink-0 overflow-hidden"
        style={{ borderColor: 'rgba(0, 245, 160, 0.14)' }}
      >
        <div
          className="w-8 h-8 rounded-lg flex items-center justify-center shrink-0"
          style={{
            background: 'rgba(0, 245, 160, 0.12)',
            border: '1px solid rgba(0, 245, 160, 0.35)',
          }}
        >
          <Fingerprint size={18} className="text-[#00F5A0]" />
        </div>
        {!collapsed && (
          <motion.div 
            initial={{ opacity: 0 }} 
            animate={{ opacity: 1 }} 
            className="min-w-0 flex-1 overflow-hidden"
          >
            <div className="flex items-center gap-1.5">
              <span className="text-xs font-bold tracking-wider text-[#E8FFF6] uppercase font-sans truncate">
                ShadowTrap
              </span>
              <span className="text-[10px] font-semibold px-1.5 py-0.2 rounded bg-[rgba(0,245,160,0.12)] text-[#00F5A0] font-mono shrink-0">
                SOC
              </span>
            </div>
            <div className="flex items-center gap-1.5 mt-0.5">
              <span className="live-dot-sm" />
              <span className="text-[10px] text-[#9BB7AD] font-mono tracking-wider truncate">
                SENTINEL.ONLINE
              </span>
            </div>
          </motion.div>
        )}
      </div>

      {/* Navigation Sections */}
      <nav className="flex-1 py-3 px-2.5 space-y-4 overflow-y-auto overflow-x-hidden">
        {navGroups.map((group) => (
          <div key={group.title} className="space-y-1">
            {!collapsed && (
              <p className="px-2.5 pb-1 text-[10px] font-semibold tracking-wider uppercase text-[#607A71] font-sans truncate">
                {group.title}
              </p>
            )}
            {group.items.map(({ path, icon: Icon, label }) => {
              const isActive = path === '/sentinel'
                ? location.pathname === '/sentinel' || location.pathname === '/sentinel/'
                : location.pathname.startsWith(path)

              return (
                <NavLink 
                  key={path} 
                  to={path} 
                  end={path === '/sentinel'} 
                  title={collapsed ? label : undefined}
                  className="block"
                >
                  <div
                    className={`flex items-center gap-2.5 px-2.5 py-2 rounded-lg text-[13px] font-medium transition-all duration-150 relative ${
                      isActive
                        ? 'text-[#E8FFF6] bg-[rgba(0,245,160,0.08)] border border-[rgba(0,245,160,0.24)]'
                        : 'text-[#9BB7AD] hover:text-[#E8FFF6] hover:bg-[rgba(255,255,255,0.03)] border border-transparent'
                    }`}
                  >
                    {isActive && (
                      <div className="absolute left-0 top-1.5 bottom-1.5 w-1 bg-[#00F5A0] rounded-r-sm" />
                    )}
                    <Icon 
                      size={16} 
                      className={`shrink-0 ${isActive ? 'text-[#00F5A0]' : 'text-[#9BB7AD]'}`} 
                    />
                    {!collapsed && (
                      <span className="truncate font-sans tracking-normal">
                        {label}
                      </span>
                    )}
                  </div>
                </NavLink>
              )
            })}
          </div>
        ))}
      </nav>

      {/* Bottom System Status */}
      {!collapsed && (
        <div 
          className="m-2.5 p-2.5 rounded-lg border shrink-0 flex items-center justify-between overflow-hidden"
          style={{
            backgroundColor: '#050908',
            borderColor: 'rgba(0, 245, 160, 0.12)',
          }}
        >
          <div className="min-w-0 flex-1 truncate">
            <p className="text-[10px] font-semibold text-[#E8FFF6] font-sans truncate">
              SENTINEL SOC v2.5
            </p>
            <p className="text-[9px] text-[#607A71] font-mono mt-0.5 truncate">
              SECURE GRID ACTIVE
            </p>
          </div>
          <span className="live-dot-sm shrink-0 ml-2" />
        </div>
      )}

      {/* Collapse Toggle Button */}
      <button
        onClick={onToggle}
        aria-label={collapsed ? "Expand sidebar" : "Collapse sidebar"}
        className="hidden lg:flex items-center justify-center h-9 hover:bg-[rgba(255,255,255,0.04)] text-[#607A71] hover:text-[#E8FFF6] transition-colors border-t border-[rgba(0,245,160,0.12)] cursor-pointer shrink-0 w-full"
      >
        {collapsed ? <ChevronRight size={15} /> : <ChevronLeft size={15} />}
      </button>
    </motion.aside>
  )
}
