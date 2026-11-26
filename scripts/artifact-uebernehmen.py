#!/usr/bin/env python3
"""Übernimmt die fertigen Madagaskar-Artifacts (self-contained HTML) als statische
Seiten in den Blog.

- Eingebettete Bilder (data:image/…;base64) werden als Dateien nach
  bilder-original/madagaskar/ geschrieben. Danach `npm run bilder` ausführen:
  das komprimiert sie nach public/bilder/madagaskar/ und entfernt alle Metadaten.
- Eingebettete Videos landen in bilder-original/videos/ (ffmpeg entfernt danach
  die Metadaten, siehe verarbeite_videos()).
- Links zwischen den Artifacts werden auf die Blog-Adressen umgeschrieben.
- Jede Seite bekommt Kopfzeile (zurück zum Blog) und Fußzeile (Impressum, Datenschutz).

Aufruf: python3 scripts/artifact-uebernehmen.py <ordner-mit-artifact-html> <ordner-mit-mp4>
Danach: python3 scripts/madagaskar-anpassungen.py (fixierte Karte, Reiseplanung-Link,
Tsingy-Abstecher in der Übersicht). Das passiert am Ende dieses Skripts automatisch.
"""
import base64, hashlib, html, re, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
QUELLE, VIDEOS_IN = Path(sys.argv[1]), Path(sys.argv[2])
BILD_ORIG = ROOT / 'bilder-original' / 'madagaskar'
VIDEO_ZIEL = ROOT / 'public' / 'videos' / 'madagaskar'
SEITEN = ROOT / 'public' / 'madagaskar'
SITE = 'https://reiseblog-dln.pages.dev'

# Artifact-ID → (Blog-Pfad, Datei der gespeicherten Artifact-Version)
ARTIFACTS = {
    'R3HuZUxBxUwMWbMzbdqcDM': ('', 'artifact-c2ad3bf4-1793190959-64ca.html'),
    'XqKKKNonPcmjaBVzLVPCz9': ('hochland', 'artifact-f9b125f5-1793190964-4bce.html'),
    'JVmtLSeXuvwsjtu13SHwwD': ('trockener-westen', 'artifact-8dafd81d-1793190967-c6d0.html'),
    'MBrGYBaSM2cSnr8bCawNQv': ('suedwesten', 'artifact-a37a92c4-1793190970-5658.html'),
    '3nLcVeSmbHKNx4zExMGtnf': ('isalo', 'artifact-1686d551-1793190973-ee9b.html'),
    'CHez9yXWaDRcTKodUg3b7U': ('sava', 'artifact-5b67d5be-1793190961-52a0.html'),
    # Nützliche Reiseinfos (öffentlich seit 2026-11-24, ohne Namen/Nummern von Fahrern)
    'HpmerbTZ3LTpjQopaiy5GP': ('reiseplanung', 'artifact-883db1a5-1793301442-41f2.html'),
    'DmJsHNQeyEXqgi9Qriuyd4': ('hochland/reiseinfos', 'artifact-675d6693-1793207640-8ac6.html'),
    'BYD7yP4k8bMgGdv5UZRQi7': ('trockener-westen/reiseinfos', 'artifact-5556e9ae-1793196219-2832.html'),
    'PWkNfVxLXHnXRowxA89Zbu': ('suedwesten/reiseinfos', 'artifact-b6505987-1793196226-d529.html'),
    '7oXUC5QbfshYxD3NUitR3x': ('isalo/reiseinfos', 'artifact-3715d28c-1793196229-9dd5.html'),
    'RkVe67Q2qcmZYyMEcyEKLc': ('sava/reiseinfos', 'artifact-c86df5aa-1793301536-d1bb.html'),
}
# Bericht → Reiseinfo-Seite (für den Link in der Kopfleiste)
REISEINFO = {'hochland': 'hochland/reiseinfos', 'trockener-westen': 'trockener-westen/reiseinfos',
             'suedwesten': 'suedwesten/reiseinfos', 'isalo': 'isalo/reiseinfos', 'sava': 'sava/reiseinfos', '': 'reiseplanung'}
def ist_info(slug): return slug == 'reiseplanung' or slug.endswith('/reiseinfos')

def blogpfad(slug): return '/madagaskar/' + (slug + '/' if slug else '')

