#!/usr/bin/env python3
"""Baut Jannis' Kamerafotos in den Alta-Via-2-Bericht ein (nach altavia-uebernehmen.py ausführen).

- Ersetzt den Abschnitt „Der Weg, Tag für Tag“ (Tag 1 bis Tag 7) durch eine Sticky-Story je Tag.
  Die Texte bleiben unverändert, sie werden nur absatzweise auf Bildwechsel verteilt.
- Hoch- und Querformat werden unterschiedlich behandelt:
    * Sticky-Bild: Handy = Streifen oben (Querformat füllt ihn, Hochformat ganz sichtbar auf Schwarz),
      Desktop = linke Spalte in voller Höhe (Hochformat füllt sie, Querformat ganz sichtbar auf Schwarz).
    * Bildreihe je Tag: Bildbreite richtet sich nach dem Seitenverhältnis (Blocksatz-Reihen). Am Handy
      stehen Hochformate paarweise nebeneinander, Querformate über die volle Breite.
    * Panoramen: Desktop über die volle Breite, Handy groß und seitlich zum Wischen.
- Hüttenmarker der Karte bekommen ein Foto, wo es eins gibt (sonst bleibt es bei Name und Höhe).
- Bilder liegen fertig verkleinert und ohne Metadaten unter public/bilder/alta-via-2/kamera-NNN.jpg
  (Quelle: E:\\Fotos\\2026\\Import Sep\\DNG\\JPEG\\2026MMTT_AltaVia2_NNN.jpg).

Aufruf: python3 scripts/altavia-fotos.py
"""
import json
import math
import re
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
SEITE = ROOT / 'public' / 'alta-via-2' / 'index.html'
BILD = ROOT / 'public' / 'bilder' / 'alta-via-2'
ALT = '/bilder/alta-via-2/'

def k(n):  # Kamerafoto
    return f'{ALT}kamera-{n:03d}.jpg'

