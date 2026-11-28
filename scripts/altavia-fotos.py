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
# Bildfolge je Tag in Aufnahme-Reihenfolge (Wunsch Jannis 28.11.2026: Chronologie beachten).
# ('text', bild) = nächster Textabschnitt mit diesem Sticky-Bild (None = Bild bleibt wie davor),
# ('bild', bild) = Bildabschnitt ohne Text, ('pano'|'gross', bild) und ('reihe', [bilder]) unterbrechen die Story.
TAGE = {
    1: [('text', k(3)), ('text', f'{ALT}s1-1-a928bf.jpg')],
    # Hochformat vom Peitlerkofel raus (Jannis 28.11.: das Panorama zeigt dasselbe)
    2: [('text', k(12)), ('text', None), ('pano', k(66)), ('text', k(88)), ('bild', k(90))],
    3: [('text', k(102)), ('text', k(128)), ('pano', k(137)), ('text', k(146))],
    # Alle drei Fotos vom selben Abend an der Pisciadùhütte; Panorama nicht vor die Tagesüberschrift
    4: [('text', k(189)), ('pano', k(177)), ('text', k(201))],
    5: [('text', k(216)), ('bild', k(257)), ('reihe', [f'{ALT}handy-piz-boe-gipfel.jpg', k(282)]), ('bild', k(284)), ('bild', k(291))],
    6: [('text', k(304)), ('text', k(311)), ('text', None)],
    7: [('text', k(320)), ('bild', k(326)), ('gross', k(327)), ('text', f'{ALT}handy-gulasch-selle.jpg'), ('text', k(353)), ('text', k(356))],
}
TITELBILD = f'{ALT}kamera-251.jpg'
# Bildunterschriften (Wunsch Jannis 28.11.2026: knapp, was man sieht). Nach Ansicht der Fotos formuliert;
# Orts- und Gipfelnamen nur, wo sie sicher sind (Schild im Bild, Fotoauswahl-Notizen oder eindeutige Ansicht).
BU = {
    # Überarbeitet nach Wunsch Jannis 28.11.2026: Ort und Kontext statt Bildbeschreibung.
    # Verortung über Tag (Aufnahmedatum), Reihenfolge der Dateinummern, Berichtstext und Ansicht.
    TITELBILD: 'Sellagruppe: Tiefblick zwischen den Felstürmen',
    k(3): 'Seilbahn und Almen an der Plose, am Morgen nach der Ankunft',
    f'{ALT}s1-1-a928bf.jpg': 'Vorspeisenteller am ersten Abend auf der Plosehütte',
    k(12): 'Weidenröschen auf dem Weg Richtung Peitlerkofel',
    k(63): 'Aussicht beim Abstecher auf den Peitlerkofel',
    k(66): 'Panorama beim Abstecher auf den Peitlerkofel',
    k(88): 'Sonnenuntergang an der Schlüterhütte',
    k(90): 'Abendlicht über den Almen an der Schlüterhütte',
    k(102): 'Morgennebel nach dem Start an der Schlüterhütte',
    k(128): 'Unterwegs von der Schlüterhütte Richtung Roascharte',
    k(133): 'Unsere Gruppe auf dem Weg Richtung Roascharte',
    k(137): 'Panorama auf dem Weg Richtung Roascharte',
    k(146): 'Ausblick bei der Roascharte',
    k(189): 'Abendstimmung an der Pisciadùhütte: Wolken ziehen durchs Tal',
    k(201): 'Blaue Stunde: Blick von der Pisciadùhütte hinunter nach Kolfuschg',
    k(177): 'Abendpanorama von der Pisciadùhütte ins Gadertal',
    k(216): 'Sonnenaufgang an der Pisciadùhütte',
    k(257): 'Felstürme der Sellagruppe auf dem Weg zum Piz Boè',
    k(284): 'Abstieg durch die Forcella Pordoi',
    k(291): 'Vom Bindelweg auf Marmolada und Fedaia-Stausee',
    f'{ALT}handy-piz-boe-gipfel.jpg': 'Andrang an der Capanna Piz Fassa auf dem Gipfel des Piz Boè',
    k(282): 'Blick zur Marmolada, darunter die Serpentinen am Pordoijoch',
    k(304): 'Aufbruch am Fedaia-Stausee beim Rifugio Castiglioni',
    k(311): 'Schmelzwassersee am Marmoladagletscher',
    k(320): 'Morgens im Contrintal: Kühe auf der Alm',
    k(326): 'Holzbrücke im Contrintal',
    k(353): 'Letzter Morgen am Passo delle Selle',
    k(356): 'Morgenlicht am Passo delle Selle vor dem Abstieg',
    k(327): 'Bachbett und Holzsteg im Contrintal',
    f'{ALT}handy-gulasch-selle.jpg': 'Gulasch zum Abschluss im Rifugio Passo delle Selle',
    k(219): 'Sonnenaufgang über dem Gadertal, oberhalb der Pisciadùhütte',
    k(229): 'Rückblick auf die Pisciadùhütte und ihren See',
    k(297): 'Abendlicht am Bindelweg',
    k(333): 'Pfad durch die Lärchen Richtung Passo San Nicolò',
    k(354): 'Das Rifugio Passo delle Selle auf dem Grat',
    k(365): 'Kuh am Passo delle Selle am letzten Morgen',
}
# „Weitere Eindrücke“: nur Kamerafotos (Jannis 26.11.: Handyfotos wirken daneben flau), entlastet die Bildreihen
GALERIE = [k(219), k(229), k(297), k(333), k(354), k(365)]
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
.bildreihe img { display: block; height: auto; min-width: 0; cursor: zoom-in; object-fit: cover; aspect-ratio: var(--ar); }
.uebergang { background: #000; }
.uebergang img { display: block; width: 100%; max-height: 90vh; object-fit: cover; cursor: zoom-in; }
.pano { background: #000; overflow-x: auto; overscroll-behavior-x: contain; scrollbar-width: thin; }
.pano img { display: block; width: 100%; height: auto; max-width: 100%; cursor: zoom-in; }
.pano .wisch { display: none; }
@media (max-width: 799px) {
  .pano img { width: auto; height: 62vh; max-width: none; }
  .pano .wisch { display: block; position: sticky; left: 0; color: #ddd; font-size: .78rem; padding: .4rem 1rem .6rem; }
}
/* Bildunterschriften */
.bu-unter { margin: .45rem 0 0; font-size: .82rem; line-height: 1.45; color: var(--muted); text-align: left; }
figure.foto { margin: 0; }
.hero figure.foto { margin-bottom: 1.5rem; }
.hero figure.foto .hero-img { margin-bottom: 0; }
.plain figure.foto { margin: 1rem 0; }
.plain figure.foto .inline-img { margin: 0; }
.gallery-grid figure.foto .bu-unter { font-size: .76rem; margin-top: .3rem; }
.bildreihe figure { position: relative; margin: 0; min-width: 0;
  flex-grow: var(--ar); flex-basis: calc(var(--ar) * 9rem); }
@media (min-width: 800px) { .bildreihe figure { flex-basis: calc(var(--ar) * 15rem); } }
.bildreihe figure img { width: 100%; }
.bu-drauf { position: absolute; left: 0; right: 0; bottom: 0; padding: 1.6rem .8rem .55rem; color: #fff;
  font-size: .78rem; line-height: 1.4; background: linear-gradient(transparent, rgba(0,0,0,.6));
  text-shadow: 0 1px 3px rgba(0,0,0,.6); pointer-events: none; }
.uebergang { position: relative; }
.pano figcaption { color: #ddd; font-size: .78rem; padding: .45rem 1rem .6rem; }
.lightbox-overlay { flex-direction: column; gap: .6rem; }
.lightbox-full { max-height: calc(100% - 3rem); }
.lightbox-bu { color: #ddd; font-size: .85rem; text-align: center; max-width: 40rem; }
/* Hochformat (Wunsch Jannis 28.11.2026): am Handy nicht im Sticky-Streifen, sondern als Vollbild –
   mit Text darüber oder (ohne Text) als Atempause. Am Desktop bleibt es in der linken Spalte. */
.vollbild, .vollbild-luft { display: none; }
@media (max-width: 799px) {
  .tagstory .story-img.hoch { display: none; }
  /* Bild läuft einmal allein herein, bleibt dann stehen (sticky) und nur der Textkasten scrollt darüber.
     Der Text beginnt erst unterhalb des Bildes, damit Bild und Kasten nie zusammen hochfahren.
     Bewusst nur position: sticky (kein fixed/clip-path, kein background-attachment) – läuft so auch in iOS Safari. */
  .tagstory .story-section.hochbild { position: relative; z-index: 4; padding: 0; background: #000; min-height: 0; }
  .hochbild .vollbild { display: block; position: -webkit-sticky; position: sticky; top: 0; height: 100vh; height: 100svh; margin: 0; }
  .hochbild .vollbild img { display: block; width: 100%; height: 100%; object-fit: cover; cursor: zoom-in; }
  .hochbild .vollbild .bu-drauf { padding-bottom: max(.8rem, env(safe-area-inset-bottom, 0px)); }
  .story-section.pic.hochbild .vollbild-luft { height: 35vh; height: 35svh; }
  .hochbild .vollbild-text { position: relative; margin: 0 1rem; padding: 1.1rem 1.25rem 1.2rem;
    background: rgba(18,17,15,.78); -webkit-backdrop-filter: blur(5px); backdrop-filter: blur(5px);
    border-radius: 12px; color: #f3f1ec; }
  .hochbild .vollbild-luft { display: block; height: 55vh; height: 55svh; }
  .hochbild .vollbild-text h3 { color: #f2b47a; }
  .hochbild .vollbild-text p { color: #f3f1ec; }
  .hochbild .vollbild-text blockquote { color: #d8d4cc; }
  .hochbild .vollbild-text > :last-child { margin-bottom: 0; }
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

def tag_html(nr, folge, text):
    titel = re.sub(r'<.*?>', '', text['titel'])
    abschn = list(abschnitte(text['teile']))
    n_text = sum(1 for art_, _ in folge if art_ == 'text')
    assert n_text == len(abschn), f'Tag {nr}: {n_text} Textplätze, aber {len(abschn)} Abschnitte'
    zaehler = [0]  # fortlaufende Bildnummer im Tag (data-unit)
    out, gruppe = [], []
    def figur(s, cls='bu-drauf'):
        return f'<img class="lightbox-img" src="{s}" alt="{BU[s]}" loading="lazy"><figcaption class="{cls}">{BU[s]}</figcaption>'
    def story_schliessen():
        if not gruppe:
            return
        bilder = []  # (unit, src) in Reihenfolge
        for _, src, _ in gruppe:
            if src and src not in [b for _, b in bilder]:
                bilder.append((f't{nr}-{zaehler[0]}', src)); zaehler[0] += 1
        unit_von = {b: u for u, b in bilder}
        def ersatz(src):
            i = [b for _, b in bilder].index(src)
            vor = [u for u, b in bilder[:i] if art(b) != 'hoch']
            nach = [u for u, b in bilder[i+1:] if art(b) != 'hoch']
            return (vor[-1:] or nach[:1] or [None])[0]
        imgs = [f'<img class="story-img {art(b)}{" active" if j == 0 else ""}" data-unit="{u}" src="{b}" alt="{BU[b]}" loading="lazy">'
                for j, (u, b) in enumerate(bilder)]
        secs, gesehen = [], set()
        for typ, src, inhalt in gruppe:
            u = unit_von[src]
            attr = f'{inhalt[1]} data-unit="{u}" data-caption="{BU[src]}"'
            cls = '' if typ == 'text' else ' pic'
            if art(src) == 'hoch':
                e_ = ersatz(src)
                if e_:
                    attr += f' data-unit-mobil="{e_}"'
            if art(src) != 'hoch' or src in gesehen:
                secs.append(f'<section class="story-section{cls}"{attr}>{inhalt[0]}</section>')
                continue
            gesehen.add(src)
            voll = f'<figure class="vollbild">{figur(src)}</figure>'
            text_ = (f'<div class="vollbild-text">{inhalt[0]}</div>' if inhalt[0] else '') + '<div class="vollbild-luft"></div>'
            secs.append(f'<section class="story-section{cls} hochbild"{attr}>{voll}{text_}</section>')
        out.append(f'''<div class="story tagstory">
  <div class="story-media lightbox-container">
    {"".join(imgs)}
    <div class="story-caption">{BU[bilder[0][1]]}</div>
  </div>
  <div class="story-text">
    {"".join(secs)}
  </div>
</div>''')
        gruppe.clear()
    i_text, letztes = 0, None
    for typ, x in folge:
        for b in (x if isinstance(x, list) else [x]):
            assert b is None or b in BU, f'Bildunterschrift fehlt: {b}'
            assert b is None or (ROOT / 'public' / b.lstrip('/')).exists(), b
        if typ in ('text', 'bild'):
            src = x or letztes
            letztes = src
            if typ == 'text':
                kopf = f' id="tag{nr}"' if i_text == 0 else ''
                inhalt = ((text['titel'] if i_text == 0 else '') + abschn[i_text], kopf); i_text += 1
            else:
                inhalt = ('', '')
            gruppe.append((typ, src, inhalt))
            continue
        story_schliessen(); letztes = None
        if typ == 'pano':
            out.append(f'<figure class="pano" style="margin:0"><img class="lightbox-img" src="{x}" alt="{BU[x]}" loading="lazy">'
                       f'<span class="wisch">← Panorama: zur Seite wischen →</span><figcaption>{BU[x]}</figcaption></figure>')
        elif typ == 'gross':
            out.append(f'<figure class="uebergang" style="margin:0">{figur(x)}</figure>')
        elif typ == 'reihe':
            out.append('<div class="bildreihe">' + ''.join(f'<figure style="--ar:{ar(b):.3f}">{figur(b)}</figure>' for b in x) + '</div>')
    story_schliessen()
    return '\n'.join(out)

def main():
    s = SEITE.read_text(encoding='utf-8')
    assert 'class="story tagstory"' not in s, 'Fotos sind schon eingebaut – zuerst altavia-uebernehmen.py neu ausführen'
    start = s.index('<div class="story">', s.index('<h2>Der Weg, Tag für Tag</h2>'))
    ende = s.index('<section class="plain sub"><h3>Rückreise</h3>')
    block = s[start:ende]
    text = absaetze_je_tag(block)
    assert sorted(text) == list(range(1, 8)), sorted(text)
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
               # Keine Dauer (Jannis 26.11.: nichts Geschätztes). −610 Hm: Rifugio 2528 m → Pass 1918 m
               "      ab.bindPopup('<div class=\"title\">Abstieg am 29. August: Rifugio Passo delle Selle → Bushaltestelle Passo San Pellegrino Costabella</div>' +\n"
               "        '<div class=\"segstat\"><span class=\"ic\">↔</span>ca. 3,8 km</div>' +\n"
               "        '<div class=\"segstat\"><svg class=\"ic\" viewBox=\"0 0 24 24\" fill=\"currentColor\"><path d=\"M3 20 L9 8 L13 14 L16 9 L21 20 Z\"/></svg>ca. −610 Hm</div>' +\n"
               "        '<small>Diesen Abschnitt habe ich nicht mehr aufgezeichnet. Verlauf, Distanz und Höhenmeter sind aus der Wanderkarte abgeleitet.</small>', { maxWidth: 230 });\n"
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
    # Tag 1 (Anreise → Plosehütte) fehlte auf der Karte (Wunsch Jannis 26.11.2026); Track aus Komoot (Artifact „Meine Touren“)
    tag1 = json.loads((ROOT / 'scripts' / 'daten' / 'altavia-tag1.json').read_text(encoding='utf-8'))
    s = einmal(s, 'window.__routemapSegs = [', 'window.__routemapTag1 = ' + json.dumps(tag1) + ';\nwindow.__routemapSegs = [')
    s = einmal(s, "    stops.forEach(function(s){\n",
               "    if (window.__routemapTag1) {\n"
               "      L.polyline(window.__routemapTag1, { color: '#fff', weight: 9, opacity: 0.95, interactive: false }).addTo(map);\n"
               "      var t1 = L.polyline(window.__routemapTag1, { color: '#d9480f', weight: 4.5, opacity: 1 }).addTo(map);\n"
               "      t1.bindPopup('<div class=\"title\">Tag 1: Anreise \\u2192 Plosehütte</div>' +\n"
               "        '<div class=\"segstat\"><span class=\"ic\">\\u2194</span>2,7 km</div>' +\n"
               "        '<div class=\"segstat\"><svg class=\"ic\" viewBox=\"0 0 24 24\" fill=\"currentColor\"><path d=\"M3 20 L9 8 L13 14 L16 9 L21 20 Z\"/></svg>+370 / \\u22120 m</div>' +\n"
               "        '<a href=\"#tag1\">Tagesbeschreibung lesen \\u2192</a>', { maxWidth: 220 });\n"
               "      t1.on('mouseover', function(){ t1.setStyle({ weight: 6 }); });\n"
               "      t1.on('mouseout', function(){ t1.setStyle({ weight: 4.5 }); });\n"
               "    }\n"
               "    stops.forEach(function(s){\n")
    s = einmal(s, "      (window.__routemapAbstieg || []).forEach(function(p){ allPts.push(p); });\n",
               "      (window.__routemapAbstieg || []).forEach(function(p){ allPts.push(p); });\n"
               "      (window.__routemapTag1 || []).forEach(function(p){ allPts.push(p); });\n")
    # GPS-Ausreißer entfernen (Jannis 26.11.: Schleife vor der Pisciadùhütte an Tag 4 ist ein GPS-Fehler):
    # einzelne Punkte, die >250 m vom Vorgänger und Nachfolger wegspringen, während diese nah beieinander liegen
    m = re.search(r'window\.__routemapSegLatLon = (\[.*?\]);', s, re.S)
    segs = json.loads(m.group(1))
    def _d(a, b): return math.hypot((a[0]-b[0])*111320, (a[1]-b[1])*111320*math.cos(math.radians(a[0])))
    raus = 0
    for t in segs:
        i = 1
        while i < len(t) - 1:
            x, y, z = _d(t[i-1], t[i]), _d(t[i], t[i+1]), _d(t[i-1], t[i+1])
            if x > 250 and y > 250 and z < 0.4 * min(x, y):
                del t[i]; raus += 1
            else:
                i += 1
    assert raus == 1, raus
    s = s[:m.start(1)] + '[\n' + ',\n'.join(json.dumps(t, separators=(',', ':')) for t in segs) + '\n]' + s[m.end(1):]
    # Abstecher (Wunsch Jannis 26.11.2026): Tageswerte enthalten freiwillige Abstecher → Stern + Fußnote.
    # Werte aus Track (Hin-und-zurück-Stück) + Komoot-Höhenprofil; keine Zeiten (Track ohne Zeitstempel, Wunsch Jannis: nichts Geschätztes).
    ABSTECHER = {
        2: ('20,7 km', 'Peitlerkofel', 'ca. 4 km, ca. +500 Hm'),
        3: ('14,7 km', 'Piz Duleda', 'ca. 1,3 km, ca. +160 Hm'),
        7: ('15,7 km', 'Punta Alochet', 'ca. 2 km, ca. +100 Hm'),
    }
    for tag, (km, ziel, werte) in ABSTECHER.items():
        s = einmal(s, '{km:"' + km + '",', '{note:"* inkl. Abstecher auf ' + ('die ' if ziel.startswith('Punta') else 'den ') + ziel + ' (' + werte + ')",km:"' + km + '*",')
    s = einmal(s, "</svg>' + s.hm + '</div>' +\n",
               "</svg>' + s.hm + '</div>' +\n        (s.note ? '<div class=\"segnote\"><small>' + s.note + '</small></div>' : '') +\n")
    g0 = s.index('<section class="plain sub"><h3>Weitere Eindrücke</h3><div class="gallery-grid">')
    g1 = s.index('</div>', g0)
    kopf = '<section class="plain sub"><h3>Weitere Eindrücke</h3><div class="gallery-grid">'
    for src in GALERIE:
        assert (ROOT / 'public' / src.lstrip('/')).exists(), src
    s = s[:g0] + kopf + ''.join(f'<figure class="foto"><img class="gallery-img lightbox-img" src="{src}" alt="{BU[src]}" loading="lazy">'
                                f'<figcaption class="bu-unter">{BU[src]}</figcaption></figure>' for src in GALERIE) + s[g1:]
    # Titelbild (Wunsch Jannis 26.11.2026): Kamerafoto statt Handyfoto mit Personen im Fokus
    s = s.replace('/bilder/alta-via-2/titel-2af9ad.jpg', TITELBILD)
    s = einmal(s, f'<img class="hero-img lightbox-img" src="{TITELBILD}" alt="Alta Via 2 in den Dolomiten: 7 Tage über Klettersteige und einen Gletscher">',
               f'<figure class="foto"><img class="hero-img lightbox-img" src="{TITELBILD}" alt="{BU[TITELBILD]}">'
               f'<figcaption class="bu-unter">{BU[TITELBILD]}</figcaption></figure>')
    # „Begegnungen am Weg“: Kamerafoto 133 statt flauem Handyfoto (Jannis 28.11.2026)
    b = f'{ALT}kamera-133.jpg'
    s = einmal(s, f'<img loading="lazy" class="inline-img lightbox-img" src="{ALT}bild-1f9f89.jpg" alt="Begegnungen am Weg">',
               f'<figure class="foto"><img loading="lazy" class="inline-img lightbox-img" src="{b}" alt="{BU[b]}">'
               f'<figcaption class="bu-unter">{BU[b]}</figcaption></figure>')
    # Story-Skript: am Handy bleibt bei Hochformat-Abschnitten das Querformat im Streifen (data-unit-mobil)
    s = einmal(s, '      var unit = activeSection.getAttribute("data-unit");\n',
               '      var unit = (window.innerWidth < 800 && activeSection.getAttribute("data-unit-mobil")) || activeSection.getAttribute("data-unit");\n')
    s = einmal(s, '        var capText = activeSection.getAttribute("data-caption");\n',
               '        var aktivBild = story.querySelector(\'.story-img[data-unit="\' + unit + \'"]\');\n'
               '        var capText = aktivBild ? aktivBild.getAttribute("alt") : activeSection.getAttribute("data-caption");\n')
    # Lightbox zeigt die Bildunterschrift mit an
    s = einmal(s, "overlay.innerHTML = '<img loading=\"lazy\" class=\"lightbox-full\">';",
               "overlay.innerHTML = '<img loading=\"lazy\" class=\"lightbox-full\"><div class=\"lightbox-bu\"></div>';")
    s = einmal(s, "      full.src = img.tagName === \"IMG\" ? img.src : img.getAttribute(\"data-full\");\n",
               "      full.src = img.tagName === \"IMG\" ? img.src : img.getAttribute(\"data-full\");\n"
               "      overlay.querySelector(\".lightbox-bu\").textContent = img.getAttribute(\"alt\") || \"\";\n")
    s = einmal(s, "      if (best) { full.src = best.src; overlay.classList.add(\"open\"); }",
               "      if (best) { full.src = best.src; overlay.querySelector(\".lightbox-bu\").textContent = best.getAttribute(\"alt\") || \"\"; overlay.classList.add(\"open\"); }")
    # Persönliche Verbindung zum Traumpfad (Jannis 28.11.2026)
    s = einmal(s, 'unter die Füße nahmen – ein Weg, der offensichtlich viele Menschen zusammenbringt.', 'unter die Füße nahmen – ein Weg, der offensichtlich viele Menschen zusammenbringt. Spannend für uns: Im Vorjahr waren wir mit derselben Gruppe schon im Karwendel auf einem Abschnitt des Traumpfads unterwegs.')
    # Praktisches gehört nach Zahlen & Fakten, nicht in den Bericht (Jannis 27.11.2026)
    s = einmal(s, ' (Bus und Einzelfahrt mit der Seilbahn zusammen 26 € pro Person)', '')
    s = einmal(s, ' Wer am Vortag mehr Strecke schafft und es bis zum Rifugio Boè schafft – es wirkte übrigens sehr modern und gepflegt – kann früh losgehen und noch vor der ersten Gondel oben sein; das lohnt sich definitiv.', '')
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
        # Summe inkl. Abstieg 29.08. (Jannis 28.11.): Tage 103,7 km + 3,8 km; +6.212 / −5.674−610 Hm
        f = einmal(f, '<td>ca. 104 km, ca. +6.200 / −5.700 Hm</td>', '<td>ca. 108 km, ca. +6.200 / −6.300 Hm*<br><small>* inkl. Abstecher und Abstieg am 29.08. (Abstieg nicht aufgezeichnet, aus der Wanderkarte), siehe „Der Weg, Tag für Tag“</small></td>')
        f = einmal(f, '<td>7 Wandertage</td>', '<td>7 Wandertage und ein Abstieg am Morgen des 8. Tages</td>')
        f = einmal(f, '</tbody></table></div></section>\n<section class="plain"><h2>Packen',
                   '</tbody></table></div>\n<p class="tabnote"><small>* inkl. Abstecher, die nicht zwingend zur Route gehören. ' + ' · '.join(fuss) + '. Distanz und Höhenmeter der Abstecher aus dem Track abgeleitet.</small></p></section>\n<section class="plain"><h2>Packen')
        fakten.write_text(f, encoding='utf-8')
    f = fakten.read_text(encoding='utf-8')
    if 'Nützliche Hinweise' not in f:
        f = einmal(f, '</small></p></section>\n<section class="plain"><h2>Packen',
                   '</small></p></section>\n<section class="plain"><h2>Nützliche Hinweise</h2>'
                   '<p><strong>Anreise zur Plosehütte:</strong> Bus vom Bahnhof Brixen zur Talstation der Plosebahn und Einzelfahrt mit der Seilbahn kosteten zusammen 26 € pro Person (August 2026).</p>'
                   '<p><strong>Piz Boè ohne Seilbahn-Andrang:</strong> Wer am Vortag mehr Strecke schafft und es bis zum Rifugio Boè schafft – es wirkte sehr modern und gepflegt –, kann früh losgehen und noch vor der ersten Gondel oben sein. Das lohnt sich definitiv.</p>'
                   '<p><strong>Steigeisen leihen:</strong> Am Rifugio Castiglioni Marmolada konnten wir uns für die Gletscherquerung zum Rifugio Contrin Steigeisen leihen (ca. 15 €) und sie dort unkompliziert wieder abgeben. So muss man sie nicht die ganze Tour mitschleppen. Am besten vorher bei der Hütte abklären, ob das möglich ist, und auf steigeisenfeste Schuhe achten. Unsere Grödel hätten wir dafür daheim lassen können.</p></section>\n<section class="plain"><h2>Packen')
        fakten.write_text(f, encoding='utf-8')
    f = fakten.read_text(encoding='utf-8')
    if '<td>29.08.</td>' not in f:  # Abstieg als eigene Zeile (Jannis 28.11.2026), keine Gehzeit: nicht aufgezeichnet
        f = einmal(f, '<td>8:42 h</td></tr>\n', '<td>8:42 h</td></tr>\n<tr><td>8</td><td>29.08.</td><td>Rifugio Passo delle Selle → Bushaltestelle Passo San Pellegrino (Abstieg)</td><td>ca. 3,8 km**</td><td>ca. −610</td><td>–</td></tr>\n')
        f = einmal(f, 'aus dem Track abgeleitet.</small></p>', 'aus dem Track abgeleitet.<br>** Abstieg nicht aufgezeichnet; Distanz und Höhenmeter aus der Wanderkarte abgeleitet, daher ohne Gehzeit.</small></p>')
        fakten.write_text(f, encoding='utf-8')
    print('✓ Zeitraum 22.–29. August:', fakten.relative_to(ROOT))

if __name__ == '__main__':
    main()
