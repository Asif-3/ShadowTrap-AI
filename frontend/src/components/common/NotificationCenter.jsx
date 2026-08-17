import { motion, AnimatePresence } from 'framer-motion'
import { AlertTriangle, ShieldAlert, X, Check } from 'lucide-react'

export default function NotificationCenter({ open, onClose, alerts = [], onDismiss }) {
  if (!open) return null

  return (
    <AnimatePresence>
      <div className="fixed inset-0 z-50 bg-[var(--color-overlay-bg)] backdrop-blur-xs flex justify-end">
        <motion.div
          initial={{ x: '100%' }}
          animate={{ x: 0 }}
          exit={{ x: '100%' }}
          transition={{ type: 'spring', damping: 25, stiffness: 300 }}
          className="w-full max-w-md h-full glass-strong border-l border-[var(--color-border)] p-5 flex flex-col justify-between"
        >
          <div>
            <div className="flex items-center justify-between pb-4 border-b border-[var(--color-border)] mb-4">
              <div className="flex items-center gap-2">
                <ShieldAlert className="text-[var(--color-danger)]" size={20} />
                <h2 className="text-sm font-bold text-[var(--color-text-primary)]">SOC Threat Notification Center</h2>
              </div>
              <button
                onClick={onClose}
                className="p-1 rounded-lg hover:bg-[var(--color-input-bg)] text-[var(--color-text-muted)] cursor-pointer"
              >
                <X size={18} />
              </button>
            </div>

            <div className="space-y-3 overflow-y-auto max-h-[calc(100vh-140px)]">
              {alerts.length === 0 ? (
                <div className="py-12 text-center text-xs text-[var(--color-text-muted)] space-y-2">
                  <Check size={28} className="mx-auto text-[var(--color-success)]" />
                  <p>All clear! No active high-risk alerts.</p>
                </div>
              ) : (
                alerts.map((alert) => (
                  <motion.div
                    key={alert.id}
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="p-3.5 rounded-xl border border-[var(--color-danger-dim)] bg-[var(--color-danger-dim)]/20 space-y-1 relative group"
                  >
                    <div className="flex items-center justify-between">
                      <span className="text-[10px] font-bold uppercase text-[var(--color-danger)] flex items-center gap-1">
                        <AlertTriangle size={12} /> {alert.severity || 'CRITICAL'}
                      </span>
                      <span className="text-[10px] text-[var(--color-text-muted)]">{alert.timestamp}</span>
                    </div>
                    <p className="text-xs font-bold text-[var(--color-text-primary)]">{alert.title}</p>
                    <p className="text-[11px] text-[var(--color-text-secondary)]">{alert.message}</p>

                    <button
                      onClick={() => onDismiss(alert.id)}
                      className="absolute top-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity p-1 text-[var(--color-text-muted)] hover:text-white cursor-pointer"
                    >
                      <X size={12} />
                    </button>
                  </motion.div>
                ))
              )}
            </div>
          </div>
        </motion.div>
      </div>
    </AnimatePresence>
  )
}
