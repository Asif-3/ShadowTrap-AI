// Express / Node.js Backend Server Example
// Configured to listen on 0.0.0.0 to accept connections from any network interface (e.g. Kali Linux VM)

import express from 'express'
import cors from 'cors'

const app = express()
const PORT = process.env.PORT || 5000

// 1. Enable CORS for cross-origin requests from Vite frontend running on another machine
app.use(cors({
  origin: '*',
  credentials: true
}))

app.use(express.json())

// API Routes
app.get('/api/health', (req, res) => {
  res.json({ status: 'ok', message: 'Backend is reachable on LAN network' })
})

// 2. Ensure backend listens on "0.0.0.0" instead of "127.0.0.1" / "localhost"
app.listen(PORT, '0.0.0.0', () => {
  console.log(`🚀 Server listening on http://0.0.0.0:${PORT}`)
  console.log(`🌐 Network Accessible at http://<HOST-IP>:${PORT}`)
})
