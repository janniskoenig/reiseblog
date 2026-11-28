#!/usr/bin/env python3
"""Suchmaschinen-Angaben für die handgebauten Seiten unter public/madagaskar/.

Setzt pro Seite Titel, Beschreibung, Open-Graph-/Twitter-Angaben und
strukturierte Daten (JSON-LD) und lässt Fotos erst laden, wenn man in ihre
Nähe scrollt (Lazy Loading). Das Skript kann beliebig oft laufen.

Aufruf:  python3 scripts/seo.py
Nach jedem erneuten `artifact-uebernehmen.py` wieder ausführen.

Faustregeln: Titel höchstens ca. 60 Zeichen (der Blogname wird nur angehängt,
wenn er noch passt; Google zeigt ihn ohnehin über jedem Treffer an),
Beschreibung ca. 120–155 Zeichen. Google kürzt längere Texte in der Trefferliste.
"""
import html, json, re
from pathlib import Path

SITE = 'https://reiseblog-dln.pages.dev'   # bei eigener Domain hier und in astro.config.mjs ändern
SEITENNAME = 'Jannis Outdoor-Reisen'       # wie `seitenname` in src/layouts/Basis.astro
AUTOR = 'Jannis König'
VEROEFFENTLICHT = '2026-11-24'             # erstmals online
REISE = ('Madagaskar 2026', '/madagaskar/')

# Pfad → (Titel ohne Seitennamen, Beschreibung, Art)
# Art: 'reise' = Übersicht, 'bericht' = Reisebericht, 'info' = Reiseinfos/Planung
SEITEN = {
    '/madagaskar/': (
        'Madagaskar-Rundreise: Route durch fünf Regionen',
        'Unsere Madagaskar-Reise im Oktober 2026: vom Hochland über den Trockenen Westen, '
        'den Südwesten und Isalo bis in die SAVA-Region im Nordosten.',
        'reise'),
    '/madagaskar/hochland/': (
        'Madagaskar Hochland: Von Tana nach Morondava',
        'Durchs Hochland Madagaskars: Reisterrassen, Pousse-pousse in Antsirabe, der Kratersee '
        'Lac Tritriva, Goldwäsche am Fluss und die ersten Baobabs bei Morondava.',
        'bericht'),
    '/madagaskar/trockener-westen/': (
        'Trockener Westen Madagaskars: Baobabs und Tsingy',
        'Von Morondava nach Norden: Allee der Baobabs, Mangroven von Kivalo, Lemuren im '
        'Kirindy-Wald und die Tsingy de Bemaraha. Reisebericht mit Fotos und Videos.',
        'bericht'),
    '/madagaskar/suedwesten/': (
        'Madagaskars Südwesten: Sandpisten und Traumstrände',
        'Über Sandpisten von Morondava nach Toliara: Belo-sur-Mer, die Pirogenfähre über '
        'den Mangoky, Baobabwälder, Korallenriffe und einsame Strände.',
        'bericht'),
    '/madagaskar/isalo/': (
        'Isalo-Nationalpark: Über die RN7 zu den Canyons',
        'Von Toliara über die RN7 zum Isalo-Massiv: Fenêtre de l’Isalo im Sonnenuntergang, '
        'zwei Tage Trekking durch Canyons, Naturpools, Zeltcamp und Lemuren.',
        'bericht'),
    '/madagaskar/sava/': (
        'SAVA-Region Madagaskar: Vanille, Küste, Tsingy',
        'Der tropische Nordosten Madagaskars: Sambava, Andapa, die Küste bis Vohémar und Diego '
        'mit Abstecher zu den Tsingy Rouge. Reisebericht aus der Vanilleregion.',
        'bericht'),
    '/madagaskar/reiseplanung/': (
        'Madagaskar Reiseplanung: Routen, Kosten, Tipps',
        'Madagaskar planen: Routenvorschläge für 2 bis 4 Wochen, Fahrer und Verkehrsmittel, '
        'Unterkünfte, Geld, typische Preise und Budget pro Tag aus eigener Erfahrung.',
        'info'),
    '/madagaskar/hochland/reiseinfos/': (
        'Madagaskar Hochland: Reiseinfos und Strecken',
        'Reiseinfos Hochland: Strecken und Straßenzustand von Tana über Antsirabe und den '
        'Lac Tritriva bis Morondava, Mountainbike-Runden, Unterkünfte und Essen.',
        'info'),
    '/madagaskar/trockener-westen/reiseinfos/': (
        'Trockener Westen Madagaskar: Reiseinfos Tsingy',
        'Reiseinfos Trockener Westen: Fahrzeiten und Fähren, Eintritt und Guides in Kirindy und '
        'den Tsingy de Bemaraha, Rundwege, Klettersteig und Unterkünfte.',
        'info'),
    '/madagaskar/suedwesten/reiseinfos/': (
        'Südwesten Madagaskar: Reiseinfos Sandpisten',
        'Reiseinfos Südwesten: Fahrzeiten auf den Sandpisten, Mangoky-Fähre, Maut und Gebühren, '
        'Belo-sur-Mer, Nosy Tania, Morombe und Ambatomilo.',
        'info'),
    '/madagaskar/isalo/reiseinfos/': (
        'Isalo-Nationalpark: Reiseinfos Trekking, Camp',
        'Reiseinfos Isalo: Strecke Toliara – Ranohira, Trekking im Nationalpark mit Guide, '
        'Zeltcamp, Unterkünfte in Ranohira und Toliara, beste Reisezeit.',
        'info'),
    '/madagaskar/sava/reiseinfos/': (
        'SAVA-Region Madagaskar: Reiseinfos und Strecken',
        'Reiseinfos Nordosten: Anreise per Flug, Straßenzustand von Sambava über Andapa und '
        'Vohémar bis Diego, Unterkünfte und Tipps zum Vanillekauf.',
        'info'),
}


