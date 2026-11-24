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
