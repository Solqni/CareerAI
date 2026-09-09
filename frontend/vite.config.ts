import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import path from 'node:path'

// GitHub Pages 部署时通过环境变量切换 base，本地开发不受影响
const isGhPages = process.env.GITHUB_PAGES === 'true'

export default defineConfig({
  base: isGhPages ? '/CareerAI/' : '/',
  plugins: [vue()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, 'src'),
    },
  },
  server: {
    host: '0.0.0.0',
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
})
