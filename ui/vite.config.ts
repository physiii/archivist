import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  build: {
    rollupOptions: {
      output: {
        manualChunks(id) {
          if (!id.includes('node_modules')) return undefined
          if (id.includes('/three/examples/')) return 'three-examples'
          if (id.includes('/three/')) return 'three-core'
          if (
            id.includes('/react-markdown/') ||
            id.includes('/remark-gfm/') ||
            id.includes('/remark-') ||
            id.includes('/rehype-') ||
            id.includes('/mdast-') ||
            id.includes('/micromark/') ||
            id.includes('/unist-') ||
            id.includes('/hast-')
          ) {
            return 'markdown-vendor'
          }
          return undefined
        },
      },
    },
  },
})
