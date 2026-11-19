"""Envía notificaciones push cuando la directiva publica algo nuevo.

Lo ejecuta GitHub Actions cada ~5 minutos (.github/workflows/push.yml).
Necesita el secreto FIREBASE_SA: la cuenta de servicio de Firebase en JSON
(Firebase > Configuración del proyecto > Cuentas de servicio > Generar nueva clave privada).

- Revisa informativos, eventos (citaciones) y encuestas creados desde la última pasada,
  tanto del Sindicato N°2 (colecciones raíz) como de cada sindicato de la plataforma (sindicatos/{id}/...).
- Envía el aviso al tema de ese sindicato: «sin2» para el N°2 y «s_<código>» para los demás.
  La app suscribe a cada socio activo a su tema al iniciar sesión.
- Guarda la hora de lo último avisado en el documento _push/estado (los socios no pueden leerlo).
"""
import datetime as dt
import json
import os
import sys

import requests
from google.auth.transport.requests import Request
from google.oauth2 import service_account

TIPOS = {
    'informativos': '📢 Nuevo informativo',
    'eventos': '📅 Nueva citación / evento',
    'encuestas': '🗳️ Nueva encuesta',
}
MAX_POR_SINDICATO = 5   # si hay muchas publicaciones juntas, no saturar a los socios

sa = json.loads(os.environ['FIREBASE_SA'])
PROY = sa['project_id']
cred = service_account.Credentials.from_service_account_info(
    sa, scopes=['https://www.googleapis.com/auth/cloud-platform'])
cred.refresh(Request())
H = {'Authorization': 'Bearer ' + cred.token, 'Content-Type': 'application/json'}
DOCS = f'https://firestore.googleapis.com/v1/projects/{PROY}/databases/(default)/documents'
RAIZ = f'projects/{PROY}/databases/(default)/documents'


def ts(v):
    # Firestore entrega nanosegundos; se ordena con el texto normalizado a 9 decimales
    fecha, _, resto = v.rstrip('Z').partition('.')
    return fecha + '.' + (resto + '000000000')[:9] + 'Z'


def texto(f, k):
    v = f.get(k) or {}
    return str(v.get('stringValue') or '').strip()


def leer_estado():
    r = requests.get(DOCS + '/_push/estado', headers=H, timeout=30)
    if r.status_code == 404:
        return None
    r.raise_for_status()
    v = r.json().get('fields', {}).get('ultimo', {}).get('timestampValue')
    return ts(v) if v else None


def guardar_estado(t):
    body = {'fields': {'ultimo': {'timestampValue': t}}}
    requests.patch(DOCS + '/_push/estado', headers=H, json=body, timeout=30).raise_for_status()


def sindicatos():
    """(tema, ruta) del N°2 y de cada sindicato activo de la plataforma."""
    out = [('sin2', RAIZ)]
    tok = None
    while True:
        p = {'pageSize': 300, 'mask.fieldPaths': 'activo'}
        if tok:
            p['pageToken'] = tok
        r = requests.get(DOCS + '/sindicatos', headers=H, params=p, timeout=30)
        r.raise_for_status()
        j = r.json()
        for d in j.get('documents', []):
            sid = d['name'].rsplit('/', 1)[1]
            if sid == 'demo' or d.get('fields', {}).get('activo', {}).get('booleanValue') is False:
                continue
            out.append(('s_' + sid, f'{RAIZ}/sindicatos/{sid}'))
        tok = j.get('nextPageToken')
        if not tok:
            return out


def nuevos(ruta, coleccion, desde):
    q = {'structuredQuery': {
        'from': [{'collectionId': coleccion}],
        'where': {'fieldFilter': {'field': {'fieldPath': 'creado'}, 'op': 'GREATER_THAN',
                                  'value': {'timestampValue': desde}}},
        'orderBy': [{'field': {'fieldPath': 'creado'}, 'direction': 'ASCENDING'}],
        'limit': 20}}
    r = requests.post(f'https://firestore.googleapis.com/v1/{ruta}:runQuery', headers=H, json=q, timeout=30)
    r.raise_for_status()
    return [x['document'] for x in r.json() if 'document' in x]


def enviar(tema, titulo, cuerpo, tipo, doc_id):
    msg = {'message': {
        'topic': tema,
        'notification': {'title': titulo, 'body': cuerpo},
        'android': {'priority': 'high', 'notification': {'channel_id': 'avisos', 'tag': doc_id}},
        'data': {'tipo': tipo, 'id': doc_id, 'titulo': titulo, 'texto': cuerpo}}}
    r = requests.post(f'https://fcm.googleapis.com/v1/projects/{PROY}/messages:send', headers=H, json=msg, timeout=30)
    if r.status_code != 200:
        print('  ERROR al enviar a', tema, r.status_code, r.text[:300])
        return False
    return True


def main():
    ahora = dt.datetime.now(dt.timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.%f000Z')
    desde = leer_estado()
    if desde is None:
        # Primera vez: no avisar de publicaciones antiguas
        guardar_estado(ahora)
        print('Primera pasada: se avisará lo que se publique desde ahora.')
        return 0
    errores, enviados = 0, 0
    for tema, ruta in sindicatos():
        items = []
        for col in TIPOS:
            for d in nuevos(ruta, col, desde):
                t = ts(d['fields']['creado']['timestampValue'])
                if t <= ahora:          # lo posterior se avisa en la próxima pasada
                    items.append((t, col, d))
        items.sort(key=lambda x: x[0])
        for t, col, d in items[:MAX_POR_SINDICATO]:
            f = d['fields']
            cuerpo = texto(f, 'titulo')
            extra = texto(f, 'resumen') or (texto(f, 'fecha') if col == 'eventos' else '')
            if extra:
                cuerpo += ' — ' + extra
            ok = enviar(tema, TIPOS[col], cuerpo[:240], col, d['name'].rsplit('/', 1)[1])
            print(('enviado ' if ok else 'falló   ') + tema, col, texto(f, 'titulo')[:60])
            enviados += ok
            errores += not ok
    guardar_estado(ahora)
    print(f'{enviados} aviso(s) enviado(s), {errores} error(es).')
    return 1 if errores else 0


if __name__ == '__main__':
    sys.exit(main())
