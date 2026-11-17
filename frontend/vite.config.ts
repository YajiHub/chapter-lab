import tailwindcss from '@tailwindcss/vite'
import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

export default defineConfig({
  plugins: [react(), tailwindcss()],
  // Same-origin in dev too, so the session cookie + CSRF flow matches production.
  server: { proxy: { '/api': 'http://localhost:8000' } },
})