def jsonld(pfad, titel, beschreibung, art, bild):
    url = SITE + pfad
    kette = [('Start', '/'), REISE]
    if pfad.endswith('/reiseinfos/'):
        bericht = pfad[:-len('reiseinfos/')]
        kette.append((SEITEN[bericht][0].split(':')[0], bericht))
    if pfad != REISE[1]:
        kette.append((titel, pfad))
    daten = [{
        '@context': 'https://schema.org', '@type': 'BreadcrumbList',
        'itemListElement': [{'@type': 'ListItem', 'position': i + 1, 'name': n, 'item': SITE + p}
                            for i, (n, p) in enumerate(kette)],
    }]
    if art in ('bericht', 'info'):
        artikel = {
            '@context': 'https://schema.org', '@type': 'BlogPosting' if art == 'bericht' else 'Article',
            'headline': titel, 'description': beschreibung, 'inLanguage': 'de-DE',
            'datePublished': VEROEFFENTLICHT, 'mainEntityOfPage': url,
            'author': {'@type': 'Person', 'name': AUTOR, 'url': SITE + '/'},
            'publisher': {'@type': 'Person', 'name': AUTOR},
        }
        if bild: artikel['image'] = [bild]
        daten.append(artikel)
    return '\n'.join('<script type="application/ld+json">' + json.dumps(d, ensure_ascii=False) + '</script>'
                     for d in daten)


def kopf(pfad, alt):
    titel, beschreibung, art = SEITEN[pfad]
    assert len(titel) <= 60, f'Titel zu lang: {titel}'
    assert 110 <= len(beschreibung) <= 160, f'Beschreibung {len(beschreibung)} Zeichen: {pfad}'
    m = re.search(r'<meta property="og:image" content="([^"]+)"', alt)
    bild = m.group(1) if m else None
    if not bild:  # erstes Foto der Seite als Vorschaubild
        m = re.search(r'<img[^>]+src="(/bilder/[^"]+)"', DATEI_TEXT)
        bild = SITE + m.group(1) if m else None
    if not bild and pfad.endswith('/reiseinfos/'):  # sonst das Bild des zugehörigen Berichts
        b = Path('public' + pfad[:-len('reiseinfos/')] + 'index.html').read_text(encoding='utf-8')
        m = re.search(r'<meta property="og:image" content="([^"]+)"', b)
        bild = m.group(1) if m else None
    t, d = html.escape(titel), html.escape(beschreibung)
    zeilen = [
        f'<title>{t} · {SEITENNAME}</title>' if len(titel) + len(SEITENNAME) + 3 <= 65 else f'<title>{t}</title>',
        f'<meta name="description" content="{d}">',
        f'<link rel="canonical" href="{SITE}{pfad}">',
        f'<meta property="og:type" content="{"article" if art != "reise" else "website"}">',
        f'<meta property="og:site_name" content="{SEITENNAME}">',
        '<meta property="og:locale" content="de_DE">',
        f'<meta property="og:url" content="{SITE}{pfad}">',
        f'<meta property="og:title" content="{t}">',
        f'<meta property="og:description" content="{d}">',
    ]
    if bild: zeilen.append(f'<meta property="og:image" content="{bild}">')
    zeilen.append('<meta name="twitter:card" content="summary_large_image">')
    if art != 'reise': zeilen.append(f'<meta property="article:published_time" content="{VEROEFFENTLICHT}">')
    zeilen.append(jsonld(pfad, titel, beschreibung, art, bild))
    return '\n'.join(zeilen) + '\n'


def lazy(s):
    """Fotos erst laden, wenn sie in die Nähe des Bildschirms kommen.
    Ausnahmen: das Titelbild (soll sofort erscheinen) und Bilder, deren Größe
    das Scrollytelling-Skript sofort braucht (Klasse „settle“)."""
    erstes = [True]
    def ersetze(m):
        tag = m.group(0)
        if 'src=' not in tag or 'loading=' in tag: return tag
        if 'ihero-img' in tag and erstes[0]:
            erstes[0] = False
            return tag if 'fetchpriority' in tag else tag.replace('<img ', '<img fetchpriority="high" ', 1)
        if re.search(r'class="[^"]*\bsettle\b', tag): return tag
        return tag[:-1].rstrip('/').rstrip() + ' loading="lazy" decoding="async">'
    return re.sub(r'<img\b[^>]*>', ersetze, s)


for pfad in SEITEN:
    datei = Path('public' + pfad + 'index.html')
    DATEI_TEXT = s = datei.read_text(encoding='utf-8')
    # Alles von <title> bis vor das Favicon ist der SEO-Block und wird neu geschrieben.
    m = re.search(r'<title>.*?(?=<link rel="icon")', s, re.S)
    s = s[:m.start()] + kopf(pfad, m.group(0)) + s[m.end():]
    # Blogname in Kopfleiste und Fußzeile (aus dem Import-Skript)
    s = re.sub(r'(<nav class="blog-bar[^"]*" aria-label="Blog"><a href="/">← )[^<]*(</a>)', r'\g<1>' + SEITENNAME + r'\2', s)
    s = re.sub(r'(<footer class="blog-foot"><a href="/">)[^<]*(</a>)', r'\g<1>' + SEITENNAME + r'\2', s)
    if SEITEN[pfad][2] == 'bericht':
        s = lazy(s)
    datei.write_text(s, encoding='utf-8')
    print('✓', pfad)
