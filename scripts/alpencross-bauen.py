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
from PIL import Image

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
    9: ['Ruhetag am Gardasee: Mittags waren wir am Lago di Ledro. Am Abend war in der Ferne ein Waldbrand zu sehen.'],
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
    'Tag 8: Ging es über den Passo Bregn de l’Ors? Der höchste Punkt liegt laut GPS bei ca. 1.860 m.',
    'Kais Bremse: auf den letzten Kilometern welcher Etappe?',
    'Texte: Stichpunkte zu Tag 6 und 7 und gern mehr zu jedem Tag (Landschaft, Wetter, Essen, Unterkünfte)',
]

# --------------------------------------------------------------------------- Fotos
# Auswahl und Bildunterschriften von Jannis (28.11.2026), je Tag in Aufnahme-Reihenfolge.
# Zweite Auswahl (28.11. abends): bearbeitete iPhone-Fassungen. Foto 44fb5825 (Abschied vom Ristorante Da Giusy)
# bewusst noch nicht drin: Einverständnis der Wirtin ungeklärt.
# Dateien: bilder-original/mtb-alpencross/ (nicht im Repo) → npm run bilder → public/bilder/mtb-alpencross/
# (verkleinert, ohne EXIF/GPS). „geteilt-…“ = von Kai geteilte Fotos. Kai ist mit erkennbaren Fotos einverstanden.
# Eintrag: (Datei, Bildunterschrift, Absatz) – Absatz = Index in TEXTE[tag], der neben diesem Foto steht.
# Das erste Foto eines Tages trägt immer die Tagesüberschrift.
BILD = f'/bilder/{SLUG}/'
TITELBILD = ('geteilt-1703fca4', 'Angekommen im Gardasee')
FOTOS = {
    1: [('img-4141', 'Schloss Neuschwanstein mit der Marienbrücke', None),
        ('img-4143', 'Auf dem Weg Richtung Plansee', None),
        ('img-4147', 'Erste Pause am Plansee', 0),
        ('img-4169', 'Auf dem Uferweg hoch über dem Plansee', None),
        ('img-4177', 'Auf dem Uferweg am Plansee', None)],
    2: [('img-4208', 'Morgennebel auf dem Weg Richtung Ehrwald', None),
        ('img-4217', 'Einstieg in den Blindseetrail', 0),
        ('img-4224', 'Blick vom Blindseetrail auf den Blindsee', None),
        ('img-4231', 'Rastbank am Blindseetrail', None)],
    3: [('img-4264', 'Morgen am Klostergut Kronburg', None),
        ('img-4268', 'Pause oberhalb des Paznauntals', None),
        ('img-4270', 'An der Trisanna im Paznaun', None),
        ('img-4272', 'Die Trisanna bei Ischgl', None)],
    4: [('img-4279', 'Morgens im Fimbatal', 0),
        ('img-4286', 'Schiebepassage kurz vor dem Fimbapass', None),
        ('img-4289', 'Auf dem Fimbapass Trail', None),
        ('img-4293', 'Scuol mit der Kirche über dem Inn', None),
        ('img-4298', 'Im Val S-charl', 1)],
    5: [('img-4321', 'Bach auf dem Weg zum Döss Radond', None),
        ('img-4336', 'Im Val Mora', None),
        ('img-4347', 'Die Serpentinen der Scale di Fraele', None),
        ('img-4358', 'Almsiedlung im Val Grosina', None),
        ('img-4368', 'Willkommen an der Hütte La Baita', 0),
        ('img-4378', 'Abendspaziergang an der Hütte La Baita', None),
        ('img-4390', 'Die Hütte La Baita am Abend', None)],
    6: [('img-4399', 'See unterhalb des Passo di Gavia', None),
        ('img-4403', 'Trail hinunter Richtung Pezzo', None),
        ('img-4404', 'Trail hinunter Richtung Pezzo', None),
        ('img-4406', 'Alm auf dem Weg nach Pezzo', None),
        ('geteilt-3f14a706', 'Trail hinunter Richtung Pezzo', None),
        ('geteilt-07575dc2', 'Aperitif am Abend in Pezzo', None)],
    7: [('img-4425', 'Rückblick ins Tal oberhalb von Pezzo', None),
        ('img-4431', 'Steinmänner am Montozzo', None),
        ('img-4432', 'Abfahrt mit Blick auf den Stausee', None),
        ('img-4435', 'Trail hinunter zum Stausee', None),
        ('img-4442', 'Erster Blick auf die Brenta', None),
        ('img-4443', 'Hinweis auf Braunbären', None),
        ('img-4466', 'Abend am Rifugio Vallesinella', None),
        ('img-4467', 'Ein Brenta Bräu am Rifugio Vallesinella', None),
        ('geteilt-1f369e19', 'Feierabendbier am Rifugio Vallesinella', None),
        ('img-4468', 'Abend am Rifugio Vallesinella', None)],
    8: [('img-4477', 'Wasserfall bei Vallesinella', None),
        ('img-4478', 'Morgens in den Brenta-Dolomiten', None),
        ('img-4487', 'Pause am Lago di Valagola', None),
        ('img-4497', 'Schiebestück kurz vor dem höchsten Punkt der Etappe', None),
        ('img-4513', 'Lago di Tenno', 0),
        ('img-4517', 'Erster Blick auf den Gardasee', None),
        ('img-4524', 'Angekommen: am Hafen von Riva del Garda', None),
        ('img-4526', 'Eis zur Ankunft in Riva del Garda', None),
        ('geteilt-1703fca4', 'Angekommen im Gardasee', None),
        ('img-4536', 'Abend mit Blick auf den Gardasee', None),
        ('img-4538', 'Abendessen oberhalb von Torbole', None)],
    9: [('img-4597', 'Pizza am Ufer in Torbole', 0)],
}
# Unterkunft auf der Karte → Foto (nur wo eins von der Unterkunft dabei ist)
UNTERKUNFT_FOTO = {2: 'img-4264', 5: 'img-4390', 7: 'img-4466'}