# Pro Tag: Sticky-Bilder (eins je Absatz, in Reihenfolge; überzählige Bilder bekommen eine
# eigene Bildstrecke ohne Text), danach Bildreihe und ein großes Übergangsbild zum nächsten Tag.
# Bilder ohne „kamera“ stammen aus dem ursprünglichen Bericht.
TAGE = {
    1: dict(sticky=[k(3), f'{ALT}s1-1-a928bf.jpg'], reihe=[], danach=None),
    2: dict(sticky=[k(12), k(63), k(88), k(90)], reihe=[], danach=k(66)),
    3: dict(sticky=[k(102), k(128), k(146)], reihe=[], danach=k(137)),
    4: dict(sticky=[k(189), k(201)], reihe=[], danach=k(177)),
    5: dict(sticky=[k(216), k(257), k(284), k(291)], reihe=[f'{ALT}handy-piz-boe-gipfel.jpg', k(219), k(229), k(251), k(282), k(297)], danach=None),
    6: dict(sticky=[k(304), k(311)], reihe=[], danach=None),
    7: dict(sticky=[k(320), k(326), k(353), k(356)], reihe=[k(327), k(333), k(354), k(365), f'{ALT}handy-gulasch-selle.jpg'], danach=None),
}
TITELBILD = f'{ALT}kamera-251.jpg'
HUETTEN = {  # Kartenmarker → Foto
    'Schlüterhütte': (k(92), 'Die Schlüterhütte am Morgen'),
    'Pisciadùhütte': (k(186), 'Die Pisciadùhütte am Abend'),
    'Rifugio Passo delle Selle': (f'{ALT}kamera-354-huette.jpg', 'Das Rifugio Passo delle Selle auf dem Grat'),
    'Rifugio Castiglioni (Marmolada)': (f'{ALT}huette-castiglioni.jpg', 'Das Rifugio Castiglioni vor der Marmolada'),
    'Rifugio Contrin': (f'{ALT}huette-contrin.jpg', 'Das Rifugio Contrin'),
}
# Hütten unterwegs (kein Etappenziel): Koordinaten am Track geprüft (Halslhütte 134 m zum nächsten Trackpunkt bei ~170 m Punktabstand, Boè 30 m, Forcella Pordoi 5 m, San Nicolò 12 m, Baita alle Cascate 4 m, Capanna Piz Fassa 32 m, Viel dal Pan 6 m)
UNTERWEGS = [
    dict(name='Medalges-Alm', elev='2293 m', day='Tag 3', lat=46.62462, lon=11.79779, img='', imgAlt=''),  # OSM, 31 m vom Track
    dict(name='Halslhütte', elev='1866 m', day='Tag 2', lat=46.66657, lon=11.77067, img='', imgAlt='',
         info='Berggasthaus direkt an der Würzjoch-Straße'),
    dict(name='Tal bei Kolfuschg', elev='', day='Tag 4', lat=46.554543, lon=11.856001, img='', imgAlt='',
         info='Mehrere Cafés und Supermärkte im Tal'),
    dict(name='Rifugio Boè', elev='2873 m', day='Tag 5', lat=46.514416, lon=11.823517,
         img=f'{ALT}huette-boe.jpg', imgAlt='Das Rifugio Boè'),
    dict(name='Capanna Piz Fassa', elev='3152 m', day='Tag 5', lat=46.508925, lon=11.828067,
         img=f'{ALT}handy-piz-boe-gipfel.jpg', imgAlt='Die Capanna Piz Fassa auf dem Gipfel des Piz Boè'),
    dict(name='Rifugio Forcella Pordoi', elev='2848 m', day='Tag 5', lat=46.501807, lon=11.812463, img='', imgAlt=''),
    dict(name='Passo Pordoi', elev='', day='Tag 5', lat=46.487555, lon=11.813445, img='', imgAlt='',
         info='Mehrere Restaurants und Bars am Pass'),
    dict(name='Rifugio Viel dal Pan', elev='2432 m', day='Tag 5', lat=46.474242, lon=11.834336, img='', imgAlt='',
         info='Toller Blick von der Terrasse'),
    dict(name='Rifugio Passo San Nicolò', elev='', day='Tag 7', lat=46.42161, lon=11.79317,
         img=f'{ALT}huette-san-nicolo.jpg', imgAlt='Das Rifugio Passo San Nicolò'),
    dict(name='Baita alle Cascate', elev='', day='Tag 7', lat=46.416182, lon=11.781796, img='', imgAlt=''),
]

CSS = """
/* Kamerafotos: Hoch-/Querformat je Gerät */
.story-media.lightbox-container { cursor: zoom-in; }
.story-img.quer { object-fit: cover; }
.story-img.hoch { object-fit: contain; background: #000; }
@media (max-width: 799px) { .tagstory .story-media { height: 40vh; } }
@media (min-width: 800px) {
  .story-img.hoch { object-fit: cover; }
  .story-img.quer { object-fit: contain; background: #000; }
}
.tagstory .story-section.pic { min-height: 55vh; }
.tagstory .story-section:last-child { padding-bottom: 8vh; }
.bildreihe { display: flex; flex-wrap: wrap; gap: .4rem; padding: .4rem; background: #000; }
.bildreihe img { display: block; height: auto; min-width: 0; cursor: zoom-in; object-fit: cover;
  flex-grow: var(--ar); flex-basis: calc(var(--ar) * 9rem); aspect-ratio: var(--ar); }
@media (min-width: 800px) { .bildreihe img { flex-basis: calc(var(--ar) * 15rem); } }
.uebergang { background: #000; }
.uebergang img { display: block; width: 100%; max-height: 90vh; object-fit: cover; cursor: zoom-in; }
.pano { background: #000; overflow-x: auto; overscroll-behavior-x: contain; scrollbar-width: thin; }
.pano img { display: block; width: 100%; height: auto; max-width: 100%; cursor: zoom-in; }
.pano .wisch { display: none; }
@media (max-width: 799px) {
  .pano img { width: auto; height: 62vh; max-width: none; }
  .pano .wisch { display: block; position: sticky; left: 0; color: #ddd; font-size: .78rem; padding: .4rem 1rem .6rem; }
}
.leaflet-popup-content .huette-img { display: block; width: 100%; height: 110px; object-fit: cover; border-radius: 6px; margin-bottom: .4rem; }
"""

