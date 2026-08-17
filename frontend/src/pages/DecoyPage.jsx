import { useState, useEffect, useRef } from 'react'
import { motion } from 'framer-motion'
import {
  Cloud, Shield, Cpu, BarChart3, Users, Mail,
  ArrowRight, Check, Globe, Zap, Lock, Server,
  ChevronRight, Phone, MapPin, Star
} from 'lucide-react'

/* ══════════════════════════════════════════════════════
   DECOY PAGE — TechNova Solutions
   ══════════════════════════════════════════════════════
   This page looks like a normal corporate website.
   Behind the scenes it silently fingerprints the visitor
   and sends all telemetry to the backend trap endpoint.
   ══════════════════════════════════════════════════════ */

// ─── Silent Fingerprinting Engine ───
function collectFingerprint() {
  const fp = {
    userAgent: navigator.userAgent,
    language: navigator.language,
    languages: navigator.languages?.join(','),
    platform: navigator.platform,
    screenWidth: screen.width,
    screenHeight: screen.height,
    screenDepth: screen.colorDepth,
    timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
    timezoneOffset: new Date().getTimezoneOffset(),
    cookiesEnabled: navigator.cookieEnabled,
    doNotTrack: navigator.doNotTrack,
    hardwareConcurrency: navigator.hardwareConcurrency,
    maxTouchPoints: navigator.maxTouchPoints,
    webdriver: navigator.webdriver,
    connectionType: navigator.connection?.effectiveType,
    deviceMemory: navigator.deviceMemory,
    windowWidth: window.innerWidth,
    windowHeight: window.innerHeight,
    pixelRatio: window.devicePixelRatio,
    referrer: document.referrer,
    timestamp: new Date().toISOString(),
  }

  // Canvas fingerprint
  try {
    const canvas = document.createElement('canvas')
    const ctx = canvas.getContext('2d')
    canvas.width = 200
    canvas.height = 50
    ctx.textBaseline = 'top'
    ctx.font = '14px Arial'
    ctx.fillStyle = '#7C3AED'
    ctx.fillRect(0, 0, 200, 50)
    ctx.fillStyle = '#FFF'
    ctx.fillText('TechNova FP', 10, 15)
    fp.canvasHash = canvas.toDataURL().slice(-32)
  } catch { fp.canvasHash = 'blocked' }

  // WebGL fingerprint
  try {
    const gl = document.createElement('canvas').getContext('webgl')
    const debugInfo = gl?.getExtension('WEBGL_debug_renderer_info')
    fp.webglVendor = gl?.getParameter(debugInfo?.UNMASKED_VENDOR_WEBGL) || 'unknown'
    fp.webglRenderer = gl?.getParameter(debugInfo?.UNMASKED_RENDERER_WEBGL) || 'unknown'
  } catch { fp.webglVendor = 'blocked'; fp.webglRenderer = 'blocked' }

  return fp
}

function sendTrapData(data) {
  try {
    const payload = JSON.stringify(data)
    // Use sendBeacon for reliability (survives page unload)
    if (navigator.sendBeacon) {
      navigator.sendBeacon('/api/trap/log', new Blob([payload], { type: 'application/json' }))
    } else {
      fetch('/api/trap/log', { method: 'POST', body: payload, headers: { 'Content-Type': 'application/json' }, keepalive: true })
    }
  } catch { /* silent fail */ }
}

// ─── DevTools Detection ───
function detectDevTools() {
  const threshold = 160
  const widthDiff = window.outerWidth - window.innerWidth
  const heightDiff = window.outerHeight - window.innerHeight
  return widthDiff > threshold || heightDiff > threshold
}

