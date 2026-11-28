#!/usr/bin/env python3
"""Baut das Gerüst für den MTB-Alpencross (1.–10. August 2026) im Alta-Via-Stil:

  /mtb-alpencross/                Bericht (Karte + Tag für Tag, Texte und Fotos folgen)
  /mtb-alpencross/zahlen-fakten/  Zahlen & Fakten (Etappen, Unterkünfte, Einkehr)

Quellen (nur Jannis' eigene Daten, nichts geschätzt):
- scripts/daten/alpencross-track.json       Track je Tag aus den vollständigen GPX-Dateien (Second Brain,
                                            raw/reisen/AlpenCross-Albrecht-2026-GPX), Douglas-Peucker 12 m
- scripts/daten/alpencross-hoechste-punkte.json  höchster Punkt je Tag aus denselben GPX-Dateien
- scripts/daten/alpencross-hoehenprofil.json Höhenprofil je Tag ([km, h0, h1, …], 90 Stützstellen)
- Jannis' Notizen (Second Brain, AlpenCross-Albrecht-Erfahrungsbericht-2026.md) für die Texte
- ETAPPEN unten: Distanz, Höhenmeter, Fahrzeit aus den Komoot-Aufzeichnungen (Artifact „Meine Touren“)

Layout, CSS und Story-/Lightbox-Skript kommen 1:1 aus public/alta-via-2/index.html, damit beide
Berichte gleich aussehen. Wenn sich dort etwas ändert, dieses Skript einfach erneut ausführen.

Offene Angaben stehen als sichtbare Platzhalter (Klasse .luecke) auf der Seite und in OFFEN.

Aufruf: python3 scripts/alpencross-bauen.py
"""
import html, json, re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SLUG = 'mtb-alpencross'
SITE = 'https://reiseblog-dln.pages.dev'
PFAD_BERICHT, PFAD_FAKTEN = f'/{SLUG}/', f'/{SLUG}/zahlen-fakten/'
VORLAGE = ROOT / 'public' / 'alta-via-2' / 'index.html'
TRACK = json.loads((ROOT / 'scripts' / 'daten' / 'alpencross-track.json').read_text())
PROFIL = json.loads((ROOT / 'scripts' / 'daten' / 'alpencross-hoehenprofil.json').read_text())
HOECHSTE = json.loads((ROOT / 'scripts' / 'daten' / 'alpencross-hoechste-punkte.json').read_text())
THUNDERFOREST_KEY = 'c4727ce21bbf4fbd8633df99582a9e88'
KARTENSTIL = 'landscape'
PLATZHALTER = f'/bilder/{SLUG}/platzhalter.svg'
# Solange Texte und Fotos fehlen: nicht von Suchmaschinen indexieren lassen
ENTWURF = True

TITEL = 'MTB-Alpencross: In acht Etappen vom Allgäu an den Gardasee'
BESCHREIBUNG = ('Mit dem Mountainbike in acht Etappen von Füssen über Landeck, das Münstertal und '
                'Madonna di Campiglio bis nach Torbole am Gardasee. Reisebericht mit Karte.')

# Tag, Datum, von, nach, km, +Hm, −Hm, Fahrzeit (h, Komoot-Aufzeichnung)
ETAPPEN = [
    (1, '01.08.', 'Füssen', 'Heiterwang', 33.8, 712, 525, 3.73),
    (2, '02.08.', 'Heiterwang', 'Landeck', 64.4, 1266, 1331, 6.28),
    (3, '03.08.', 'Landeck', 'Bodenalpe', 45.6, 1516, 636, 5.77),
    (4, '04.08.', 'Bodenalpe', 'Tschierv (Münstertal)', 64.5, 1991, 2130, 9.35),
    (5, '05.08.', 'Tschierv', 'Grosio', 73.4, 1726, 1543, 7.95),
    (6, '06.08.', 'Grosio', 'Pezzo', 25.8, 929, 1237, 4.38),
    (7, '07.08.', 'Pezzo', 'Madonna di Campiglio', 65.5, 2026, 2090, 8.87),
    (8, '08.08.', 'Madonna di Campiglio', 'Torbole (Gardasee)', 64.2, 1160, 2606, 8.17),
]
RUECKFAHRT = (10, '10.08.', 'Torbole', 'Bahnhof Rovereto', 22.2, 271, 146, 2.57)

