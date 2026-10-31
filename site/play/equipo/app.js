// The team's device: its folder of evidence (kit, envelope 1 and everything the director hands out), kept in
// IndexedDB and in the service worker's cache, so it works without a connection.
import { h, clear, toast } from '../js/dom.js';
import { loadStrings, t, plural, registerWorker, PLAY_ROOT } from '../js/i18n.js';
import * as store from '../js/store.js';
import { decode, kindOf, naturalCompare } from '../js/delivery.js';
import { decodeFile, scanCamera } from '../js/qr.js';
import { openViewer } from '../js/viewer.js';
import { DeviceRoom, keepAwake, newId, normalizePin, validPin, pinFromHash } from '../js/room.js';

const app = document.getElementById('app');
let state = null;          // what this device knows (also saved in IndexedDB under 'team')
let teamJson = null;       // team.json of the version the folder started with
let filter = 'all';
let tab = 'folder';
let busy = null;           // {done, total} while downloading
let online = navigator.onLine;
let room = null;           // the live room (js/room.js) this phone is in, if any
let deviceId = null;       // this phone's id in rooms; kept, so a reload is the same phone
let stopAwake = null;
let netQueue = Promise.resolve();

const caseUrl = (version, file = '') => new URL(`cases/${state.slug}/${state.lang}/${version}/${file}`, PLAY_ROOT);
const save = () => store.set('team', state);

// --- Downloading ----------------------------------------------------------------------------------------------

async function fetchJson(url) {
  const r = await fetch(url, { cache: 'no-cache' });
  if (!r.ok) { const e = new Error(String(r.status)); e.status = r.status; throw e; }
  return r.json();
}

function absolute(base, ref) { return new URL(ref, base).href; }

// The page and what it needs to be drawn (styles, photos), so it opens later without a connection.
async function download(url) {
  const r = await fetch(url);
  if (!r.ok) { const e = new Error(String(r.status)); e.status = r.status; throw e; }
  const html = await r.text();
  const doc = new DOMParser().parseFromString(html, 'text/html');
  const label = (doc.title || '').replace(/\s*·\s*[^·]*$/, '').trim();
  const refs = [...doc.querySelectorAll('link[rel~=stylesheet][href], img[src]')].map((el) => absolute(url, el.getAttribute('href') || el.getAttribute('src')));
  const seen = new Set();
  const queue = [...refs];
  while (queue.length) {
    const u = queue.pop();
    if (seen.has(u)) continue;
    seen.add(u);
    try {
      const res = await fetch(u);
      if (res.ok && u.endsWith('.css')) {   // fonts.css is imported by open-case.css; the fonts themselves load when a page uses them
        const css = await res.text();
        for (const m of css.matchAll(/@import\s+(?:url\()?['"]?([^'")]+)['"]?\)?/g)) queue.push(absolute(u, m[1]));
      }
    } catch (e) { /* a missing photo does not stop the page */ }
  }
  return label;
}

async function fetchItem(item) {
  // Normally the version the director handed it out with. If the site was updated meanwhile that folder is gone (404):
  // use the current version when the format is the same, or tell the team to finish with what it has.
  const versions = [item.v];
  for (let n = 0; n < versions.length; n++) {
    try {
      const label = await download(caseUrl(versions[n], item.file));
      item.v = versions[n];
      item.status = 'ok';
      if (label && !item.label) item.label = label;
      return;
    } catch (e) {
      if (e.status === 404 && n === 0) {
        const next = await currentCompatibleVersion();
        if (next && next !== item.v) { versions.push(next); continue; }
        if (next === null) { item.status = 'unavailable'; state.notice = 'format'; return; }
      }
      item.status = e.status === 404 ? 'unavailable' : 'pending';   // anything else (no connection, a busy server): try again later
      return;
    }
  }
  item.status = 'unavailable';
}

// The current version of this case if its format is the one the folder was made with; null if the format changed;
// undefined if it could not be checked (no connection).
async function currentCompatibleVersion() {
  try {
    const index = await fetchJson(new URL('cases/index.json', PLAY_ROOT));
    const entry = index.cases.find((c) => c.slug === state.slug && c.language === state.lang);
    if (!entry) return null;
    const manifest = await fetchJson(new URL(`${entry.path}manifest.json`, PLAY_ROOT));
    if (manifest.schema_version !== state.schema) return null;
    if (entry.version !== state.version) state.notice = state.notice || 'updated';
    state.latest = entry.version;
    return entry.version;
  } catch (e) { return undefined; }
}

