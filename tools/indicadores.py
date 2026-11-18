"""Genera indicadores.json para la app del Sindicato N°2.
Fuentes: mindicador.cl (UF, dólar, euro, UTM, IPC, libra de cobre),
Stooq / Yahoo Finance (oro y plata, US$/onza troy) y Westmetall (zinc LME, US$/tonelada)."""
import json, re, csv, io, ssl, urllib.request, datetime

UA = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36'}

import subprocess
def get(url, timeout=40):
    """Descarga con curl (reintentos y redirecciones)."""
    r = subprocess.run(['curl', '-sfL', '--retry', '3', '--retry-delay', '3', '--max-time', str(timeout),
                        '-A', UA['User-Agent'], url], capture_output=True)
    if r.returncode != 0 or not r.stdout:
        raise IOError(f'curl {r.returncode} {url}')
    return r.stdout.decode('utf-8', 'replace')

def first(*fns):
    for f in fns:
        try:
            v = f()
            if v and v.get('valor'):
                return v
        except Exception as e:
            print('  falla', getattr(f, '__name__', f), e)
    return None

def stooq(sym):
    def f():
        rows = list(csv.DictReader(io.StringIO(get(f'https://stooq.com/q/l/?s={sym}&f=sd2t2c&h&e=csv'))))
        r = rows[0]; v = float(r['Close'])
        return {'valor': round(v, 2), 'fecha': r['Date'] + 'T00:00:00Z', 'fuente': 'Stooq'}
    f.__name__ = 'stooq_' + sym; return f

def yahoo(sym):
    def f():
        j = json.loads(get(f'https://query1.finance.yahoo.com/v8/finance/chart/{sym}?range=5d&interval=1d'))
        m = j['chart']['result'][0]['meta']
        t = datetime.datetime.utcfromtimestamp(m['regularMarketTime']).strftime('%Y-%m-%dT%H:%M:%SZ')
        return {'valor': round(float(m['regularMarketPrice']), 2), 'fecha': t, 'fuente': 'Yahoo Finance'}
    f.__name__ = 'yahoo_' + sym; return f

def westmetall(field):
    def f():
        h = get(f'https://www.westmetall.com/en/markdaten.php?action=table&field={field}')
        for row in re.findall(r'<tr[^>]*>(.*?)</tr>', h, re.S):
            cells = [re.sub(r'<[^>]+>|&nbsp;', ' ', c).strip() for c in re.findall(r'<td[^>]*>(.*?)</td>', row, re.S)]
            if len(cells) >= 2 and re.search(r'\d{4}', cells[0]) and re.match(r'^[\d.,]+$', cells[1].replace(' ', '')):
                v = float(cells[1].replace(',', ''))
                d = datetime.datetime.strptime(re.sub(r'\.', '', cells[0]).strip(), '%d %B %Y').strftime('%Y-%m-%dT00:00:00Z')
                return {'valor': round(v, 2), 'fecha': d, 'fuente': 'LME vía Westmetall'}
        raise ValueError('sin datos')
    f.__name__ = 'westmetall_' + field; return f

def ipc_ine():
    h = get('https://www.ine.gob.cl/estadisticas/economia/indices-de-precio-e-inflacion/indice-de-precios-al-consumidor')
    t = re.sub(r'<[^>]+>', ' ', h); t = re.sub(r'\s+', ' ', t)
    m = re.search(r'(enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|octubre|noviembre|diciembre)\s+(?:de\s+)?(20\d\d)[^.]{0,160}?variaci[oó]n mensual de\s+(-?\d+(?:,\d+)?)\s*%', t, re.I)
    print('  INE muestra:', t[t.lower().find('variación mensual')-200:t.lower().find('variación mensual')+80] if 'variación mensual' in t.lower() else t[:200])
    if not m: raise ValueError('patrón IPC no encontrado')
    meses = ['enero','febrero','marzo','abril','mayo','junio','julio','agosto','septiembre','octubre','noviembre','diciembre']
    mes = meses.index(m.group(1).lower()) + 1
    return {'valor': float(m.group(3).replace(',', '.')), 'fecha': f'{m.group(2)}-{mes:02d}-01T00:00:00Z', 'fuente': 'INE'}
def ipc_mindicador_serie():
    j = json.loads(get('https://mindicador.cl/api/ipc'))
    x = j['serie'][0]; return {'valor': x['valor'], 'fecha': x['fecha'], 'fuente': 'mindicador'}
def ipc_boostr():
    j = json.loads(get('https://api.boostr.cl/economy/indicator/ipc.json'))
    print('  boostr:', str(j)[:200]); d = j.get('data', j)
    return {'valor': float(d['value']), 'fecha': d['date'] + 'T00:00:00Z' if len(d['date']) == 10 else d['date'], 'fuente': 'boostr'}

try:
    prev = json.load(open('indicadores.json'))
except Exception:
    prev = {}
out = {}
d = {}
for u in ['https://mindicador.cl/api', 'http://mindicador.cl/api']:
    try:
        d = json.loads(get(u)); break
    except Exception as e:
        print('  falla mindicador', e)
for k in ['uf', 'dolar', 'euro', 'utm', 'libra_cobre']:
    if k in d: out[k] = {'valor': d[k]['valor'], 'fecha': d[k]['fecha']}
    elif k in prev: out[k] = prev[k]
cands = [x for x in [first(ipc_ine), first(ipc_boostr), first(ipc_mindicador_serie)] if x]
if 'ipc' in d: cands.append({'valor': d['ipc']['valor'], 'fecha': d['ipc']['fecha'], 'fuente': 'mindicador'})
print('IPC candidatos:', cands)
if cands: out['ipc'] = max(cands, key=lambda x: x['fecha'])
elif 'ipc' in prev: out['ipc'] = prev['ipc']
if not out.get('uf'): raise SystemExit('sin UF; se conserva el archivo anterior')

metales = {
    'oro':   first(stooq('xauusd'), yahoo('GC=F')),
    'plata': first(stooq('xagusd'), yahoo('SI=F')),
    'zinc':  first(westmetall('LME_Zn_cash')),
}
for k, v in metales.items():
    print(k, v)
    if v: out[k] = v
    elif k in prev: out[k] = prev[k]          # conserva el último valor conocido
json.dump(out, open('indicadores.json', 'w'), ensure_ascii=False, indent=1)
print(json.dumps(out, ensure_ascii=False))