# Übernachtungen: Name wie in Jannis' Stichpunkten; Lage = Etappenende im Track
UNTERKUENFTE = [
    dict(tag=1, name='Pension Posthansel', ort='Heiterwang'),
    dict(tag=2, name='Klostergut Kronburg', ort='bei Landeck'),
    dict(tag=3, name='Bodenalpe', ort=''),
    dict(tag=4, name='Al Rom', ort='Tschierv, Münstertal'),
    dict(tag=5, name='La Baita', ort='Grosio'),
    dict(tag=6, name='Ristorante Da Giusy', ort='Pezzo'),
    dict(tag=7, name='Vallesinella', ort='Madonna di Campiglio'),
    dict(tag=8, name='Eco Hotel Garnì Bonapace', ort='Torbole', naechte='Tag 8 und 9'),
]
# Einkehrmöglichkeiten unterwegs (graue Tasse): erst eintragen, wenn Jannis sie bestätigt hat.
# Format wie Alta Via: dict(name=…, elev='… m', day='Tag N', lat=…, lon=…, info='…', img='', imgAlt='')
EINKEHR = []

# Texte nur aus Jannis' Notizen (Second Brain: Erfahrungsbericht + Antworten vom 17.11. und 26.11.2026).
# Nichts ergänzen, was dort nicht steht; Lücken bleiben Platzhalter.
EINLEITUNG = ('Mein erster Alpencross, zusammen mit meinem Freund Kai: in acht Etappen mit dem Mountainbike '
              'von Füssen an den Gardasee, in Anlehnung an die Albrecht-Route. Unterwegs gab es viele schöne '
              'Trails und eine schöne Abwechslung bei Unterkünften und Regionen – am Ende wäre ich gerne noch '
              'weitergefahren.')
TEXTE = {
    1: ['Mit dem Zug ging es nach Füssen. Weil wir erst spät ankamen und am Nachmittag losfuhren, haben wir '
        'die erste Etappe auf zwei Tage aufgeteilt. Gleich am ersten Tag gab es ein Highlight: Baden im Plansee '
        'und die Fahrt auf dem Uferweg.'],
    2: ['Ein Highlight des Tages war der Blindseetrail.'],
    4: ['Von der Heidelberger Hütte ging es über den Fimbapass und dann auf dem Fimbapass Trail bergab, '
        'eines der Highlights der Tour.',
        'Ein weiteres Highlight war die Fahrt entlang eines Flusses durch die UNESCO-Biosfera Engiadina Val Müstair, '
        'zu der auch der Schweizerische Nationalpark gehört.'],
    5: ['Unterkunft war die entlegene Hütte La Baita in einer pittoresken Landschaft.'],
    8: ['Auf dem Weg zum Gardasee und am See selbst war das mediterrane Flair deutlich zu spüren.'],
    10: ['Der letzte Tag war keine richtige Etappe mehr, nur noch die Fahrt vom Gardasee zum Bahnhof in '
         'Rovereto. Von dort ging es mit dem Fernverkehrszug samt Rad nach Hause.'],
}
GESAMTEINDRUCK = [
    'Vor einigen Trails gab es Schiebepassagen, und manche Trails waren für mich zu anspruchsvoll. Wir sind '
    'aber immer auf Nummer sicher gefahren und haben nichts riskiert. Pannen hatte ich keine – bei Kai ging '
    'auf den letzten Kilometern die Bremse kaputt, zum Glück konnten wir sicher ausrollen.',
    'Die Regeneration war super: Dank der Vorbereitung konnte ich alles gut genießen, war nie so richtig k.o. '
    'und hatte auch nach langen Fahrtagen noch Kraftpuffer.',
    'Zum Gepäck: Die Kombination aus einem Cyclite-Touring-Rucksack (23 l) und der Cyclite-Lenkerrolle war '
    'super und stabil.',
]
FAZIT = 'Eine tolle Tour und Erfahrung mit schönen Trails. Ich wäre gerne noch weitergefahren.'

