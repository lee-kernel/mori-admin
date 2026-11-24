import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import path from 'path'

// https://vite.dev/config/
export default defineConfig(() => {
  return {
    base: './',
    plugins: [vue()],
    server: {
      host: '127.0.0.1',
      proxy: {
        '/api': {
          target: 'http://127.0.0.1:9394',
          changeOrigin: true,
        },
      },
    },
    // @ 指向 src
    resolve: {
      alias: {
        '@': path.resolve(__dirname, 'src'),
      },
    },
    css: {
      preprocessorOptions: {
        scss: {
          // Vite 5 默认仍使用 Sass 旧版 JS API；提前切换为现代 API。
          api: 'modern-compiler',
        },
      },
    },
    build: {
      target: ['es2015'],
      cssCodeSplit: true,
      chunkSizeWarningLimit: 1200,
      rollupOptions: {
        output: {
          manualChunks: {
            vue: ['vue', 'vue-router', 'pinia'],
            antd: ['ant-design-vue'],
            antIcons: ['@ant-design/icons-vue'],
          },
        },
      },
    },
  }
})
