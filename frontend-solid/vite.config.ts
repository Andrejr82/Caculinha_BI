import { defineConfig } from 'vite';
import solidPlugin from 'vite-plugin-solid';
import path from 'path';

export default defineConfig({
  plugins: [solidPlugin()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: ['./vitest.setup.ts'],
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json', 'html'],
      exclude: [
        'node_modules/',
        'dist/',
        '**/*.config.*',
        '**/index.tsx',
      ],
    },
  },
  server: {
    host: '127.0.0.1',
    port: 3000,
    strictPort: true,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
        secure: false,
      },
      '/health': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
        secure: false,
      },
    },
  },
  build: {
    target: 'esnext',
    commonjsOptions: {
      transformMixedEsModules: true,
    },
    rollupOptions: {
      output: {
        manualChunks(id) {
          if (!id.includes('node_modules')) return;
          if (id.includes('plotly.js-dist-min')) return 'vendor-plotly';
          if (id.includes('marked') || id.includes('remark') || id.includes('highlight.js')) return 'vendor-markdown';
          if (id.includes('@supabase/')) return 'vendor-supabase';
          if (id.includes('@tanstack/')) return 'vendor-query';
          if (id.includes('@solidjs/router')) return 'vendor-router';
          if (id.includes('lucide-solid')) return 'vendor-icons';
          return 'vendor';
        },
      },
    },
  },
});