# Offene Fragen (erscheinen unten in Zahlen & Fakten unter „Noch zu ergänzen“)
OFFEN = [
    'Tag 2: Der Blindseetrail liegt am Fernpass, also auf der Etappe Heiterwang → Landeck. Passt das?',
    'Tag 8: Ging es über den Passo Bregn de l’Ors? Der höchste Punkt liegt laut GPS bei ca. 1.860 m.',
    'Kais Bremse: auf den letzten Kilometern welcher Etappe?',
    'Texte: Stichpunkte zu Tag 6 und 7 und gern mehr zu jedem Tag (Landschaft, Wetter, Essen, Unterkünfte)',
    'Fotos: Titelbild und Bilder je Tag',
]

# ---------------------------------------------------------------------------

def zahl(x, nachkomma=1):
    return f'{x:.{nachkomma}f}'.replace('.', ',')

def tsd(n):
    return f'{n:,}'.replace(',', '.')

def fahrzeit(h):
    m = round(h * 60)
    return f'{m // 60}:{m % 60:02d} h'

# Höchster Punkt je Tag: Name nur, wo GPS-Hochpunkt und Quelle zusammenpassen
# (bergwelten.com Albrechtroute-Etappen 3–6, tirol.at „Fimbapass … knapp über 2.600 m“)
PAESSE = {4: 'Fimbapass', 5: 'Döss Radond (2.240 m)', 6: 'Passo di Gavia (2.621 m)',
          7: 'Forcellina di Montozzo (2.613 m)'}

def hoechster(tag):
    return round(HOECHSTE[tag - 1], -1)

def ende_hoehe(tag):
    return round(PROFIL[tag - 1][-1], -1)

def esc(s):
    return html.escape(s, quote=True)

def hm_svg():
    return '<svg class="ic" viewBox="0 0 24 24" fill="currentColor"><path d="M3 20 L9 8 L13 14 L16 9 L21 20 Z"/></svg>'

vorlage = VORLAGE.read_text(encoding='utf-8')
STILE = re.findall(r'<style>.*?</style>', vorlage, flags=re.S)
assert len(STILE) == 2, 'Alta-Via-Vorlage: zwei <style>-Blöcke erwartet'
SKRIPTE = re.findall(r'<script>(.*?)</script>', vorlage, flags=re.S)
STORY_JS = SKRIPTE[1]
assert 'lightbox-overlay' in STORY_JS and 'routemap-leaflet' in STORY_JS
# Kartenteil der Vorlage abschneiden, die Karte baut dieses Skript selbst
STORY_JS = STORY_JS[:STORY_JS.index('  // interactive route map')] + '})();\n'

ZUSATZ_CSS = """<style>
.luecke{border:1.5px dashed #c98a4b;background:rgba(217,72,15,.05);color:inherit;padding:.7rem .9rem;border-radius:8px;font-size:.93rem;margin:.8rem 0}
.luecke strong{color:#b5651d}
.luecke ul{margin:.4rem 0 0;padding-left:1.2rem}
.luecke li{margin:.2rem 0}
td .luecke{margin:0;padding:.3rem .5rem;font-size:.88rem;white-space:normal}
.factstable td{white-space:normal}
.etappe-zahlen{display:flex;flex-wrap:wrap;gap:.3rem 1rem;font-size:.9rem;color:var(--muted,#6b6b66);margin:.2rem 0 .6rem}
.etappe-zahlen span{white-space:nowrap}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]) .luecke{border-color:#a8703c;background:rgba(224,151,90,.08)}}
:root[data-theme="dark"] .luecke{border-color:#a8703c;background:rgba(224,151,90,.08)}
</style>"""

