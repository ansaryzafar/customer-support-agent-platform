import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      // Forwards frontend calls to /api/* to the FastAPI backend during
      // local dev, so the browser never needs to know the backend port.
      '/api': 'http://localhost:8000',
    },
  },
})
