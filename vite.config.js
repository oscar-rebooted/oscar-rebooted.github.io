import { defineConfig } from 'vite'
import { resolve } from 'path'

export default defineConfig({
  build: {
    rollupOptions: {
      input: {
        main: resolve(__dirname, 'index.html'),
        scienceFiction: resolve(__dirname, 'science-fiction.html'),
        growingUp: resolve(__dirname, 'growing-up.html'),
      },
    },
  },
})