KOPF_CSS = """
.blog-bar{display:flex;justify-content:space-between;align-items:center;gap:1rem;max-width:52rem;margin:0 auto;
 padding:max(.9rem,env(safe-area-inset-top,0px)) 1.5rem .9rem;font:600 .9rem/1.2 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif}
.blog-bar a{color:var(--muted,#6b6b66);text-decoration:none}
.blog-bar a:hover{text-decoration:underline}
.blog-bar span{display:flex;gap:1rem}
.blog-foot{padding:2rem 1.5rem 2.5rem;text-align:center;font:.85rem/1.5 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;color:var(--muted,#6b6b66)}
.blog-foot a{color:inherit}
"""

def kopf(titel, beschreibung, pfad, mit_karte):
    t, d = esc(titel), esc(beschreibung)
    leaflet = '<script src="/vendor/leaflet-1.9.4.js"></script>' if mit_karte else ''
    return f"""<!doctype html>
<html lang="de">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>{t} · Reiseblog</title>
<meta name="description" content="{d}">
{'<meta name="robots" content="noindex">' + chr(10) if ENTWURF else ''}<link rel="canonical" href="{SITE}{pfad}">
<meta property="og:type" content="article">
<meta property="og:title" content="{t}">
<meta property="og:description" content="{d}">
<link rel="icon" href="/favicon.svg" type="image/svg+xml">
<style>{KOPF_CSS}</style>
{''.join(STILE)}{ZUSATZ_CSS}{leaflet}
</head>
<body>

<nav class="blog-bar" aria-label="Blog"><a href="/">← Reiseblog</a><span><a href="{PFAD_BERICHT}">Bericht</a><a href="{PFAD_FAKTEN}">Zahlen &amp; Fakten</a></span></nav>
<article>
"""

FUSS = ('</article>\n<footer class="blog-foot"><a href="/">Reiseblog</a> · <a href="/impressum/">Impressum</a> · '
        '<a href="/datenschutz/">Datenschutz</a></footer>\n')

def luecke(text):
    return f'<div class="luecke"><strong>Platzhalter:</strong> {text}</div>'

# --------------------------------------------------------------------------- Karte

def stops():
    out = []
    for u in UNTERKUENFTE:
        lat, lon = TRACK[u['tag'] - 1][-1]
        name = u['name'] + (f", {u['ort']}" if u['ort'] else '')
        out.append(dict(name=name, elev=f"ca. {tsd(ende_hoehe(u['tag']))} m", tag=u['tag'],
                        day=u.get('naechte', f"Tag {u['tag']}"), lat=lat, lon=lon, img='', imgAlt=''))
    return out