async function downloadAll(items) {
  busy = { done: 0, total: items.length };
  render();
  let next = 0;
  const worker = async () => {
    while (next < items.length) {
      const it = items[next++];
      await fetchItem(it);
      busy.done++;
      updateProgress();
    }
  };
  await Promise.all([worker(), worker(), worker(), worker()]);
  busy = null;
  await save();
  render();
  warmUp();
}

// One page of each kind is drawn once in a hidden frame, so the fonts the pages use are kept too.
function warmUp() {
  const pick = (kind) => Object.values(state.items).find((i) => i.kind === kind && i.status === 'ok');
  for (const it of [pick('sheet'), pick('suspect')].filter(Boolean)) {
    const f = h('iframe', { src: caseUrl(it.v, it.file).href, 'aria-hidden': 'true', tabindex: '-1', style: 'position:absolute;width:1px;height:1px;border:0;opacity:0' });
    document.body.append(f);
    setTimeout(() => f.remove(), 6000);
  }
}

function updateProgress() {
  const bar = document.querySelector('.oc-progress > i');
  if (bar && busy) bar.style.width = `${Math.round((busy.done / busy.total) * 100)}%`;
}

// --- Joining and receiving ------------------------------------------------------------------------------------

async function start(msg) {
  const v = msg.version;
  state = { slug: msg.slug, lang: msg.lang, version: v, team: msg.team, schema: null, items: {}, seq: 0, notice: null, created: Date.now() };
  busy = { done: 0, total: 1 };
  render();
  try {
    const manifest = await fetchJson(caseUrl(v, 'manifest.json'));
    state.schema = manifest.schema_version;
    teamJson = await fetchJson(caseUrl(v, 'team.json'));
  } catch (e) {
    busy = null; state = null; teamJson = null;
    return fail(e.status === 404 ? t('team.error.gone') : t('team.error.offline'));
  }
  await store.set('teamjson', teamJson);
  const items = [];
  const add = (file, code, label, group, extra = {}) => { const it = { file, code, label, kind: kindOf(file), group, v, status: 'pending', seen: group === 'kit', at: Date.now(), ...extra }; state.items[file] = it; items.push(it); };
  for (const k of teamJson.kit) add(k.file, '', k.title, 'kit');
  for (const s of teamJson.suspects) add(s.card, s.letter, s.name, 'suspects');
  const first = teamJson.envelopes.find((e) => e.number === 1) || teamJson.envelopes[0];
  if (first) for (const sec of first.sections) for (const it of sec.items) add(it.file, it.code, '', 'folder', { origin: `E${first.number}`, section: sec.title });
  await save();
  await downloadAll(items);
}

async function receive(msg, quiet = false) {
  if (!state) { await start(msg); }
  else if (state.slug !== msg.slug || state.lang !== msg.lang || state.team !== msg.team) {
    return askSwitch(msg);
  }
  if (!msg.items.length) return;
  const fresh = [];
  for (const [file, code] of msg.items) {
    if (state.items[file]) continue;
    const it = { file, code, label: '', kind: kindOf(file), group: 'folder', origin: 'delivery', v: msg.version, status: 'pending', seen: false, at: Date.now() };
    state.items[file] = it;
    (state.order = state.order || []).push(file);     // the order things arrived in
    fresh.push(it);
  }
  state.seq = Math.max(state.seq || 0, msg.seq);
  if (msg.version !== state.version) state.latest = msg.version;
  await save();
  if (fresh.length) {
    toast(plural('team.toast.received', fresh.length));
    await downloadAll(fresh);
  } else if (!quiet) toast(t('team.toast.nothing_new'));
}

function askSwitch(msg) {
  return new Promise((resolve) => {
    const close = (fn) => () => { modal.remove(); fn(); };
    const modal = h('div', { class: 'oc-modal' }, h('div', { class: 'oc-modal__box' },
      h('h2', {}, t('team.switch.title')),
      h('p', {}, t('team.switch.text', { current: state.team, other: msg.team })),
      h('div', { class: 'oc-row' },
        h('button', { class: 'oc-btn', type: 'button', onclick: close(async () => { await store.del('team'); state = null; await receive(msg); resolve(); }) }, t('team.switch.yes', { team: msg.team })),
        h('button', { class: 'oc-btn oc-btn--ghost', type: 'button', onclick: close(resolve) }, t('team.switch.no')))));
    document.body.append(modal);
  });
}

async function handleText(text) {
  const msg = decode(text);
  if (!msg) { toast(t('team.error.bad_link')); return false; }
  await receive(msg);
  return true;
}

