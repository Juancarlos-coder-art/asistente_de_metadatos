import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/blocks': 'http://localhost:8080',
      '/complete': 'http://localhost:8080',
      '/save-manual': 'http://localhost:8080',
      '/metadata': 'http://localhost:8080',
      '/validate': 'http://localhost:8080',
      '/missing': 'http://localhost:8080',
      '/finalize': 'http://localhost:8080',
      '/reset': 'http://localhost:8080',
      '/llm-status': 'http://localhost:8080',
    }
  }
})