// ─── Decoy Content Data ───
const services = [
  { icon: Cloud, title: 'Cloud Migration', desc: 'Seamless migration to AWS, Azure, and GCP with zero-downtime deployment strategies.' },
  { icon: Shield, title: 'Cybersecurity', desc: 'Enterprise-grade security auditing, penetration testing, and compliance frameworks.' },
  { icon: Cpu, title: 'AI & Machine Learning', desc: 'Custom AI models and intelligent automation to transform your business workflows.' },
  { icon: BarChart3, title: 'Data Analytics', desc: 'Real-time dashboards, predictive analytics, and business intelligence solutions.' },
  { icon: Server, title: 'Infrastructure', desc: 'Scalable microservices architecture with Kubernetes orchestration and monitoring.' },
  { icon: Lock, title: 'Compliance', desc: 'SOC 2, HIPAA, GDPR compliance consulting with automated audit trails.' },
]

const stats = [
  { value: '500+', label: 'Enterprise Clients' },
  { value: '99.99%', label: 'Uptime SLA' },
  { value: '24/7', label: 'Support Coverage' },
  { value: '40+', label: 'Countries Served' },
]

const testimonials = [
  { name: 'Sarah Chen', role: 'CTO, Meridian Corp', text: 'TechNova transformed our entire cloud infrastructure. Migration was seamless with zero downtime.' },
  { name: 'James Miller', role: 'VP Engineering, Apex Digital', text: 'Their AI solutions reduced our processing costs by 60%. Exceptional technical team.' },
  { name: 'Priya Sharma', role: 'CISO, GlobalFintech', text: 'Outstanding security posture assessment. They identified vulnerabilities our internal team missed.' },
]

