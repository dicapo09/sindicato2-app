"""Genera noticias.json (rubro minería) y noticias_pesca.json (rubro pesca y acuicultura) con titulares de cada medio.
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
    ('sindical', 'Mundo sindical', [gnews('"sindicato minero" OR "sindicato de trabajadores" minera OR "Federación Minera" OR "Confederación Minera" OR "Dirección del Trabajo" Chile')]),
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

# Redes sociales recomendadas (se muestran como accesos directos; editar esta lista para cambiarlas)
REDES = [
    {'red': 'Instagram', 'nombre': 'Minera Pacífico del Sur', 'usuario': '@minerapacificodelsur', 'url': 'https://www.instagram.com/minerapacificodelsur/', 'tema': 'Empresa'},
    {'red': 'Instagram', 'nombre': 'Confederación Minera de Chile (CONFEMIN)', 'usuario': '@confemin', 'url': 'https://www.instagram.com/confemin/', 'tema': 'Sindical minero'},
    {'red': 'Facebook', 'nombre': 'Confederación Minera de Chile (CONFEMIN)', 'usuario': 'confeminchile', 'url': 'https://www.facebook.com/confeminchile/', 'tema': 'Sindical minero'},
    {'red': 'X', 'nombre': 'Federación Minera de Chile (FMC)', 'usuario': '@fedeminerachile', 'url': 'https://x.com/fedeminerachile', 'tema': 'Sindical minero'},
    {'red': 'Instagram', 'nombre': 'CUT Chile', 'usuario': '@cutchileoficial', 'url': 'https://www.instagram.com/cutchileoficial/', 'tema': 'Sindical'},
    {'red': 'TikTok', 'nombre': 'Codelco', 'usuario': '@codelco', 'url': 'https://www.tiktok.com/@codelco', 'tema': 'Minería'},
    {'red': 'TikTok', 'nombre': 'Codelco División El Teniente', 'usuario': '@codelcoelteniente', 'url': 'https://www.tiktok.com/@codelcoelteniente', 'tema': 'Minería subterránea'},
]
# ===== Rubro pesca y acuicultura (salmoneros, pesqueros, artesanales, buzos) =====
FUENTES_PESCA = [
    ('subpesca', 'Sernapesca y Subpesca', [gnews('Sernapesca OR Subpesca OR "Subsecretaría de Pesca"')]),
    ('aqua', 'Aqua', ['https://www.aqua.cl/feed/', gnews('site:aqua.cl')]),
    ('salmonexpert', 'Salmonexpert', ['https://www.salmonexpert.cl/rss', gnews('site:salmonexpert.cl')]),
    ('mundoacuicola', 'Mundo Acuícola', ['https://www.mundoacuicola.cl/new/feed/', gnews('site:mundoacuicola.cl')]),
    ('artesanal', 'Pesca artesanal', [gnews('"pesca artesanal" OR "pescadores artesanales" OR caleta OR buzos mariscadores Chile')]),
    ('sur', 'Pesca en el sur', [gnews('salmonicultura OR acuicultura OR pesca Aysén OR "Los Lagos" OR Chiloé OR Magallanes')]),
    ('sindical', 'Mundo sindical', [gnews('sindicato salmonero OR "trabajadores del salmón" OR "sindicato pesquero" OR CONAPACH OR "Dirección del Trabajo" pesca')]),
]
# Sitios oficiales del rubro (se muestran en la pestaña Redes sociales)
REDES_PESCA = [
    {'red': 'Sitio web', 'nombre': 'Sernapesca', 'usuario': 'sernapesca.cl', 'url': 'https://www.sernapesca.cl', 'tema': 'Servicio Nacional de Pesca'},
    {'red': 'Sitio web', 'nombre': 'Subpesca', 'usuario': 'subpesca.cl', 'url': 'https://www.subpesca.cl', 'tema': 'Vedas y normativa'},
    {'red': 'Sitio web', 'nombre': 'CONAPACH', 'usuario': 'conapach.cl', 'url': 'https://www.conapach.cl', 'tema': 'Pescadores artesanales'},
    {'red': 'Sitio web', 'nombre': 'Directemar', 'usuario': 'directemar.cl', 'url': 'https://www.directemar.cl', 'tema': 'Autoridad Marítima'},
    {'red': 'Sitio web', 'nombre': 'SHOA', 'usuario': 'shoa.cl', 'url': 'https://www.shoa.cl', 'tema': 'Mareas'},
    {'red': 'Instagram', 'nombre': 'CUT Chile', 'usuario': '@cutchileoficial', 'url': 'https://www.instagram.com/cutchileoficial/', 'tema': 'Sindical'},
]

LEYES = ('leyes', 'Leyes laborales', [gnews('"Dirección del Trabajo" OR "40 horas" OR "Código del Trabajo" OR "negociación colectiva" Chile')])
def web(nombre, dominio, tema): return {'red': 'Sitio web', 'nombre': nombre, 'usuario': dominio, 'url': 'https://www.' + dominio, 'tema': tema}
CUT = {'red': 'Instagram', 'nombre': 'CUT Chile', 'usuario': '@cutchileoficial', 'url': 'https://www.instagram.com/cutchileoficial/', 'tema': 'Sindical'}
DT = web('Dirección del Trabajo', 'dt.gob.cl', 'Derechos laborales')
SUSESO = web('Superintendencia de Seguridad Social', 'suseso.cl', 'Licencias y accidentes')

OTROS_RUBROS = {
    'retail': ([
        ('retail', 'Retail en Chile', [gnews('retail OR supermercados OR "grandes tiendas" Chile Cencosud OR Walmart OR Falabella OR SMU OR Ripley')]),
        ('sindical', 'Mundo sindical', [gnews('sindicato Walmart OR Líder OR Cencosud OR Jumbo OR "Santa Isabel" OR Falabella OR Sodimac OR Tottus OR Unimarc OR Ripley OR Paris')]),
        ('comercio', 'Jornada y comercio', [gnews('"cierre del comercio" OR "feriado irrenunciable" OR "trabajadores del comercio" Chile')]),
        ('araucania', 'Comercio en La Araucanía', [gnews('comercio Temuco OR Villarrica OR Pucón OR Araucanía')]),
        LEYES], [DT, SUSESO, web('Ministerio del Trabajo', 'mintrab.gob.cl', 'Leyes laborales'), CUT]),
    'forestal': ([
        ('forestal', 'Sector forestal', [gnews('sector forestal OR CMPC OR Arauco OR celulosa OR aserradero Chile')]),
        ('incendios', 'Incendios forestales', [gnews('"incendio forestal" OR Conaf brigadistas Araucanía OR Biobío OR Ñuble OR Maule OR "Los Ríos"')]),
        ('araucania', 'Forestal en La Araucanía', [gnews('forestal Araucanía OR Malleco OR Cautín OR Villarrica')]),
        ('sindical', 'Mundo sindical', [gnews('sindicato forestal OR "trabajadores forestales" OR "contratistas forestales" OR "transportistas forestales"')]),
        LEYES], [web('CONAF', 'conaf.cl', 'Incendios y bosques'), web('Corma', 'corma.cl', 'Gremio forestal'), DT, SUSESO, CUT]),
    'banca': ([
        ('banca', 'Banca y finanzas', [gnews('banca Chile OR bancos chilenos OR BancoEstado OR Santander OR BCI OR "Banco de Chile"')]),
        ('economia', 'CMF y Banco Central', [gnews('"Banco Central" tasa OR IPoM OR "Comisión para el Mercado Financiero"')]),
        ('sindical', 'Mundo sindical', [gnews('sindicato bancario OR "sindicato BancoEstado" OR "Confederación Bancaria" OR "trabajadores bancarios"')]),
        LEYES], [web('Comisión para el Mercado Financiero', 'cmfchile.cl', 'Regulador'), web('Banco Central de Chile', 'bcentral.cl', 'Economía'), DT, CUT]),
    'salud': ([
        ('salud', 'Salud pública', [gnews('Minsal OR "atención primaria" OR CESFAM OR hospitales públicos Chile')]),
        ('gremios', 'Gremios de salud y públicos', [gnews('CONFUSAM OR FENPRUSS OR ANEF OR FENATS OR "asistentes de la educación"')]),
        ('publico', 'Sector público', [gnews('"reajuste del sector público" OR "funcionarios públicos" OR "Ley de Presupuestos"')]),
        ('araucania', 'Salud en La Araucanía', [gnews('"Servicio de Salud Araucanía" OR "Hospital de Villarrica" OR CESFAM Temuco OR Villarrica OR Pucón')]),
        ], [web('Ministerio de Salud', 'minsal.cl', 'Salud'), web('Superintendencia de Salud', 'supersalud.gob.cl', 'Salud'), web('Contraloría', 'contraloria.cl', 'Dictámenes sector público'), SUSESO, CUT]),
    'turismo': ([
        ('turismo', 'Turismo en Chile', [gnews('turismo Chile OR Sernatur OR temporada turística')]),
        ('lacustre', 'Villarrica y Pucón', [gnews('turismo Villarrica OR Pucón OR "Araucanía Lacustre" OR Licán Ray')]),
        ('hoteleria', 'Hotelería y gastronomía', [gnews('hotelería OR gastronomía OR casino OR "centro de ski" Chile trabajadores')]),
        ('sindical', 'Mundo sindical', [gnews('sindicato hotel OR "trabajadores gastronómicos" OR "trabajadores de casino" OR "sindicato de turismo" Chile')]),
        LEYES], [web('Sernatur', 'sernatur.cl', 'Turismo'), DT, SUSESO, CUT]),
    'agricola': ([
        ('agro', 'Agro en Chile', [gnews('agricultura Chile OR fruticultura OR "exportación de fruta" OR SAG OR Indap')]),
        ('araucania', 'Agro en La Araucanía', [gnews('agricultura Araucanía OR berries Araucanía OR Indap Araucanía OR lechería Araucanía')]),
        ('temporeros', 'Temporeros', [gnews('temporeros OR temporeras OR "trabajadores agrícolas" Chile')]),
        ('sindical', 'Mundo sindical', [gnews('sindicato agrícola OR "sindicato de temporeros" OR "trabajadores agrícolas" sindicato')]),
        LEYES], [web('SAG', 'sag.gob.cl', 'Servicio Agrícola y Ganadero'), web('INDAP', 'indap.gob.cl', 'Pequeña agricultura'), DT, SUSESO, CUT]),
}

def generar(fuentes, redes, archivo):
    res = {'actualizado': datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'), 'fuentes': [], 'redes': redes}
    try: prev = {f['clave']: f for f in json.load(open(archivo)).get('fuentes', [])}
    except Exception: prev = {}
    for clave, nombre, urls in fuentes:
        items = []
        for u in urls:
            try:
                items = parse(get(u), nombre)
                print(f'{clave}: {len(items)} desde {u[:70]}')
                if items: break
            except Exception as e:
                print(f'{clave}: falla {u[:70]} -> {e}')
        items.sort(key=lambda x: x['fecha'], reverse=True)
        vistos, unicos = set(), []
        for x in items:
            k = re.sub(r'\W+', '', x['titulo'].lower())[:60]
            if k not in vistos: vistos.add(k); unicos.append(x)
        items = unicos
        if not items and clave in prev: items = prev[clave]['items']
        res['fuentes'].append({'clave': clave, 'nombre': nombre, 'items': items[:15]})
    json.dump(res, open(archivo, 'w'), ensure_ascii=False, indent=1)
    for f in res['fuentes']:
        print('==', f['nombre'], len(f['items'])); [print('  ', x['fecha'][:10], x['medio'], '|', x['titulo'][:90]) for x in f['items'][:3]]

generar(FUENTES, REDES, 'noticias.json')
generar(FUENTES_PESCA, REDES_PESCA, 'noticias_pesca.json')
for rubro, (fuentes, redes) in OTROS_RUBROS.items():
    generar(fuentes, redes, f'noticias_{rubro}.json')
