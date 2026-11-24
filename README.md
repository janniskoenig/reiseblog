# Reiseblog

Reise- und Outdoor-Blog mit [Astro](https://astro.build): Scrollytelling-Berichte, Karten mit GPX-Tracks, Galerien und ein einfaches Dashboard. Gehostet kostenlos auf Cloudflare Pages.

## Aufbau

| Ordner / Datei | Inhalt |
|---|---|
| `src/content/berichte/*.mdx` | Ein Bericht pro Region/Etappe. `beispiel.mdx` ist die Vorlage. |
| `src/components/` | Bausteine: `Hero`, `Story` + `Szene` (Sticky-Bild), `Atempause`, `Galerie` (mit Lightbox), `Karte` (Leaflet + GPX) |
| `src/pages/` | Seiten: Start, Berichte, Karte, Dashboard, Impressum, Datenschutz |
| `public/bilder/<bericht>/` | Fertig verkleinerte Fotos |
| `public/gpx/` | GPX-Dateien deiner Touren |
| `bilder-original/` | Deine Originalfotos (werden **nicht** hochgeladen) |

## Neuen Bericht schreiben

1. `src/content/berichte/beispiel.mdx` kopieren und umbenennen, z. B. `dolomiten.mdx`. Der Dateiname wird die Adresse: `/berichte/dolomiten/`.
2. Originalfotos nach `bilder-original/dolomiten/` legen und `npm run bilder` ausführen. Das verkleinert sie auf max. 2200 px und **entfernt die GPS-Daten** aus den Fotos (sonst könnte jeder z. B. deinen Wohnort aus Fotos von zu Hause auslesen).
3. Kopfbereich (Titel, Teaser, Highlights, Orte) ausfüllen, Szenen schreiben.
4. `entwurf: true` lassen, bis der Text fertig ist. Entwürfe sieht man nur lokal.

Regeln für Text und Aufbau stehen als Kommentare in der Vorlage.

## Lokal ansehen (optional)

Voraussetzung: [Node.js](https://nodejs.org) ab Version 22.

```bash
npm install
npm run dev      # öffnet http://localhost:4321
```

## Online stellen mit Cloudflare Pages (kostenlos)

1. Konto anlegen auf <https://dash.cloudflare.com/sign-up>.
2. Im Dashboard: **Workers & Pages → Create → Pages → Connect to Git**, GitHub verbinden und dieses Repository auswählen.
   (Cloudflare bietet inzwischen auch „Workers“ für statische Seiten an. Beides ist kostenlos; Pages ist für den Anfang am einfachsten.)
3. Build-Einstellungen:
   - Framework preset: **Astro**
   - Build command: `npm run build`
   - Build output directory: `dist`
   - Umgebungsvariable `NODE_VERSION` = `22` (falls der Build über die Node-Version klagt)
4. **Save and Deploy.** Nach 1–2 Minuten ist die Seite unter `https://<projektname>.pages.dev` erreichbar.
5. In `astro.config.mjs` bei `site` diese Adresse eintragen.

Ab dann geht jede Änderung, die auf GitHub landet, automatisch online.

**Grenzen im Gratis-Tarif** (laut Cloudflare, Stand Nov. 2026): 500 Builds pro Monat, 20.000 Dateien pro Seite, max. 25 MiB pro Datei. Für einen Blog reicht das gut. Videos besser komprimieren oder extern ablegen.

## Vor dem Veröffentlichen

- [ ] **Impressum** (`src/pages/impressum.astro`) und **Datenschutzerklärung** (`src/pages/datenschutz.astro`) ausfüllen. In Deutschland Pflicht für einen öffentlichen Blog.
- [ ] Blognamen in `src/layouts/Basis.astro` (`seitenname`) und Text auf der Startseite anpassen.
- [ ] Beispielbericht, Beispielbilder (`public/bilder/beispiel/`) und `public/gpx/beispiel.gpx` löschen.

## Hinweise

- Die Karten nutzen Kacheln von [OpenTopoMap](https://opentopomap.org) (kostenlos, Namensnennung ist eingebaut). Beim Öffnen einer Karte lädt der Browser die Kacheln von deren Servern; das gehört in die Datenschutzerklärung.
- Längen und Höhenmeter auf der Karte werden aus den GPX-Dateien berechnet (Höhenmeter mit 5-m-Schwelle gegen GPS-Rauschen). Sie können von Komoot/Strava abweichen.
- Alles, was auf der Seite liegt, ist öffentlich. Private „Nützliche Reiseinfos“ gehören nicht in ein öffentliches Repository bzw. auf die Seite, oder brauchen einen Zugangsschutz (z. B. Cloudflare Access, für bis zu 50 Personen kostenlos).
