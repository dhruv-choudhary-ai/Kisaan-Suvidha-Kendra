#!/usr/bin/env node

/**
 * Production Server - Single Port
 * Serves both frontend static files and proxies backend API
 * This allows everything to run on a single port (default: 3000)
 */

const express = require('express')
const { createProxyMiddleware } = require('http-proxy-middleware')
const path = require('path')

const app = express()
const PORT = process.env.PORT || 3000

// Configuration
const BACKEND_PORT = process.env.BACKEND_PORT || 5000
const AVATAR_PORT = process.env.AVATAR_PORT || 8010

console.log('🚀 Starting production server...')
console.log('')

// Health check endpoint
app.get('/health', (req, res) => {
  res.json({ 
    status: 'healthy', 
    timestamp: new Date().toISOString(),
    ports: {
      frontend: PORT,
      backend: BACKEND_PORT,
      avatar: AVATAR_PORT
    }
  })
})

// Proxy API requests to backend
app.use('/api', createProxyMiddleware({
  target: `http://localhost:${BACKEND_PORT}`,
  changeOrigin: true,
  pathRewrite: {
    '^/api': '' // Remove /api prefix
  },
  onError: (err, req, res) => {
    console.error('❌ Backend proxy error:', err.message)
    res.status(502).json({ 
      error: 'Backend service unavailable',
      message: 'Please ensure backend is running on port ' + BACKEND_PORT
    })
  },
  onProxyReq: (proxyReq, req, res) => {
    console.log('→ API:', req.method, req.path)
  }
}))

// Proxy avatar requests
app.use(['/human', '/is_speaking'], createProxyMiddleware({
  target: `http://localhost:${AVATAR_PORT}`,
  changeOrigin: true,
  onError: (err, req, res) => {
    console.error('❌ Avatar proxy error:', err.message)
    res.status(502).json({
      error: 'Avatar service unavailable',
      message: 'Please ensure avatar service is running on port ' + AVATAR_PORT
    })
  },
  onProxyReq: (proxyReq, req, res) => {
    console.log('→ Avatar:', req.method, req.path)
  }
}))

// Serve static files from dist directory
const distPath = path.join(__dirname, 'dist')
app.use(express.static(distPath))

// Handle client-side routing - serve index.html for all other routes
app.get('*', (req, res) => {
  res.sendFile(path.join(distPath, 'index.html'))
})

// Error handler
app.use((err, req, res, next) => {
  console.error('❌ Server error:', err)
  res.status(500).json({ 
    error: 'Internal server error',
    message: err.message
  })
})

// Start server
app.listen(PORT, '0.0.0.0', () => {
  console.log('')
  console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━')
  console.log('')
  console.log('✅ Production server is running!')
  console.log('')
  console.log(`  🌐 Frontend:        http://localhost:${PORT}`)
  console.log(`  🌐 Network:         http://0.0.0.0:${PORT}`)
  console.log(`  🔧 Backend Proxy:   http://localhost:${PORT}/api`)
  console.log(`  🎭 Avatar Service:  http://localhost:${PORT}/human`)
  console.log(`  💚 Health Check:    http://localhost:${PORT}/health`)
  console.log('')
  console.log(`  Expected backend services:`)
  console.log(`     Backend:       http://localhost:${BACKEND_PORT}`)
  console.log(`     Avatar:        http://localhost:${AVATAR_PORT}`)
  console.log('')
  console.log('  Press Ctrl+C to stop')
  console.log('')
  console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━')
  console.log('')
})

// Graceful shutdown
process.on('SIGTERM', () => {
  console.log('⚠️  SIGTERM received, shutting down gracefully...')
  process.exit(0)
})

process.on('SIGINT', () => {
  console.log('')
  console.log('⚠️  SIGINT received, shutting down gracefully...')
  process.exit(0)
})




