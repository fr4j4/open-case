# Prueba de conexión en redes reales (F0)

Esta hoja es el protocolo para saber, con datos, qué transporte usar en la sala en vivo de la versión web
(Open Case sin servidor propio). Está en español porque la usa fr4j4 en terreno; el resto de `docs/` está en inglés.

**Qué se decide:** si los teléfonos de una mesa se hablan directo por WebRTC (Trystero), por el bus de
mensajes cifrado que pasa por relés públicos (`relay`), por los dos, o si hace falta un servicio como Firebase o Supabase.
**Qué se cambia al decidir:** solo `site/play/js/transport/config.js` (`primary` y `fallback`). Mientras no haya
datos, el archivo queda en WebRTC primero (`trystero-nostr`) y el bus de respaldo (`relay`).

## Qué mide la página

Para cada **transporte**, en cada **red**, en cada **intento** (un intento = todos los teléfonos entran a una sala nueva):

| Medida | Cómo |
|---|---|
| Conectó en menos de 10 s | Cada teléfono mide desde que entra a la sala hasta ver al director. |
| Tiempo hasta conectar | Ese mismo tiempo; la tabla muestra la mediana. |
| Ida y vuelta | El director manda 10 mensajes a cada teléfono y mide cuánto tarda la confirmación; mediana y p95. |
| 100 mensajes seguidos | El director manda 100 numerados; el teléfono cuenta cuántos llegaron, si hubo repetidos y si llegaron en orden. |
| Recuperación tras bloquear | (Solo en "Una ronda con bloqueo".) Cada teléfono bloquea la pantalla 30 s; al volver pregunta si la sala sigue viva (< 15 s). |

Un intento cuenta como **éxito** si conectó en menos de 10 s **y** recibió los 100 mensajes sin pérdidas, repetidos ni desorden.
(La capa de ids y reintentos de `transport.js` corrige pérdidas y repetidos del canal; lo que se mide es que el
conjunto llegue completo a tiempo. Los reintentos y las pérdidas de cada ronda quedan en el JSON.)

Transportes que se prueban: `trystero-nostr`, `trystero-mqtt`, `trystero-torrent` (las tres formas de encontrarse
de Trystero; después de encontrarse, los datos van directo por WebRTC) y `relay` (los mensajes pasan por relés
Nostr, cifrados con una clave que sale del nombre de la sala).

## Antes de salir (una vez)

1. Instala `cloudflared` en tu computador: macOS `brew install cloudflared`; Windows `winget install Cloudflare.cloudflared`;
   otros: <https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/downloads/>. No pide cuenta.
2. En la carpeta del repo, en la rama `feature/web-p2p`: `make install` (si no lo hiciste) y `make web-preview`.
3. La terminal muestra una URL `https://….trycloudflare.com/` y el enlace de la prueba. **La URL cambia cada vez**
   y dura lo que dure el comando; no cierres la terminal durante la sesión.
   (Alternativa sin túnel: un repositorio de pruebas con su propio Pages. Es más trabajo de montar; ver el plan.)

## Qué redes y qué teléfonos

- **Al menos 3 teléfonos**, entre ellos **un iPhone y un Android**. Un cuarto ayuda.
- **Al menos 4 tipos de red**, cada uno con su etiqueta en la página:

  | Etiqueta | Cómo armarla |
  |---|---|
  | Wi-Fi de casa | Todos en el mismo Wi-Fi doméstico. |
  | Wi-Fi institucional | Un Wi-Fi de universidad, oficina o colegio (suele bloquear WebRTC: es la prueba más dura). |
  | Datos móviles mezclados con Wi-Fi | Parte de los teléfonos en datos móviles y parte en Wi-Fi. |
  | Hotspot del director | El teléfono del director comparte internet y los demás se conectan a él. |

- **Al menos 10 intentos por transporte y por red** (la página tiene por defecto 10).
- **En dos días distintos**: los relés públicos cambian de un día a otro. Cada día se suman al mismo resultado (ver abajo).

## Paso a paso (una red)

1. En el teléfono del director abre la URL de la prueba con `?rol=director` (la terminal la imprime). Aparece un **código QR** y un código de sala.
2. En cada otro teléfono, escanea el QR. Entra como "teléfono de equipo" y se anota en la lista del director.
   Si el QR no sirve, abre la página, toca "Soy un teléfono de equipo" y escribe el código de sala.
3. Cuando el director vea todos los teléfonos y "Control: conectado", elige la **red** que estás probando, deja
   "Intentos por transporte" en 10 y toca **Prueba completa**. Cada ronda dura entre 10 y 30 s; los cuatro transportes
   con 10 intentos son unos 15 minutos por red. **Mantén las pantallas encendidas y la página en primer plano.**
