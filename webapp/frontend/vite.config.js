import { fileURLToPath, URL } from 'node:url'

import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import vueDevTools from 'vite-plugin-vue-devtools'

// https://vite.dev/config/
export default defineConfig({
  plugins: [
    vue(),
    vueDevTools(),
  ],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url))
    },
  },
  server: {
    // En dev, proxifie /api vers le backend (le Pi par défaut, comme en prod via nginx).
    proxy: {
      '/api': {
        target: process.env.VITE_DEV_API_PROXY || 'http://raspberrypi.local:5001',
        changeOrigin: true,
      },
    },
  },
})
