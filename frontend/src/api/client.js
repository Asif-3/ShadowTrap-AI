import axios from 'axios'

const API_BASE = '/api'

const api = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor to attach JWT token
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('shadowtrap_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Auth API
export const authAPI = {
  login: (credentials, password) => {
    const payload = typeof credentials === 'object' ? credentials : { email: credentials, password }
    return api.post('/auth/login', payload)
  },
  forgotPassword: (email) => api.post('/auth/forgot-password', { email }),
  me: () => api.get('/auth/me'),
  getProfile: () => api.get('/auth/me'),
  getUsers: () => api.get('/auth/users'),
  updateProfile: (data) => api.put('/auth/profile', data),
  logout: () => api.post('/auth/logout'),
  changePassword: (currentPassword, newPassword) =>
    api.post('/auth/change-password', { current_password: currentPassword, new_password: newPassword }),
}

// Dashboard API
export const dashboardAPI = {
  getWidgets: () => api.get('/dashboard/widgets'),
  getStats: () => api.get('/dashboard/stats'),
  getTimeline: (days = 30) => api.get(`/dashboard/timeline?days=${days}`),
}

// Attacks API
export const attacksAPI = {
  getAttacks: (params) => api.get('/attacks', { params }),
  getAttackById: (id) => api.get(`/attacks/${id}`),
  getAttackBySession: (sessionId) => api.get(`/attacks/session/${sessionId}`),
  getLiveSessions: () => api.get('/attacks/live'),
  getRecent: (limit = 10) => api.get(`/attacks/recent?limit=${limit}`),
  triggerSimulator: (type) => api.post('/attacks/simulate', { type }),
  analyzeAttack: (id) => api.post(`/attacks/${id}/analyze`),
  deleteAttacks: (sessionIds) => api.delete('/attacks', { data: { session_ids: sessionIds } }),
}

// Replay API
export const replayAPI = {
  getReplay: (sessionId) => api.get(`/replay/${sessionId}`),
}

// Analytics API
export const analyticsAPI = {
  getStats: () => api.get('/analytics/stats'),
}

// Reports API
export const reportsAPI = {
  getReports: () => api.get('/reports'),
  generateReport: (data) => api.post('/reports/generate', data),
  downloadReport: (reportId) => api.get(`/reports/download/${reportId}`, { responseType: 'blob' }),
  sendReportToTelegram: (reportId) => api.post(`/reports/${reportId}/send-telegram`),
}

// Knowledge Graph API
export const knowledgeGraphAPI = {
  getGraph: () => api.get('/knowledge-graph'),
  getSessionGraph: (sessionId) => api.get(`/knowledge-graph/session/${sessionId}`),
}

// Threat Intelligence API
export const threatIntelAPI = {
  getFeed: () => api.get('/threat-intel/feed'),
  getLandscape: () => api.get('/threat-intel/landscape'),
  getFullIntel: () => api.get('/threat-intel/full'),
  getIpDetails: (ip) => api.get(`/threat-intel/ip/${ip}`),
}

// AI Models API
export const aiModelsAPI = {
  getStatus: () => api.get('/ai-models/status'),
  getHistory: () => api.get('/ai-models/history'),
  retrain: () => api.post('/ai-models/retrain'),
}

// LLM API
export const llmAPI = {
  getSummary: (sessionId) => api.get(`/llm/summary/${sessionId}`),
  explain: (prompt, sessionId = null) => api.post('/llm/explain', { prompt, session_id: sessionId }, { timeout: 120000 }),
  getStatus: () => api.get('/llm/status'),
}

// Settings API
export const settingsAPI = {
  get: () => api.get('/settings'),
  getSettings: () => api.get('/settings'),
  update: (settings) => api.put('/settings', settings),
  updateSettings: (settings) => api.put('/settings', settings),
}

export default api

