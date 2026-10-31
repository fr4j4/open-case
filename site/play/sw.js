// Service worker of the web app (scope: play/). It makes the team's folder work without a connection.
//   cases/<case>/<lang>/<version>/…   cache-first: a version never changes, so what was seen once is kept
//   cases/index.json, strings/…        network first, the last copy when there is no connection
//   the app itself (pages, scripts…)   network first with a short wait, the last copy otherwise
// Nothing is cached ahead of time except the app's own pages: which pages of a case a device keeps is decided by
// the app (a team's device downloads only what the team may have; the director's file is never asked for there).
const SHELL = 'oc-play-shell-2';
const CASES = 'oc-play-cases-1';
const APP = ['./', './equipo/', './director/', './css/play.css', './js/dom.js', './js/store.js', './js/i18n.js', './js/delivery.js',
  './js/qr.js', './js/viewer.js', './js/canal.js', './js/room.js', './js/log.js', './js/transport/config.js', './js/transport/index.js',
  './js/transport/transport.js', './js/transport/broadcast.js', './js/transport/relay.js', './js/transport/trystero.js', './js/rules.js', './js/requests.js', './equipo/app.js', './equipo/pedir.js', './director/app.js', './director/panel.js', './vendor/qrcode-generator.js'];

self.addEventListener('install', (e) => {
  e.waitUntil((async () => {
    const cache = await caches.open(SHELL);
    await Promise.all(APP.map((u) => cache.add(u).catch(() => null)));   // a missing page must not block the install
    await self.skipWaiting();
  })());
});

self.addEventListener('activate', (e) => {
  e.waitUntil((async () => {
    for (const k of await caches.keys()) if (![SHELL, CASES].includes(k)) await caches.delete(k);
    await self.clients.claim();
  })());
});

const WAIT_MS = 4000;
function networkFirst(req, cacheName, ignoreSearch) {
  return (async () => {
    const cache = await caches.open(cacheName);
    try {
      const res = await Promise.race([fetch(req), new Promise((_, no) => setTimeout(() => no(new Error('slow')), WAIT_MS))]);
      if (res.ok) cache.put(req, res.clone());
      return res;
    } catch (err) {
      const hit = await cache.match(req, { ignoreSearch });
      if (hit) return hit;
      return fetch(req);   // no copy: let the real error (or a slow answer) through
    }
  })();
}

self.addEventListener('fetch', (e) => {
  const req = e.request;
  if (req.method !== 'GET' || req.headers.has('range')) return;
  const url = new URL(req.url);
  if (url.origin !== self.location.origin) return;
  const scope = new URL(self.registration.scope).pathname;
  if (!url.pathname.startsWith(scope)) return;
  const rel = url.pathname.slice(scope.length);
  if (rel.startsWith('cases/') && rel !== 'cases/index.json') {
    e.respondWith((async () => {
      const cache = await caches.open(CASES);
      const hit = await cache.match(req);
      if (hit) return hit;
      const res = await fetch(req);
      if (res.ok) cache.put(req, res.clone());
      return res;
    })());
  } else if (rel === 'cases/index.json' || rel.startsWith('strings/')) {
    e.respondWith(networkFirst(req, CASES, false));
  } else {
    e.respondWith(networkFirst(req, SHELL, req.mode === 'navigate'));
  }
});
