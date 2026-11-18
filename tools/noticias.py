"""Genera noticias.json: titulares de portales mineros y de Minera Pacífico del Sur (Google Noticias).
Solo guarda titular, fuente, fecha y enlace: la noticia completa se lee en el sitio original."""
import json, re, subprocess, html, datetime, urllib.parse
import xml.etree.ElementTree as ET
from email.utils import parsedate_to_datetime

UA = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36'
def get(url):
    r = subprocess.run(['curl', '-sfL', '--retry', '2', '--max-time', '30', '-A', UA, url], capture_output=True)
    if r.returncode != 0 or not r.stdout: raise IOError(f'curl {r.returncode}')
    return r.stdout

def gnews(q):
    return 'https://news.google.com/rss/search?' + urllib.parse.urlencode({'q': q, 'hl': 'es-419', 'gl': 'CL', 'ceid': 'CL:es-419'})

FUENTES = [
    # (clave, nombre visible, [urls candidatas])
    ('pds', 'Minera Pacífico del Sur', [gnews('"Minera Pacífico del Sur" OR "Pacífico del Sur" Aysén OR "El Toqui" Mañihuales')]),
    ('portalminero', 'Portal Minero', ['https://www.portalminero.com/feed/', 'https://www.portalminero.com/rss', gnews('site:portalminero.com')]),
    ('mch', 'Minería Chilena', ['https://www.mch.cl/feed/', gnews('site:mch.cl')]),
    ('reporteminero', 'Reporte Minero', ['https://www.reporteminero.cl/rss', 'https://www.reporteminero.cl/feed', gnews('site:reporteminero.cl')]),
    ('aysen', 'Minería en Aysén', [gnews('minería Aysén OR Coyhaique minera')]),
]
SPAM = re.compile(r'casino|apuesta|bono|1win|pin.?up|slot|tragamonedas|ruleta|bet', re.I)

def parse(raw, nombre):
    root = ET.fromstring(raw)
    out = []
    for it in root.iter('item'):
        t = html.unescape((it.findtext('title') or '').strip())
        l = (it.findtext('link') or '').strip()
        d = it.findtext('pubDate') or ''
        src = it.find('source')
        if src is not None and src.text and t.endswith(' - ' + src.text.strip()):
            t = t[: -len(src.text.strip()) - 3]
        if not t or not l.startswith('http') or SPAM.search(t) or '/otras-noticias/' in l: continue
        try: f = parsedate_to_datetime(d).astimezone(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
        except Exception: f = ''
        out.append({'titulo': t[:200], 'enlace': l, 'fecha': f, 'medio': (src.text.strip() if src is not None and src.text else nombre)})
    return out

res = {'actualizado': datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ'), 'fuentes': []}
try: prev = {f['clave']: f for f in json.load(open('noticias.json')).get('fuentes', [])}
except Exception: prev = {}
for clave, nombre, urls in FUENTES:
    items = []
    for u in urls:
        try:
            items = parse(get(u), nombre)
            print(f'{clave}: {len(items)} desde {u[:70]}')
            if items: break
        except Exception as e:
            print(f'{clave}: falla {u[:70]} -> {e}')
    items.sort(key=lambda x: x['fecha'], reverse=True)
    if not items and clave in prev: items = prev[clave]['items']
    res['fuentes'].append({'clave': clave, 'nombre': nombre, 'items': items[:15]})
json.dump(res, open('noticias.json', 'w'), ensure_ascii=False, indent=1)
for f in res['fuentes']:
    print('==', f['nombre'], len(f['items'])); [print('  ', x['fecha'][:10], x['medio'], '|', x['titulo'][:90]) for x in f['items'][:3]]
