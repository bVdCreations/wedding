import { defineConfig } from 'astro/config';
import tailwind from '@astrojs/tailwind';

export default defineConfig({
  output: 'static',
  integrations: [tailwind()],
  redirects: {
    '/': '/en',
  },
  server: {
    port: 4321,
    host: true,
  },
});
