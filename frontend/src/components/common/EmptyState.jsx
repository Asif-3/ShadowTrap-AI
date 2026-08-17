import { motion } from 'framer-motion'
import { Shield, Radar, Radio, ShieldAlert, BarChart3, FileText, Network, Globe, Cpu, Zap, Eye, Terminal, Users, Settings } from 'lucide-react'

const PRESETS = {
  dashboard: {
    icon: Shield,
    title: 'Honeypot Armed & Listening',
    description: 'ShadowTrap AI is actively monitoring all attack surfaces. Data will appear here once threat activity is detected.',
    accent: '#00F5A0',
  },
  attacks: {
    icon: ShieldAlert,
    title: 'No Attack Sessions Recorded',
    description: 'The honeypot has not captured any attacker sessions yet. Once SSH/Telnet intrusions are detected, they will appear here.',
    accent: '#FF4D67',
  },
  sessions: {
    icon: Radio,
    title: 'No Live Sessions Active',
    description: 'There are no active honeypot sessions at this time. Live attacker connections will stream here in real-time.',
    accent: '#20E67A',
  },
  analytics: {
    icon: BarChart3,
    title: 'Awaiting Telemetry Data',
    description: 'Analytics will populate once attack sessions are captured and processed by the AI engine.',
    accent: '#9B6CFF',
  },
  reports: {
    icon: FileText,
    title: 'No Reports Generated Yet',
    description: 'Generate incident reports after capturing attack sessions. Reports include MITRE mappings, threat scores, and AI analysis.',
    accent: '#4DB8FF',
  },
  graph: {
    icon: Network,
    title: 'Knowledge Graph Empty',
    description: 'The threat knowledge graph will visualize attacker relationships once sessions are recorded and analyzed.',
    accent: '#9B6CFF',
  },
  intel: {
    icon: Globe,
    title: 'No Threat Intelligence Available',
    description: 'IP reputation and threat actor profiles will appear here after honeypot interactions are logged.',
    accent: '#4DB8FF',
  },
  mitre: {
    icon: Cpu,
    title: 'No MITRE ATT&CK Detections',
    description: 'Tactics, Techniques, and Procedures will be mapped automatically once real attack commands are captured.',
    accent: '#F5C451',
  },
  map: {
    icon: Globe,
    title: 'No Geolocated Attacks Yet',
    description: 'Attack origin markers will appear on the map once threat IPs are geolocated.',
    accent: '#4DB8FF',
  },
  heatmap: {
    icon: Zap,
    title: 'No Activity Recorded',
    description: 'The heatmap will show attack velocity patterns once honeypot traffic is logged.',
    accent: '#F5C451',
  },
  cluster: {
    icon: Radar,
    title: 'No Behavior Clusters',
    description: 'Attacker behavior clustering requires captured session data. Clusters will form as attack patterns emerge.',
    accent: '#9B6CFF',
  },
  model: {
    icon: Cpu,
    title: 'AI Model Awaiting Data',
    description: 'Model performance metrics will be available after training on captured attack data.',
    accent: '#00F5A0',
  },
  copilot: {
    icon: Terminal,
    title: 'AI Security Copilot Ready',
    description: 'Select an attack session and start a conversation to analyze threats with your local AI copilot.',
    accent: '#9B6CFF',
  },
  replay: {
    icon: Radio,
    title: 'No Session Selected',
    description: 'Select an attack session to replay the complete command timeline and MITRE ATT&CK progression.',
    accent: '#4DB8FF',
  },
  visitors: {
    icon: Eye,
    title: 'No Trapped Visitors',
    description: 'Visitor telemetry will appear here when attackers interact with the decoy page.',
    accent: '#F5C451',
  },
  users: {
    icon: Users,
    title: 'No Users Found',
    description: 'User accounts will appear here once they are created by an administrator.',
    accent: '#9BB7AD',
  },
  search: {
    icon: Shield,
    title: 'No Results Found',
    description: 'Try adjusting your search terms or clearing filters.',
    accent: '#9BB7AD',
  },
}

/**
 * Professional SOC Empty State Component.
 * Compact icon + title + explanation + optional action button.
 */
export default function EmptyState({ preset = 'dashboard', title, description, size = 'lg', children }) {
  const config = PRESETS[preset] || PRESETS.dashboard
  const Icon = config.icon

  const sizes = {
    sm: { icon: 24, padding: 'py-6', titleSize: 'text-xs', descSize: 'text-[11px]', ringSize: 48, gap: 'gap-2' },
    md: { icon: 30, padding: 'py-8', titleSize: 'text-sm', descSize: 'text-xs', ringSize: 60, gap: 'gap-2.5' },
    lg: { icon: 36, padding: 'py-12', titleSize: 'text-base', descSize: 'text-sm', ringSize: 72, gap: 'gap-3' },
  }
  const s = sizes[size] || sizes.lg

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.35 }}
      className={`flex flex-col items-center justify-center text-center ${s.padding} ${s.gap}`}
    >
      {/* Icon Container */}
      <div
        className="relative flex items-center justify-center rounded-xl"
        style={{
          width: s.ringSize,
          height: s.ringSize,
          backgroundColor: `${config.accent}0D`,
          border: `1px solid ${config.accent}22`,
        }}
      >
        <Icon size={s.icon} style={{ color: config.accent }} strokeWidth={1.5} />
      </div>

      {/* Title */}
      <h3 className={`${s.titleSize} font-semibold text-[#E8FFF6] font-sans`}>
        {title || config.title}
      </h3>

      {/* Description */}
      <p className={`${s.descSize} text-[#607A71] max-w-sm leading-relaxed font-sans`}>
        {description || config.description}
      </p>

      {/* Optional Actions */}
      {children && <div className="mt-2">{children}</div>}
    </motion.div>
  )
}
