// Verkleinert Fotos aus bilder-original/ nach public/bilder/ (gleiche Ordner).
// Längste Kante max. 2200 px, JPEG-Qualität 78. sharp entfernt dabei alle
// Metadaten (EXIF), also auch GPS-Koordinaten, Kamera und Seriennummer.
// Aufruf: npm run bilder
import { readdir, mkdir, stat } from 'node:fs/promises';
import { join, relative, dirname, extname, basename } from 'node:path';
import sharp from 'sharp';

const QUELLE = 'bilder-original', ZIEL = 'public/bilder', MAX = 2200, QUALITAET = 78;
const endungen = new Set(['.jpg', '.jpeg', '.png', '.heic', '.heif', '.webp', '.tif', '.tiff']);

async function* dateien(dir) {
  for (const e of await readdir(dir, { withFileTypes: true })) {
    const p = join(dir, e.name);
    if (e.isDirectory()) yield* dateien(p);
    else if (endungen.has(extname(e.name).toLowerCase())) yield p;
  }
}

let n = 0;
for await (const datei of dateien(QUELLE)) {
  const ziel = join(ZIEL, dirname(relative(QUELLE, datei)), basename(datei, extname(datei)).toLowerCase() + '.jpg');
  try { if ((await stat(ziel)).mtimeMs > (await stat(datei)).mtimeMs) continue; } catch {}
  await mkdir(dirname(ziel), { recursive: true });
  try {
    await sharp(datei).rotate() // Ausrichtung aus EXIF übernehmen, bevor EXIF entfernt wird
      .resize({ width: MAX, height: MAX, fit: 'inside', withoutEnlargement: true })
      .jpeg({ quality: QUALITAET, mozjpeg: true }).toFile(ziel);
    console.log('✓', ziel); n++;
  } catch (err) {
    console.warn('✗', datei, '–', err.message, '(HEIC ggf. vorher als JPEG exportieren)');
  }
}
console.log(n ? `${n} Bild(er) verarbeitet.` : 'Nichts zu tun.');
