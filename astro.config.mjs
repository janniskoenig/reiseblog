// @ts-check
import { defineConfig } from 'astro/config';
import mdx from '@astrojs/mdx';
import sitemap from '@astrojs/sitemap';

// TODO: nach dem ersten Deploy durch deine echte Adresse ersetzen,
// z. B. https://reiseblog.pages.dev oder https://deine-domain.de
export default defineConfig({
  site: 'https://reiseblog.pages.dev',
  integrations: [mdx(), sitemap()],
});