export default function DecoyPage() {
  const [contactForm, setContactForm] = useState({ name: '', email: '', message: '' })
  const [formSubmitted, setFormSubmitted] = useState(false)
  const behaviorRef = useRef({ mousePositions: [], scrollDepths: [], clicks: 0, keyPresses: 0, startTime: Date.now() })
  const devToolsDetectedRef = useRef(false)

  useEffect(() => {
    // ─── Initial Fingerprint ───
    const fp = collectFingerprint()
    sendTrapData({ type: 'fingerprint', ...fp })

    // ─── Mouse Movement Tracking ───
    const onMouseMove = (e) => {
      const b = behaviorRef.current
      if (b.mousePositions.length < 200) {
        b.mousePositions.push({ x: e.clientX, y: e.clientY, t: Date.now() - b.startTime })
      }
    }

    // ─── Scroll Tracking ───
    const onScroll = () => {
      const scrollPercent = Math.round((window.scrollY / (document.body.scrollHeight - window.innerHeight)) * 100)
      const b = behaviorRef.current
      if (!b.scrollDepths.includes(scrollPercent)) {
        b.scrollDepths.push(scrollPercent)
      }
    }

    // ─── Click Tracking ───
    const onClick = () => { behaviorRef.current.clicks++ }

    // ─── Key Press Tracking ───
    const onKeyDown = () => { behaviorRef.current.keyPresses++ }

    // ─── DevTools Detection Interval ───
    const devToolsInterval = setInterval(() => {
      if (detectDevTools() && !devToolsDetectedRef.current) {
        devToolsDetectedRef.current = true
        sendTrapData({ type: 'devtools_detected', timestamp: new Date().toISOString() })
      }
    }, 2000)

    // ─── Periodic Behavior Report ───
    const behaviorInterval = setInterval(() => {
      const b = behaviorRef.current
      sendTrapData({
        type: 'behavior',
        timeOnPage: Math.round((Date.now() - b.startTime) / 1000),
        mousePositions: b.mousePositions.length,
        maxScrollDepth: Math.max(...b.scrollDepths, 0),
        clicks: b.clicks,
        keyPresses: b.keyPresses,
        devToolsOpen: devToolsDetectedRef.current,
        timestamp: new Date().toISOString(),
      })
    }, 15000)

    window.addEventListener('mousemove', onMouseMove, { passive: true })
    window.addEventListener('scroll', onScroll, { passive: true })
    window.addEventListener('click', onClick, { passive: true })
    window.addEventListener('keydown', onKeyDown, { passive: true })

    // ─── Cleanup + Final Report on Unload ───
    const onUnload = () => {
      const b = behaviorRef.current
      sendTrapData({
        type: 'session_end',
        totalTime: Math.round((Date.now() - b.startTime) / 1000),
        totalMousePositions: b.mousePositions.length,
        maxScrollDepth: Math.max(...b.scrollDepths, 0),
        totalClicks: b.clicks,
        totalKeyPresses: b.keyPresses,
        devToolsDetected: devToolsDetectedRef.current,
        timestamp: new Date().toISOString(),
      })
    }
    window.addEventListener('beforeunload', onUnload)

    return () => {
      window.removeEventListener('mousemove', onMouseMove)
      window.removeEventListener('scroll', onScroll)
      window.removeEventListener('click', onClick)
      window.removeEventListener('keydown', onKeyDown)
      window.removeEventListener('beforeunload', onUnload)
      clearInterval(devToolsInterval)
      clearInterval(behaviorInterval)
    }
  }, [])

  const handleContactSubmit = (e) => {
    e.preventDefault()
    // Trap: capture form submission data
    sendTrapData({
      type: 'form_submission',
      formData: contactForm,
      timestamp: new Date().toISOString(),
    })
    setFormSubmitted(true)
  }

  return (
    <div style={{ fontFamily: "'Inter', system-ui, sans-serif", background: '#FAFBFF', color: '#1a1a2e', minHeight: '100vh' }}>
      {/* ─── Navigation Bar ─── */}
      <header style={{
        position: 'sticky', top: 0, zIndex: 50,
        background: 'rgba(255,255,255,0.92)', backdropFilter: 'blur(16px)',
        borderBottom: '1px solid rgba(0,0,0,0.06)',
        padding: '0 40px', height: 72, display: 'flex', alignItems: 'center', justifyContent: 'space-between'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <div style={{
            width: 38, height: 38, borderRadius: 10,
            background: 'linear-gradient(135deg, #2563EB, #0EA5E9)',
            display: 'flex', alignItems: 'center', justifyContent: 'center'
          }}>
            <Globe size={20} color="#fff" />
          </div>
          <span style={{ fontSize: 20, fontWeight: 800, color: '#1a1a2e' }}>TechNova</span>
          <span style={{ fontSize: 11, fontWeight: 600, color: '#64748B', marginLeft: -4 }}>Solutions</span>
        </div>
        <nav style={{ display: 'flex', gap: 32, alignItems: 'center' }}>
          {['Services', 'About', 'Careers', 'Contact'].map(item => (
            <a key={item} href={`#${item.toLowerCase()}`}
              style={{ fontSize: 14, fontWeight: 500, color: '#475569', textDecoration: 'none', transition: 'color 0.2s' }}
              onMouseEnter={e => e.target.style.color = '#2563EB'}
              onMouseLeave={e => e.target.style.color = '#475569'}
            >{item}</a>
          ))}
          <button style={{
            padding: '8px 20px', borderRadius: 8, border: 'none', cursor: 'pointer',
            background: 'linear-gradient(135deg, #2563EB, #0EA5E9)',
            color: '#fff', fontSize: 13, fontWeight: 600
          }}>Get Started</button>
        </nav>
      </header>

      {/* ─── Hero Section ─── */}
      <section style={{
        padding: '100px 40px 80px', textAlign: 'center',
        background: 'linear-gradient(180deg, #FAFBFF 0%, #EFF6FF 100%)',
        position: 'relative', overflow: 'hidden'
      }}>
        {/* Decorative gradient blobs */}
        <div style={{
          position: 'absolute', top: -100, right: -100, width: 400, height: 400,
          borderRadius: '50%', background: 'radial-gradient(circle, rgba(37,99,235,0.08), transparent 70%)',
          pointerEvents: 'none'
        }} />
        <div style={{
          position: 'absolute', bottom: -80, left: -80, width: 350, height: 350,
          borderRadius: '50%', background: 'radial-gradient(circle, rgba(14,165,233,0.06), transparent 70%)',
          pointerEvents: 'none'
        }} />

        <motion.div initial={{ opacity: 0, y: 30 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.6 }}>
          <span style={{
            display: 'inline-block', fontSize: 12, fontWeight: 700, color: '#2563EB',
            background: 'rgba(37,99,235,0.08)', padding: '6px 16px', borderRadius: 20,
            marginBottom: 24, letterSpacing: 0.5
          }}>🚀 Trusted by 500+ Enterprise Companies</span>
          <h1 style={{
            fontSize: 52, fontWeight: 900, lineHeight: 1.15, maxWidth: 700, margin: '0 auto 20px',
            background: 'linear-gradient(135deg, #1a1a2e, #2563EB)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent'
          }}>
            Cloud Infrastructure Built for Scale
          </h1>
          <p style={{ fontSize: 18, color: '#64748B', maxWidth: 560, margin: '0 auto 36px', lineHeight: 1.7 }}>
            Enterprise cloud migration, AI-powered analytics, and cybersecurity solutions that drive digital transformation.
          </p>
          <div style={{ display: 'flex', gap: 14, justifyContent: 'center' }}>
            <button style={{
              padding: '14px 32px', borderRadius: 10, border: 'none', cursor: 'pointer',
              background: 'linear-gradient(135deg, #2563EB, #0EA5E9)',
              color: '#fff', fontSize: 15, fontWeight: 700, display: 'flex', alignItems: 'center', gap: 8,
              boxShadow: '0 4px 16px rgba(37,99,235,0.25)'
            }}>
              Schedule Demo <ArrowRight size={16} />
            </button>
            <button style={{
              padding: '14px 32px', borderRadius: 10, cursor: 'pointer',
              background: '#fff', border: '1px solid #E2E8F0',
              color: '#1a1a2e', fontSize: 15, fontWeight: 600, display: 'flex', alignItems: 'center', gap: 8,
              boxShadow: '0 2px 8px rgba(0,0,0,0.04)'
            }}>
              View Case Studies <ChevronRight size={16} />
            </button>
          </div>
        </motion.div>
      </section>

      {/* ─── Stats Bar ─── */}
      <section style={{
        padding: '40px', display: 'flex', justifyContent: 'center', gap: 60,
        background: '#fff', borderTop: '1px solid rgba(0,0,0,0.04)', borderBottom: '1px solid rgba(0,0,0,0.04)'
      }}>
        {stats.map((s, i) => (
          <motion.div key={i} initial={{ opacity: 0, y: 15 }} animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.1 + 0.3 }} style={{ textAlign: 'center' }}>
            <p style={{ fontSize: 32, fontWeight: 800, color: '#2563EB' }}>{s.value}</p>
            <p style={{ fontSize: 13, color: '#64748B', fontWeight: 500, marginTop: 4 }}>{s.label}</p>
          </motion.div>
        ))}
      </section>

      {/* ─── Services Grid ─── */}
      <section id="services" style={{ padding: '80px 40px', maxWidth: 1200, margin: '0 auto' }}>
        <div style={{ textAlign: 'center', marginBottom: 50 }}>
          <h2 style={{ fontSize: 36, fontWeight: 800, color: '#1a1a2e' }}>Our Services</h2>
          <p style={{ fontSize: 16, color: '#64748B', marginTop: 12, maxWidth: 500, margin: '12px auto 0' }}>
            End-to-end technology solutions tailored for modern enterprises
          </p>
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 24 }}>
          {services.map((s, i) => (
            <motion.div key={i} initial={{ opacity: 0, y: 20 }} whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }} transition={{ delay: i * 0.08 }}
              style={{
                padding: 32, borderRadius: 16, background: '#fff', border: '1px solid rgba(0,0,0,0.06)',
                transition: 'all 0.25s', cursor: 'default',
                boxShadow: '0 2px 8px rgba(0,0,0,0.03)'
              }}
              onMouseEnter={e => { e.currentTarget.style.borderColor = '#2563EB30'; e.currentTarget.style.boxShadow = '0 8px 30px rgba(37,99,235,0.08)' }}
              onMouseLeave={e => { e.currentTarget.style.borderColor = 'rgba(0,0,0,0.06)'; e.currentTarget.style.boxShadow = '0 2px 8px rgba(0,0,0,0.03)' }}
            >
              <div style={{
                width: 48, height: 48, borderRadius: 12, display: 'flex', alignItems: 'center', justifyContent: 'center',
                background: 'linear-gradient(135deg, rgba(37,99,235,0.1), rgba(14,165,233,0.08))', marginBottom: 16
              }}>
                <s.icon size={22} color="#2563EB" />
              </div>
              <h3 style={{ fontSize: 17, fontWeight: 700, color: '#1a1a2e', marginBottom: 8 }}>{s.title}</h3>
              <p style={{ fontSize: 14, color: '#64748B', lineHeight: 1.65 }}>{s.desc}</p>
            </motion.div>
          ))}
        </div>
      </section>

      {/* ─── Testimonials ─── */}
      <section style={{ padding: '80px 40px', background: '#F8FAFC' }}>
        <div style={{ maxWidth: 1200, margin: '0 auto' }}>
          <h2 style={{ fontSize: 36, fontWeight: 800, textAlign: 'center', marginBottom: 50, color: '#1a1a2e' }}>
            What Our Clients Say
          </h2>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 24 }}>
            {testimonials.map((t, i) => (
              <motion.div key={i} initial={{ opacity: 0, y: 20 }} whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }} transition={{ delay: i * 0.1 }}
                style={{
                  padding: 28, borderRadius: 16, background: '#fff', border: '1px solid rgba(0,0,0,0.06)',
                  boxShadow: '0 2px 8px rgba(0,0,0,0.03)'
                }}>
                <div style={{ display: 'flex', gap: 3, marginBottom: 14 }}>
                  {[1,2,3,4,5].map(s => <Star key={s} size={14} fill="#F59E0B" color="#F59E0B" />)}
                </div>
                <p style={{ fontSize: 14, color: '#475569', lineHeight: 1.7, fontStyle: 'italic', marginBottom: 16 }}>
                  "{t.text}"
                </p>
                <div>
                  <p style={{ fontSize: 14, fontWeight: 700, color: '#1a1a2e' }}>{t.name}</p>
                  <p style={{ fontSize: 12, color: '#64748B' }}>{t.role}</p>
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* ─── Contact Section ─── */}
      <section id="contact" style={{ padding: '80px 40px', maxWidth: 800, margin: '0 auto' }}>
        <div style={{ textAlign: 'center', marginBottom: 40 }}>
          <h2 style={{ fontSize: 36, fontWeight: 800, color: '#1a1a2e' }}>Get in Touch</h2>
          <p style={{ fontSize: 15, color: '#64748B', marginTop: 10 }}>Have a project in mind? We'd love to hear from you.</p>
        </div>

        {formSubmitted ? (
          <motion.div initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }}
            style={{
              padding: 40, borderRadius: 16, background: '#fff', textAlign: 'center',
              border: '1px solid rgba(16,185,129,0.2)', boxShadow: '0 4px 20px rgba(16,185,129,0.08)'
            }}>
            <div style={{
              width: 56, height: 56, borderRadius: '50%', margin: '0 auto 16px',
              background: 'rgba(16,185,129,0.1)', display: 'flex', alignItems: 'center', justifyContent: 'center'
            }}>
              <Check size={28} color="#10B981" />
            </div>
            <h3 style={{ fontSize: 20, fontWeight: 700, color: '#1a1a2e', marginBottom: 8 }}>Thank you!</h3>
            <p style={{ fontSize: 14, color: '#64748B' }}>We'll get back to you within 24 hours.</p>
          </motion.div>
        ) : (
          <form onSubmit={handleContactSubmit} style={{
            padding: 36, borderRadius: 16, background: '#fff',
            border: '1px solid rgba(0,0,0,0.06)', boxShadow: '0 4px 20px rgba(0,0,0,0.04)'
          }}>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16, marginBottom: 16 }}>
              <div>
                <label style={{ fontSize: 13, fontWeight: 600, color: '#475569', display: 'block', marginBottom: 6 }}>Full Name</label>
                <input type="text" value={contactForm.name} onChange={e => setContactForm(p => ({ ...p, name: e.target.value }))}
                  placeholder="John Smith" required
                  style={{
                    width: '100%', padding: '12px 14px', borderRadius: 10, border: '1px solid #E2E8F0',
                    fontSize: 14, outline: 'none', background: '#F8FAFC', color: '#1a1a2e', boxSizing: 'border-box'
                  }} />
              </div>
              <div>
                <label style={{ fontSize: 13, fontWeight: 600, color: '#475569', display: 'block', marginBottom: 6 }}>Email</label>
                <input type="email" value={contactForm.email} onChange={e => setContactForm(p => ({ ...p, email: e.target.value }))}
                  placeholder="john@company.com" required
                  style={{
                    width: '100%', padding: '12px 14px', borderRadius: 10, border: '1px solid #E2E8F0',
                    fontSize: 14, outline: 'none', background: '#F8FAFC', color: '#1a1a2e', boxSizing: 'border-box'
                  }} />
              </div>
            </div>
            <div style={{ marginBottom: 20 }}>
              <label style={{ fontSize: 13, fontWeight: 600, color: '#475569', display: 'block', marginBottom: 6 }}>Message</label>
              <textarea value={contactForm.message} onChange={e => setContactForm(p => ({ ...p, message: e.target.value }))}
                placeholder="Tell us about your project..." rows={4} required
                style={{
                  width: '100%', padding: '12px 14px', borderRadius: 10, border: '1px solid #E2E8F0',
                  fontSize: 14, outline: 'none', background: '#F8FAFC', resize: 'vertical', color: '#1a1a2e',
                  fontFamily: "'Inter', sans-serif", boxSizing: 'border-box'
                }} />
            </div>
            <button type="submit" style={{
              width: '100%', padding: '14px', borderRadius: 10, border: 'none', cursor: 'pointer',
              background: 'linear-gradient(135deg, #2563EB, #0EA5E9)',
              color: '#fff', fontSize: 15, fontWeight: 700,
              boxShadow: '0 4px 16px rgba(37,99,235,0.2)'
            }}>
              Send Message
            </button>
          </form>
        )}
      </section>

      {/* ─── Footer ─── */}
      <footer style={{
        padding: '48px 40px', background: '#1a1a2e', color: '#94A3B8',
        display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 20
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <div style={{
            width: 32, height: 32, borderRadius: 8,
            background: 'linear-gradient(135deg, #2563EB, #0EA5E9)',
            display: 'flex', alignItems: 'center', justifyContent: 'center'
          }}>
            <Globe size={16} color="#fff" />
          </div>
          <span style={{ fontSize: 15, fontWeight: 700, color: '#E2E8F0' }}>TechNova Solutions</span>
        </div>
        <div style={{ display: 'flex', gap: 24, fontSize: 13 }}>
          <span style={{ display: 'flex', alignItems: 'center', gap: 6 }}><Mail size={14} /> info@technova.io</span>
          <span style={{ display: 'flex', alignItems: 'center', gap: 6 }}><Phone size={14} /> +1 (555) 123-4567</span>
          <span style={{ display: 'flex', alignItems: 'center', gap: 6 }}><MapPin size={14} /> San Francisco, CA</span>
        </div>
        <p style={{ fontSize: 12, color: '#64748B', width: '100%', textAlign: 'center', marginTop: 16 }}>
          © 2026 TechNova Solutions Inc. All rights reserved. Privacy Policy | Terms of Service
        </p>
      </footer>
    </div>
  )
}
