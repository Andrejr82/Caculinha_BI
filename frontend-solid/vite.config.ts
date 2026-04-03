import path from 'node:path';
import { fileURLToPath } from 'node:url';

import { defineConfig } from 'vite';
import solidPlugin from 'vite-plugin-solid';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const root = __dirname;

const argv = process.argv.join(' ').toLowerCase();
const isVitest =
  process.env.VITEST === 'true' ||
  process.env.NODE_ENV === 'test' ||
  argv.includes('vitest');

export default defineConfig({
  root,
  plugins: [solidPlugin()],
  resolve: {
    preserveSymlinks: isVitest,
    alias: {
      '@': path.resolve(root, './src'),
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
          if (id.includes('plotly.js/lib/core')) return 'plotly-core';
          if (id.includes('plotly.js/lib/scatter')) return 'plotly-trace-scatter';
          if (id.includes('plotly.js/lib/bar')) return 'plotly-trace-bar';
          if (id.includes('plotly.js/lib/pie')) return 'plotly-trace-pie';
          if (id.includes('plotly.js/lib/histogram')) return 'plotly-trace-histogram';
          if (id.includes('plotly.js/lib/treemap')) return 'plotly-trace-treemap';
          if (id.includes('plotly.js/lib/box')) return 'plotly-trace-box';
          if (id.includes('marked') || id.includes('remark') || id.includes('highlight.js')) return 'vendor-markdown';
          if (id.includes('@supabase/')) return 'vendor-supabase';
          if (id.includes('@tanstack/')) return 'vendor-query';
          if (id.includes('@solidjs/router')) return 'vendor-router';
          if (id.includes('lucide-solid')) return 'vendor-icons';
        },
      },
    },
  },
  optimizeDeps: {
    noDiscovery: true,
    include: [],
  },
});