def bild(name):
    return f'{BILD}{name}.jpg'

def art(name):
    w, h = Image.open(ROOT / 'public' / bild(name).lstrip('/')).size
    return 'quer' if w / h > 1.05 else 'hoch'

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

def _ersetze(js, alt, neu):
    if neu in js:  # Vorlage hat es schon (Alta-Via-Fotos eingebaut)
        return js
    assert js.count(alt) == 1, alt[:60]
    return js.replace(alt, neu)
# Am Handy bleibt bei Hochformat-Abschnitten das Querformat im Streifen (data-unit-mobil)
STORY_JS = _ersetze(STORY_JS, '      var unit = activeSection.getAttribute("data-unit");\n',
    '      var unit = (window.innerWidth < 800 && activeSection.getAttribute("data-unit-mobil")) || activeSection.getAttribute("data-unit");\n')
# Streifen-Unterschrift = Unterschrift des aktiven Bildes
STORY_JS = _ersetze(STORY_JS, '        var capText = activeSection.getAttribute("data-caption");\n',
    '        var aktivBild = story.querySelector(\'.story-img[data-unit="\' + unit + \'"]\');\n'
    '        var capText = aktivBild ? aktivBild.getAttribute("alt") : activeSection.getAttribute("data-caption");\n')
# Lightbox zeigt die Bildunterschrift
STORY_JS = _ersetze(STORY_JS, "overlay.innerHTML = '<img loading=\"lazy\" class=\"lightbox-full\">';",
    "overlay.innerHTML = '<img loading=\"lazy\" class=\"lightbox-full\"><div class=\"lightbox-bu\"></div>';")
STORY_JS = _ersetze(STORY_JS, '      full.src = img.tagName === "IMG" ? img.src : img.getAttribute("data-full");\n',
    '      full.src = img.tagName === "IMG" ? img.src : img.getAttribute("data-full");\n'
    '      overlay.querySelector(".lightbox-bu").textContent = img.getAttribute("alt") || "";\n')
STORY_JS = _ersetze(STORY_JS, '      if (best) { full.src = best.src; overlay.classList.add("open"); }',
    '      if (best) { full.src = best.src; overlay.querySelector(".lightbox-bu").textContent = best.getAttribute("alt") || ""; overlay.classList.add("open"); }')

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
/* Fotos: Hoch-/Querformat je Gerät (wie Alta Via) */
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
figure.foto { margin: 0; }
.bu-unter { margin: .45rem 0 0; font-size: .82rem; line-height: 1.45; color: var(--muted); text-align: left; }
.bu-drauf { position: absolute; left: 0; right: 0; bottom: 0; padding: 1.6rem .8rem .55rem; color: #fff;
  font-size: .78rem; line-height: 1.4; background: linear-gradient(transparent, rgba(0,0,0,.6));
  text-shadow: 0 1px 3px rgba(0,0,0,.6); pointer-events: none; }
