#!/usr/bin/env python3
"""Übernimmt den fertigen Alta-Via-2-Bericht (zwei Artifacts) als statische Seiten:

  /alta-via-2/                Reisebericht (Scrollytelling)
  /alta-via-2/zahlen-fakten/  Zahlen & Fakten

- Eingebettete Fotos landen in bilder-original/alta-via-2/. Danach `npm run bilder`
  ausführen: das verkleinert sie nach public/bilder/alta-via-2/ und entfernt alle
  Metadaten (auch GPS).
- Die Karte nutzt Thunderforest (Stil in KARTENSTIL, Schlüssel in THUNDERFOREST_KEY)
  und ein lokal ausgeliefertes Leaflet (kein Abruf von fremden Servern außer den Kacheln).
- Die GPX-Downloads sind entfernt: Die Karte enthält nur einen stark vereinfachten
  Track (pro Etappe 150 Punkte, 30–50 % zu kurz), zum Nachwandern taugt der nicht.
  Echte GPX-Dateien bei Bedarf nach public/gpx/alta-via-2/ legen.
- Tippfehler und Platzhalter im Text werden über KORREKTUREN behoben.

Aufruf: python3 scripts/altavia-uebernehmen.py <bericht.html> <zahlen-fakten.html>
"""
import base64, hashlib, html, re, shutil, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BERICHT, FAKTEN = Path(sys.argv[1]), Path(sys.argv[2])
SLUG = 'alta-via-2'
BILD_ORIG = ROOT / 'bilder-original' / SLUG
SEITEN = ROOT / 'public' / SLUG
SITE = 'https://reiseblog-dln.pages.dev'
# Kartenanbieter: Thunderforest (kommerzielle Nutzung erlaubt, Gratis-Tarif 150.000 Kacheln/Monat).
# Der Schlüssel ist öffentlich im Seitenquelltext sichtbar, das ist bei Kartendiensten so vorgesehen.
THUNDERFOREST_KEY = 'c4727ce21bbf4fbd8633df99582a9e88'
KARTENSTIL = 'landscape'   # oder 'outdoors'
ID_BERICHT, ID_FAKTEN = '5UasJpd77p8L7U8QhbsPxu', 'LNQAen7CZcoiVQooHo5i5V'
PFAD_BERICHT, PFAD_FAKTEN = f'/{SLUG}/', f'/{SLUG}/zahlen-fakten/'

