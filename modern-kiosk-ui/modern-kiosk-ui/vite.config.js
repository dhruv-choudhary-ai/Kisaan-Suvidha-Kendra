import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    host: '0.0.0.0',
    proxy: {
      // Kisaan Backend API endpoints
      '/voice': {
        target: 'http://localhost:8000',
        changeOrigin: true
      },
      '/camera': {
        target: 'http://localhost:8000',
        changeOrigin: true
      },
      '/farmer': {
        target: 'http://localhost:8000',
        changeOrigin: true
      },
      '/crop': {
        target: 'http://localhost:8000',
        changeOrigin: true
      },
      '/session': {
        target: 'http://localhost:8000',
        changeOrigin: true
      },
      '/products': {
        target: 'http://localhost:8000',
        changeOrigin: true
      },
      '/health': {
        target: 'http://localhost:8000',
        changeOrigin: true
      },
      '/ws': {
        target: 'ws://localhost:8000',
        ws: true,
        changeOrigin: true
      },
      // Avatar WebRTC endpoints (keep existing RunPod proxy)
      '/human': {
        target: 'https://jltzsxc1c8xlp3-8010.proxy.runpod.net',
        changeOrigin: true,
        secure: false
      },
      '/is_speaking': {
        target: 'https://jltzsxc1c8xlp3-8010.proxy.runpod.net',
        changeOrigin: true,
        secure: false
      },
      '/offer': {
        target: 'https://jltzsxc1c8xlp3-8010.proxy.runpod.net',
        changeOrigin: true,
        secure: false
      }
    }
  },
  build: {
    outDir: 'dist',
    assetsDir: 'assets',
    sourcemap: false
  }
})
