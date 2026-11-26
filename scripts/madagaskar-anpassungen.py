#!/usr/bin/env python3
"""Nachträgliche Anpassungen an den übernommenen Madagaskar-Seiten.

Die Seiten unter public/madagaskar/ entstehen aus den Artifacts
(scripts/artifact-uebernehmen.py). Damit die folgenden Änderungen einen
erneuten Import überleben, stehen sie hier und werden danach ausgeführt:

1. Übersicht „Alle Regionen im Überblick“ (Desktop): Karte samt Regionsknöpfen
   bleibt beim Scrollen links fixiert und immer vollständig sichtbar, rechts
   scrollen nur die Berichte. Längere Regionstexte unter der Karte scrollen
   innerhalb der Kartenspalte.
2. Übersicht: Link auf die übergreifende Reiseplanung unter der Überschrift.
3. Prolog-Animation der Übersicht, Nordosten: Der Abstecher zu den Tsingy Rouge
   wird gezeichnet, bevor die Route bis Diego weiterläuft (vorher: erst Diego,
   dann der Abstecher). Die Scroll-Karte im SAVA-Bericht macht das bereits so.

Das Skript ist idempotent (mehrfach ausführbar).
Aufruf: python3 scripts/madagaskar-anpassungen.py
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
UEBERSICHT = ROOT / 'public' / 'madagaskar' / 'index.html'
MARKE = 'data-anpassung="1"'

STICKY_CSS = """
<style data-anpassung="1">
/* Desktop: Karte links fixiert, rechts scrollen die Berichte (scripts/madagaskar-anpassungen.py) */
.mapside { display: contents; }
.hero-plan { margin: 1rem 0 0; font-size: .98rem; color: var(--muted); max-width: 40rem; }
.hero-plan a { font-weight: 600; text-decoration: none; border-bottom: 2px solid currentColor; padding-bottom: 1px; }
@media (min-width: 56rem) {
  .layout { grid-template-areas: "side reports"; }
  .mapside { display: flex; flex-direction: column; gap: .9rem; grid-area: side; min-width: 0;
    position: sticky; top: 1rem; max-height: calc(100vh - 2rem); max-height: calc(100dvh - 2rem); }
  /* Knöpfe als Raster 3 × 2; die Farbe der Region steht als Strich im Knopf, die Legende entfällt */
  .mapside .tools { flex: none; }
  .mapside .legend { display: none; }
  .mapside .views { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 1px; background: var(--border); width: 100%; }
  .mapside .views button { border: 0; font-size: .86rem; padding: .42rem .6rem; white-space: nowrap;
    display: flex; align-items: center; justify-content: center; gap: .45rem; }
  .mapside .views button:not([aria-pressed="true"]) { background: var(--bg); }
  .mapside .views button:not([aria-pressed="true"]):hover { background: var(--land); }
  .mapside .views button:not([data-view="all"])::before { content: ""; width: .85rem; border-top: 3px solid var(--accent); flex: none; }
  .mapside .views button[data-view="hoch"]::before { border-top-color: var(--teal); }
  .mapside .views button[data-view="dry"]::before { border-top-color: var(--violet); }
  .mapside .views button[data-view="sued"]::before { border-top-color: var(--sued); }
  .mapside .views button[data-view="isalo"]::before { border-top-color: var(--isalo); }
  .mapside .mapcol { flex: 1 1 auto; min-height: 0; display: flex; flex-direction: column; }
  /* Karte so groß wie möglich, aber nie höher als der Bildschirm abzüglich Knöpfe und
     einem Streifen Regionstext darunter (der Text scrollt bei Bedarf in sich) */
  .mapside .mapbox { flex: none; width: min(100%, calc((100vh - 15rem) * 1030 / 1400)); width: min(100%, calc((100dvh - 15rem) * 1030 / 1400)); margin-inline: auto; }
  .mapside .teaser { overflow-y: auto; min-height: 0; flex: 0 1 auto; scrollbar-width: thin; padding-right: .5rem; }
}
</style>
"""

PLAN_LINK = ('\n    <p class="hero-plan">Routenvorschläge, Verkehrsmittel, Unterkünfte, Preise und Packliste: '
             'Alles Übergreifende zur Planung steht unter '
             '<a href="/madagaskar/reiseplanung/">Übergreifende Infos &amp; Reiseplanung →</a></p>')


def ersetze(s, alt, neu, was):
    assert s.count(alt) == 1, f'{was}: Stelle nicht eindeutig gefunden ({s.count(alt)}×)'
    return s.replace(alt, neu)


def tsingy_vor_diego(s):
    """Teilt im Prolog die Strecke Vohémar → Diego am Abzweig zu den Tsingy Rouge
    und setzt den Abstecher dazwischen."""
    m = re.search(r'<g class="pl-r sava">(.*?)</g>', s, re.S)
    assert m, 'Prolog: Gruppe pl-r sava fehlt'
    pfade = re.findall(r'<path class="pl-draw" data-d="([^"]+)" d=""/>', m.group(1))
    # Abstecher: kurzer Pfad vom Abzweig (601.7,112.2) zu den Tsingy Rouge (615,113.9)
    abstecher = [p for p in pfade if p.startswith('M601.7,112.2') and p.endswith('615,113.9')]
    assert len(abstecher) == 1, 'Prolog: Tsingy-Abstecher nicht gefunden'
    start = abstecher[0].split()[0][1:]
    if pfade.index(abstecher[0]) < len(pfade) - 1:
        return s  # schon umgestellt
    diego = [p for p in pfade if (' ' + start + ' ') in p and not p.startswith('M' + start)]
    assert len(diego) == 1, 'Prolog: Strecke nach Diego nicht gefunden'
    pkt = diego[0][1:].split()
    i = pkt.index(start)
    teil1, teil2 = 'M' + ' '.join(pkt[:i + 1]), 'M' + ' '.join(pkt[i:])
    neu = []
    for p in pfade:
        if p == abstecher[0]:
            continue
        if p == diego[0]:
            neu += [teil1, abstecher[0], teil2]
        else:
            neu.append(p)
    inhalt = ''.join(f'<path class="pl-draw" data-d="{p}" d=""/>' for p in neu)
    alt_inhalt = ''.join(f'<path class="pl-draw" data-d="{p}" d=""/>' for p in pfade)
    assert m.group(1) == alt_inhalt, 'Prolog: unerwarteter Inhalt in pl-r sava'
    return s[:m.start(1)] + inhalt + s[m.end(1):]


def uebersicht():
    s = UEBERSICHT.read_text(encoding='utf-8')
    s = tsingy_vor_diego(s)
    if MARKE not in s:
        s = ersetze(s, '</style>\n\n<section class="prolog"', '</style>\n' + STICKY_CSS + '\n<section class="prolog"', 'CSS')
        s = ersetze(s, '<h2 class="h1like">Alle Regionen im Überblick</h2>',
                    '<h2 class="h1like">Alle Regionen im Überblick</h2>' + PLAN_LINK, 'Reiseplanung-Link')
        # Regionsknöpfe und Karte in eine gemeinsame Spalte, die auf dem Desktop fixiert bleibt
        s = ersetze(s, '<div class="layout">\n    <div class="tools">',
                    '<div class="layout">\n    <div class="mapside">\n    <div class="tools">', 'Kartenspalte Anfang')
        s = ersetze(s, '    </section>\n\n    <section class="reports"',
                    '    </section>\n    </div>\n\n    <section class="reports"', 'Kartenspalte Ende')
    UEBERSICHT.write_text(s, encoding='utf-8')
    print('✓', UEBERSICHT.relative_to(ROOT))


if __name__ == '__main__':
    uebersicht()
