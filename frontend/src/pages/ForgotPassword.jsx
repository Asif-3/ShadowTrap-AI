import { useState } from 'react'
import { authAPI } from '../api/client'
import { motion } from 'framer-motion'
import { Mail, ArrowLeft, Fingerprint } from 'lucide-react'
import { useNavigate } from 'react-router-dom'

export default function ForgotPassword() {
  const [email, setEmail] = useState('')
  const [sent, setSent] = useState(false)
  const [error, setError] = useState('')
  const navigate = useNavigate()

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    try {
      await authAPI.forgotPassword(email)
      setSent(true)
    } catch (err) {
      setError(err.response?.data?.error || 'Something went wrong')
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-[var(--color-bg-primary)] p-4">
      <motion.div initial={{ opacity: 0, y: 25 }} animate={{ opacity: 1, y: 0 }} className="w-full max-w-md">
        <div className="glass-strong rounded-2xl p-8 border border-[var(--color-border)] bg-[var(--color-bg-secondary)] shadow-xl">
          <div className="text-center mb-6">
            <div className="w-14 h-14 mx-auto rounded-2xl flex items-center justify-center mb-3 purple-gradient shadow-lg">
              <Fingerprint size={28} className="text-white" />
            </div>
            <h1 className="text-xl font-extrabold text-[var(--color-text-primary)]">Reset Password</h1>
            <p className="text-xs text-[var(--color-text-muted)] mt-1">Enter your email to receive a reset link</p>
          </div>

          {sent ? (
            <div className="text-center py-6">
              <Mail size={40} className="text-[var(--color-primary)] mx-auto mb-3" />
              <p className="text-sm font-semibold text-[var(--color-text-primary)]">Check your email for a reset link</p>
              <button onClick={() => navigate('/sentinel/login')} className="text-xs mt-4 font-bold text-[var(--color-primary)] hover:underline cursor-pointer">
                ← Back to Sentinel Login
              </button>
            </div>
          ) : (
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="text-xs font-semibold mb-2 block text-[var(--color-text-secondary)]">Email Address</label>
                <input type="email" value={email} onChange={(e) => setEmail(e.target.value)}
                  className="w-full px-4 py-3 rounded-xl text-xs outline-none bg-[var(--color-input-bg)] border border-[var(--color-border)] text-[var(--color-text-primary)]"
                  placeholder="admin@shadowtrap.ai" required />
              </div>
              {error && <p className="text-xs font-semibold text-[var(--color-danger)]">{error}</p>}
              <motion.button whileHover={{ scale: 1.01 }} whileTap={{ scale: 0.99 }} type="submit"
                className="w-full py-3 rounded-xl text-xs font-bold text-white purple-gradient shadow-md cursor-pointer">
                Send Reset Link
              </motion.button>
              <button type="button" onClick={() => navigate('/sentinel/login')} className="w-full text-center text-xs font-semibold text-[var(--color-text-muted)] hover:text-[var(--color-text-primary)] transition cursor-pointer">
                <ArrowLeft size={14} className="inline mr-1" /> Back to Sentinel Login
              </button>
            </form>
          )}
        </div>
      </motion.div>
    </div>
  )
}