4. Al terminar, la tabla muestra por transporte: intentos, % de éxito, conexión, ida y vuelta. Debajo, "Lectura de las
   reglas" y lo que todavía falta según este protocolo.
5. **Prueba de bloqueo:** con la red ya medida, toca **Una ronda con bloqueo** (deja marcado solo un transporte, por ejemplo
   el que va ganando: la ronda usa el primero marcado). Cuando el director lo indique, cada teléfono **bloquea la pantalla 30 segundos y vuelve**. Repítelo
   un par de veces por transporte candidato. Esto no es parte de la regla de decisión, pero decide cómo se escribe la
   app: un transporte que no sobrevive al bloqueo necesita reconexión automática.
6. Cambia de red, cambia la etiqueta en el director y repite desde el paso 3. No hace falta recargar ni volver a escanear
   si los teléfonos siguen en la página.

### Si algo no conecta

- **"sin control":** el control de la prueba usa el bus por relé. Si ni eso conecta, la red bloquea los relés. Es un dato:
  anótalo y usa el **modo manual** (en los teléfonos, "Modo manual": elegir transporte y número de intento, y en el
  director "Una ronda"). Cada teléfono entonces copia su propio JSON; no habrá tabla única.
- **Un teléfono no aparece en la lista:** recarga su página (el código QR trae la sala).
- **Todo falla en una red:** déjalo correr igual. Los fallos cuentan: son justo lo que se quiere saber.

## Guardar los resultados

Los resultados se guardan solos en el teléfono del director (`localStorage`). Al final de cada sesión:

1. **Copiar JSON** (o **Descargar JSON**) en el director y pégalo en un archivo o en un mensaje a ti mismo.
2. El segundo día, en el director, abre "Sumar resultados de otra sesión", pega el JSON del primer día y toca **Sumar**:
   la tabla y la lectura de las reglas pasan a incluir los dos días.
3. Entrega el JSON final al coordinador para el informe.

## Cómo se decide

La página aplica las reglas a los datos en este orden y se queda con la primera que se cumple; el código está en
`site/lab/red/decision.js` y lo prueba la CI con datos inventados.

1. Si el **bus por relé** (`relay`) logra **≥ 95 %** en **todas** las redes → **bus primero**, WebRTC opcional (menos piezas que mantener).
2. Si **WebRTC** (alguna de las tres estrategias) conecta en **≥ 90 %** en la casa **y** en el hotspot, y el bus por relé cubre las
   redes donde WebRTC se queda corto con **≥ 95 %** → **WebRTC primero y el bus de respaldo**.
3. Si ninguno llega → **plan B**: Firebase o Supabase en F3 (se decide con fr4j4), o quedarse en F2, que no necesita red.

La decisión vale solo con los datos completos: **≥ 10 intentos por transporte y red, 2 días, 4 tipos de red, 3 teléfonos,
un iPhone y un Android.** Mientras falte algo, la página lo lista bajo la lectura y la regla es provisoria.

### Cómo se aplica

Escribir en `site/play/js/transport/config.js` lo que muestra la lectura (`primary` y `fallback`):

| Regla | `primary` | `fallback` |
|---|---|---|
| 1 | `relay` | la estrategia WebRTC que mejor haya salido, o `null` |
| 2 | la estrategia WebRTC que cumplió (p. ej. `trystero-nostr`) | `relay` |
| 3 | no se cambia: F3 se detiene y se replanifica | – |

Y dejar el informe en `/mnt/project-files/open-case/propuestas/web_red_resultados.md`: la tabla, el JSON adjunto
(o su ruta), lo que se decidió y las notas de terreno (qué red falló y cómo).

## Lo que la CI sí prueba y lo que no

En la CI (Chromium, `pytest -m web`):

- `broadcast` con 1 director y 3 equipos entrega 100 de 100 mensajes a cada uno, en orden y sin repetidos.
- La capa de ids, confirmaciones y reintentos entrega todo una sola vez y en orden contra un canal simulado que pierde el 30 %
  y repite el 30 % de los mensajes (el mismo contrato corre contra `broadcast`).
- Las reglas de decisión, con datos inventados para cada caso.
- La página del laboratorio de punta a punta con 4 páginas (director y 3 teléfonos) sobre `broadcast`.
- `trystero` y `relay` cargan y cumplen la interfaz; el bus firma y cifra lo que publica (con un WebSocket falso).

**No se prueba en la CI** (depende de relés, redes y Safari reales): que `trystero` y `relay` conecten de verdad, los tiempos
reales, el comportamiento en iPhone y la recuperación tras bloquear la pantalla. Eso es el **cierre de campo** de esta fase, y es
lo que cubre este protocolo.
