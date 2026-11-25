// @ts-check
import { defineConfig } from 'astro/config';
import mdx from '@astrojs/mdx';
import sitemap from '@astrojs/sitemap';

// Live-Adresse (Cloudflare Pages). Bei eigener Domain hier ändern.
export default defineConfig({
  site: 'https://reiseblog-dln.pages.dev',
  integrations: [mdx(), sitemap({
    // Seiten mit „noindex“ gehören nicht in die Sitemap (sonst meldet Google einen Widerspruch).
    filter: (seite) => !/\/(impressum|datenschutz)\/$/.test(seite),
    // Handgebaute Seiten unter public/ kennt Astro nicht, deshalb hier nennen.
    customPages: ['', 'hochland/', 'trockener-westen/', 'suedwesten/', 'isalo/', 'sava/', 'reiseplanung/', 'hochland/reiseinfos/', 'trockener-westen/reiseinfos/', 'suedwesten/reiseinfos/', 'isalo/reiseinfos/', 'sava/reiseinfos/']
      .map((p) => `https://reiseblog-dln.pages.dev/madagaskar/${p}`),
  })],
});