KOPF_CSS = """
.blog-bar{position:absolute;top:0;left:0;right:0;z-index:50;display:flex;justify-content:space-between;align-items:center;gap:1rem;
 padding:max(.7rem,env(safe-area-inset-top,0px)) 1.1rem .7rem;font:600 .9rem/1.2 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;
 background:linear-gradient(to bottom,rgba(0,0,0,.55),rgba(0,0,0,0));pointer-events:none}
.blog-bar a{color:#fff;text-decoration:none;text-shadow:0 1px 4px rgba(0,0,0,.6);pointer-events:auto}
.blog-bar a:hover{text-decoration:underline}
.blog-bar span{display:flex;gap:1rem}
.blog-bar.hell{position:static;background:none;padding:max(.7rem,env(safe-area-inset-top,0px)) 0 .2rem;max-width:52rem;margin:0 auto}
.blog-bar.hell a{color:var(--muted,#6b6b66);text-shadow:none}
.blog-foot{padding:2rem 1.5rem 2.5rem;text-align:center;font:.85rem/1.5 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;color:var(--muted,#6b6b66)}
.blog-foot a{color:inherit}
"""

def kopf(titel, beschreibung, bild, pfad, slug):
    t = html.escape(titel)
    d = html.escape(beschreibung)
    return f"""<!doctype html>
<html lang="de">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>{t} · Reiseblog</title>
<meta name="description" content="{d}">
<link rel="canonical" href="{SITE}{pfad}">
<meta property="og:title" content="{t}">
<meta property="og:description" content="{d}">
{f'<meta property="og:image" content="{SITE}{bild}">' if bild else ''}
<link rel="icon" href="/favicon.svg" type="image/svg+xml">
<style>:root{{box-sizing:border-box;padding-top:env(safe-area-inset-top,0px);padding-bottom:env(safe-area-inset-bottom,0px)}}html{{scroll-padding-top:env(safe-area-inset-top,0px)}}body{{margin:0;padding:0;font:14px -apple-system,BlinkMacSystemFont,sans-serif;background:#faf8f4;color:#2c2c2a}}img{{max-width:100%}}[hidden]:not([hidden=until-found i]){{display:none!important}}{KOPF_CSS}</style>
</head>
<body>
{leiste(slug)}
"""

def leiste(slug):
    rechts = '<a href="/madagaskar/">Madagaskar 2026</a>'
    if slug in REISEINFO:
        rechts += f'<a href="{blogpfad(REISEINFO[slug])}">{"Reiseplanung" if slug == "" else "Reiseinfos"}</a>'
    if ist_info(slug):
        return f'<nav class="blog-bar hell" aria-label="Blog"><a href="/">← Reiseblog</a><span>{rechts}</span></nav>'
    return f'<nav class="blog-bar" aria-label="Blog"><a href="/">← Reiseblog</a><span>{rechts}</span></nav>'

FUSS = """
<footer class="blog-foot"><a href="/">Reiseblog</a> · <a href="/impressum/">Impressum</a> · <a href="/datenschutz/">Datenschutz</a></footer>
</body>
</html>
"""

bilder = {}   # sha → Dateiname (seitenübergreifend dedupliziert)
namen = set()

def bild_name(sha, hinweis):
    if sha in bilder: return bilder[sha]
    basis = re.sub(r'[^a-z0-9_-]+', '-', (hinweis or 'bild').lower()).strip('-') or 'bild'
    name, i = basis, 2
    while name in namen: name, i = f'{basis}-{i}', i + 1
    namen.add(name); bilder[sha] = name
    return name