function fail(text) {
  toast(text, 6000);
  render(text);
}

// --- The live room --------------------------------------------------------------------------------------------

function netReceive(msg, kind) {
  netQueue = netQueue.then(async () => {
    if (state && (state.team !== msg.team || state.slug !== msg.slug || state.lang !== msg.lang)) {
      // The director moved this phone to another team: its folder is replaced, with no question.
      await store.del('team'); await store.del('teamjson');
      state = null; teamJson = null;
      toast(t('room.join.other_team', { team: msg.team }), 6000);
    }
    await receive(msg, kind === 'sync');
    render();
  }).catch((e) => console.error(e));
  return netQueue;
}

async function joinRoom(pin, session = null) {
  pin = normalizePin(pin);
  if (!validPin(pin)) return toast(t('room.join.bad_pin'));
  await leaveRoom(false);
  const nameInput = document.getElementById('oc-room-name');
  const name = ((nameInput && nameInput.value) || (await store.get('devicename')) || '').trim().slice(0, 40);
  if (name) await store.set('devicename', name);
  room = new DeviceRoom({
    id: deviceId, name, pin, session,
    onStatus: () => render(),
    onMessage: (msg, kind) => netReceive(msg, kind),
    onSession: (sess) => { if (sess) store.set('session', sess); else store.del('session'); },
  });
  stopAwake = keepAwake();
  render();
  await room.start();
  render();
}

async function leaveRoom(forget = true) {
  if (room) { await room.stop(); room = null; }
  if (stopAwake) { stopAwake(); stopAwake = null; }
  if (forget) { await store.del('session'); render(); }
}

function roomStatusText() {
  if (!room) return '';
  if (room.status === 'approved') return room.connected ? t('room.join.approved') : t('room.join.director_away');
  return t(`room.join.${room.status}`);
}

function roomBox() {
  if (!room) {
    return h('form', { class: 'oc-field', id: 'oc-room-form', onsubmit: (e) => { e.preventDefault(); joinRoom(document.getElementById('oc-room-pin').value); } },
      h('h2', {}, t('room.join.title')), h('p', {}, t('room.join.text')),
      h('label', { class: 'oc-field' }, t('room.join.pin'), h('input', { class: 'oc-input', id: 'oc-room-pin', autocomplete: 'off', autocapitalize: 'characters', maxlength: '8', inputmode: 'text', style: 'letter-spacing:.2em;text-transform:uppercase' })),
      h('label', { class: 'oc-field' }, t('room.join.name'), h('input', { class: 'oc-input', id: 'oc-room-name', autocomplete: 'off', maxlength: '40' })),
      h('button', { class: 'oc-btn', type: 'submit', id: 'oc-room-enter' }, t('room.join.enter')));
  }
  return h('div', { class: `oc-notice${room.status === 'denied' || room.status === 'out' ? ' oc-notice--bad' : ''}`, id: 'oc-room-status', dataset: { status: room.status, connected: String(room.connected) } },
    roomStatusText(), ' ', h('button', { class: 'oc-btn oc-btn--small oc-btn--ghost', type: 'button', id: 'oc-room-leave', onclick: () => leaveRoom() }, t('room.join.leave')));
}

// --- Drawing --------------------------------------------------------------------------------------------------

function render(error) {
  clear(app);
  document.body.className = state ? `oc-team-${state.team}` : '';
  app.append(header());
  const main = h('main', { class: 'oc-wrap' });
  app.append(main);
  if (!store.store.persistent) main.append(h('div', { class: 'oc-notice' }, t('team.no_storage')));
  if (!('serviceWorker' in navigator) || !navigator.serviceWorker.controller) main.append(h('div', { class: 'oc-notice', id: 'oc-nosw' }, t('team.no_offline')));
  if (room) main.append(roomBox());
  if (!state) return main.append(joinScreen(error));
  if (state.notice === 'updated') main.append(h('div', { class: 'oc-notice' }, t('team.notice.updated')));
  if (state.notice === 'format') main.append(h('div', { class: 'oc-notice oc-notice--bad' }, t('team.notice.format')));
  if (busy) main.append(h('div', {}, h('p', {}, t('team.downloading')), h('div', { class: 'oc-progress' }, h('i', {}))));
  main.append(tabs());
  if (tab === 'folder') main.append(folderView());
  else if (tab === 'room') main.append(room ? h('p', { class: 'oc-muted' }, roomStatusText()) : roomBox());
  else if (tab === 'kit') main.append(listView(group('kit'), false));
  else main.append(listView(group('suspects'), false));
  updateProgress();
}

