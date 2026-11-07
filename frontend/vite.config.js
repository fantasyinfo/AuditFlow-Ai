import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    host: true,
    proxy: {
      '/auth': 'http://127.0.0.1:8000',
      '/documents': 'http://127.0.0.1:8000',
      '/invoices': 'http://127.0.0.1:8000',
      '/findings': 'http://127.0.0.1:8000',
      '/agent': 'http://127.0.0.1:8000',
      '/audit-logs': 'http://127.0.0.1:8000',
      '/health': 'http://127.0.0.1:8000',
    },
  },
});