def uebernehmen(aid, slug, datei):
    s = (QUELLE / datei).read_text(encoding='utf-8')
    # Hülle der Artifact-Auslieferung entfernen
    i = s.index('<body>') + len('<body>')
    j = s.rindex('</body>')
    s = s[i:j]
    titel = html.unescape(re.search(r'<title>(.*?)</title>', s, re.S).group(1)).strip()
    s = re.sub(r'<title>.*?</title>', '', s, count=1, flags=re.S)

    def ersetze(m):
        typ, b64 = m.group(1), m.group(2)
        daten = base64.b64decode(b64)
        sha = hashlib.sha1(daten).hexdigest()
        if typ.startswith('video/'):
            ziel = VIDEO_ZIEL / f'{slug}-eingebettet-{sha[:8]}.mp4'
            roh = ROOT / 'bilder-original' / 'videos' / ziel.name
            roh.parent.mkdir(parents=True, exist_ok=True); roh.write_bytes(daten)
            return '/videos/madagaskar/' + ziel.name
        # Namenshinweis: data-id / data-same / Klasse sp-… im selben Tag
        start = s.rfind('<', 0, m.start())
        tag = s[start:m.start()]
        h = re.search(r'data-id="([^"]+)"', tag) or re.search(r'\bsp-([\w-]+)', tag)
        name = bild_name(sha, (h.group(1) if h else f'{slug or "uebersicht"}-{sha[:6]}'))
        endung = '.png' if typ == 'image/png' else '.jpg'
        if endung == '.png':
            # png bleibt png, sharp-Skript wandelt es in jpg um
            pass
        (BILD_ORIG / (name + endung)).write_bytes(daten)
        return f'/bilder/madagaskar/{name}.jpg'

    # Interne Lückenlisten („Noch zu ergänzen“) nicht veröffentlichen
    s = re.sub(r'<h2>Noch zu ergänzen</h2>\s*<div class="gaps">.*?</div>', '', s, flags=re.S)
    # GPX-Download: statt der Claude-Schnittstelle normaler Browser-Download
    s = s.replace('!window.claude||!claude.use)return;claude.use("downloads")',
                  '0)return;Promise.resolve({save:function(o){var a=document.createElement("a");'
                  'a.href=URL.createObjectURL(new Blob([o.data],{type:"application/zip"}));a.download=o.filename;'
                  'document.body.appendChild(a);a.click();a.remove();return Promise.resolve();}})')
    s = re.sub(r'data:(image/[\w+.-]+|video/mp4);base64,([A-Za-z0-9+/=]+)', ersetze, s)

    # Videos, die als eigene Dateien mit dem Artifact veröffentlicht waren
    for mp4 in sorted(set(re.findall(r'(?<=["\'])([\w-]+\.mp4)(?=["\'])', s))):
        s = re.sub(r'(?<=["\'])' + re.escape(mp4) + r'(?=["\'])', '/videos/madagaskar/' + mp4, s)

    # Links zwischen den Artifacts
    for a, (sl, _) in ARTIFACTS.items():
        s = re.sub(r'https://claude\.ai/(?:code/)?artifact/' + a + r'(?:[/?#][^"\']*)?', blogpfad(sl), s)
    rest = re.findall(r'https://claude\.ai/[^"\'\s<]+', s)
    assert not rest, f'unbekannte Artifact-Links in {datei}: {rest}'
    # Links innerhalb der Seite im selben Fenster öffnen
    s = re.sub(r'(href="/madagaskar/[^"]*")\s+target="_(?:blank|top)"(?:\s+rel="[^"]*")?', r'\1', s)

    sub = re.search(r'class="(?:ihero-sub|pl-sub|lead)"[^>]*>(.*?)</p>', s, re.S)
    beschreibung = html.unescape(re.sub(r'<[^>]+>', '', sub.group(1))).strip() if sub else titel
    og = re.search(r'class="ihero-img[^"]*"[^>]*?src="([^"]+)"', s) or re.search(r'src="(/bilder/[^"]+)"', s)
    pfad = blogpfad(slug)
    ziel = SEITEN / slug / 'index.html' if slug else SEITEN / 'index.html'
    ziel.parent.mkdir(parents=True, exist_ok=True)
    ziel.write_text(kopf(titel, beschreibung, og.group(1) if og else None, pfad, slug) + s + FUSS, encoding='utf-8')
    print(f'✓ {pfad}  ({titel}) – {ziel.stat().st_size // 1024} KB')

def verarbeite_videos():
    VIDEO_ZIEL.mkdir(parents=True, exist_ok=True)
    quellen = list(VIDEOS_IN.rglob('*.mp4')) + list((ROOT / 'bilder-original' / 'videos').glob('*.mp4'))
    for q in quellen:
        ziel = VIDEO_ZIEL / q.name
        # Metadaten (Ort, Gerät, Datum) entfernen, Bild/Ton unverändert kopieren
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', str(q), '-map', '0', '-map_metadata', '-1',
                        '-map_chapters', '-1', '-c', 'copy', '-movflags', '+faststart', str(ziel)], check=True)
        print('✓ Video', ziel.name)

if __name__ == '__main__':
    BILD_ORIG.mkdir(parents=True, exist_ok=True)
    for aid, (slug, datei) in ARTIFACTS.items():
        uebernehmen(aid, slug, datei)
    verarbeite_videos()
    subprocess.run([sys.executable, str(ROOT / 'scripts' / 'madagaskar-anpassungen.py')], check=True)
    print(len(bilder), 'Bilder nach', BILD_ORIG.relative_to(ROOT), '– jetzt `npm run bilder` ausführen.')
