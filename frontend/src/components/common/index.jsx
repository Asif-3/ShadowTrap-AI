import { motion } from 'framer-motion'
import { cn } from '../../lib/utils'
import AttackSimulator from './AttackSimulator'
import EmptyState from './EmptyState'

export { AttackSimulator, EmptyState }

/**
 * Standard Dark Elevated Surface Card
 */
export function SentinelCard({ children, className, hover = true, style, ...props }) {
  return (
    <div
      className={cn(
        'sentinel-card p-5',
        hover && 'sentinel-card-hover',
        className
      )}
      style={{
        backgroundColor: '#0B1412',
        borderColor: 'rgba(0, 245, 160, 0.16)',
        ...style
      }}
      {...props}
    >
      {children}
    </div>
  )
}

// Backward compatibility alias for GlassCard
export const GlassCard = SentinelCard

/**
 * Unified Page Header with Title, Status Tag, Subtitle & Action Bar
 */
export function PageHeader({ 
  title, 
  subtitle, 
  badge, 
  icon: Icon,
  actions, 
  className 
}) {
  return (
    <div className={cn('flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-5 border-b border-[rgba(0,245,160,0.14)]', className)}>
      <div>
        <div className="flex items-center gap-2.5">
          {Icon && <Icon size={22} className="text-[#00F5A0] shrink-0" />}
          <h1 className="text-xl sm:text-2xl font-bold tracking-tight text-[#E8FFF6] font-sans">
            {title}
          </h1>
          {badge && (
            <span className="px-2 py-0.5 rounded text-[11px] font-semibold font-mono bg-[rgba(0,245,160,0.12)] text-[#00F5A0] border border-[rgba(0,245,160,0.25)]">
              {badge}
            </span>
          )}
        </div>
        {subtitle && (
          <p className="text-xs sm:text-sm text-[#9BB7AD] mt-1 font-sans">
            {subtitle}
          </p>
        )}
      </div>
      {actions && (
        <div className="flex items-center gap-2.5 flex-wrap shrink-0">
          {actions}
        </div>
      )}
    </div>
  )
}

/**
 * Section Title Header
 */
export function SectionHeader({ title, badge, action, className }) {
  return (
    <div className={cn('flex items-center justify-between gap-3 mb-3.5', className)}>
      <div className="flex items-center gap-2">
        <h2 className="text-sm font-semibold text-[#E8FFF6] uppercase tracking-wider font-sans">
          {title}
        </h2>
        {badge && (
          <span className="text-[10px] font-semibold px-2 py-0.5 rounded bg-[#0F1A17] text-[#9BB7AD] border border-[rgba(0,245,160,0.12)] font-mono">
            {badge}
          </span>
        )}
      </div>
      {action && <div>{action}</div>}
    </div>
  )
}

/**
 * Executive KPI Stat Card
 */
export function KPICard({ 
  label, 
  value, 
  icon: Icon, 
  trend, 
  trendUp, 
  statusText,
  color = '#00F5A0', 
  delay = 0,
  className 
}) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.25, delay }}
      className={cn(
        'sentinel-card sentinel-card-hover p-4 sm:p-5 flex items-start justify-between min-h-[104px]',
        className
      )}
      style={{
        backgroundColor: '#0B1412',
        borderColor: 'rgba(0, 245, 160, 0.16)',
      }}
    >
      <div className="min-w-0 flex-1 pr-2">
        <p className="text-xs font-medium text-[#9BB7AD] tracking-wide font-sans truncate mb-1">
          {label}
        </p>
        <p className="text-2xl sm:text-3xl font-bold tracking-tight text-[#E8FFF6] font-sans">
          {value}
        </p>
        <div className="flex items-center gap-2 mt-1">
          {trend && (
            <span 
              className="text-xs font-semibold font-mono"
              style={{ color: trendUp ? '#20E67A' : '#FF4D67' }}
            >
              {trendUp ? '↑' : '↓'} {trend}
            </span>
          )}
          {statusText && (
            <span className="text-[11px] text-[#607A71] font-sans">
              {statusText}
            </span>
          )}
        </div>
      </div>
      {Icon && (
        <div 
          className="p-2.5 rounded-lg shrink-0 border"
          style={{
            backgroundColor: '#0F1A17',
            borderColor: 'rgba(0, 245, 160, 0.16)',
          }}
        >
          <Icon size={18} style={{ color }} />
        </div>
      )}
    </motion.div>
  )
}

// Backward compatibility alias for StatCard
export const StatCard = KPICard

/**
 * Standard Sentinel Action Button
 */
export function SentinelButton({ 
  children, 
  variant = 'primary', 
  size = 'md', 
  className, 
  disabled,
  ...props 
}) {
  const sizes = {
    sm: 'px-3 py-1.5 text-xs',
    md: 'px-4 py-2 text-sm',
    lg: 'px-5 py-2.5 text-base',
  }

  const variantClass = {
    primary: 'btn-primary',
    secondary: 'btn-secondary',
    danger: 'btn-danger',
    ghost: 'btn-ghost',
    success: 'btn-primary',
    warning: 'btn-secondary',
    accent: 'btn-primary'
  }[variant] || 'btn-primary'

  return (
    <button
      disabled={disabled}
      className={cn(
        variantClass,
        sizes[size],
        disabled && 'opacity-50 cursor-not-allowed pointer-events-none',
        className
      )}
      {...props}
    >
      {children}
    </button>
  )
}