function header() {
  return h('header', { class: 'oc-top' }, h('div', { class: 'oc-top__in' },
    h('span', { class: 'oc-brand' }, 'Open Case'),
    state ? h('span', { class: 'oc-badge' }, t('team.badge', { team: state.team })) : null,
    state && teamJson ? h('span', { class: 'oc-case' }, teamJson.texts.title) : null,
    h('span', { class: 'oc-grow' }),
    online ? null : h('span', { class: 'oc-offline', id: 'oc-offline' }, t('team.offline')),
    h('button', { class: 'oc-btn oc-btn--small', type: 'button', id: 'oc-scan', onclick: openScanner }, t('team.scan'))));
}

function joinScreen(error) {
  return h('div', {},
    room ? null : roomBox(),
    h('h1', {}, t('team.join.title')),
    h('p', {}, t('team.join.text')),
    error ? h('div', { class: 'oc-notice oc-notice--bad' }, error) : null,
    h('div', { class: 'oc-row' }, h('button', { class: 'oc-btn', type: 'button', onclick: openScanner }, t('team.scan'))),
    h('label', { class: 'oc-field' }, t('team.join.paste'),
      h('textarea', { class: 'oc-input', id: 'oc-paste', rows: '3', placeholder: 'https://…/play/equipo/#oc1.…' })),
    h('button', { class: 'oc-btn oc-btn--ghost', type: 'button', onclick: () => handleText(document.getElementById('oc-paste').value) }, t('team.join.open')));
}

function tabs() {
  const mk = (id, text) => h('button', { class: 'oc-tab', role: 'tab', type: 'button', 'aria-selected': String(tab === id), onclick: () => { tab = id; render(); } }, text);
  return h('div', { class: 'oc-tabs', role: 'tablist' }, mk('folder', t('team.tab.folder')), mk('kit', t('team.tab.kit')), mk('suspects', t('team.tab.suspects')), mk('room', t('room.tab')));
}

const group = (g) => Object.values(state.items).filter((i) => i.group === g);

function labelOf(it) { return it.label || it.code || it.file; }

function folderView() {
  const all = group('folder').sort((a, b) => naturalCompare(a.code || a.file, b.code || b.file));
  const shown = all.filter((i) => filter === 'all' || (filter === 'card' ? i.kind === 'card' : i.kind !== 'card'));
  const chip = (id, text) => h('button', { class: 'oc-chip', type: 'button', 'aria-pressed': String(filter === id), onclick: () => { filter = id; render(); } }, text);
  return h('div', {},
    h('div', { class: 'oc-chips' }, chip('all', `${t('team.filter.all')} (${all.length})`), chip('sheet', t('team.filter.sheets')), chip('card', t('team.filter.cards'))),
    shown.length ? listView(shown, true) : h('p', { class: 'oc-muted' }, t('team.empty')));
}

function listView(items, showCode) {
  const ul = h('ul', { class: 'oc-list' });
  items.forEach((it, idx) => {
    const unseen = !it.seen;
    ul.append(h('li', { class: `oc-item${unseen ? ' oc-item--new' : ''}`, dataset: { file: it.file } },
      h('button', { class: 'oc-item__open', type: 'button', onclick: () => open(items, idx) },
        showCode && it.code ? h('span', { class: 'oc-item__code' }, it.code) : null,
        labelOf(it) === it.code ? null : labelOf(it),
        unseen ? h('span', { class: 'oc-new' }, t('team.new')) : null,
        it.status === 'pending' ? h('span', { class: 'oc-pending' }, t('team.pending')) : null,
        it.status === 'unavailable' ? h('span', { class: 'oc-pending' }, t('team.unavailable')) : null,
        it.section || it.origin === 'delivery' ? h('div', { class: 'oc-item__tag' }, it.origin === 'delivery' ? t('team.from_director') : it.section) : null)));
  });
  return ul;
}

async function open(items, idx) {
  const it = items[idx];
  if (it.status === 'pending') await fetchItem(it);
  if (it.status !== 'ok') { await save(); render(); return toast(it.status === 'unavailable' ? t('team.unavailable_toast') : t('team.error.offline')); }
  const list = items.filter((x) => x.status === 'ok');
  openViewer({
    items: list.map((x) => ({ url: caseUrl(x.v, x.file).href, title: [x.code, x.label].filter((s) => s && s !== x.code).join(' · ') || x.code || x.file })),
    index: list.indexOf(it),
    labels: { close: t('team.viewer.close'), prev: t('team.viewer.prev'), next: t('team.viewer.next'), zoomIn: t('team.viewer.zoom_in'), zoomOut: t('team.viewer.zoom_out'), fit: t('team.viewer.fit') },
    onShow: (_, i) => { const x = list[i]; if (!x.seen) { x.seen = true; save(); } },
  });
}