def masse(src):
    w, h = Image.open(ROOT / 'public' / src.lstrip('/')).size
    return w, h

def ar(src):
    w, h = masse(src)
    return w / h

def art(src):
    a = ar(src)
    return 'pano' if a > 2 else 'quer' if a > 1.05 else 'hoch'

def einmal(s, alt, neu):
    n = s.count(alt)
    assert n == 1, f'„{alt[:60]}…“ kommt {n}× vor (erwartet 1×)'
    return s.replace(alt, neu)

def absaetze_je_tag(block):
    """Alle Absätze (p, blockquote) und Überschriften der Tage aus den bisherigen Story-Abschnitten."""
    tage, aktuell = {}, None
    for inhalt in re.findall(r'<section class="story-section[^"]*"[^>]*>(.*?)</section>', block, re.S):
        for teil in re.findall(r'<h3>.*?</h3>|<p>.*?</p>|<blockquote>.*?</blockquote>', inhalt, re.S):
            m = re.match(r'<h3>Tag (\d)', teil)
            if m:
                aktuell = int(m.group(1)); tage[aktuell] = {'titel': teil, 'teile': []}
            elif teil.startswith('<h3>'):
                raise SystemExit(f'unerwartete Überschrift: {teil}')
            else:
                tage[aktuell]['teile'].append(teil)
    return tage

def abschnitte(teile):
    """Ein Bildwechsel je Absatz; ein Praxis-Tipp bleibt beim folgenden Absatz."""
    out, puffer = [], ''
    for t in teile:
        if t.startswith('<blockquote>'):
            puffer += t + '\n'
        else:
            out.append(puffer + t); puffer = ''
    if puffer:
        out.append(puffer)
    return out

def tag_html(nr, d, text):
    titel = re.sub(r'<.*?>', '', text['titel'])
    abschn = abschnitte(text['teile'])
    bilder = d['sticky']
    imgs, secs = [], []
    for i, src in enumerate(bilder):
        aktiv = ' active' if i == 0 else ''
        imgs.append(f'<img class="story-img {art(src)}{aktiv}" data-unit="t{nr}-{i}" src="{src}" alt="{titel}" loading="lazy">')
    for i, a in enumerate(abschn):
        unit = f't{nr}-{min(i, len(bilder) - 1)}'
        kopf = (f' id="tag{nr}"' if i == 0 else '')
        h = text['titel'] if i == 0 else ''
        secs.append(f'<section class="story-section"{kopf} data-unit="{unit}" data-caption="{titel}">{h}{a}</section>')
    for i in range(len(abschn), len(bilder)):  # mehr Bilder als Absätze: Bildstrecke
        secs.append(f'<section class="story-section pic" data-unit="t{nr}-{i}" data-caption="{titel}"></section>')
    out = [f'''<div class="story tagstory">
  <div class="story-media lightbox-container">
    {"".join(imgs)}
    <div class="story-caption">{titel}</div>
  </div>
  <div class="story-text">
    {"".join(secs)}
  </div>
</div>''']
    if d['reihe']:
        out.append('<div class="bildreihe">' + ''.join(
            f'<img class="lightbox-img" style="--ar:{ar(s):.3f}" src="{s}" alt="{titel}" loading="lazy">' for s in d['reihe']) + '</div>')
    if d['danach']:
        s = d['danach']
        if art(s) == 'pano':
            out.append(f'<div class="pano"><img class="lightbox-img" src="{s}" alt="Panorama, {titel}" loading="lazy">'
                       f'<span class="wisch">← Panorama: zur Seite wischen →</span></div>')
        else:
            out.append(f'<div class="uebergang"><img class="lightbox-img" src="{s}" alt="{titel}" loading="lazy"></div>')
    return '\n'.join(out)

