import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    host: true, // Allow access from network
    allowedHosts: [
      'localhost',
      '.ngrok-free.dev', // Allow all ngrok free domains
      '.ngrok.io', // Allow ngrok paid domains
      '.loca.lt' // Allow localtunnel domains
    ],
    proxy: {
      '/api': {
        target: 'http://localhost:5000',
        changeOrigin: true,
      },
      '/videos': {
        target: 'http://localhost:5000',
        changeOrigin: true,
      },
      '/sentiment': {
        target: 'http://localhost:5000',
        changeOrigin: true,
      },
      '/chat': {
        target: 'http://localhost:5000',
        changeOrigin: true,
      },
      '/health': {
        target: 'http://localhost:5000',
        changeOrigin: true,
      }
    }
  },
  build: {
    outDir: 'dist',
    sourcemap: true,
  }
})
