# Librerías copiadas (vendor)

Ninguna se carga de un CDN: la app funciona sin conexión a un tercero y no cambia sola. Cada archivo es un
solo módulo ES, sin dependencias sueltas. Una línea por librería (versión, licencia, de dónde sale).

| Archivo | Librería | Versión | Licencia | Para qué |
|---|---|---|---|---|
| `trystero-nostr.js` | `@trystero-p2p/nostr` (Trystero) | 0.26.0 | MIT, `licenses/trystero.txt` | WebRTC; los pares se encuentran por relés Nostr. También da la lista de relés públicos al transporte `relay`. |
| `trystero-torrent.js` | `@trystero-p2p/torrent` | 0.26.0 | MIT | Lo mismo, encontrándose por trackers BitTorrent. |
| `trystero-mqtt.js` | `@trystero-p2p/mqtt` + `mqtt` 5.16.1 | 0.26.0 | MIT, `licenses/mqtt.txt` | Lo mismo, por brokers MQTT. Pesa 400 KB: solo se descarga si se prueba esa estrategia. |
| `noble-secp256k1.js` | `@noble/secp256k1` | 3.2.0 | MIT, `licenses/noble-secp256k1.txt` | Firma Schnorr de los eventos del transporte `relay`. |
| `qrcode-generator.js` | `qrcode-generator` (Kazuhiko Arase) | 2.0.4 | MIT, `licenses/qrcode-generator.txt` | Dibuja el QR para unirse a una sala. |

Un lector de QR (para el modo sin red) llega con F2, que es quien lo usa.

## Cómo se hicieron

Los paquetes de Trystero se publican en varios archivos con importaciones sueltas, así que se juntaron en uno
con esbuild (herramienta de una sola vez, no forma parte del repo ni de la CI):

```
npm i esbuild @trystero-p2p/nostr@0.26.0 @trystero-p2p/mqtt@0.26.0 @trystero-p2p/torrent@0.26.0 @noble/secp256k1@3.2.0
echo "export * from '@trystero-p2p/nostr';" > e.js
npx esbuild e.js --bundle --format=esm --minify --platform=browser --target=es2020 --outfile=trystero-nostr.js
# igual con mqtt y torrent, y con '@noble/secp256k1' para noble-secp256k1.js
```

`qrcode-generator.js` es `dist/qrcode.mjs` del paquete `qrcode-generator@2.0.4`, sin cambios.

Para actualizar una: repetir lo de arriba con la versión nueva, cambiar la tabla y correr `pytest -m web`.
