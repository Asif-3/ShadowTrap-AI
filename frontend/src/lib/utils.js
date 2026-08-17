import { clsx } from 'clsx'
import { twMerge } from 'tailwind-merge'

export function cn(...inputs) {
  return twMerge(clsx(inputs))
}

export function formatNumber(num) {
  if (num >= 1000000) return (num / 1000000).toFixed(1) + 'M'
  if (num >= 1000) return (num / 1000).toFixed(1) + 'K'
  return num?.toString() || '0'
}

export function formatDate(dateStr) {
  if (!dateStr) return 'N/A'
  const d = new Date(dateStr)
  return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
}

export function formatTime(dateStr) {
  if (!dateStr) return 'N/A'
  const d = new Date(dateStr)
  return d.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', second: '2-digit' })
}

export function formatDateTime(dateStr) {
  if (!dateStr) return 'N/A'
  return `${formatDate(dateStr)} ${formatTime(dateStr)}`
}

export function getThreatColor(score) {
  if (score >= 80) return '#FF4D67' // Critical danger
  if (score >= 60) return '#FF7043' // High warning
  if (score >= 35) return '#F5C451' // Medium warning
  return '#20E67A' // Low / Normal
}

export function getThreatLevel(score) {
  if (score >= 80) return 'Critical'
  if (score >= 60) return 'High'
  if (score >= 35) return 'Medium'
  return 'Low'
}

export function getStageColor(stage) {
  const colors = {
    'Reconnaissance': '#4DB8FF',
    'Discovery': '#9B6CFF',
    'Credential Discovery': '#FF4D67',
    'Payload Download': '#FF7043',
    'Privilege Escalation': '#F5C451',
    'Persistence': '#9B6CFF',
    'Defense Evasion': '#FF4D67',
    'Command And Control': '#FF4D67',
    'Data Collection': '#F5C451',
    'Exfiltration': '#FF4D67',
  }
  return colors[stage] || '#9BB7AD'
}
