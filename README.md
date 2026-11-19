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

## Notificaciones push
Cuando la directiva publica un **informativo, citación/evento o encuesta**, los socios reciben un aviso en el teléfono (llega en 5–15 minutos; lo envía GitHub Actions gratis con `.github/workflows/push.yml`).

Configuración (una sola vez, en la consola de Firebase del proyecto `sindicato2-pds`):
1. **Agregar app Android**: Configuración del proyecto › Tus apps › Android, paquete `cl.sindicato.pacificodelsur`. Descarga `google-services.json` y pega su contenido en el secreto del repositorio **`GOOGLE_SERVICES_JSON`** (Settings › Secrets and variables › Actions).
2. **Cuenta de servicio**: Configuración del proyecto › Cuentas de servicio › *Generar nueva clave privada*. Pega el JSON completo en el secreto **`FIREBASE_SA`**. Nunca subas este archivo al repositorio.
3. Compila el APK nuevo con *Compilar app Android* (versionCode 11, versionName 2.2), fírmalo, súbelo a `apk/SindicatoN2.apk` y sube `"apk"` a 11 en `version.json`.

Los socios con el APK nuevo quedan suscritos al iniciar sesión (tema `sin2`; los sindicatos de la plataforma usan `s_<código>`). Con el APK antiguo la app sigue funcionando igual, sin avisos.
