import { useState, useEffect, useRef } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  Server, Shield, Database, Cpu, HardDrive, Terminal,
  Radio, RefreshCw, Key, Download, LogOut, CheckCircle, AlertTriangle,
  Activity, Cloud, Wifi, Code, Copy, Check, Eye, Lock, Globe,
  Layers, Settings, ChevronRight, CornerDownLeft, AlertCircle, X, Search
} from 'lucide-react'

const DUMMY_ENV_SECRETS = `
# ===================================================
# TECHNOVA ENTERPRISE INFRASTRUCTURE SECRETS
# ENVIRONMENT: PRODUCTION (CRITICAL)
# ===================================================

# Database Credentials
DB_HOST=db-primary.prod.technova.internal
DB_PORT=5432
DB_NAME=technova_production
DB_USER=pg_root_admin
DB_PASSWORD=TechNova_P@ssw0rd_2026!#
DB_SSL_MODE=require

# AWS Master Credentials
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE
AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
AWS_KMS_KEY_ARN=arn:aws:kms:us-east-1:123456789012:key/12345678-1234-1234-1234-123456789012

# Cache & Redis Cluster
REDIS_URL=redis://:cache_root_sec123@redis-master.prod.technova.internal:6379/0
REDIS_CLUSTER_AUTH=Red!s_M@ster_Auth_Key_2026

# Payment Gateway Secrets
STRIPE_LIVE_KEY=sk_live_51M0x7K8s9L1m2N3o4P5q6R7s8T9u0V1w2X3y4Z
STRIPE_WEBHOOK_SECRET=whsec_991823749123849128394182934812934

# Security Tokens & Master Keys
JWT_SECRET=super_secret_master_jwt_key_9948127391823912
ENCRYPTION_PEPPER=Pepper_Secret_2026_TechNova_Prod
`.trim()

const DUMMY_RSA_PEM = `
-----BEGIN RSA PRIVATE KEY-----
MIIEowIBAAKCAQEAz8q/7Z91b1Kx...[REDACTED RSA MASTER KEY]...
vQ92Z1R8m4K2L5N6P7Q8R9S0T1U2V3W4X5Y6Z7a8b9c0d1e2f3g4h5i6j7k8
l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3A4B5C6D7E8F9G0H1I2J3K4L5M6N7O8
P9Q0R1S2T3U4V5W6X7Y8Z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8
-----END RSA PRIVATE KEY-----
`.trim()

