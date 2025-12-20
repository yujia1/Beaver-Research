import { defineConfig, loadEnv } from 'vite'
import vue from '@vitejs/plugin-vue'

// https://vitejs.dev/config/
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')

  return {
    plugins: [vue()],
    define: {
      // Replace process.env with import.meta.env for Vite
      'process.env.VITE_API_URL': JSON.stringify(env.VITE_API_URL || 'http://localhost:8000'),
    },
    server: {
      port: 5173,
      proxy: {
        // Only proxy in development
        '/api': {
          target: env.VITE_API_URL || 'http://localhost:8000',
          changeOrigin: true,
        }
      }
    }
  }
})
