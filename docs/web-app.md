# The web app: team folder and delivery by QR (F2)

`site/play/` is the app. It reads only what `opencase.web` compiles (see `web-format.md`); it never reads YAML. Two pages:

- `play/equipo/` is a team's device. It opens with its team's link or QR, downloads the kit, envelope 1 and the suspect
  cards, and keeps a **folder** of everything handed out, sorted by code, with zoom. It works without a connection
  (IndexedDB for the state, the service worker `play/sw.js` for the pages).
- `play/director/` is the director's device. It chooses a case and the number of teams, shows the kit, and hands out
  sheets and cards: tick the team and the codes, and it shows a QR and a link. The game is kept in IndexedDB.

## What travels

Only codes, in the `#fragment` of the link (which no server receives): `…/play/equipo/#oc1.<base64url JSON>` with
`{c: case, l: language, v: version, t: team, s: delivery number, i: [[file, code], …]}`. An empty `i` is the link that
joins a team. `js/delivery.js` checks every field (a file can only be `sheets|cards|suspects/<name>.html`), and delivering
the same file twice changes nothing. The team's device downloads only the files it is given; it never asks for
`director.json`. The QR is the link: `js/qr.js` draws it (`vendor/qrcode-generator.js`) and reads it (`BarcodeDetector`,
or `vendor/jsQR.js` where the browser has none, as on iOS; also from a photo or a screenshot).

## Updating the site in the middle of a game

Pages replaces the whole site on every deployment, so the folder of an old version disappears. A team's device keeps
what it already loaded (the cache keeps old files). For a file that is gone (404) it asks `cases/index.json`: if the
current version has the same `schema_version`, it takes the file from there and tells the team; if the format changed,
it says so and the game goes on with what is loaded. The director's panel shows the same notice.

## Files

| File | What it does |
|---|---|
| `js/store.js` | IndexedDB key/value, with a memory fallback |
| `js/delivery.js` | encode, decode and check the message of a delivery; natural order of codes |
| `js/qr.js` | draw and read QR |
| `js/viewer.js` | full screen viewer of a page with zoom |
| `js/i18n.js`, `js/dom.js` | strings of `web.team` / `web.director`, and a small DOM helper |
| `sw.js` | cache-first for each version of a case; network-first for the app and `index.json` |
| `equipo/`, `director/` | the two pages |

Tests: `tests/web/test_folder.py` (`pytest -m web`). Not covered by the CI (it needs real phones): Safari/iOS, the camera, and a
full game at a table.
