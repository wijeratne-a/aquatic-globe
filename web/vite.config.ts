import { defineConfig } from 'vite';

export default defineConfig({
  define: {
    CESIUM_BASE_URL: JSON.stringify('/cesium'),
  },
  server: {
    port: 5173,
    host: true,
    watch: {
      ignored: ['**/public/tiles/**', '**/public/cesium/**'],
    },
  },
});