export default function DecoyAdminConsole() {
  const [activeTab, setActiveTab] = useState('overview')
  const [actionNotice, setActionNotice] = useState('')
  const [currentTime, setCurrentTime] = useState(new Date())

  // Modal states
  const [secretsModalOpen, setSecretsModalOpen] = useState(false)
  const [sslModalOpen, setSslModalOpen] = useState(false)
  const [terminalModalOpen, setTerminalModalOpen] = useState(false)
  const [copiedSecrets, setCopiedSecrets] = useState(false)

  // Interactive Terminal Emulator State
  const [terminalInput, setTerminalInput] = useState('')
  const [terminalHistory, setTerminalHistory] = useState([
    { type: 'sys', text: 'TechNova Cloud Shell v4.8.2 (x86_64-pc-linux-gnu)' },
    { type: 'sys', text: 'Type "help" for a list of available administrative commands.\n' }
  ])
  const terminalEndRef = useRef(null)

  useEffect(() => {
    const timer = setInterval(() => setCurrentTime(new Date()), 1000)
    return () => clearInterval(timer)
  }, [])

  useEffect(() => {
    terminalEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [terminalHistory, terminalModalOpen])

  const logAction = (actionName, details = {}) => {
    setActionNotice(`Executing command: ${actionName}...`)
    try {
      fetch('/api/trap/log', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          type: 'attacker_post_compromise_action',
          action: actionName,
          details,
          timestamp: new Date().toISOString()
        })
      })
    } catch {}
    setTimeout(() => setActionNotice(`Command executed: ${actionName} (Status: Simulated Output)`), 1500)
  }

  const handleLogout = () => {
    localStorage.removeItem('technova_decoy_session')
    window.location.href = '/admin-login'
  }

  const downloadFile = (filename, content, actionType) => {
    logAction(actionType, { filename })
    const element = document.createElement('a')
    const file = new Blob([content], { type: 'text/plain' })
    element.href = URL.createObjectURL(file)
    element.download = filename
    document.body.appendChild(element)
    element.click()
    document.body.removeChild(element)
  }

  const copySecretsToClipboard = () => {
    navigator.clipboard.writeText(DUMMY_ENV_SECRETS)
    setCopiedSecrets(true)
    logAction('COPIED_PRODUCTION_ENV_TO_CLIPBOARD')
    setTimeout(() => setCopiedSecrets(false), 2000)
  }

  const handleTerminalSubmit = (e) => {
    e.preventDefault()
    const cmd = terminalInput.trim()
    if (!cmd) return

    // Append user input line
    const newHistory = [...terminalHistory, { type: 'prompt', text: `root@tn-cluster-east-01:~# ${cmd}` }]
    const lowerCmd = cmd.toLowerCase()

    // Telemetry log
    logAction('TERMINAL_COMMAND_EXECUTED', { command: cmd })

    let output = ''
    if (lowerCmd === 'help' || lowerCmd === '?') {
      output = `Available administrative commands:
  ls, dir         - List directory contents
  cat <file>      - Read file contents (e.g. cat production.env)
  whoami          - Display current user identity
  id              - Display user IDs and group memberships
  uname -a        - Display Linux system kernel information
  ps aux, top     - Display active running processes
  ifconfig, ip a  - Display network interfaces
  clear           - Clear terminal screen`
    } else if (lowerCmd === 'ls' || lowerCmd === 'dir') {
      output = `production.env    ssl_master.key    db_secrets.dump    app.py    config.json    ssl/`
    } else if (lowerCmd.startsWith('cat ')) {
      const filename = lowerCmd.replace('cat ', '').trim()
      if (filename === 'production.env' || filename === '.env') {
        output = DUMMY_ENV_SECRETS
      } else if (filename === 'ssl_master.key' || filename === 'ssl/master.key') {
        output = DUMMY_RSA_PEM
      } else if (filename === 'config.json') {
        output = `{\n  "environment": "production",\n  "cluster_id": "tn-cluster-east-01",\n  "region": "us-east-1",\n  "nodes": 5\n}`
      } else {
        output = `cat: ${filename}: Permission denied or file not found.`
      }
    } else if (lowerCmd === 'whoami') {
      output = 'root'
    } else if (lowerCmd === 'id') {
      output = 'uid=0(root) gid=0(root) groups=0(root)'
    } else if (lowerCmd === 'uname -a') {
      output = 'Linux tn-cluster-east-01 5.15.0-88-generic #98-Ubuntu SMP Mon Oct 2 15:18:56 UTC 2026 x86_64 GNU/Linux'
    } else if (lowerCmd === 'ps aux' || lowerCmd === 'top') {
      output = `USER       PID %CPU %MEM    VSZ   RSS TTY      STAT START   TIME COMMAND
root         1  0.1  0.4 168392  9420 ?        Ss   08:12   0:02 /sbin/init
postgres   412  2.4  4.2 849200 89200 ?        Ss   08:12   0:45 postgres: master
redis      520  0.8  1.1 249200 24100 ?        Ss   08:12   0:15 redis-server *:6379
root       890  1.2  2.8 450120 58400 ?        S    08:14   0:22 gunicorn app:main
root      1042  0.0  0.2  18400  4100 pts/0    Ss+  08:20   0:00 /bin/bash`
    } else if (lowerCmd === 'ifconfig' || lowerCmd === 'ip a') {
      output = `eth0: flags=4163<UP,BROADCAST,RUNNING,MULTICAST>  mtu 1500
        inet 10.0.4.12  netmask 255.255.255.0  broadcast 10.0.4.255
        rx_bytes: 489210482  tx_bytes: 894120934`
    } else if (lowerCmd === 'clear') {
      setTerminalHistory([])
      setTerminalInput('')
      return
    } else {
      output = `bash: ${cmd}: command not found. Type "help" for valid commands.`
    }

    newHistory.push({ type: 'output', text: output })
    setTerminalHistory(newHistory)
    setTerminalInput('')
  }

  const timeStr = currentTime.toLocaleTimeString('en-US', { hour12: false })

  return (
    <div className="min-h-screen text-slate-900 font-sans flex flex-col dot-grid-bg bg-slate-50">
      {/* ── Top Corporate Bar ── */}
      <header className="h-14 px-6 flex items-center justify-between sticky top-0 z-20 bg-white/95 backdrop-blur-md border-b border-slate-200 shadow-xs">
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-lg bg-blue-600 flex items-center justify-center shadow-xs">
              <Server size={18} className="text-white" />
            </div>
            <div>
              <h1 className="text-sm font-bold text-slate-900 tracking-tight flex items-center gap-2">
                TechNova Cloud Console
                <span className="text-[10px] bg-blue-100 text-blue-700 px-2 py-0.5 rounded font-mono font-bold">
                  PROD-US-EAST-1
                </span>
              </h1>
              <p className="text-[10px] text-slate-500 font-mono">NODE: TN-CLUSTER-EAST-01 • ROLE: SUPERADMIN</p>
            </div>
          </div>

          {/* Module Nav Tabs */}
          <nav className="hidden xl:flex items-center gap-1 ml-6 pl-6 border-l border-slate-200">
            {[
              { id: 'overview', label: 'Overview', icon: Activity },
              { id: 'instances', label: 'Compute Nodes', icon: Server },
              { id: 'databases', label: 'Databases & Secrets', icon: Database },
              { id: 'network', label: 'Network & Firewall', icon: Shield },
              { id: 'terminal', label: 'Web Shell TTY', icon: Terminal },
            ].map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-semibold transition cursor-pointer ${
                  activeTab === tab.id
                    ? 'bg-blue-50 text-blue-700 border border-blue-200'
                    : 'text-slate-600 hover:bg-slate-100 hover:text-slate-900'
                }`}
              >
                <tab.icon size={14} />
                <span>{tab.label}</span>
              </button>
            ))}
          </nav>
        </div>

        <div className="flex items-center gap-3">
          {/* Quick Terminal Launcher */}
          <button
            onClick={() => setTerminalModalOpen(true)}
            className="flex items-center gap-1.5 text-xs font-mono font-bold text-slate-700 bg-slate-100 hover:bg-slate-200 px-3 py-1.5 rounded-lg border border-slate-200 transition cursor-pointer"
          >
            <Terminal size={13} className="text-blue-600" />
            <span>Launch Web TTY</span>
          </button>

          {/* System Time */}
          <div className="hidden md:flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-slate-100 border border-slate-200">
            <Activity size={12} className="text-blue-600" />
            <span className="text-[11px] font-mono text-slate-700 font-medium">{timeStr}</span>
          </div>

          {/* Status */}
          <span className="text-[11px] font-semibold text-emerald-700 px-3 py-1 rounded-full bg-emerald-50 border border-emerald-200 flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
            Operational
          </span>

          {/* Logout */}
          <button
            onClick={handleLogout}
            className="flex items-center gap-2 text-xs font-semibold text-slate-700 hover:text-slate-900 bg-slate-100 hover:bg-slate-200 px-3 py-1.5 rounded-lg border border-slate-200 transition cursor-pointer"
          >
            <LogOut size={14} /> Exit
          </button>
        </div>
      </header>

      {/* Mobile Nav Bar */}
      <div className="xl:hidden flex items-center gap-1 p-2 bg-white border-b border-slate-200 overflow-x-auto">
        {[
          { id: 'overview', label: 'Overview', icon: Activity },
          { id: 'instances', label: 'Compute Nodes', icon: Server },
          { id: 'databases', label: 'Databases & Secrets', icon: Database },
          { id: 'network', label: 'Network', icon: Shield },
          { id: 'terminal', label: 'Terminal TTY', icon: Terminal },
        ].map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold whitespace-nowrap cursor-pointer ${
              activeTab === tab.id
                ? 'bg-blue-50 text-blue-700 border border-blue-200'
                : 'text-slate-600 hover:bg-slate-100'
            }`}
          >
            <tab.icon size={13} />
            <span>{tab.label}</span>
          </button>
        ))}
      </div>

      {/* ── Main Container ── */}
      <div className="flex-1 p-6 max-w-7xl mx-auto w-full space-y-6">
        {/* Banner Alert */}
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          className="p-4 rounded-xl bg-blue-50/80 border border-blue-200 flex flex-col md:flex-row md:items-center justify-between gap-3 shadow-xs"
        >
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-lg bg-blue-600/10 flex items-center justify-center flex-shrink-0">
              <Shield className="text-blue-600" size={18} />
            </div>
            <div>
              <p className="text-xs font-bold text-slate-900">Privileged Administrative Session Authorized</p>
              <p className="text-xs text-slate-600 mt-0.5">Full root access granted to core infrastructure, database secret stores, and SSL master keys.</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={() => setSecretsModalOpen(true)}
              className="text-xs font-bold bg-blue-600 hover:bg-blue-700 text-white px-3.5 py-1.5 rounded-lg transition cursor-pointer flex items-center gap-1.5 shadow-xs"
            >
              <Key size={14} /> View Production .env Secrets
            </button>
          </div>
        </motion.div>

        {/* Action Notice */}
        <AnimatePresence>
          {actionNotice && (
            <motion.div
              initial={{ opacity: 0, y: -8, height: 0 }}
              animate={{ opacity: 1, y: 0, height: 'auto' }}
              exit={{ opacity: 0, y: -8, height: 0 }}
              className="p-3 rounded-lg text-xs font-mono flex items-center gap-2 font-medium bg-blue-50 border border-blue-200 text-blue-800"
            >
              <RefreshCw size={14} className="animate-spin text-blue-600" />
              <span>{actionNotice}</span>
            </motion.div>
          )}
        </AnimatePresence>

        {/* ── TAB CONTENT ── */}
        {activeTab === 'overview' && (
          <div className="space-y-6">
            {/* Top Metric Cards */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
              {[
                { label: 'CPU Utilization', value: '42.8%', pct: 42.8, icon: Cpu, color: 'bg-blue-600' },
                { label: 'Memory Allocated', value: '24.6 GB / 32 GB', pct: 76, icon: HardDrive, color: 'bg-indigo-600' },
                { label: 'Active DB Connections', value: '14 Active', pct: 35, icon: Database, color: 'bg-emerald-600' },
                { label: 'Primary Gateway', value: '1.4 GB/s', pct: 60, icon: Radio, color: 'bg-amber-600' },
              ].map((metric, idx) => (
                <div
                  key={idx}
                  className="bg-white border border-slate-200 rounded-xl p-4 shadow-xs hover:border-slate-300 transition"
                >
                  <div className="flex justify-between items-center text-xs text-slate-500 font-medium mb-3">
                    <span>{metric.label}</span>
                    <div className="w-8 h-8 rounded-lg bg-slate-100 flex items-center justify-center">
                      <metric.icon size={16} className="text-slate-700" />
                    </div>
                  </div>
                  <p className="text-xl font-bold text-slate-900 font-mono mb-3">{metric.value}</p>
                  <div className="w-full h-2 bg-slate-100 rounded-full overflow-hidden">
                    <div className={`h-full rounded-full ${metric.color}`} style={{ width: `${metric.pct}%` }} />
                  </div>
                </div>
              ))}
            </div>

            {/* Core Operations Grid */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              {/* Operations Panel */}
              <div className="lg:col-span-2 bg-white border border-slate-200 rounded-xl p-6 space-y-4 shadow-xs">
                <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2 pb-2 border-b border-slate-100">
                  <div className="w-7 h-7 rounded-md bg-blue-50 flex items-center justify-center">
                    <Terminal size={15} className="text-blue-600" />
                  </div>
                  Core Infrastructure Actions
                </h3>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  {[
                    {
                      onClick: () => setSecretsModalOpen(true),
                      icon: Database,
                      title: 'Export Core Database Secrets',
                      desc: 'Dump PostgreSQL credentials, password hashes & config keys.',
                      iconColor: 'text-blue-600 bg-blue-50',
                    },
                    {
                      onClick: () => setSslModalOpen(true),
                      icon: Key,
                      title: 'Export SSL Private Master Key',
                      desc: 'Download RSA 4096-bit master domain SSL certificates.',
                      iconColor: 'text-indigo-600 bg-indigo-50',
                    },
                    {
                      onClick: () => logAction('REBOOT_PRIMARY_CLUSTER_NODE'),
                      icon: AlertTriangle,
                      title: 'Restart Primary Node',
                      desc: 'Initiate graceful reboot of TN-CLUSTER-EAST-01.',
                      iconColor: 'text-amber-600 bg-amber-50',
                    },
                    {
                      onClick: () => logAction('FLUSH_FIREWALL_RULES'),
                      icon: Shield,
                      title: 'Disable Security Firewall',
                      desc: 'Temporarily flush iptables and perimeter defense rules.',
                      iconColor: 'text-red-600 bg-red-50',
                    },
                  ].map((op, idx) => (
                    <button
                      key={idx}
                      onClick={op.onClick}
                      className="p-4 rounded-xl text-left bg-slate-50 hover:bg-slate-100/80 border border-slate-200 transition cursor-pointer group flex flex-col justify-between"
                    >
                      <div className="flex items-center justify-between mb-3">
                        <div className={`w-8 h-8 rounded-lg flex items-center justify-center ${op.iconColor}`}>
                          <op.icon size={16} />
                        </div>
                        <Download size={14} className="text-slate-400 group-hover:text-blue-600 transition-colors" />
                      </div>
                      <div>
                        <p className="text-xs font-bold text-slate-900 mb-1">{op.title}</p>
                        <p className="text-[11px] text-slate-500 font-normal leading-relaxed">{op.desc}</p>
                      </div>
                    </button>
                  ))}
                </div>
              </div>

              {/* Live Console Stream */}
              <div className="bg-white border border-slate-200 rounded-xl p-6 space-y-4 shadow-xs flex flex-col">
                <div className="flex items-center justify-between pb-2 border-b border-slate-100">
                  <h3 className="text-sm font-bold text-slate-900">Live Activity Log</h3>
                  <div className="flex items-center gap-1.5 bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200">
                    <Wifi size={10} className="text-emerald-600" />
                    <span className="text-[10px] font-mono text-emerald-700 font-semibold">LIVE</span>
                  </div>
                </div>

                <div className="p-4 rounded-lg font-mono text-xs leading-relaxed space-y-1.5 h-[260px] overflow-y-auto bg-slate-900 text-slate-100 border border-slate-800">
                  <div className="text-[9px] text-slate-400 tracking-wider mb-2 pb-1.5 border-b border-slate-800">
                    TECHNOVA://CONSOLE — ACTIVE SESSION
                  </div>
                  <p className="text-emerald-400">[SYSTEM] Session initialized for root</p>
                  <p className="text-blue-300">[AUTH] Granted token decoy_admin_session_token_991823</p>
                  <p className="text-slate-400">[IP] Client Address: Connected</p>
                  <p className="text-slate-400">[STATUS] Cluster Node 1: Online</p>
                  <p className="text-slate-400">[STATUS] Cluster Node 2: Online</p>
                  <p className="text-amber-400">[SECURITY] Log level set to VERBOSE</p>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* ── COMPUTE INSTANCES TAB ── */}
        {activeTab === 'instances' && (
          <div className="bg-white border border-slate-200 rounded-xl p-6 space-y-4 shadow-xs">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-4 border-b border-slate-100">
              <div>
                <h3 className="text-base font-bold text-slate-900">Production Servers & Instances</h3>
                <p className="text-xs text-slate-500 mt-0.5">Active bare-metal & EC2 cluster node inventory.</p>
              </div>
              <button
                onClick={() => setTerminalModalOpen(true)}
                className="bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold px-4 py-2 rounded-lg flex items-center gap-2 cursor-pointer transition"
              >
                <Terminal size={14} /> Open Cluster Shell TTY
              </button>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead>
                  <tr className="bg-slate-50 border-b border-slate-200 text-slate-500 font-semibold uppercase tracking-wider">
                    <th className="p-3">Instance ID & Hostname</th>
                    <th className="p-3">Private IP</th>
                    <th className="p-3">OS / Environment</th>
                    <th className="p-3">Status</th>
                    <th className="p-3">CPU / RAM Load</th>
                    <th className="p-3 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 font-medium">
                  {[
                    { id: 'tn-web-prod-01', ip: '10.0.4.12', os: 'Ubuntu 22.04 LTS', status: 'Active', cpu: '38%', ram: '4.2 GB' },
                    { id: 'tn-db-primary-01', ip: '10.0.4.15', os: 'PostgreSQL 15 Cluster', status: 'Active', cpu: '54%', ram: '16.8 GB' },
                    { id: 'tn-redis-cache-01', ip: '10.0.4.18', os: 'Redis 7.0 Sentinel', status: 'Active', cpu: '18%', ram: '3.1 GB' },
                    { id: 'tn-worker-celery-01', ip: '10.0.4.22', os: 'Python 3.11 Worker', status: 'Active', cpu: '29%', ram: '2.0 GB' },
                    { id: 'tn-bastion-gateway', ip: '10.0.1.5', os: 'Alpine Linux TTY', status: 'Active', cpu: '8%', ram: '512 MB' },
                  ].map((srv, idx) => (
                    <tr key={idx} className="hover:bg-slate-50 transition">
                      <td className="p-3 font-mono font-bold text-slate-900">{srv.id}</td>
                      <td className="p-3 font-mono text-slate-600">{srv.ip}</td>
                      <td className="p-3 text-slate-700">{srv.os}</td>
                      <td className="p-3">
                        <span className="bg-emerald-50 text-emerald-700 border border-emerald-200 px-2.5 py-0.5 rounded-full font-bold text-[10px] inline-flex items-center gap-1">
                          <span className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
                          {srv.status}
                        </span>
                      </td>
                      <td className="p-3 font-mono text-slate-600">{srv.cpu} / {srv.ram}</td>
                      <td className="p-3 text-right">
                        <button
                          onClick={() => {
                            logAction('ATTACKER_LAUNCHED_SSH_SHELL', { server: srv.id })
                            setTerminalModalOpen(true)
                          }}
                          className="bg-slate-100 hover:bg-slate-200 text-slate-700 hover:text-slate-900 px-3 py-1 rounded-md text-xs font-semibold transition cursor-pointer"
                        >
                          SSH Shell
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* ── DATABASES & SECRETS TAB ── */}
        {activeTab === 'databases' && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div className="bg-white border border-slate-200 rounded-xl p-6 space-y-4 shadow-xs">
              <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2 pb-2 border-b border-slate-100">
                <Database className="text-blue-600" size={16} /> Production Database Clusters
              </h3>

              <div className="space-y-3 text-xs">
                <div className="p-4 rounded-lg bg-slate-50 border border-slate-200 space-y-2">
                  <div className="flex justify-between items-center font-bold text-slate-900">
                    <span>PostgreSQL Master Database</span>
                    <span className="text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded font-mono text-[10px]">CONNECTED</span>
                  </div>
                  <p className="font-mono text-slate-600 text-[11px]">postgresql://pg_root_admin:***@10.0.4.15:5432/technova_production</p>
                  <button
                    onClick={() => setSecretsModalOpen(true)}
                    className="mt-2 text-xs text-blue-600 hover:underline font-semibold flex items-center gap-1 cursor-pointer"
                  >
                    <Key size={12} /> View Connection Secret Keys →
                  </button>
                </div>

                <div className="p-4 rounded-lg bg-slate-50 border border-slate-200 space-y-2">
                  <div className="flex justify-between items-center font-bold text-slate-900">
                    <span>Redis Cache Sentinel Cluster</span>
                    <span className="text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded font-mono text-[10px]">ACTIVE</span>
                  </div>
                  <p className="font-mono text-slate-600 text-[11px]">redis://:cache_root_sec123@10.0.4.18:6379/0</p>
                </div>
              </div>
            </div>

            <div className="bg-white border border-slate-200 rounded-xl p-6 space-y-4 shadow-xs">
              <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2 pb-2 border-b border-slate-100">
                <Key className="text-indigo-600" size={16} /> AWS KMS & Master Secrets
              </h3>

              <div className="p-4 rounded-lg bg-slate-900 text-slate-100 font-mono text-xs space-y-2">
                <p className="text-slate-400">// AWS Secrets Manager Payload</p>
                <p className="text-emerald-400">AWS_ACCESS_KEY_ID: AKIAIOSFODNN7EXAMPLE</p>
                <p className="text-emerald-400">AWS_SECRET_ACCESS_KEY: wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY</p>
                <p className="text-purple-300">JWT_SECRET: super_secret_master_jwt_key_994812739</p>

                <div className="pt-3 border-t border-slate-800 flex gap-2">
                  <button
                    onClick={copySecretsToClipboard}
                    className="bg-blue-600 hover:bg-blue-700 text-white px-3 py-1.5 rounded text-xs font-sans font-semibold flex items-center gap-1.5 cursor-pointer"
                  >
                    {copiedSecrets ? <Check size={13} /> : <Copy size={13} />}
                    {copiedSecrets ? 'Copied!' : 'Copy Credentials'}
                  </button>
                  <button
                    onClick={() => downloadFile('production.env', DUMMY_ENV_SECRETS, 'DOWNLOADED_ENV_FILE')}
                    className="bg-slate-800 hover:bg-slate-700 text-slate-200 px-3 py-1.5 rounded text-xs font-sans font-semibold flex items-center gap-1.5 cursor-pointer"
                  >
                    <Download size={13} /> Download .env
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* ── NETWORK & FIREWALL TAB ── */}
        {activeTab === 'network' && (
          <div className="bg-white border border-slate-200 rounded-xl p-6 space-y-4 shadow-xs">
            <h3 className="text-base font-bold text-slate-900">Perimeter Security & VPC Subnets</h3>
            <p className="text-xs text-slate-500">Virtual Private Cloud (VPC) ingress/egress rules and security group policies.</p>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-2">
              {[
                { name: 'VPC Router', val: 'vpc-0a891f2c4d9e (10.0.0.0/16)', status: 'Online' },
                { name: 'Public Ingress Subnet', val: 'subnet-0123abcd (10.0.1.0/24)', status: 'Active' },
                { name: 'Private Database Subnet', val: 'subnet-0987efgh (10.0.4.0/24)', status: 'Isolated' },
              ].map((net, i) => (
                <div key={i} className="p-4 rounded-lg bg-slate-50 border border-slate-200">
                  <p className="text-xs font-bold text-slate-900 mb-1">{net.name}</p>
                  <p className="text-[11px] font-mono text-slate-600 mb-2">{net.val}</p>
                  <span className="text-[10px] font-mono bg-blue-100 text-blue-800 px-2 py-0.5 rounded">{net.status}</span>
                </div>
              ))}
            </div>

            <div className="pt-4 border-t border-slate-100 flex justify-end">
              <button
                onClick={() => logAction('FLUSH_FIREWALL_RULES')}
                className="bg-red-600 hover:bg-red-700 text-white text-xs font-bold px-4 py-2 rounded-lg flex items-center gap-2 cursor-pointer transition shadow-xs"
              >
                <Shield size={14} /> Disable Security Firewall (Flush iptables)
              </button>
            </div>
          </div>
        )}

        {/* ── TERMINAL TTY TAB ── */}
        {activeTab === 'terminal' && (
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-xl space-y-4 font-mono text-xs">
            <div className="flex items-center justify-between pb-3 border-b border-slate-800">
              <div className="flex items-center gap-2">
                <Terminal className="text-blue-400" size={16} />
                <span className="text-slate-200 font-bold">TechNova Interactive Root Shell (TTY)</span>
              </div>
              <span className="text-[10px] text-emerald-400 bg-emerald-950/60 px-2.5 py-0.5 rounded border border-emerald-800">
                CONNECTED: root@10.0.4.12
              </span>
            </div>

            <div className="h-[380px] overflow-y-auto space-y-2 pr-2">
              {terminalHistory.map((item, index) => (
                <div key={index} className="whitespace-pre-wrap leading-relaxed">
                  {item.type === 'prompt' && (
                    <span className="text-blue-400 font-bold">{item.text}</span>
                  )}
                  {item.type === 'sys' && (
                    <span className="text-slate-400">{item.text}</span>
                  )}
                  {item.type === 'output' && (
                    <span className="text-slate-200">{item.text}</span>
                  )}
                </div>
              ))}
              <div ref={terminalEndRef} />
            </div>

            <form onSubmit={handleTerminalSubmit} className="pt-3 border-t border-slate-800 flex items-center gap-2">
              <span className="text-blue-400 font-bold whitespace-nowrap">root@tn-cluster-east-01:~#</span>
              <input
                type="text"
                value={terminalInput}
                onChange={(e) => setTerminalInput(e.target.value)}
                placeholder="Type 'help' for commands..."
                className="flex-1 bg-transparent text-slate-100 outline-none font-mono text-xs"
                autoFocus
              />
              <button type="submit" className="text-slate-400 hover:text-blue-400">
                <CornerDownLeft size={14} />
              </button>
            </form>
          </div>
        )}
      </div>

      {/* ── MODALS ── */}

      {/* 1. Secrets Viewer Modal */}
      <AnimatePresence>
        {secretsModalOpen && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-xs">
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              className="bg-white border border-slate-200 rounded-2xl shadow-2xl max-w-2xl w-full overflow-hidden"
            >
              <div className="p-4 bg-slate-900 text-slate-100 flex items-center justify-between border-b border-slate-800">
                <div className="flex items-center gap-2">
                  <Key size={16} className="text-blue-400" />
                  <h3 className="font-bold text-sm font-mono">production.env — Confidential Secrets</h3>
                </div>
                <button
                  onClick={() => setSecretsModalOpen(false)}
                  className="text-slate-400 hover:text-white p-1 rounded cursor-pointer"
                >
                  <X size={18} />
                </button>
              </div>

              <div className="p-5 bg-slate-950 font-mono text-xs text-emerald-400 h-[340px] overflow-y-auto leading-relaxed">
                <pre>{DUMMY_ENV_SECRETS}</pre>
              </div>

              <div className="p-4 bg-slate-50 border-t border-slate-200 flex items-center justify-between">
                <p className="text-xs text-slate-500">Access to these keys is monitored and audited.</p>
                <div className="flex items-center gap-2">
                  <button
                    onClick={copySecretsToClipboard}
                    className="bg-slate-200 hover:bg-slate-300 text-slate-800 text-xs font-semibold px-3 py-2 rounded-lg flex items-center gap-1.5 cursor-pointer"
                  >
                    {copiedSecrets ? <Check size={14} /> : <Copy size={14} />}
                    {copiedSecrets ? 'Copied' : 'Copy'}
                  </button>
                  <button
                    onClick={() => {
                      downloadFile('production.env', DUMMY_ENV_SECRETS, 'DOWNLOADED_PRODUCTION_ENV')
                      setSecretsModalOpen(false)
                    }}
                    className="bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold px-4 py-2 rounded-lg flex items-center gap-1.5 cursor-pointer shadow-xs"
                  >
                    <Download size={14} /> Download .env File
                  </button>
                </div>
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>

      {/* 2. SSL Private Key Viewer Modal */}
      <AnimatePresence>
        {sslModalOpen && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-xs">
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              className="bg-white border border-slate-200 rounded-2xl shadow-2xl max-w-xl w-full overflow-hidden"
            >
              <div className="p-4 bg-slate-900 text-slate-100 flex items-center justify-between border-b border-slate-800">
                <div className="flex items-center gap-2">
                  <Lock size={16} className="text-indigo-400" />
                  <h3 className="font-bold text-sm font-mono">ssl_master_key.pem — RSA 4096 Key</h3>
                </div>
                <button
                  onClick={() => setSslModalOpen(false)}
                  className="text-slate-400 hover:text-white p-1 rounded cursor-pointer"
                >
                  <X size={18} />
                </button>
              </div>

              <div className="p-5 bg-slate-950 font-mono text-xs text-purple-300 h-[260px] overflow-y-auto leading-relaxed">
                <pre>{DUMMY_RSA_PEM}</pre>
              </div>

              <div className="p-4 bg-slate-50 border-t border-slate-200 flex items-center justify-between">
                <p className="text-xs text-slate-500">Master domain wildcard SSL certificate key.</p>
                <button
                  onClick={() => {
                    downloadFile('ssl_master_key.pem', DUMMY_RSA_PEM, 'DOWNLOADED_SSL_PEM_KEY')
                    setSslModalOpen(false)
                  }}
                  className="bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-semibold px-4 py-2 rounded-lg flex items-center gap-1.5 cursor-pointer shadow-xs"
                >
                  <Download size={14} /> Download .pem Key
                </button>
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>

      {/* 3. Interactive Web Terminal Modal */}
      <AnimatePresence>
        {terminalModalOpen && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/70 backdrop-blur-xs">
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              className="bg-slate-950 border border-slate-800 rounded-2xl shadow-2xl max-w-3xl w-full overflow-hidden flex flex-col h-[520px]"
            >
              <div className="p-4 bg-slate-900 text-slate-100 flex items-center justify-between border-b border-slate-800">
                <div className="flex items-center gap-2">
                  <Terminal size={16} className="text-blue-400" />
                  <h3 className="font-bold text-sm font-mono">root@tn-cluster-east-01:~ (Interactive TTY Shell)</h3>
                </div>
                <button
                  onClick={() => setTerminalModalOpen(false)}
                  className="text-slate-400 hover:text-white p-1 rounded cursor-pointer"
                >
                  <X size={18} />
                </button>
              </div>

              <div className="flex-1 p-4 font-mono text-xs text-slate-100 overflow-y-auto space-y-2">
                {terminalHistory.map((item, index) => (
                  <div key={index} className="whitespace-pre-wrap leading-relaxed">
                    {item.type === 'prompt' && (
                      <span className="text-blue-400 font-bold">{item.text}</span>
                    )}
                    {item.type === 'sys' && (
                      <span className="text-slate-400">{item.text}</span>
                    )}
                    {item.type === 'output' && (
                      <span className="text-slate-200">{item.text}</span>
                    )}
                  </div>
                ))}
                <div ref={terminalEndRef} />
              </div>

              <form onSubmit={handleTerminalSubmit} className="p-4 bg-slate-900 border-t border-slate-800 flex items-center gap-2">
                <span className="text-blue-400 font-bold whitespace-nowrap font-mono text-xs">root@tn-cluster-east-01:~#</span>
                <input
                  type="text"
                  value={terminalInput}
                  onChange={(e) => setTerminalInput(e.target.value)}
                  placeholder="Type 'cat production.env', 'ls', 'ps aux'..."
                  className="flex-1 bg-transparent text-slate-100 outline-none font-mono text-xs"
                  autoFocus
                />
                <button type="submit" className="text-slate-400 hover:text-blue-400">
                  <CornerDownLeft size={16} />
                </button>
              </form>
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </div>
  )
}
