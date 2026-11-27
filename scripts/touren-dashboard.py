#!/usr/bin/env python3
"""Erzeugt die Daten für das Touren-Dashboard auf der Startseite.

Quelle: Artifact „Meine Touren“ (claude.ai/artifact/EaA4w59sc1yyi5rNHRwDuo), exportiert nach
scripts/daten/meine-touren-meta.json (Touren-Liste) und meine-touren-spuren.json (vereinfachte GPX-Tracks je Tag).

Ausgabe:
  src/data/touren.json   – Steckbriefe (Name, Datum, Art, Region, km, Hm), OHNE die privaten Stichpunkte
  public/touren/spuren.json – eine Linie pro Tour

Datenschutz: Die Tagesetappen werden zu einer Linie zusammengehängt und Tagesenden nicht markiert,
damit Übernachtungsplätze (z. B. Wildcamping) nicht ablesbar sind.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
meta = json.loads((ROOT / 'scripts/daten/meine-touren-meta.json').read_text())
spuren = json.loads((ROOT / 'scripts/daten/meine-touren-spuren.json').read_text())

# Touren mit eigener Seite im Blog. entwurf=True: Bericht nur in Branch-Vorschauen verlinkt,
# auf der Live-Seite (main) erscheint die Tour ohne Bericht. Erst auf False setzen, wenn er final ist.
BERICHTE = {
    'madagaskar': {'link': '/madagaskar/', 'entwurf': False},
    'dolomiten': {'link': '/alta-via-2/', 'entwurf': False},
    'alpencross': {'link': '/mtb-alpencross/', 'entwurf': True},
}
# Bessere Linien aus dem Blog statt der Artifact-Spur
ROUTEN = {
    'dolomiten': 'public/routen/alta-via-2.json',  # GPS-Ausreißer Tag 4 entfernt
}
# Tage, die nicht zur Tour gehören (Alpencross: letzter Tag = Rückfahrt Riva → Rovereto)
OHNE_LETZTEN_TAG = {'alpencross'}
# Namen, die im Blog anders heißen
NAMEN = {'dolomiten': 'Alta Via 2', 'madagaskar': 'Madagaskar'}


def ausduennen(punkte, min_abstand=0.0004):
    """Entfernt Punkte, die näher als ca. 40 m am vorigen liegen (Pausen, GPS-Rauschen)."""
    aus = []
    for p in punkte:
        if not aus or abs(p[0] - aus[-1][0]) + abs(p[1] - aus[-1][1]) >= min_abstand:
            aus.append([round(p[0], 4), round(p[1], 4)])
    return aus


touren, linien = [], {}
for t in meta['T']:
    tid = t['id']
    if tid in ROUTEN:
        d = json.loads((ROOT / ROUTEN[tid]).read_text())
        tage = [d['linie'] if isinstance(d, dict) else d]
    else:
        tage = spuren.get(tid, [])
        if tid in OHNE_LETZTEN_TAG:
            tage = tage[:-1]
    # Tage zu Linien zusammenhängen; neue Linie nur bei Sprung > ca. 5 km (z. B. Bus/Zug dazwischen)
    teile = []
    for tag in tage:
        tag = ausduennen(tag)
        if not tag:
            continue
        if teile and abs(tag[0][0] - teile[-1][-1][0]) + abs(tag[0][1] - teile[-1][-1][1]) < 0.06:
            teile[-1].extend(tag)
        else:
            teile.append(tag)
    linien[tid] = teile
    touren.append({
        'id': tid,
        'name': NAMEN.get(tid, t['name']),
        'start': t['s'],
        'ende': t['e'],
        'art': t['type'],
        'region': t['region'],
        'gebiet': meta['AREA'].get(tid, meta['REGIONS'][t['region']]),
        'km': t['km'],
        'hm': t['up'],
        'bericht': BERICHTE.get(tid, {}).get('link'),
        'entwurf': BERICHTE.get(tid, {}).get('entwurf', False),
    })

touren.sort(key=lambda t: t['start'])
(ROOT / 'src/data/touren.json').write_text(json.dumps({
    'arten': meta['TYPES'], 'regionen': meta['REGIONS'], 'touren': touren,
}, ensure_ascii=False, indent=1) + '\n')
(ROOT / 'public/touren/spuren.json').write_text(json.dumps(linien, separators=(',', ':')))
print(len(touren), 'Touren,', sum(len(l) for t in linien.values() for l in t), 'Punkte')
