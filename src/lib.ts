import { getCollection, type CollectionEntry } from 'astro:content';

export type Bericht = CollectionEntry<'berichte'>;

/** Alle veröffentlichten Berichte; Entwürfe nur im Entwicklungsmodus. */
export async function berichte(): Promise<Bericht[]> {
  const alle = await getCollection('berichte', (b) => import.meta.env.DEV || !b.data.entwurf);
  return alle.sort((a, b) =>
    a.data.reise === b.data.reise
      ? a.data.reihenfolge - b.data.reihenfolge
      : b.data.datum.valueOf() - a.data.datum.valueOf());
}

export const url = (pfad: string) => import.meta.env.BASE_URL.replace(/\/$/, '') + pfad;

/** Adresse eines Berichts: eigene Seite (extern) oder die gerenderte .mdx-Seite. */
export const link = (b: Bericht) => url(b.data.extern ?? `/berichte/${b.id}/`);

/** Reisen mit eigener Einstiegsseite (Übersicht über alle Etappen). */
export const reisen = [
  {
    name: 'Madagaskar 2026',
    link: url('/madagaskar/'),
    bild: '/bilder/madagaskar/allee_karren.jpg',
    text: 'Eine Reise durch fünf Regionen: Hochland, Trockener Westen, Südwesten, Isalo und Nordosten.',
    planung: url('/madagaskar/reiseplanung/'),
  },
];

// Übersichtskarten: ein Punkt pro Bericht (Region), nicht pro Ort.
// Position = Mittelpunkt der Orte des Berichts. Berichte mit durchgehender Route werden als Linie gezeichnet.
export function kartenpunkte(alle: Bericht[]) {
  return alle.filter((b) => !b.data.route && b.data.orte.length > 0).map((b) => {
    const o = b.data.orte;
    return {
      name: `${b.data.titel}<br><small>${o.map((x) => x.name).join(' · ')}</small>`,
      lat: o.reduce((s, x) => s + x.lat, 0) / o.length,
      lng: o.reduce((s, x) => s + x.lng, 0) / o.length,
      link: link(b),
    };
  });
}
