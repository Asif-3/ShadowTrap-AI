import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { motion } from 'framer-motion'
import { Shield, Eye, EyeOff, AlertCircle, Fingerprint, Lock } from 'lucide-react'

export default function Login() {
  const [email, setEmail] = useState('admin@shadowtrap.ai')
  const [password, setPassword] = useState('ShadowTrap@2024')
  const [showPassword, setShowPassword] = useState(false)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const { login } = useAuth()
  const navigate = useNavigate()

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      await login(email, password)
      navigate('/sentinel')
    } catch (err) {
      setError(err.response?.data?.error || 'Invalid credentials')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div 
      className="min-h-screen flex items-center justify-center relative overflow-hidden p-6 cyber-grid-bg"
      style={{ backgroundColor: '#050908' }}
    >
      <motion.div
        initial={{ opacity: 0, y: 12, scale: 0.99 }}
        animate={{ opacity: 1, y: 0, scale: 1 }}
        transition={{ duration: 0.25 }}
        className="relative z-10 w-full max-w-md"
      >
        {/* Login Card */}
        <div
          className="rounded-xl p-8 sm:p-9 shadow-2xl border"
          style={{
            backgroundColor: '#0B1412',
            borderColor: 'rgba(0, 245, 160, 0.18)',
            boxShadow: '0 20px 50px rgba(0, 0, 0, 0.8), 0 0 20px rgba(0, 245, 160, 0.05)',
          }}
        >
          {/* Logo & Title */}
          <div className="text-center mb-7">
            <div
              className="w-14 h-14 mx-auto rounded-xl flex items-center justify-center mb-3.5 border"
              style={{
                backgroundColor: 'rgba(0, 245, 160, 0.12)',
                borderColor: 'rgba(0, 245, 160, 0.35)',
              }}
            >
              <Fingerprint size={26} className="text-[#00F5A0]" />
            </div>

            <h1 className="text-xl font-bold tracking-tight text-[#E8FFF6] font-sans">
              ShadowTrap Sentinel
            </h1>
            <p className="text-xs text-[#9BB7AD] mt-1 font-sans">
              Autonomous Cybersecurity Honeypot SOC Platform
            </p>
          </div>

          {/* Error Message Banner */}
          {error && (
            <motion.div
              initial={{ opacity: 0, y: -6 }}
              animate={{ opacity: 1, y: 0 }}
              className="flex items-center gap-2 p-3 rounded-lg mb-5 text-xs font-semibold bg-[rgba(255,77,103,0.12)] border border-[rgba(255,77,103,0.3)] text-[#FF4D67]"
            >
              <AlertCircle size={15} className="shrink-0 text-[#FF4D67]" />
              <span>{error}</span>
            </motion.div>
          )}

          {/* Authentication Form */}
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label
                htmlFor="login-email"
                className="block text-xs font-medium text-[#9BB7AD] mb-1.5 font-sans"
              >
                Analyst Email
              </label>
              <input
                id="login-email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="st-input font-mono text-xs"
                placeholder="analyst@shadowtrap.ai"
                required
              />
            </div>

            <div>
              <label
                htmlFor="login-password"
                className="block text-xs font-medium text-[#9BB7AD] mb-1.5 font-sans"
              >
                Access Password
              </label>
              <div className="relative">
                <input
                  id="login-password"
                  type={showPassword ? 'text' : 'password'}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="st-input font-mono text-xs pr-10"
                  placeholder="••••••••••••"
                  required
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-[#607A71] hover:text-[#00F5A0] transition cursor-pointer"
                >
                  {showPassword ? <EyeOff size={15} /> : <Eye size={15} />}
                </button>
              </div>
            </div>

            <div className="flex items-center justify-between pt-1">
              <label className="flex items-center gap-2 cursor-pointer select-none">
                <input type="checkbox" className="rounded accent-[#00F5A0] cursor-pointer" />
                <span className="text-xs text-[#9BB7AD] font-sans">
                  Remember Session
                </span>
              </label>
              <a
                href="/sentinel/forgot-password"
                className="text-xs text-[#00F5A0] hover:underline font-sans"
              >
                Forgot Password?
              </a>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full btn-primary justify-center h-10 mt-2 text-xs font-semibold"
            >
              {loading ? (
                <div className="w-4 h-4 border-2 border-[#050908] border-t-transparent rounded-full animate-spin" />
              ) : (
                <>
                  <Shield size={15} /> Authenticate Sentinel
                </>
              )}
            </button>
          </form>
        </div>

        {/* Footer Info */}
        <div className="text-center mt-5 space-y-1">
          <p className="text-[10px] text-[#607A71] font-mono">
            SENTINEL v2.5 SOC // TLS 1.3 ENCRYPTED GATEWAY
          </p>
        </div>
      </motion.div>
    </div>
  )
}
