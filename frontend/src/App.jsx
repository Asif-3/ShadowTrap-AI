import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider } from './context/AuthContext'
import { ThemeProvider } from './context/ThemeContext'
import DashboardLayout from './components/layout/DashboardLayout'

// Decoy (Attacker-facing)
import DecoyPage from './pages/DecoyPage'
import DecoyAdminLogin from './pages/DecoyAdminLogin'
import DecoyAdminConsole from './pages/DecoyAdminConsole'

// SOC Pages (Hidden behind /sentinel/)
import Login from './pages/Login'
import ForgotPassword from './pages/ForgotPassword'
import Dashboard from './pages/Dashboard'
import LiveSessions from './pages/LiveSessions'
import Attacks from './pages/Attacks'
import AttackDetails from './pages/AttackDetails'
import AttackReplay from './pages/AttackReplay'
import Reports from './pages/Reports'
import Analytics from './pages/Analytics'
import Settings from './pages/Settings'
import Profile from './pages/Profile'
import KnowledgeGraph from './pages/KnowledgeGraph'
import ThreatIntelligence from './pages/ThreatIntelligence'
import MitreMatrix from './pages/MitreMatrix'
import UserManagement from './pages/UserManagement'
import SecurityCopilot from './pages/SecurityCopilot'
import TrapVisitors from './pages/TrapVisitors'

export default function App() {
  return (
    <ThemeProvider>
      <AuthProvider>
        <BrowserRouter>
          <Routes>
            {/* ═══ DECOY — Attacker sees this ═══ */}
            <Route path="/" element={<DecoyPage />} />
            <Route path="/admin-login" element={<DecoyAdminLogin />} />
            <Route path="/login" element={<DecoyAdminLogin />} />
            <Route path="/decoy-login" element={<DecoyAdminLogin />} />
            <Route path="/decoy-admin-dashboard" element={<DecoyAdminConsole />} />

            {/* ═══ HIDDEN SOC — Auth Routes ═══ */}
            <Route path="/sentinel/login" element={<Login />} />
            <Route path="/sentinel/forgot-password" element={<ForgotPassword />} />

            {/* ═══ HIDDEN SOC — Protected Dashboard ═══ */}
            <Route path="/sentinel" element={<DashboardLayout />}>
              <Route index element={<Dashboard />} />
              <Route path="live-sessions" element={<LiveSessions />} />
              <Route path="attacks" element={<Attacks />} />
              <Route path="attacks/:id" element={<AttackDetails />} />
              <Route path="replay" element={<AttackReplay />} />
              <Route path="replay/:sessionId" element={<AttackReplay />} />
              <Route path="knowledge-graph" element={<KnowledgeGraph />} />
              <Route path="threat-intel" element={<ThreatIntelligence />} />
              <Route path="mitre-matrix" element={<MitreMatrix />} />
              <Route path="copilot" element={<SecurityCopilot />} />
              <Route path="reports" element={<Reports />} />
              <Route path="analytics" element={<Analytics />} />
              <Route path="users" element={<UserManagement />} />
              <Route path="trap-visitors" element={<TrapVisitors />} />
              <Route path="settings" element={<Settings />} />
              <Route path="profile" element={<Profile />} />
            </Route>

            {/* ═══ FALLBACK — Unknown routes show decoy ═══ */}
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </BrowserRouter>
      </AuthProvider>
    </ThemeProvider>
  )
}
