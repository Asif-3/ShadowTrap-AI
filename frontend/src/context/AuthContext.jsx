import { createContext, useContext, useState, useEffect } from 'react'
import { authAPI } from '../api/client'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const token = localStorage.getItem('shadowtrap_token')
    if (token) {
      authAPI.me()
        .then(res => setUser(res.data.data))
        .catch(() => {
          localStorage.removeItem('shadowtrap_token')
          localStorage.removeItem('shadowtrap_refresh')
        })
        .finally(() => setLoading(false))
    } else {
      setLoading(false)
    }
  }, [])

  const login = async (email, password) => {
    const res = await authAPI.login(email, password)
    const { access_token, refresh_token, user: userData } = res.data.data
    localStorage.setItem('shadowtrap_token', access_token)
    localStorage.setItem('shadowtrap_refresh', refresh_token)
    setUser(userData)
    return userData
  }

  const logout = () => {
    authAPI.logout().catch(() => {})
    localStorage.removeItem('shadowtrap_token')
    localStorage.removeItem('shadowtrap_refresh')
    setUser(null)
  }

  return (
    <AuthContext.Provider value={{ user, loading, login, logout, setUser }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (!context) throw new Error('useAuth must be used within AuthProvider')
  return context
}
