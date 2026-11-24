// @ts-check
import { defineConfig } from 'astro/config';
import mdx from '@astrojs/mdx';
import sitemap from '@astrojs/sitemap';

// Live-Adresse (Cloudflare Pages). Bei eigener Domain hier ändern.
export default defineConfig({
  site: 'https://reiseblog-dln.pages.dev',
  integrations: [mdx(), sitemap()],
});
