import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import { Command } from 'cmdk'
import {
  Search, Shield, Radio, PlayCircle, FileText,
  BarChart3, Settings, Network, Cpu, Terminal, Eye
} from 'lucide-react'

export default function CommandPalette({ open, onOpenChange }) {
  const navigate = useNavigate()
  const [search, setSearch] = useState('')

  useEffect(() => {
    const down = (e) => {
      if (e.key === 'k' && (e.metaKey || e.ctrlKey)) {
        e.preventDefault()
        onOpenChange((prev) => !prev)
      }
    }
    document.addEventListener('keydown', down)
    return () => document.removeEventListener('keydown', down)
  }, [onOpenChange])

  const runCommand = (action) => {
    onOpenChange(false)
    action()
  }

  if (!open) return null

  return (
    <AnimatePresence>
      <div className="fixed inset-0 z-50 bg-[var(--color-overlay-bg)] backdrop-blur-sm flex items-start justify-center pt-24 px-4">
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          exit={{ opacity: 0, scale: 0.95 }}
          className="w-full max-w-xl glass-strong border border-[var(--color-border)] rounded-2xl shadow-2xl overflow-hidden"
        >
          <Command className="w-full bg-transparent">
            <div className="flex items-center border-b border-[var(--color-border)] px-4 py-3 gap-3">
              <Search size={18} className="text-[var(--color-text-muted)]" />
              <Command.Input
                value={search}
                onValueChange={setSearch}
                placeholder="Search attacks, IPs, commands, pages, or tools (Cmd+K)..."
                className="w-full bg-transparent outline-none text-sm text-[var(--color-text-primary)] placeholder-[var(--color-text-muted)]"
              />
            </div>

            <Command.List className="max-h-80 overflow-y-auto p-2 space-y-1">
              <Command.Empty className="py-6 text-center text-xs text-[var(--color-text-muted)]">
                No matching results found.
              </Command.Empty>

              <Command.Group heading="Navigation" className="text-[10px] font-bold text-[var(--color-text-muted)] uppercase px-2 py-1">
                <Command.Item
                  onSelect={() => runCommand(() => navigate('/sentinel'))}
                  className="flex items-center gap-3 px-3 py-2 rounded-xl text-xs text-[var(--color-text-primary)] hover:bg-[var(--color-primary-dim)] cursor-pointer"
                >
                  <Shield size={16} className="text-[var(--color-primary)]" /> SOC Dashboard
                </Command.Item>
                <Command.Item
                  onSelect={() => runCommand(() => navigate('/sentinel/trap-visitors'))}
                  className="flex items-center gap-3 px-3 py-2 rounded-xl text-xs text-[var(--color-text-primary)] hover:bg-[var(--color-primary-dim)] cursor-pointer"
                >
                  <Eye size={16} className="text-[var(--color-primary)]" /> Trap Visitors & Telemetry
                </Command.Item>
                <Command.Item
                  onSelect={() => runCommand(() => navigate('/sentinel/live-sessions'))}
                  className="flex items-center gap-3 px-3 py-2 rounded-xl text-xs text-[var(--color-text-primary)] hover:bg-[var(--color-primary-dim)] cursor-pointer"
                >
                  <Radio size={16} className="text-[var(--color-success)]" /> Live Attack Sessions
                </Command.Item>
                <Command.Item
                  onSelect={() => runCommand(() => navigate('/sentinel/knowledge-graph'))}
                  className="flex items-center gap-3 px-3 py-2 rounded-xl text-xs text-[var(--color-text-primary)] hover:bg-[var(--color-primary-dim)] cursor-pointer"
                >
                  <Network size={16} className="text-[var(--color-accent)]" /> Knowledge Graph
                </Command.Item>
                <Command.Item
                  onSelect={() => runCommand(() => navigate('/sentinel/mitre-matrix'))}
                  className="flex items-center gap-3 px-3 py-2 rounded-xl text-xs text-[var(--color-text-primary)] hover:bg-[var(--color-primary-dim)] cursor-pointer"
                >
                  <Cpu size={16} className="text-[var(--color-warning)]" /> MITRE ATT&CK Matrix
                </Command.Item>
                <Command.Item
                  onSelect={() => runCommand(() => navigate('/sentinel/copilot'))}
                  className="flex items-center gap-3 px-3 py-2 rounded-xl text-xs text-[var(--color-text-primary)] hover:bg-[var(--color-primary-dim)] cursor-pointer"
                >
                  <Terminal size={16} className="text-[var(--color-primary)]" /> LLM Security Copilot
                </Command.Item>
              </Command.Group>
            </Command.List>
          </Command>
        </motion.div>
      </div>
    </AnimatePresence>
  )
}
