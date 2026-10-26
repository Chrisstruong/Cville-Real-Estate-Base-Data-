import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  // Standalone local development; Vercel uses the root service rewrites.
  server: {
    proxy: {
      '/api': 'http://127.0.0.1:8000',
    },
  },
  optimizeDeps: {
    exclude: ['maplibre-gl'],
  },
})