KARTE_JS = r"""
(function(){
  if (!window.L || !document.getElementById("routemap-leaflet")) return;
  var D = window.__alpencross;
  var map = L.map("routemap-leaflet", { scrollWheelZoom: false });
  window.addEventListener("resize", function(){ map.invalidateSize(); });
  window.addEventListener("load", function(){ map.invalidateSize(); });
  L.tileLayer("https://tile.thunderforest.com/__STIL__/{z}/{x}/{y}{r}.png?apikey=__KEY__", {
    maxZoom: 18,
    attribution: "Karten &copy; <a href=\"https://www.thunderforest.com\">Thunderforest</a>, Daten &copy; <a href=\"https://www.openstreetmap.org/copyright\">OpenStreetMap</a>-Mitwirkende"
  }).addTo(map);
  var HM = '__HMSVG__';
  var alle = [];
  D.segs.forEach(function(s){
    s.pts.forEach(function(p){ alle.push(p); });
    L.polyline(s.pts, { color: "#fff", weight: 9, opacity: 0.95, interactive: false }).addTo(map);
    var line = L.polyline(s.pts, { color: "#d9480f", weight: 4.5, opacity: 1 }).addTo(map);
    line.bindPopup('<div class="title">' + s.titel + '</div>' +
      '<div class="segstat"><span class="ic">↔</span>' + s.km + '</div>' +
      '<div class="segstat">' + HM + s.hm + '</div>' +
      '<a href="#tag' + s.tag + '">Tagesbeschreibung lesen →</a>', { maxWidth: 220 });
    line.on("mouseover", function(){ line.setStyle({ weight: 6 }); });
    line.on("mouseout", function(){ line.setStyle({ weight: 4.5 }); });
  });
  D.stops.forEach(function(s){
    var m = L.marker([s.lat, s.lon], { icon: L.divIcon({ className: "mk-haus",
      html: "<svg viewBox=\"0 0 24 24\" width=\"28\" height=\"28\"><path d=\"M12 2.5 1.8 11.2h3v10h14.4v-10h3z\" fill=\"#d9480f\" stroke=\"#fff\" stroke-width=\"1.6\" stroke-linejoin=\"round\"/><text x=\"12\" y=\"18.6\" text-anchor=\"middle\" font-size=\"9.5\" font-weight=\"700\" fill=\"#fff\" font-family=\"system-ui,sans-serif\">" + s.tag + "</text></svg>",
      iconSize: [28, 28], iconAnchor: [14, 20] }) }).addTo(map);
    m.bindPopup((s.img ? '<img class="huette-img" src="' + s.img + '" alt="' + s.imgAlt + '">' : '') +
      '<div class="title">Übernachtung · ' + s.day + '</div>' + s.name + ' (' + s.elev + ')', { maxWidth: 220 });
  });
  (D.geplant || []).forEach(function(g){
    var gl = L.polyline(g.pts, { color: '#6f6f6f', weight: 3.5, opacity: 0.9, dashArray: '6 7' }).addTo(map);
    gl.bindPopup(g.html, { maxWidth: 240 });
  });
  (D.einkehr || []).forEach(function(s){
    var m = L.marker([s.lat, s.lon], { icon: L.divIcon({ className: 'mk-einkehr', html: "<svg viewBox=\"0 0 24 24\" width=\"18\" height=\"18\"><circle cx=\"12\" cy=\"12\" r=\"11\" fill=\"#fff\" stroke=\"#8a8a8a\" stroke-width=\"1.2\"/><path d=\"M6.5 9h8.5v4.2a3.6 3.6 0 0 1-3.6 3.6h-1.3a3.6 3.6 0 0 1-3.6-3.6z M15 10h1.2a1.9 1.9 0 0 1 0 3.8H15\" fill=\"none\" stroke=\"#6f6f6f\" stroke-width=\"1.7\" stroke-linejoin=\"round\"/></svg>",
      iconSize: [18, 18], iconAnchor: [9, 9] }) }).addTo(map);
    m.bindPopup((s.img ? '<img class="huette-img" src="' + s.img + '" alt="' + s.imgAlt + '">' : '') +
      '<div class="title">Einkehrmöglichkeit · ' + s.day + '</div>' + s.name + (s.elev ? ' (' + s.elev + ')' : '') + (s.info ? '<br><small>' + s.info + '</small>' : ''), { maxWidth: 220 });
  });
  var z = D.ziel;
  L.circleMarker(z.pt, { radius: 5, color: '#fff', weight: 2, fillColor: '#555', fillOpacity: 1 })
    .bindPopup('<div class="title">' + z.titel + '</div>' + z.text).addTo(map);
  map.fitBounds(alle, { padding: [20, 20] });
})();
""".replace('__STIL__', KARTENSTIL).replace('__KEY__', THUNDERFOREST_KEY).replace('__HMSVG__', hm_svg())

def karten_daten():
    sg = []
    for i, e in enumerate(ETAPPEN + [RUECKFAHRT]):
        tag, datum, von, nach, km, up, dn, h = e
        sg.append(dict(tag=tag, titel=f'Tag {tag}: {von} → {nach}', km=f'{zahl(km)} km',
                       hm=f'+{tsd(up)} / −{tsd(dn)} m', pts=TRACK[i]))
    return dict(segs=sg, stops=stops(), einkehr=EINKEHR, geplant=[],
                ziel=dict(pt=TRACK[8][-1], titel='Bahnhof Rovereto', text='Ende der Tour, Rückreise mit dem Zug'))

