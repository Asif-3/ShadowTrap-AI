import { io } from 'socket.io-client'

const getSocketUrl = () => {
  if (import.meta.env.VITE_SOCKET_URL) {
    return import.meta.env.VITE_SOCKET_URL
  }
  const host = typeof window !== 'undefined' ? window.location.hostname : 'localhost'
  return `http://${host}:5000`
}

const SOCKET_URL = getSocketUrl()

let socket = null

export const getSocket = () => {
  if (!socket) {
    socket = io(SOCKET_URL, {
      autoConnect: true,
      reconnection: true,
      reconnectionAttempts: 10,
      reconnectionDelay: 1000,
      transports: ['websocket', 'polling'],
    })

    socket.on('connect', () => {
      console.log('⚡ Connected to ShadowTrap Real-Time Engine (Socket.IO)')
    })

    socket.on('disconnect', (reason) => {
      console.warn(`⚠️ Socket.IO disconnected: ${reason}`)
    })

    socket.on('connect_error', (error) => {
      console.error('Socket.IO connection error:', error)
    })
  }

  return socket
}

export const subscribeToSession = (sessionId) => {
  const s = getSocket()
  if (s && sessionId) {
    s.emit('subscribe_session', { session_id: sessionId })
  }
}

export const unsubscribeFromSession = (sessionId) => {
  const s = getSocket()
  if (s && sessionId) {
    s.emit('unsubscribe_session', { session_id: sessionId })
  }
}
