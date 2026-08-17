import { useState } from 'react'
import { Outlet, Navigate, useLocation } from 'react-router-dom'
import { useAuth } from '../../context/AuthContext'
import Sidebar from './Sidebar'
import Topbar from './Topbar'
import { AnimatePresence, motion } from 'framer-motion'

export default function DashboardLayout() {
  const { user, loading } = useAuth()
  const [sidebarOpen, setSidebarOpen] = useState(true)
  const [mobileSidebarOpen, setMobileSidebarOpen] = useState(false)
  const location = useLocation()

  if (loading) {
    return (
      <div 
        className="h-screen w-screen flex flex-col items-center justify-center select-none"
        style={{ backgroundColor: '#050908' }}
      >
        <motion.div
          animate={{ rotate: 360 }}
          transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
          className="w-10 h-10 border-2 border-t-[#00F5A0] border-r-transparent border-b-transparent border-l-transparent rounded-full"
        />
        <p className="mt-4 text-[11px] tracking-[0.2em] uppercase text-[#9BB7AD] font-mono">
          INITIALIZING SENTINEL SOC...
        </p>
      </div>
    )
  }

  if (!user) return <Navigate to="/sentinel/login" replace />

  return (
    <div 
      className="h-screen w-screen flex overflow-hidden cyber-grid-bg text-[#E8FFF6]"
      style={{ backgroundColor: '#050908' }}
    >
      {/* Desktop Navigation Sidebar — 100% Fixed height & position */}
      <div className="hidden lg:flex shrink-0 h-full">
        <Sidebar collapsed={!sidebarOpen} onToggle={() => setSidebarOpen(!sidebarOpen)} />
      </div>

      {/* Mobile Drawer Navigation Sidebar */}
      <AnimatePresence>
        {mobileSidebarOpen && (
          <>
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="fixed inset-0 bg-[#050908]/80 z-40 lg:hidden backdrop-blur-xs"
              onClick={() => setMobileSidebarOpen(false)}
            />
            <motion.div
              initial={{ x: -280 }}
              animate={{ x: 0 }}
              exit={{ x: -280 }}
              transition={{ type: 'spring', damping: 25, stiffness: 200 }}
              className="fixed inset-y-0 left-0 z-50 lg:hidden h-full"
            >
              <Sidebar collapsed={false} onToggle={() => setMobileSidebarOpen(false)} />
            </motion.div>
          </>
        )}
      </AnimatePresence>

      {/* Main Operations Content Region — Fixed Topbar + Scrolling Page Body */}
      <div className="flex-1 flex flex-col h-full min-w-0 overflow-hidden relative z-[1]">
        <Topbar
          onMenuClick={() => setMobileSidebarOpen(true)}
          sidebarOpen={sidebarOpen}
        />
        <main className="flex-1 overflow-y-auto overflow-x-hidden px-4 sm:px-6 lg:px-7 py-6 space-y-6">
          <AnimatePresence mode="wait">
            <motion.div
              key={location.pathname}
              initial={{ opacity: 0, y: 6 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -6 }}
              transition={{ duration: 0.18 }}
            >
              <Outlet />
            </motion.div>
          </AnimatePresence>
        </main>
      </div>
    </div>
  )
}