def main():
    s = SEITE.read_text(encoding='utf-8')
    assert 'class="story tagstory"' not in s, 'Fotos sind schon eingebaut – zuerst altavia-uebernehmen.py neu ausführen'
    start = s.index('<div class="story">', s.index('<h2>Der Weg, Tag für Tag</h2>'))
    ende = s.index('<section class="plain sub"><h3>Rückreise</h3>')
    block = s[start:ende]
    text = absaetze_je_tag(block)
    assert sorted(text) == list(range(1, 8)), sorted(text)
    for src in [b for d in TAGE.values() for b in d['sticky'] + d['reihe'] + ([d['danach']] if d['danach'] else [])]:
        assert (ROOT / 'public' / src.lstrip('/')).exists(), src
    neu = '\n\n'.join(tag_html(n, TAGE[n], text[n]) for n in range(1, 8)) + '\n'
    s = s[:start] + neu + s[ende:]
    s = einmal(s, '</style><script src="/vendor/leaflet-1.9.4.js">', CSS + '</style><script src="/vendor/leaflet-1.9.4.js">')
    # Karte: Hüttenfotos
    for name, (src, alt) in HUETTEN.items():
        s = einmal(s, f'{{name:"{name}",', f'{{name:"{name}",img:"{src}",imgAlt:"{alt}",')
    s = einmal(s, "var html = '<div class=\"title\">' + s.day + '</div>' + s.name + ' (' + s.elev + ')';",
               "var html = (s.img ? '<img class=\"huette-img\" src=\"' + s.img + '\" alt=\"' + s.imgAlt + '\">' : '') +\n"
               "        '<div class=\"title\">' + s.day + '</div>' + s.name + ' (' + s.elev + ')';")
    # Kartenmarker: Übernachtung = Häuschen mit Tageszahl, Einkehrmöglichkeit = kleine graue Tasse (Wunsch Jannis 26.11.)
    HAUS = ('<svg viewBox="0 0 24 24" width="28" height="28"><path d="M12 2.5 1.8 11.2h3v10h14.4v-10h3z" fill="#d9480f" '
            'stroke="#fff" stroke-width="1.6" stroke-linejoin="round"/><text x="12" y="18.6" text-anchor="middle" '
            'font-size="9.5" font-weight="700" fill="#fff" font-family="system-ui,sans-serif">N</text></svg>')
    TASSE = ('<svg viewBox="0 0 24 24" width="18" height="18"><circle cx="12" cy="12" r="11" fill="#fff" stroke="#8a8a8a" stroke-width="1.2"/>'
             '<path d="M6.5 9h8.5v4.2a3.6 3.6 0 0 1-3.6 3.6h-1.3a3.6 3.6 0 0 1-3.6-3.6z M15 10h1.2a1.9 1.9 0 0 1 0 3.8H15" '
             'fill="none" stroke="#6f6f6f" stroke-width="1.7" stroke-linejoin="round"/></svg>')
    s = einmal(s, 'window.__routemapSegs = [', 'window.__routemapHuts = ' + json.dumps(UNTERWEGS, ensure_ascii=False) + ';\nwindow.__routemapSegs = [')
    s = einmal(s, "      marker.bindPopup(html, { maxWidth: 220 });\n    });\n",
               "      marker.bindPopup(html, { maxWidth: 220 });\n    });\n"
               "    (window.__routemapHuts || []).forEach(function(s){\n"
               "      var m = L.marker([s.lat, s.lon], { icon: L.divIcon({ className: 'mk-einkehr', html: " + json.dumps(TASSE) + ",\n"
               "        iconSize: [18, 18], iconAnchor: [9, 9] }) }).addTo(map);\n"
               "      m.bindPopup((s.img ? '<img class=\"huette-img\" src=\"' + s.img + '\" alt=\"' + s.imgAlt + '\">' : '') +\n"
               "        '<div class=\"title\">Einkehrmöglichkeit · ' + s.day + '</div>' + s.name + (s.elev ? ' (' + s.elev + ')' : '') + (s.info ? '<br><small>' + s.info + '</small>' : ''), { maxWidth: 220 });\n"
               "    });\n")
    s = einmal(s, """      var marker = L.circleMarker([s.lat, s.lon], {
        radius: 7, color: "#fff", fillColor: "#d9480f", fillOpacity: 1, weight: 3
      }).addTo(map);""", """      var marker = L.marker([s.lat, s.lon], { icon: L.divIcon({ className: "mk-haus",
        html: """ + json.dumps(HAUS).replace('>N<', '>" + s.tag + "<') + """, iconSize: [28, 28], iconAnchor: [14, 20] }) }).addTo(map);""")
    # Abstieg zur Bushaltestelle Passo San Pellegrino (29.08.): nicht aufgezeichnet, Verlauf nach OSM-Wegen
    # (Sentiero 604, aus public/routen/alta-via-2.json → ergaenzt), gestrichelt (Wunsch Jannis 26.11.2026)
    abstieg = json.loads((ROOT / 'public' / 'routen' / 'alta-via-2.json').read_text(encoding='utf-8'))['ergaenzt'][0]
    s = einmal(s, 'window.__routemapSegs = [', 'window.__routemapAbstieg = ' + json.dumps(abstieg) + ';\nwindow.__routemapSegs = [')
    s = einmal(s, "    (window.__routemapHuts || []).forEach(function(s){\n",
               "    if (window.__routemapAbstieg) {\n"
               "      L.polyline(window.__routemapAbstieg, { color: '#fff', weight: 8, opacity: 0.9, interactive: false }).addTo(map);\n"
               "      var ab = L.polyline(window.__routemapAbstieg, { color: '#d9480f', weight: 4, opacity: 1, dashArray: '2 8', lineCap: 'round' }).addTo(map);\n"
               # Dauer: DAV-Faustformel (3,8 km, −610 Hm: Rifugio 2528 m → Pass 1918 m) ≈ 1:40 h; Jannis: „recht flott“ → ca. 1:30 h
               "      ab.bindPopup('<div class=\"title\">Abstieg am 29. August: Rifugio Passo delle Selle → Bushaltestelle Passo San Pellegrino Costabella</div>' +\n"
               "        '<div class=\"segstat\"><span class=\"ic\">↔</span>ca. 3,8 km</div>' +\n"
               "        '<div class=\"segstat\"><svg class=\"ic\" viewBox=\"0 0 24 24\" fill=\"currentColor\"><path d=\"M3 20 L9 8 L13 14 L16 9 L21 20 Z\"/></svg>ca. −610 Hm</div>' +\n"
               "        '<div class=\"segstat\"><span class=\"ic\">⏱</span>ca. 1:30 h</div>' +\n"
               "        '<small>Diesen Abschnitt habe ich nicht mehr aufgezeichnet. Verlauf, Distanz und Dauer sind geschätzt.</small>', { maxWidth: 230 });\n"
               "      L.circleMarker(window.__routemapAbstieg[window.__routemapAbstieg.length - 1], { radius: 5, color: '#fff', weight: 2, fillColor: '#555', fillOpacity: 1 })\n"
               "        .bindPopup('<div class=\"title\">Bushaltestelle</div>Passo San Pellegrino Costabella').addTo(map);\n"
               "    }\n"
               "    (window.__routemapHuts || []).forEach(function(s){\n")
    s = einmal(s, "      segLatLon.forEach(function(seg){ seg.forEach(function(p){ allPts.push(p); }); });\n",
               "      segLatLon.forEach(function(seg){ seg.forEach(function(p){ allPts.push(p); }); });\n"
               "      (window.__routemapAbstieg || []).forEach(function(p){ allPts.push(p); });\n")
    s = einmal(s, 'Hütten antippen für Name und Höhe,', 'Hütten antippen für Name, Höhe und Foto,')
    s = einmal(s, '<span><span class="dot"></span> Hütte antippen → Name und Höhe</span>',
               '<span>' + HAUS.replace('width="28" height="28"', 'width="20" height="20"').replace('>N<', '>1<') + ' Übernachtung</span>\n'
               '    <span>' + TASSE.replace('width="18" height="18"', 'width="15" height="15"') + ' Einkehrmöglichkeit</span>\n'
               '    <span><svg viewBox="0 0 24 6" width="22" height="6"><line x1="2" y1="3" x2="22" y2="3" stroke="#d9480f" stroke-width="3" stroke-dasharray="1.5 4" stroke-linecap="round"/></svg> Abstieg (nicht aufgezeichnet)</span>\n'
               '    <span><svg viewBox="0 0 24 6" width="22" height="6"><line x1="1" y1="3" x2="23" y2="3" stroke="#6f6f6f" stroke-width="2.5" stroke-dasharray="5 4"/></svg> Geplant, nicht gegangen</span>\n'
               '    <span>Hütte antippen → Foto</span>')
    s = einmal(s, '</style><script src="/vendor/leaflet-1.9.4.js">',
               '.mk-haus svg,.mk-einkehr svg{display:block;filter:drop-shadow(0 1px 2px rgba(0,0,0,.4))}\n'
               '</style><script src="/vendor/leaflet-1.9.4.js">')
    # Geplante, nicht gegangene Routen (Wunsch Jannis 26.11.2026): grau gestrichelt, OSM-Routing (Thread „Weitere Reisen“)
    geplant = []
    for tag, grund in ((4, 'Wegen glitschiger Bedingungen und Gewitterneigung nicht gegangen – stattdessen Abstieg nach Kolfuschg.'),
                       (7, 'Nicht gegangen: Laut Hütte war der Klettersteig nicht gut in Schuss und deutlich wilder als die übrigen der Tour.')):
        g = json.loads((ROOT / 'scripts' / 'daten' / f'altavia-geplant-tag{tag}.json').read_text(encoding='utf-8'))
        name = g['beschreibung'].split(': ', 1)[1].replace(' – ', ' → ')
        geplant.append(dict(pts=g['punkte'], html=(
            f'<div class="title">Geplant, nicht gegangen · Tag {tag}</div>{name}'
            f'<div class="segstat"><span class="ic">↔</span>ca. {str(g["km"]).replace(".", ",")} km</div>'
            f'<div class="segstat">ca. +{g["auf_hm"]} / −{g["ab_hm"]} Hm</div><small>{grund}</small>')))
    # Nur die Abschnitte zeichnen, die nicht auf dem echten Track liegen (Wunsch Jannis: „nicht doppelt auf dem orangenen“)
    _segs = json.loads(re.search(r'window\.__routemapSegLatLon\s*=\s*(\[.*?\]);', s, re.S).group(1))
    def _abst(p, a, b):
        ky = 111320; kx = 111320 * math.cos(math.radians(p[0]))
        ax, ay, bx, by, px, py = a[1]*kx, a[0]*ky, b[1]*kx, b[0]*ky, p[1]*kx, p[0]*ky
        dx, dy = bx-ax, by-ay; L = dx*dx+dy*dy
        t = 0 if L == 0 else max(0, min(1, ((px-ax)*dx+(py-ay)*dy)/L))
        return math.hypot(px-ax-t*dx, py-ay-t*dy)
    def _auf_track(p):
        return any(_abst(p, a, b) < 60 for seg in _segs for a, b in zip(seg, seg[1:])
                   if abs(a[0]-p[0]) < 0.01 and abs(a[1]-p[1]) < 0.015)
    for g in geplant:
        runs, cur = [], []
        for p in g['pts']:
            if _auf_track(p):
                if len(cur) > 3: runs.append(cur)
                cur = []
            else:
                cur.append(p)
        if len(cur) > 3: runs.append(cur)
        g['pts'] = runs
    s = einmal(s, 'window.__routemapSegs = [', 'window.__routemapGeplant = ' + json.dumps(geplant, ensure_ascii=False) + ';\nwindow.__routemapSegs = [')
    s = einmal(s, "    if (window.__routemapAbstieg) {\n",
               "    (window.__routemapGeplant || []).forEach(function(g){\n"
               "      var gl = L.polyline(g.pts, { color: '#6f6f6f', weight: 3.5, opacity: 0.9, dashArray: '6 7' }).addTo(map);\n"
               "      gl.bindPopup(g.html, { maxWidth: 240 });\n"
               "      gl.on('mouseover', function(){ gl.setStyle({ weight: 5 }); });\n"
               "      gl.on('mouseout', function(){ gl.setStyle({ weight: 3.5 }); });\n"
               "    });\n"
               "    if (window.__routemapAbstieg) {\n")
    # Abstecher (Wunsch Jannis 26.11.2026): Tageswerte enthalten freiwillige Abstecher → Stern + Fußnote.
    # Werte geschätzt aus Track (Hin-und-zurück-Stück) + Komoot-Höhenprofil; Dauer = Tagesgehzeit × Anteil nach DAV-Faustformel.
    ABSTECHER = {
        2: ('20,7 km', 'Peitlerkofel', 'ca. 4 km, ca. +500 Hm, ca. 2:30 h'),
        3: ('14,7 km', 'Piz Duleda', 'ca. 1,3 km, ca. +160 Hm, ca. 0:45 h'),
        7: ('15,7 km', 'Punta Alochet', 'ca. 2 km, ca. +100 Hm, ca. 0:50 h'),
    }
    for tag, (km, ziel, werte) in ABSTECHER.items():
        s = einmal(s, '{km:"' + km + '",', '{note:"* inkl. Abstecher auf ' + ('die ' if ziel.startswith('Punta') else 'den ') + ziel + ' (' + werte + ')",km:"' + km + '*",')
    s = einmal(s, "</svg>' + s.hm + '</div>' +\n",
               "</svg>' + s.hm + '</div>' +\n        (s.note ? '<div class=\"segnote\"><small>' + s.note + '</small></div>' : '') +\n")
    # Titelbild (Wunsch Jannis 26.11.2026): Kamerafoto statt Handyfoto mit Personen im Fokus
    s = s.replace('/bilder/alta-via-2/titel-2af9ad.jpg', TITELBILD)
    SEITE.write_text(s, encoding='utf-8')
    print('✓ Fotos eingebaut:', SEITE.relative_to(ROOT))
    # Zahlen & Fakten: Abstieg am 29.08. gehört noch zur Tour (Wunsch Jannis, 26.11.2026)
    fakten = SEITE.parent / 'zahlen-fakten' / 'index.html'
    f = fakten.read_text(encoding='utf-8')
    if '22.–29. August 2026' not in f:
        f = einmal(f, '<td>22.–28. August 2026</td>', '<td>22.–29. August 2026</td>')
        fakten.write_text(f, encoding='utf-8')
    f = fakten.read_text(encoding='utf-8')
    if 'inkl. Abstecher' not in f:
        fuss = []
        for tag, (km, ziel, werte) in ABSTECHER.items():
            f = einmal(f, '<td>' + km + '</td>', '<td>' + km + '*</td>')
            fuss.append(f'Tag {tag}: {ziel} ({werte})')
        f = einmal(f, '<td>ca. 104 km, ca. +6.200 / −5.700 Hm</td>', '<td>ca. 104 km, ca. +6.200 / −5.700 Hm*<br><small>* inkl. Abstecher, siehe „Der Weg, Tag für Tag“</small></td>')
        f = einmal(f, '</tbody></table></div></section>\n<section class="plain"><h2>Packen',
                   '</tbody></table></div>\n<p class="tabnote"><small>* inkl. Abstecher, die nicht zwingend zur Route gehören. ' + ' · '.join(fuss) + '. Werte für die Abstecher geschätzt.</small></p></section>\n<section class="plain"><h2>Packen')
        fakten.write_text(f, encoding='utf-8')
    print('✓ Zeitraum 22.–29. August:', fakten.relative_to(ROOT))

if __name__ == '__main__':
    main()