# (alt, neu) – jede Stelle muss genau so im Artifact vorkommen
KORREKTUREN = [
    ('Mit italienischen Hüttenflair', 'Mit italienischem Hüttenflair'),
    ('mit Umsteig in München', 'mit Umstieg in München'),
    # Platzhalter: Preis/Höhenmeter fehlen noch → vorerst ohne Zahl
    ('mit dem Bus zur Seilbahn (<strong>[Preis ergänzen] €</strong>)', 'mit dem Bus zur Seilbahn'),
    ('zu Fuß zurücklegen (<strong>[Höhenmeter ergänzen] Hm</strong>), das war', 'zu Fuß zurücklegen, das war'),
    ('Anstieg durch die XY-Scharte  bot', 'Anstieg durch eine Scharte bot'),
    ('Auch Busstops und -routen sind</blockquote>',
     'Auch Bushaltestellen und Busverbindungen sollte man vorher kennen.</blockquote>'),
    ('vom Essenstisch wahnsinnsblicke in das Tal', 'vom Essenstisch Wahnsinnsblicke ins Tal'),
    ('Wer am Vortagg mehr Strecke schafft und es bis zum das Rifugio Boè schafft - es wirkte',
     'Wer am Vortag mehr Strecke schafft und es bis zum Rifugio Boè schafft – es wirkte'),
    ('den Panoramaweg zum XY Stausee und unser nächsten UNterkunft dem Rifugio Rifugio Castiglioni Marmolada zu Ende ging. Hier erfreuten wir uns wieder an dem Komfort.&amp;#32;',
     'den Panoramaweg zum Fedaia-Stausee und zu unserer nächsten Unterkunft, dem Rifugio Castiglioni Marmolada, zu Ende ging. Hier erfreuten wir uns wieder am Komfort.'),
    ('ob wir ihn Queeren können um den Klettersteig zu gehen, oder eine längere umrundung',
     'ob wir ihn queren können, um den Klettersteig zu gehen, oder eine längere Umrundung'),
    ('Nicht nur ebeschrieben sie uns die aktuellen verhältnisse', 'Es beschrieb uns nicht nur die aktuellen Verhältnisse'),
    ('Auch wenn es in den Fingern juckte nochmal die Kletterfähigkeiten zu strapazieren, war es uns unklar wie viel schwieriger genau, haben wir uns entschieden',
     'Auch wenn es in den Fingern juckte, die Kletterfähigkeiten nochmal zu strapazieren: Weil unklar war, wie viel schwieriger genau, haben wir uns entschieden'),
    ('meine lieblings hütte', 'meine Lieblingshütte'),
    ('Klettersteige auslässt wäre', 'Klettersteige auslässt, wäre'),
    ('uns wieder zurück auf den Boden der Tatsachen zurückholte', 'uns wieder auf den Boden der Tatsachen zurückholte'),
    ('<p>*Mehr zu<strong> </strong>m<strong>e</strong>i<strong>n</strong>e**r Ausrüstung für Klettersteig-Hüttentouren folgt in einem eigenen Guide.*</p>',
     '<p><em>Mehr zu meiner Ausrüstung für Klettersteig-Hüttentouren folgt in einem eigenen Guide.</em></p>'),
    ('Pisciadùhütte mitzunehmen.&amp;#32;', 'Pisciadùhütte mitzunehmen.'),
    ('Polenta am Abend.&amp;#32;', 'Polenta am Abend.'),
    # Karte: Thunderforest statt Esri, Hüttenmarker ohne (fehlende) Fotos
    ('auf einer echten Geländekarte (Esri World Topo). Hütten antippen fürs Foto, Strecke antippen',
     'auf einer Geländekarte (Thunderforest). Hütten antippen für Name und Höhe, Strecke antippen'),
    ('Hütte antippen → Foto', 'Hütte antippen → Name und Höhe'),
    ('Distanz/Höhenmeter, GPX-Download und einen', 'Distanz/Höhenmeter und einen'),
    ('Strecke antippen → Zahlen, GPX &amp; Tagesbeschreibung', 'Strecke antippen → Zahlen &amp; Tagesbeschreibung'),
    ('\'<a href="\' + s.gpx + \'" download>GPX herunterladen \\u2193</a>\' +\n', ''),
    ('L.tileLayer("https://server.arcgisonline.com/ArcGIS/rest/services/World_Topo_Map/MapServer/tile/{z}/{y}/{x}", {\n      maxZoom: 17,\n      attribution: "Tiles &copy; Esri"\n    })',
     'L.tileLayer("https://tile.thunderforest.com/' + KARTENSTIL + '/{z}/{x}/{y}{r}.png?apikey=' + THUNDERFOREST_KEY + '", {\n      maxZoom: 18,\n      attribution: "Karten &copy; <a href=\\"https://www.thunderforest.com\\">Thunderforest</a>, Daten &copy; <a href=\\"https://www.openstreetmap.org/copyright\\">OpenStreetMap</a>-Mitwirkende"\n    })'),
    ('var html = \'<img src="\' + s.img + \'" alt="\' + s.name + \'" style="width:100%;height:100px;object-fit:cover;border-radius:6px;margin-bottom:.4rem;">\' +\n        \'<div class="title">\'',
     'var html = \'<div class="title">\''),
    ('<script src="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.js"></script>',
     '<script src="/vendor/leaflet-1.9.4.js"></script>'),
    # Track orange mit weißem Rand, damit er sich von der Karte abhebt
    ('      var line = L.polyline(pts, { color: "#b5651d", weight: 4, opacity: 0.85 }).addTo(map);',
     '      L.polyline(pts, { color: "#fff", weight: 9, opacity: 0.95, interactive: false }).addTo(map);\n'
     '      var line = L.polyline(pts, { color: "#d9480f", weight: 4.5, opacity: 1 }).addTo(map);'),
    ('line.on("mouseout", function(){ line.setStyle({ weight: 4 }); });',
     'line.on("mouseout", function(){ line.setStyle({ weight: 4.5 }); });'),
    ('radius: 7, color: "#b5651d", fillColor: "#b5651d", fillOpacity: 1, weight: 2',
     'radius: 7, color: "#fff", fillColor: "#d9480f", fillOpacity: 1, weight: 3'),
]
KORREKTUREN_FAKTEN = [
    ('Hütten- und Mertagestouren', 'Hütten- und Mehrtagestouren'),
    ('falls doch mal etwas dazwischenkommt, man sich trennen muss.', 'falls doch mal etwas dazwischenkommt oder man sich trennen muss.'),
]

