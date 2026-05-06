import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/blocks': 'http://localhost:8000',
      '/complete': 'http://localhost:8000',
      '/save-manual': 'http://localhost:8000',
      '/metadata': 'http://localhost:8000',
      '/validate': 'http://localhost:8000',
      '/missing': 'http://localhost:8000',
      '/finalize': 'http://localhost:8000',
      '/reset': 'http://localhost:8000',
      '/llm-status': 'http://localhost:8000',
      '/schema-info': 'http://localhost:8000',
      '/guide': 'http://localhost:8000',
    }
  }
})