LEGENDE = """  <div class="legend">
    <span><svg viewBox="0 0 24 24" width="20" height="20"><path d="M12 2.5 1.8 11.2h3v10h14.4v-10h3z" fill="#d9480f" stroke="#fff" stroke-width="1.6" stroke-linejoin="round"/><text x="12" y="18.6" text-anchor="middle" font-size="9.5" font-weight="700" fill="#fff" font-family="system-ui,sans-serif">1</text></svg> Übernachtung</span>
    <span><span class="bar"></span> Strecke antippen → Zahlen &amp; Tagesbeschreibung</span>
  </div>"""

# --------------------------------------------------------------------------- Bericht

def tag_story(tag, titel, zahlen_html, inhalt_html):
    cap = esc(titel)
    return f"""
<div class="story tagstory">
  <div class="story-media lightbox-container">
    <img class="story-img quer active" data-unit="t{tag}-0" src="{PLATZHALTER}" alt="{cap} (Foto folgt)" loading="lazy">
    <div class="story-caption">{cap}</div>
  </div>
  <div class="story-text">
    <section class="story-section" id="tag{tag}" data-unit="t{tag}-0" data-caption="{cap}"><h3>{cap}</h3>{zahlen_html}{inhalt_html}</section>
  </div>
</div>
"""

def etappe_zahlen(km, up, dn):
    return (f'<p class="etappe-zahlen"><span>↔ {zahl(km)} km</span>'
            f'<span>↑ {tsd(up)} Hm</span><span>↓ {tsd(dn)} Hm</span></p>')

def absaetze(tag):
    return ''.join('<p>' + esc(t) + '</p>' for t in TEXTE.get(tag, []))

def bericht():
    s = kopf(TITEL, BESCHREIBUNG, PFAD_BERICHT, True)
    s += f'<h1 class="posttitle">{esc(TITEL)}</h1>\n'
    s += (f'<section class="hero"><img class="hero-img" src="{PLATZHALTER}" alt="Titelbild folgt">'
          f'<div class="hero-inner">{'<p>' + esc(EINLEITUNG) + '</p>'}</div></section>\n')
    s += f"""
<section class="plain routemap-wrap">
  <h2>Die Route</h2>
  <p class="note">Der aufgezeichnete GPS-Track auf einer Geländekarte (Thunderforest). Übernachtungen antippen für Name und Höhe, Strecke antippen für Distanz/Höhenmeter und einen Sprung zur Tagesbeschreibung.</p>
  <div id="routemap-leaflet"></div>
{LEGENDE}
</section>
<script>window.__alpencross = {json.dumps(karten_daten(), ensure_ascii=False, separators=(',', ':'))};</script>
<script>{KARTE_JS}</script>
<section class="plain"><h2>Der Weg, Tag für Tag</h2><p>Acht Etappen mit dem Mountainbike vom Allgäu an den Gardasee – die genauen Etappenlängen, Höhenmeter und Fahrzeiten stehen in <a href="{PFAD_FAKTEN}">Zahlen &amp; Fakten</a>.</p></section>
"""
    for (tag, datum, von, nach, km, up, dn, h) in ETAPPEN:
        s += tag_story(tag, f'Tag {tag}: {von} → {nach}', etappe_zahlen(km, up, dn),
                       absaetze(tag) + luecke('Fotos folgen.' if tag in TEXTE else 'Text und Fotos zu diesem Tag folgen.'))
    s += tag_story(9, 'Tag 9: Am Gardasee', '', '<p>Ruhetag am Gardasee: Mittags waren wir am Lago di Ledro. Am Abend war in der Ferne ein Waldbrand zu sehen.</p>')
    tag, datum, von, nach, km, up, dn, h = RUECKFAHRT
    s += tag_story(10, f'Tag 10: {von} → {nach}', etappe_zahlen(km, up, dn),
                   absaetze(10))
    s += f"""<section class="plain"><h2>Gesamteindruck</h2>{''.join('<p>' + esc(t) + '</p>' for t in GESAMTEINDRUCK)}</section>
<section class="plain sub"><h3>Weitere Eindrücke</h3>{luecke('Galerie: Fotos folgen.')}</section>
<section class="plain"><h2>Fazit</h2><p>{esc(FAZIT)}</p></section>

<section class="plain crosslink">
  <h3>Alle Zahlen und Fakten zur Tour</h3>
  <p>Etappenlängen, Höhenmeter, Fahrzeiten, Unterkünfte – gebündelt in <a href="{PFAD_FAKTEN}">Zahlen &amp; Fakten zum Alpencross</a>.</p>
</section>
"""
    s += FUSS + f'\n<script>{STORY_JS}</script>\n</body>\n</html>\n'
    return s