KOPF_CSS = """
.blog-bar{display:flex;justify-content:space-between;align-items:center;gap:1rem;max-width:52rem;margin:0 auto;
 padding:max(.9rem,env(safe-area-inset-top,0px)) 1.5rem .9rem;font:600 .9rem/1.2 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif}
.blog-bar a{color:var(--muted,#6b6b66);text-decoration:none}
.blog-bar a:hover{text-decoration:underline}
.blog-bar span{display:flex;gap:1rem}
.blog-foot{padding:2rem 1.5rem 2.5rem;text-align:center;font:.85rem/1.5 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;color:var(--muted,#6b6b66)}
.blog-foot a{color:inherit}
"""

def kopf(titel, beschreibung, bild, pfad):
    t, d = html.escape(titel), html.escape(beschreibung)
    og = f'<meta property="og:image" content="{SITE}{bild}">\n' if bild else ''
    return f"""<!doctype html>
<html lang="de">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>{t} · Reiseblog</title>
<meta name="description" content="{d}">
<link rel="canonical" href="{SITE}{pfad}">
<meta property="og:type" content="article">
<meta property="og:title" content="{t}">
<meta property="og:description" content="{d}">
{og}<link rel="icon" href="/favicon.svg" type="image/svg+xml">
<style>{KOPF_CSS}</style>
"""

LEISTE = (f'<nav class="blog-bar" aria-label="Blog"><a href="/">← Reiseblog</a>'
          f'<span><a href="{PFAD_BERICHT}">Bericht</a><a href="{PFAD_FAKTEN}">Zahlen &amp; Fakten</a></span></nav>')
FUSS = ('<footer class="blog-foot"><a href="/">Reiseblog</a> · <a href="/impressum/">Impressum</a> · '
        '<a href="/datenschutz/">Datenschutz</a></footer>')

bilder = {}

def bild_speichern(m, s):
    daten = base64.b64decode(m.group(1))
    sha = hashlib.sha1(daten).hexdigest()
    if sha not in bilder:
        start = s.rfind('<', 0, m.start())
        tag = s[start:m.start()]
        h = re.search(r'data-unit="([\w-]+)"', tag)
        art = 'galerie' if 'gallery-img' in tag else 'titel' if 'hero-img' in tag else 'bild'
        name = f'{h.group(1) if h else art}-{sha[:6]}'
        (BILD_ORIG / f'{name}.jpg').write_bytes(daten)
        bilder[sha] = name
    return f'/bilder/{SLUG}/{bilder[sha]}.jpg'

def korrigieren(s, liste, datei):
    for alt, neu in liste:
        n = s.count(alt)
        assert n == 1, f'{datei}: „{alt[:60]}…“ kommt {n}× vor (erwartet 1×)'
        s = s.replace(alt, neu)
    return s

