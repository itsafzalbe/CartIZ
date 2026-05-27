import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    host: true,
    port: 80,
    allowedHosts: [
      'cartiz.uz',
      'www.cartiz.uz',
      'api.cartiz.uz',
    ],
    proxy: {
      '/accounts': 'http://localhost:8000',
      '/stores': 'http://localhost:8000',
    }
  }
})