# --------------------------------------------------------------------------- Zahlen & Fakten

def fakten():
    t = TITEL + ' – Zahlen & Fakten'
    s = kopf(t, 'Der MTB-Alpencross in Zahlen: Etappen, Distanzen, Höhenmeter und Fahrzeiten, '
                'dazu die Unterkünfte.', PFAD_FAKTEN, False)
    s += f'<h1 class="posttitle">{esc(t)}</h1>\n<p class="crosslink-back"><a href="{PFAD_BERICHT}">← Zurück zum Bericht</a></p>\n'
    km = sum(e[4] for e in ETAPPEN); up = sum(e[5] for e in ETAPPEN); dn = sum(e[6] for e in ETAPPEN)
    route = ' → '.join([ETAPPEN[0][2]] + [e[3] for e in ETAPPEN])
    s += f"""<section class="plain"><h2>Auf einen Blick</h2><div class="table-scroll"><table class="factstable">
<thead><tr><th></th><th></th></tr></thead>
<tbody>
<tr><td><strong>Zeitraum</strong></td><td>1.–10. August 2026</td></tr>
<tr><td><strong>Dauer</strong></td><td>8 Etappen, dazu ein Ruhetag am Gardasee und die Rückfahrt zum Bahnhof Rovereto</td></tr>
<tr><td><strong>Strecke</strong></td><td>{esc(route)}</td></tr>
<tr><td><strong>Distanz / Höhenmeter</strong></td><td>{zahl(km, 0)} km, +{tsd(up)} / −{tsd(dn)} Hm<br><small>ohne Rückfahrt nach Rovereto ({zahl(RUECKFAHRT[4])} km)</small></td></tr>
<tr><td><strong>Höchster Punkt</strong></td><td>ca. {tsd(max(hoechster(e[0]) for e in ETAPPEN))} m am Passo di Gavia (Tag 6)</td></tr>
<tr><td><strong>Rad und Gepäck</strong></td><td>Fully; Cyclite-Touring-Rucksack (23 l) und Cyclite-Lenkerrolle</td></tr>
<tr><td><strong>Unterkunft</strong></td><td>Jede Nacht woanders, siehe Unterkünfte unten</td></tr>
<tr><td><strong>Gruppengröße</strong></td><td>2 Personen</td></tr>
<tr><td><strong>An- und Abreise</strong></td><td>Mit dem Zug nach Füssen; zurück ab Rovereto mit dem Fernverkehrszug samt Rad</td></tr>
</tbody></table></div>
{luecke('Bewertung (Ausdauer, Schwierigkeit, Landschaft jeweils 1–5) wie bei der Alta Via?')}</section>
"""
    s += """<section class="plain"><h2>Die Etappen, Tag für Tag</h2><div class="table-scroll"><table class="factstable">
<thead><tr><th>Tag</th><th>Datum</th><th>Etappe</th><th>Distanz</th><th>Höhenmeter</th><th>Fahrzeit</th><th>Höchster Punkt</th></tr></thead>
<tbody>
"""
    for (tag, datum, von, nach, km_, up_, dn_, h) in ETAPPEN:
        s += (f'<tr><td>{tag}</td><td>{datum}</td><td>{esc(von)} → {esc(nach)}</td><td>{zahl(km_)} km</td>'
              f'<td>+{tsd(up_)}/−{tsd(dn_)}</td><td>{fahrzeit(h)}</td><td>ca. {tsd(hoechster(tag))} m' + (f'<br><small>{esc(PAESSE[tag])}</small>' if tag in PAESSE else '') + '</td></tr>\n')
    s += '<tr><td>9</td><td>09.08.</td><td>Gardasee</td><td>–</td><td>–</td><td>–</td><td>–</td></tr>\n'
    tag, datum, von, nach, km_, up_, dn_, h = RUECKFAHRT
    s += (f'<tr><td>{tag}</td><td>{datum}</td><td>{esc(von)} → {esc(nach)}</td><td>{zahl(km_)} km</td>'
          f'<td>+{tsd(up_)}/−{tsd(dn_)}</td><td>{fahrzeit(h)}</td><td>–</td></tr>\n')
    s += ('</tbody></table></div>\n<p class="tabnote"><small>Distanz, Höhenmeter und Fahrzeit aus den Aufzeichnungen, '
          'höchster Punkt aus den GPS-Tracks (gerundet).</small></p></section>\n')
    s += """<section class="plain"><h2>Unterkünfte</h2><div class="table-scroll"><table class="factstable">
<thead><tr><th>Nacht</th><th>Unterkunft</th><th>Ort</th><th>Höhe</th><th>Hinweise</th></tr></thead>
<tbody>
"""
    for u in UNTERKUENFTE:
        name = luecke('Name?') if u.get('offen') else esc(u['name'])
        ort = esc(u['ort']) if u['ort'] else '–'
        s += (f"<tr><td>{u.get('naechte', 'Tag ' + str(u['tag']))}</td><td>{name}</td><td>{ort}</td>"
              f"<td>ca. {tsd(ende_hoehe(u['tag']))} m</td><td>–</td></tr>\n")
    s += ('</tbody></table></div>\n'
          + luecke('Hinweise je Unterkunft: Lage, Zimmer, Essen, Radkeller, was gut oder weniger gut war.')
          + '</section>\n')
    s += '<section class="plain"><h2>Einkehr unterwegs</h2><p>Unterwegs gab es meist genug Möglichkeiten zum Einkehren.</p></section>\n'
    s += ('<section class="plain"><h2>Noch zu ergänzen</h2><div class="luecke"><ul>'
          + ''.join(f'<li>{esc(f)}</li>' for f in OFFEN) + '</ul></div></section>\n')
    s += FUSS + '\n</body>\n</html>\n'
    return s

