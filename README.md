# App Sindicato N°2 · Minera Pacífico del Sur SpA

Repositorio de **contenido y actualizaciones** de la app. Solo quien tiene acceso de escritura a este repositorio puede cambiar lo que ven los socios.

| Archivo | Para qué sirve |
|---|---|
| `contenido.json` | Informativos, noticias, calendario, encuestas, beneficios, biblioteca, directiva y contactos. Los socios lo reciben al abrir la app. |
| `app.html` | La app completa (pantallas y funciones). Se actualiza sola en los teléfonos. |
| `version.json` | Indica la versión publicada. |
| `apk/SindicatoN2.apk` | Instalador para socios nuevos. |

## Publicar contenido
Edita `contenido.json` (o usa el panel de Administración de la app: toca 7 veces la línea «Versión» al final del menú) y guarda con «Commit changes».

## Publicar una actualización de la app (automática)
1. Sube el nuevo `app.html` con `var APP_VER=` aumentado en 1 (p. ej. 5).
2. En `version.json` cambia `"app"` al mismo número.
3. Los teléfonos la descargan al abrir la app y la aplican en la siguiente apertura (o con el botón «Aplicar»). Si una versión falla al abrir, la app vuelve sola a la versión anterior.

## Nueva versión del APK (solo si cambia la parte Android)
Sube el APK firmado con `sindicato2.keystore` (nunca subas la llave) a `apk/SindicatoN2.apk` y aumenta `"apk"` en `version.json`: los socios verán un aviso para descargarlo.

Descarga para socios: https://github.com/dicapo09/sindicato2-app/raw/main/apk/SindicatoN2.apk
