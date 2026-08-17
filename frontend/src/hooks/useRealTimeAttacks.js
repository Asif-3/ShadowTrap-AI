import { useState, useCallback, useRef } from 'react'
import { useSocket } from './useSocket'

export function useRealTimeAttacks(initialAttacks = []) {
  const [attacks, setAttacks] = useState(initialAttacks)
  const [alerts, setAlerts] = useState([])
  const [liveCount, setLiveCount] = useState(0)
  const [dashboardStats, setDashboardStats] = useState(null)
  const [refreshCount, setRefreshCount] = useState(0)
  const newAttackIds = useRef(new Set())

  // Handle incoming new attack event
  const handleNewAttack = useCallback((eventData) => {
    const newAtk = eventData?.data || eventData
    if (!newAtk || !newAtk.session_id) return

    setRefreshCount((c) => c + 1)

    // Track as new for flash animation
    newAttackIds.current.add(newAtk.session_id)
    setTimeout(() => newAttackIds.current.delete(newAtk.session_id), 2000)

    setAttacks((prev) => {
      const filtered = prev.filter((a) => a.session_id !== newAtk.session_id)
      return [newAtk, ...filtered]
    })

    // Auto-generate alert for high-threat attacks
    if (newAtk.threat_score >= 70) {
      const autoAlert = {
        id: Date.now(),
        timestamp: new Date().toLocaleTimeString(),
        severity: newAtk.threat_score >= 90 ? 'CRITICAL' : 'HIGH',
        title: `High-Risk Attack Detected (Score ${newAtk.threat_score})`,
        message: `IP ${newAtk.src_ip} — ${newAtk.attack_stage || 'Unknown Stage'} / ${newAtk.intent || 'Unknown Intent'}`,
        session_id: newAtk.session_id,
      }
      setAlerts((prev) => [autoAlert, ...prev.slice(0, 29)])
    }
  }, [])

  // Handle attack updates
  const handleAttackUpdate = useCallback((eventData) => {
    const { session_id, data } = eventData
    if (!session_id || !data) return

    setAttacks((prev) =>
      prev.map((atk) => (atk.session_id === session_id ? { ...atk, ...data } : atk))
    )
  }, [])

  // Handle threat alerts from the server
  const handleThreatAlert = useCallback((eventData) => {
    const alertData = eventData.data
    if (!alertData) return

    const newAlert = {
      id: Date.now(),
      timestamp: new Date().toLocaleTimeString(),
      severity: alertData.severity || 'HIGH',
      title: alertData.title || 'Threat Alert',
      message: alertData.message || '',
      session_id: alertData.session_id || '',
      threat_score: alertData.threat_score,
    }
    setAlerts((prev) => [newAlert, ...prev.slice(0, 29)])
  }, [])

  // Handle dashboard stats updates — exposed for live stat cards
  const handleDashboardUpdate = useCallback((eventData) => {
    const data = eventData.data || eventData
    if (data) {
      setDashboardStats(data)
      setRefreshCount((c) => c + 1)
      if (data.live_sessions !== undefined) {
        setLiveCount(data.live_sessions)
      }
    }
  }, [])

  useSocket('new_attack', handleNewAttack)
  useSocket('attack_update', handleAttackUpdate)
  useSocket('threat_alert', handleThreatAlert)
  useSocket('dashboard_update', handleDashboardUpdate)

  const dismissAlert = (alertId) => {
    setAlerts((prev) => prev.filter((a) => a.id !== alertId))
  }

  const isNewAttack = (sessionId) => newAttackIds.current.has(sessionId)

  return {
    attacks,
    setAttacks,
    alerts,
    liveCount,
    dashboardStats,
    refreshCount,
    dismissAlert,
    isNewAttack,
  }
}