// Backward compatibility alias for NeonButton
export const NeonButton = SentinelButton

/**
 * Compact Status Badge Pill
 */
export function StatusBadge({ status, label: customLabel, className }) {
  const normalized = status?.toLowerCase() || 'completed'

  const styles = {
    active: { bg: 'rgba(32, 230, 122, 0.12)', color: '#20E67A', border: 'rgba(32, 230, 122, 0.3)', label: '● Live' },
    live: { bg: 'rgba(32, 230, 122, 0.12)', color: '#20E67A', border: 'rgba(32, 230, 122, 0.3)', label: '● Live' },
    analyzed: { bg: 'rgba(77, 184, 255, 0.12)', color: '#4DB8FF', border: 'rgba(77, 184, 255, 0.3)', label: 'Analyzed' },
    completed: { bg: 'rgba(0, 245, 160, 0.12)', color: '#00F5A0', border: 'rgba(0, 245, 160, 0.25)', label: 'Completed' },
    critical: { bg: 'rgba(255, 77, 103, 0.14)', color: '#FF4D67', border: 'rgba(255, 77, 103, 0.35)', label: 'Critical' },
    high: { bg: 'rgba(255, 112, 67, 0.14)', color: '#FF7043', border: 'rgba(255, 112, 67, 0.35)', label: 'High' },
    medium: { bg: 'rgba(245, 196, 81, 0.14)', color: '#F5C451', border: 'rgba(245, 196, 81, 0.35)', label: 'Medium' },
    low: { bg: 'rgba(32, 230, 122, 0.12)', color: '#20E67A', border: 'rgba(32, 230, 122, 0.3)', label: 'Low' },
    contained: { bg: 'rgba(155, 108, 255, 0.14)', color: '#9B6CFF', border: 'rgba(155, 108, 255, 0.3)', label: 'Contained' },
  }

  const s = styles[normalized] || styles.completed
  const text = customLabel || s.label

  return (
    <span 
      className={cn('inline-flex items-center px-2 py-0.5 rounded text-[11px] font-semibold font-mono tracking-wide border', className)}
      style={{ 
        backgroundColor: s.bg, 
        color: s.color, 
        borderColor: s.border 
      }}
    >
      {text}
    </span>
  )
}

/**
 * Animated Loading Spinner / Skeleton
 */
export function LoadingSpinner({ size = 'md', text }) {
  const sizes = { sm: 'w-5 h-5', md: 'w-7 h-7', lg: 'w-10 h-10' }
  return (
    <div className="flex flex-col items-center justify-center py-10 gap-3">
      <motion.div
        animate={{ rotate: 360 }}
        transition={{ duration: 0.9, repeat: Infinity, ease: 'linear' }}
        className={cn(sizes[size], 'border-2 border-t-[#00F5A0] border-r-transparent border-b-transparent border-l-transparent rounded-full')}
      />
      {text && (
        <span className="text-xs text-[#9BB7AD] font-mono tracking-wider">
          {text}
        </span>
      )}
    </div>
  )
}

/**
 * Skeleton Loader for Cards and Tables
 */
export function SkeletonLoader({ type = 'card', count = 1, className }) {
  return (
    <div className={cn('space-y-3', className)}>
      {Array.from({ length: count }).map((_, i) => (
        <div 
          key={i}
          className="animate-pulse rounded-xl bg-[#0B1412] border border-[rgba(255,255,255,0.06)] p-5"
        >
          <div className="h-4 bg-[#0F1A17] rounded w-1/3 mb-3" />
          <div className="h-6 bg-[#0F1A17] rounded w-1/2 mb-2" />
          <div className="h-3 bg-[#0F1A17] rounded w-2/3" />
        </div>
      ))}
    </div>
  )
}

/**
 * Threat Score Meter Component
 */
export function ThreatMeter({ score = 0, size = 110 }) {
  const getColor = (s) => {
    if (s >= 80) return '#FF4D67'
    if (s >= 60) return '#FF7043'
    if (s >= 35) return '#F5C451'
    return '#20E67A'
  }
  const color = getColor(score)
  const radius = 42
  const circumference = 2 * Math.PI * radius
  const offset = circumference - (score / 100) * circumference

  return (
    <div className="relative inline-flex items-center justify-center" style={{ width: size, height: size }}>
      <svg width={size} height={size} className="-rotate-90">
        <circle 
          cx={size / 2} 
          cy={size / 2} 
          r={radius} 
          fill="none" 
          stroke="rgba(255, 255, 255, 0.08)" 
          strokeWidth="7" 
        />
        <motion.circle
          cx={size / 2} 
          cy={size / 2} 
          r={radius} 
          fill="none"
          stroke={color} 
          strokeWidth="7" 
          strokeLinecap="round"
          strokeDasharray={circumference}
          initial={{ strokeDashoffset: circumference }}
          animate={{ strokeDashoffset: offset }}
          transition={{ duration: 0.9, ease: 'easeOut' }}
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center font-mono">
        <motion.span
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="text-lg font-bold" 
          style={{ color }}
        >
          {score}
        </motion.span>
        <span className="text-[10px] text-[#607A71]">/ 100</span>
      </div>
    </div>
  )
}

export function AnimatedCounter({ value }) {
  return (
    <motion.span
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      key={value}
    >
      {value}
    </motion.span>
  )
}