def karte_aufraeumen(s):
    # Verweise auf nie veröffentlichte Dateien (Hüttenfotos, GPX) entfernen
    s = re.sub(r',img:"\.\./assets/[^"]+"', '', s)
    s = re.sub(r',gpx:"\.\./assets/gpx/tag\d+\.gpx"', '', s)
    return s

def uebernehmen(quelle, liste, pfad, beschreibung):
    s = quelle.read_text(encoding='utf-8')
    # Hülle der Artifact-Auslieferung und eigenen <head> entfernen, Styles behalten
    if s.count('<body>') > 1:
        s = s[s.index('<body>') + 6:]
    styles = ''.join(re.findall(r'<style>.*?</style>', s[:s.index('<body>')], re.S))
    skripte_kopf = ''.join(re.findall(r'<script src="[^"]+"></script>', s[:s.index('<body>')]))
    titel = html.unescape(re.search(r'<title>(.*?)</title>', s, re.S).group(1)).strip()
    titel = re.sub(r' – [^–]+$', '', titel) if titel.count(' – ') > (1 if 'Zahlen' in titel else 0) else titel
    koerper = s[s.index('<body>') + 6:s.rindex('</body>')]
    s = styles + skripte_kopf + '\n</head>\n<body>\n' + koerper
    s = korrigieren(s, liste, quelle.name)
    if 'window.__routemapStops' in s:
        s = karte_aufraeumen(s)
    s = re.sub(r'data:image/jpeg;base64,([A-Za-z0-9+/=]+)', lambda m: bild_speichern(m, s), s)
    # Alte Kopf-/Fußzeile (alter Blogname) durch die des Blogs ersetzen
    s = re.sub(r'<header class="sitehead">.*?</header>', LEISTE, s, count=1, flags=re.S)
    s = re.sub(r'<footer class="sitefoot">.*?</footer>', FUSS, s, count=1, flags=re.S)
    s = s.replace(f'https://claude.ai/artifact/{ID_BERICHT}', PFAD_BERICHT)
    s = s.replace(f'https://claude.ai/artifact/{ID_FAKTEN}', PFAD_FAKTEN)
    rest = re.findall(r'https://claude\.ai/[^"\'\s<]+', s)
    assert not rest, f'unbekannte Artifact-Links: {rest}'
    # Fotos erst laden, wenn man in ihre Nähe scrollt (außer Titelbild)
    s = re.sub(r'<img (?![^>]*loading=)(?![^>]*hero-img)', '<img loading="lazy" ', s)
    og = re.search(r'class="hero-img[^"]*" src="([^"]+)"', s)
    ziel = ROOT / 'public' / pfad.strip('/') / 'index.html'
    ziel.parent.mkdir(parents=True, exist_ok=True)
    ziel.write_text(kopf(titel, beschreibung, og.group(1) if og else None, pfad) + s + '\n</body>\n</html>\n',
                    encoding='utf-8')
    print(f'✓ {pfad}  ({titel}) – {ziel.stat().st_size // 1024} KB')

if __name__ == '__main__':
    BILD_ORIG.mkdir(parents=True, exist_ok=True)
    uebernehmen(BERICHT, KORREKTUREN, PFAD_BERICHT,
                'Sieben Tage auf der Alta Via 2 durch die Dolomiten: von der Plosehütte über Puez, Sella und '
                'die Marmolada-Gletscherquerung bis zum Passo delle Selle. Reisebericht mit Karte und Fotos.')
    uebernehmen(FAKTEN, KORREKTUREN_FAKTEN, PFAD_FAKTEN,
                'Alta Via 2 in Zahlen: Etappen, Distanzen, Höhenmeter und Gehzeiten der sieben Tage, '
                'dazu Tipps zu Hüttenbuchung, Planung und Packliste.')
    vendor = ROOT / 'public' / 'vendor' / 'leaflet-1.9.4.js'
    vendor.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy(ROOT / 'node_modules' / 'leaflet' / 'dist' / 'leaflet.js', vendor)
    print(len(bilder), 'Bilder nach', BILD_ORIG.relative_to(ROOT), '– jetzt `npm run bilder` ausführen.')