PLATZHALTER_SVG = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1500 1000" width="1500" height="1000">
<rect width="1500" height="1000" fill="#e9e4dc"/>
<path d="M0 760 L330 430 L520 610 L780 300 L1080 640 L1250 500 L1500 720 L1500 1000 L0 1000 Z" fill="#d6cdbf"/>
<path d="M0 860 L420 640 L700 800 L1000 600 L1500 860 L1500 1000 L0 1000 Z" fill="#c9bead"/>
<text x="750" y="520" text-anchor="middle" font-family="system-ui,-apple-system,sans-serif" font-size="64" font-weight="600" fill="#8a7b66">Foto folgt</text>
</svg>
"""

if __name__ == '__main__':
    bild = ROOT / 'public' / 'bilder' / SLUG / 'platzhalter.svg'
    bild.parent.mkdir(parents=True, exist_ok=True)
    bild.write_text(PLATZHALTER_SVG, encoding='utf-8')
    for pfad, inhalt in ((PFAD_BERICHT, bericht()), (PFAD_FAKTEN, fakten())):
        ziel = ROOT / 'public' / pfad.strip('/') / 'index.html'
        ziel.parent.mkdir(parents=True, exist_ok=True)
        ziel.write_text(inhalt, encoding='utf-8')
        print(f'✓ {pfad} – {ziel.stat().st_size // 1024} KB')