// --- Scanning -------------------------------------------------------------------------------------------------

function openScanner() {
  const video = h('video', { muted: true, playsinline: true });
  const msg = h('p', { class: 'oc-muted', id: 'oc-scan-msg' }, t('team.scanner.hint'));
  let stop = null;
  const close = () => { if (stop) stop(); modal.remove(); };
  const file = h('input', { type: 'file', accept: 'image/*', id: 'oc-qr-file', class: 'oc-hidden', onchange: async (e) => {
    const f = e.target.files[0];
    if (!f) return;
    try {
      const text = await decodeFile(f);
      if (text && await handleText(text)) return close();
      msg.textContent = t('team.scanner.none');
    } catch (err) { msg.textContent = t('team.scanner.none'); }
  } });
  const modal = h('div', { class: 'oc-modal' }, h('div', { class: 'oc-modal__box' },
    h('h2', {}, t('team.scanner.title')), video, msg,
    h('div', { class: 'oc-row' },
      h('button', { class: 'oc-btn oc-btn--ghost', type: 'button', onclick: () => file.click() }, t('team.scanner.from_image')),
      h('button', { class: 'oc-btn oc-btn--ghost', type: 'button', onclick: close }, t('team.viewer.close'))),
    file,
    h('label', { class: 'oc-field' }, t('team.join.paste'), h('textarea', { class: 'oc-input', id: 'oc-scan-paste', rows: '2' })),
    h('button', { class: 'oc-btn', type: 'button', onclick: async () => { if (await handleText(document.getElementById('oc-scan-paste').value)) close(); } }, t('team.join.open'))));
  document.body.append(modal);
  if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
    scanCamera(video, async (text) => { if (decode(text)) { if (stop) stop(); await handleText(text); modal.remove(); } })
      .then((s) => { stop = s; })
      .catch(() => { video.remove(); msg.textContent = t('team.scanner.no_camera'); });
  } else { video.remove(); msg.textContent = t('team.scanner.no_camera'); }
}

// --- Start ----------------------------------------------------------------------------------------------------

async function main() {
  const fragment = decode(location.hash);
  const hashPin = pinFromHash(location.hash);
  deviceId = await store.get('device');
  if (!deviceId) { deviceId = newId(); await store.set('device', deviceId); }
  const session = (await store.get('session')) || null;
  state = (await store.get('team')) || null;
  teamJson = state ? (await store.get('teamjson')) || null : null;
  const lang = (fragment && fragment.lang) || (state && state.lang) || navigator.language.slice(0, 2);
  await loadStrings(lang);
  document.title = t('team.page_title');
  window.addEventListener('online', () => { online = true; retryPending(); });
  window.addEventListener('offline', () => { online = false; render(); });
  window.addEventListener('hashchange', async () => {   // a link opened while the app is already open
    const pin = pinFromHash(location.hash);
    if (pin) { history.replaceState(null, '', location.pathname + location.search); await joinRoom(pin); return; }
    const msg = decode(location.hash);
    if (location.hash.startsWith('#oc')) history.replaceState(null, '', location.pathname + location.search);
    if (msg) { await receive(msg); render(); } else if (location.hash.startsWith('#oc')) toast(t('team.error.bad_link'));
  });
  await registerWorker();
  render();
  if (fragment) {
    history.replaceState(null, '', location.pathname + location.search);   // the link's data is not kept in the address bar
    await receive(fragment);
  } else if (location.hash.startsWith('#sala') && !hashPin) {
    history.replaceState(null, '', location.pathname + location.search);
    toast(t('team.error.bad_link'));
  } else if (location.hash.startsWith('#oc')) {
    history.replaceState(null, '', location.pathname + location.search);
    toast(t('team.error.bad_link'));
  }
  if (hashPin) {
    history.replaceState(null, '', location.pathname + location.search);
    if (!session || session.pin !== hashPin) { await store.del('session'); await joinRoom(hashPin); }
  }
  if (!room && session) await joinRoom(session.pin, session);
  if (state) retryPending();
  render();
}

async function retryPending() {
  if (!state || busy) return;
  const pending = Object.values(state.items).filter((i) => i.status === 'pending');
  if (pending.length) await downloadAll(pending);
  else render();
}

main();