.lightbox-overlay { flex-direction: column; gap: .6rem; }
.lightbox-full { max-height: calc(100% - 3rem); }
.lightbox-bu { color: #ddd; font-size: .85rem; text-align: center; max-width: 40rem; }
/* Hochformat am Handy (Wunsch Jannis 28.11.2026): nicht im Streifen, sondern als Vollbild, das stehen bleibt;
   nur der Textkasten scrollt darüber. Am Desktop bleibt es in der linken Spalte. */
.vollbild, .vollbild-luft { display: none; }
@media (max-width: 799px) {
  .tagstory .story-img.hoch { display: none; }
  .tagstory.nurhoch .story-media { display: none; }
  .tagstory .story-section.hochbild { position: relative; z-index: 4; padding: 0; background: #000; min-height: 0; }
  .hochbild .vollbild { display: block; position: -webkit-sticky; position: sticky; top: 0; height: 100vh; height: 100svh; margin: 0; }
  .hochbild .vollbild img { display: block; width: 100%; height: 100%; object-fit: cover; cursor: zoom-in; }
  .hochbild .vollbild .bu-drauf { padding-bottom: max(.8rem, env(safe-area-inset-bottom, 0px)); }
  .hochbild .vollbild-text { position: relative; margin: 0 1rem; padding: 1.1rem 1.25rem 1.2rem;
    background: rgba(18,17,15,.78); -webkit-backdrop-filter: blur(5px); backdrop-filter: blur(5px);
    border-radius: 12px; color: #f3f1ec; }
  .hochbild .vollbild-luft { display: block; height: 55vh; height: 55svh; }
  .story-section.pic.hochbild .vollbild-luft { height: 35vh; height: 35svh; }
  .hochbild .vollbild-text h3 { color: #f2b47a; }
  .hochbild .vollbild-text p, .hochbild .vollbild-text .etappe-zahlen { color: #f3f1ec; }
  .hochbild .vollbild-text > :last-child { margin-bottom: 0; }
}
/* Titelbild im Hochformat: Desktop Foto neben Titel und Einleitung, Handy Foto als Vollbild, Titel darunter */
.hero-hoch { max-width: 64rem; padding: 1.5rem 1.5rem 2rem; display: grid; gap: 1rem 2.5rem; align-items: center; }
.hero-hoch .hero-img { display: block; width: 100%; height: auto; max-height: none; aspect-ratio: var(--ar); object-fit: cover; margin: 0; cursor: zoom-in; }
.hero-hoch .posttitle { padding: 0; margin: 0 0 1rem; max-width: none; }
@media (min-width: 800px) {
  .hero-hoch { grid-template-columns: minmax(0, 5fr) minmax(0, 6fr); }
  .hero-hoch .hero-img { max-height: 85vh; border-radius: 10px; }
}
@media (max-width: 799px) {
  .hero-hoch { padding: 0 0 1.5rem; }
  .hero-hoch .hero-img { border-radius: 0; max-height: 100svh; }
  .hero-hoch .bu-unter { padding: 0 1.5rem; }
  .hero-hoch .hero-inner { padding: 1rem 1.5rem 0; }
}
.leaflet-popup-content .huette-img { display: block; width: 100%; height: 110px; object-fit: cover; border-radius: 6px; margin-bottom: .4rem; }
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
                        day=u.get('naechte', f"Tag {u['tag']}"), lat=lat, lon=lon,
                        img=bild(UNTERKUNFT_FOTO[u['tag']]) if u['tag'] in UNTERKUNFT_FOTO else '',
                        imgAlt=next((b for t in FOTOS.values() for n, b, _ in t if n == UNTERKUNFT_FOTO.get(u['tag'])), '')))
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

def tag_story(tag, titel, zahlen_html, platzhalter_html=''):
    """Sticky-Story eines Tages: ein Abschnitt je Foto, Texte stehen neben dem in FOTOS genannten Foto."""
    fotos, texte = FOTOS[tag], TEXTE.get(tag, [])
    genutzt = sorted(a for _, _, a in fotos if a is not None)
    assert genutzt == list(range(len(texte))), f'Tag {tag}: Absätze {genutzt}, Texte {len(texte)}'
    arten = [art(n) for n, _, _ in fotos]
    units = [f't{tag}-{i}' for i in range(len(fotos))]
    def ersatz(i):  # Querformat für den Handy-Streifen neben einem Hochformat
        vor = [units[j] for j in range(i) if arten[j] == 'quer']
        nach = [units[j] for j in range(i + 1, len(fotos)) if arten[j] == 'quer']
        return (vor[-1:] or nach[:1] or [None])[0]
    imgs, secs = [], []
    for i, (name, bu, absatz) in enumerate(fotos):
        bu_ = esc(bu)
        imgs.append(f'<img class="story-img {arten[i]}{" active" if i == 0 else ""}" data-unit="{units[i]}" '
                    f'src="{bild(name)}" alt="{bu_}" loading="lazy">')
        inhalt = ''
        if i == 0:
            inhalt += f'<h3>{esc(titel)}</h3>{zahlen_html}'
        if absatz is not None:
            inhalt += '<p>' + esc(texte[absatz]) + '</p>'
        if i == 0:
            inhalt += platzhalter_html
        attr = (f' id="tag{tag}"' if i == 0 else '') + f' data-unit="{units[i]}" data-caption="{bu_}"'
        cls = '' if inhalt else ' pic'
        if arten[i] == 'hoch':
            e = ersatz(i)
            if e:
                attr += f' data-unit-mobil="{e}"'
            voll = (f'<figure class="vollbild"><img class="lightbox-img" src="{bild(name)}" alt="{bu_}" loading="lazy">'
                    f'<figcaption class="bu-drauf">{bu_}</figcaption></figure>')
            text_ = (f'<div class="vollbild-text">{inhalt}</div>' if inhalt else '') + '<div class="vollbild-luft"></div>'
            secs.append(f'<section class="story-section{cls} hochbild"{attr}>{voll}{text_}</section>')
        else:
            secs.append(f'<section class="story-section{cls}"{attr}>{inhalt}</section>')
    nurhoch = ' nurhoch' if 'quer' not in arten else ''
    nl = '\n    '
    return f"""
<div class="story tagstory{nurhoch}">
  <div class="story-media lightbox-container">
    {''.join(imgs)}
    <div class="story-caption">{esc(fotos[0][1])}</div>
  </div>
  <div class="story-text">
    {nl.join(secs)}
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
    w, h = Image.open(ROOT / 'public' / bild(TITELBILD[0]).lstrip('/')).size
    s += (f'<section class="hero hero-hoch"><figure class="foto"><img class="hero-img lightbox-img" style="--ar:{w / h:.3f}" '
          f'src="{bild(TITELBILD[0])}" alt="{esc(TITELBILD[1])}"><figcaption class="bu-unter">{esc(TITELBILD[1])}</figcaption></figure>'
          f'<div class="hero-inner"><h1 class="posttitle">{esc(TITEL)}</h1><p>{esc(EINLEITUNG)}</p></div></section>\n')
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
                       '' if tag in TEXTE else luecke('Text zu diesem Tag folgt.'))
    s += tag_story(9, 'Tag 9: Am Gardasee', '')
    tag, datum, von, nach, km, up, dn, h = RUECKFAHRT  # ohne Foto
    s += (f'<section class="plain" id="tag{tag}"><h3>Tag {tag}: {esc(von)} → {esc(nach)}</h3>'
          f'{etappe_zahlen(km, up, dn)}{absaetze(tag)}</section>\n')
    s += f"""<section class="plain"><h2>Gesamteindruck</h2>{''.join('<p>' + esc(t) + '</p>' for t in GESAMTEINDRUCK)}</section>
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

if __name__ == '__main__':
    for pfad, inhalt in ((PFAD_BERICHT, bericht()), (PFAD_FAKTEN, fakten())):
        ziel = ROOT / 'public' / pfad.strip('/') / 'index.html'
        ziel.parent.mkdir(parents=True, exist_ok=True)
        ziel.write_text(inhalt, encoding='utf-8')
        print(f'✓ {pfad} – {ziel.stat().st_size // 1024} KB')
