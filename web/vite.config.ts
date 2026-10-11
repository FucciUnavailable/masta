import react from '@vitejs/plugin-react'
import { defineConfig } from 'vitest/config'

// The API is served by `masta serve`; point elsewhere with MASTA_API_URL.
const apiTarget = process.env.MASTA_API_URL ?? 'http://127.0.0.1:8000'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: { '/api': apiTarget },
  },
  test: {
    environment: 'jsdom',
    setupFiles: './src/test/setup.ts',
  },
})
