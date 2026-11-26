import { defineCollection } from 'astro:content';
import { glob } from 'astro/loaders';
import { z } from 'astro/zod';

// Ein Ort auf der Karte (Koordinaten in Dezimalgrad)
const ort = z.object({
  name: z.string(),
  lat: z.number(),
  lng: z.number(),
});

// Scrollytelling-Berichte (öffentlich). Eine .mdx-Datei pro Region/Etappe.
const berichte = defineCollection({
  loader: glob({ pattern: '**/*.{md,mdx}', base: './src/content/berichte' }),
  schema: z.object({
    titel: z.string(),                         // kurz, z. B. „Tour durch den Trockenen Westen“
    kicker: z.string(),                        // Region · Orte
    untertitel: z.string(),                    // 3–4 Themen, darf den Titel nicht doppeln
    reise: z.string(),                         // z. B. „Madagaskar 2026“: gruppiert Etappen
    reihenfolge: z.number(),                   // Position in der Reiseroute (Etappen-Navigation)
    datum: z.coerce.date(),
    titelbild: z.string(),
    teaser: z.array(z.string()).min(1).max(2), // Absatz 1: Region, Absatz 2: Highlights
    highlights: z.array(z.object({ bild: z.string(), text: z.string() })).max(4).default([]),
    orte: z.array(ort).default([]),            // für Übersichtskarte und Dashboard
    gpx: z.array(z.string()).default([]),      // Pfade unter /gpx/…
    // Zusammenhängende Tour: vereinfachte Linie (JSON mit [lat, lng]-Paaren unter /routen/…).
    // Dann zeigt die Übersichtskarte eine Linie statt einzelner Orte.
    route: z.string().optional(),
    // Nur eigene, gemessene Werte eintragen. Leer lassen, wenn unbekannt.
    statistik: z.object({
      km: z.number().optional(),
      hoehenmeter: z.number().optional(),
      naechte: z.number().optional(),
      land: z.string().optional(),
    }).default({}),
    entwurf: z.boolean().default(false),       // true = wird nicht veröffentlicht
    // Fertige, handgebaute Seite unter public/ (z. B. „/madagaskar/hochland/“).
    // Dann ist die .mdx-Datei nur ein Steckbrief für Listen, Karte und Dashboard.
    extern: z.string().optional(),
  }),
});

export const collections = { berichte };
