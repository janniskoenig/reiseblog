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
    5: dict(sticky=[k(216), k(257), k(284), k(291)], reihe=[k(219), k(229), k(251), k(282), k(297)], danach=None),
    6: dict(sticky=[k(304), k(311)], reihe=[], danach=None),
    7: dict(sticky=[k(320), k(326), k(353), k(356)], reihe=[k(327), k(333), k(354), k(365)], danach=None),
}
HUETTEN = {  # Kartenmarker → Foto
    'Schlüterhütte': (k(92), 'Die Schlüterhütte am Morgen'),
    'Pisciadùhütte': (k(186), 'Die Pisciadùhütte am Abend'),
    'Rifugio Passo delle Selle': (f'{ALT}kamera-354-huette.jpg', 'Das Rifugio Passo delle Selle auf dem Grat'),
}

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
    s = einmal(s, 'Hütten antippen für Name und Höhe,', 'Hütten antippen für Name, Höhe und Foto,')
    s = einmal(s, 'Hütte antippen → Name und Höhe', 'Hütte antippen → Name, Höhe, Foto')
    SEITE.write_text(s, encoding='utf-8')
    print('✓ Fotos eingebaut:', SEITE.relative_to(ROOT))
    # Zahlen & Fakten: Abstieg am 29.08. gehört noch zur Tour (Wunsch Jannis, 26.11.2026)
    fakten = SEITE.parent / 'zahlen-fakten' / 'index.html'
    f = fakten.read_text(encoding='utf-8')
    if '22.–29. August 2026' not in f:
        f = einmal(f, '<td>22.–28. August 2026</td>', '<td>22.–29. August 2026</td>')
        fakten.write_text(f, encoding='utf-8')
    print('✓ Zeitraum 22.–29. August:', fakten.relative_to(ROOT))

if __name__ == '__main__':
    main()
