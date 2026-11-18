"""Genera indicadores.json para la app del Sindicato N°2.
Fuentes: mindicador.cl (UF, dólar, euro, UTM, IPC, libra de cobre),
Stooq / Yahoo Finance (oro y plata, US$/onza troy) y Westmetall (zinc LME, US$/tonelada)."""
import json, re, csv, io, ssl, urllib.request, datetime

UA = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36'}

def get(url, timeout=25):
    req = urllib.request.Request(url, headers=UA)
    try:
        return urllib.request.urlopen(req, timeout=timeout).read().decode('utf-8', 'replace')
    except ssl.SSLError:
        ctx = ssl.create_default_context(); ctx.set_ciphers('DEFAULT:@SECLEVEL=1')
        return urllib.request.urlopen(req, timeout=timeout, context=ctx).read().decode('utf-8', 'replace')

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

out = {}
try:
    d = json.loads(get('https://mindicador.cl/api'))
except Exception:
    d = json.loads(get('http://mindicador.cl/api'))
for k in ['uf', 'dolar', 'euro', 'utm', 'ipc', 'libra_cobre']:
    if k in d:
        out[k] = {'valor': d[k]['valor'], 'fecha': d[k]['fecha']}
assert out.get('uf'), 'mindicador sin UF'

metales = {
    'oro':   first(stooq('xauusd'), yahoo('GC=F')),
    'plata': first(stooq('xagusd'), yahoo('SI=F')),
    'zinc':  first(westmetall('LME_Zn_cash')),
}
try:
    prev = json.load(open('indicadores.json'))
except Exception:
    prev = {}
for k, v in metales.items():
    print(k, v)
    if v: out[k] = v
    elif k in prev: out[k] = prev[k]          # conserva el último valor conocido
json.dump(out, open('indicadores.json', 'w'), ensure_ascii=False, indent=1)
print(json.dumps(out, ensure_ascii=False))
