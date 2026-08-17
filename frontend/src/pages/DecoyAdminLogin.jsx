import { useState } from 'react'
import { motion } from 'framer-motion'
import { Shield, Lock, User, AlertCircle, ArrowRight, Server, Cloud } from 'lucide-react'

export default function DecoyAdminLogin() {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)

    try {
      const res = await fetch('/api/trap/admin-login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password })
      })

      const data = await res.json()

      if (res.ok && data.success) {
        localStorage.setItem('technova_decoy_session', data.token || 'granted')
        window.location.href = '/decoy-admin-dashboard'
      } else {
        setError(data.error || data.message || 'Invalid username or password')
      }
    } catch (err) {
      setError('Connection error. Security server unreachable.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen text-[#0F172A] flex items-center justify-center p-4 font-sans relative overflow-hidden dot-grid-bg">
      {/* Soft corporate background ambient glows */}
      <motion.div
        animate={{
          x: [0, 20, -15, 0],
          y: [0, -15, 10, 0],
        }}
        transition={{ duration: 18, repeat: Infinity, ease: 'easeInOut' }}
        className="decoy-orb absolute pointer-events-none"
        style={{
          top: '15%',
          left: '20%',
          width: '450px',
          height: '450px',
          background: 'radial-gradient(circle, rgba(37, 99, 235, 0.08), transparent 70%)',
        }}
      />
      <motion.div
        animate={{
          x: [0, -20, 15, 0],
          y: [0, 15, -20, 0],
        }}
        transition={{ duration: 22, repeat: Infinity, ease: 'easeInOut' }}
        className="decoy-orb absolute pointer-events-none"
        style={{
          bottom: '10%',
          right: '15%',
          width: '400px',
          height: '400px',
          background: 'radial-gradient(circle, rgba(96, 165, 250, 0.08), transparent 70%)',
        }}
      />

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4 }}
        className="w-full max-w-md relative z-10"
      >
        {/* Main Card */}
        <div className="bg-white rounded-2xl border border-slate-200 shadow-[0_8px_30px_rgb(0,0,0,0.04)] overflow-hidden relative">
          {/* Top Bar Accent */}
          <div className="absolute top-0 left-0 right-0 h-1.5 bg-gradient-to-r from-blue-600 via-blue-500 to-indigo-600 z-20" />

          <div className="p-8 pt-10">
            {/* Logo & Branding */}
            <div className="flex flex-col items-center text-center mb-8 mt-2">
              <div
                className="w-14 h-14 rounded-2xl bg-gradient-to-br from-blue-600 to-indigo-700 flex items-center justify-center mb-4 shadow-lg shadow-blue-600/20 border border-blue-500/30"
              >
                <Shield className="w-7 h-7 text-white" />
              </div>

              <h1 className="text-2xl font-bold tracking-tight text-slate-900 mb-1">
                TechNova Solutions
              </h1>
              <div className="flex items-center justify-center gap-1.5 px-3 py-1 rounded-full bg-slate-50 border border-slate-200">
                <Server size={12} className="text-slate-500" />
                <p className="text-[11px] text-slate-600 font-mono font-medium tracking-wide">
                  Enterprise Infrastructure Console v4.2
                </p>
              </div>
            </div>

            {/* Error Message */}
            {error && (
              <motion.div
                initial={{ opacity: 0, y: -8 }}
                animate={{ opacity: 1, y: 0 }}
                className="mb-6 p-3.5 rounded-xl flex items-center gap-2.5 text-xs font-medium bg-red-50 border border-red-200 text-red-700"
              >
                <AlertCircle size={16} className="flex-shrink-0 text-red-600" />
                <span>{error}</span>
              </motion.div>
            )}

            {/* Login Form */}
            <form onSubmit={handleSubmit} action="/api/trap/admin-login" method="POST" className="space-y-5">
              <div className="space-y-1.5">
                <label className="block text-xs font-semibold text-slate-700 ml-1">
                  Administrator Username
                </label>
                <div className="flex items-center bg-slate-50 border border-slate-300 rounded-xl overflow-hidden focus-within:bg-white focus-within:border-blue-500 focus-within:ring-4 focus-within:ring-blue-500/10 transition-all shadow-sm">
                  <div className="pl-3.5 pr-2.5 text-slate-400 flex items-center justify-center shrink-0">
                    <User size={16} />
                  </div>
                  <input
                    type="text"
                    name="username"
                    value={username}
                    onChange={(e) => setUsername(e.target.value)}
                    placeholder="e.g. admin"
                    required
                    className="w-full py-2.5 pr-4 text-sm text-slate-900 bg-transparent outline-none font-sans placeholder:text-slate-400"
                    style={{ border: 'none', boxShadow: 'none' }}
                  />
                </div>
              </div>

              <div className="space-y-1.5">
                <label className="block text-xs font-semibold text-slate-700 ml-1">
                  Password
                </label>
                <div className="flex items-center bg-slate-50 border border-slate-300 rounded-xl overflow-hidden focus-within:bg-white focus-within:border-blue-500 focus-within:ring-4 focus-within:ring-blue-500/10 transition-all shadow-sm">
                  <div className="pl-3.5 pr-2.5 text-slate-400 flex items-center justify-center shrink-0">
                    <Lock size={16} />
                  </div>
                  <input
                    type="password"
                    name="password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="••••••••••••"
                    required
                    className="w-full py-2.5 pr-4 text-sm text-slate-900 bg-transparent outline-none font-sans placeholder:text-slate-400"
                    style={{ border: 'none', boxShadow: 'none' }}
                  />
                </div>
              </div>

              <button
                type="submit"
                disabled={loading}
                className="w-full mt-2 py-3 px-4 rounded-xl text-sm font-semibold text-white bg-blue-600 hover:bg-blue-700 active:bg-blue-800 transition-all shadow-md shadow-blue-600/20 flex items-center justify-center gap-2 cursor-pointer disabled:opacity-50"
              >
                {loading ? (
                  <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                ) : (
                  <>
                    Sign In to Core Console
                    <ArrowRight size={16} />
                  </>
                )}
              </button>
            </form>

            {/* Footer */}
            <div className="mt-8 pt-5 text-center space-y-1.5 border-t border-slate-100">
              <div className="flex items-center justify-center gap-1.5">
                <Cloud size={13} className="text-slate-400" />
                <p className="text-[11px] text-slate-500 font-semibold tracking-wide uppercase">Protected Corporate System • All Access Logged</p>
              </div>
              <p className="text-[10px] font-mono text-slate-400">Server Node: TN-PROD-EAST-01</p>
            </div>
          </div>
        </div>
      </motion.div>
    </div>
  )
}
