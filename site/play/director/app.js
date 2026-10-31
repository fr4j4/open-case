// The director's panel (minimal, F2): choose the case and the number of teams, hand out evidence and cards by
// showing a QR or copying a link, and read the kit. The game is kept in IndexedDB; nothing goes through a server.
import { h, clear, toast } from '../js/dom.js';
import { loadStrings, t, plural, registerWorker, PLAY_ROOT, language } from '../js/i18n.js';
import * as store from '../js/store.js';
import { encode, naturalCompare } from '../js/delivery.js';
import { drawQr } from '../js/qr.js';
import { openViewer } from '../js/viewer.js';
import { DirectorRoom, roomLink, keepAwake } from '../js/room.js';
import { createGame, newBook, receive as receiveRequest, answer as answerOne, balanceFor, holdItems } from '../js/requests.js';
import { queueView, registerView, pendingList } from './panel.js';

const app = document.getElementById('app');
let game = null;         // {slug, lang, version, teams: ['A','B'], seq, log: [{seq, team, items, at}]}
let teamJson = null;
let directorJson = null;
let tab = 'give';
let target = [];         // teams the next delivery goes to
let picked = new Map();  // file -> code
let search = '';
let outdated = null;     // {version, same_format}
let room = null;         // the live room (js/room.js), once the director creates it
let stopAwake = null;
let dgame = null;        // the rules (js/rules.js) over team.json and director.json
const choices = new Map();   // request id -> what the director has chosen in its card (kept when the panel is drawn again)

const caseUrl = (file = '') => new URL(`cases/${game.slug}/${game.lang}/${game.version}/${file}`, PLAY_ROOT);
const save = () => store.set('game', game);
const teamLink = (team, items) => new URL('../equipo/', location.href).href + '#' + encode({ slug: game.slug, lang: game.lang, version: game.version, team, seq: game.seq, items });

async function json(url) {
  const r = await fetch(url, { cache: 'no-cache' });
  if (!r.ok) throw new Error(String(r.status));
  return r.json();
}

// --- Setup ----------------------------------------------------------------------------------------------------

async function setupScreen() {
  clear(app);
  app.append(topBar());
  const main = h('main', { class: 'oc-wrap' }, h('h1', {}, t('director.setup.title')), h('p', {}, t('director.setup.text')));
  app.append(main);
  let index;
  try { index = await json(new URL('cases/index.json', PLAY_ROOT)); }
  catch (e) { main.append(h('div', { class: 'oc-notice oc-notice--bad' }, t('director.setup.no_cases'))); return; }
  const cases = await Promise.all(index.cases.map(async (c) => {
    let title = c.slug;
    try { title = (await json(new URL(`${c.path}team.json`, PLAY_ROOT))).texts.title; } catch (e) { /* the slug will do */ }
    return { ...c, title };
  }));
  if (!cases.length) { main.append(h('div', { class: 'oc-notice oc-notice--bad' }, t('director.setup.no_cases'))); return; }
  const caseSel = h('select', { class: 'oc-input', id: 'oc-case' }, cases.map((c, i) => h('option', { value: String(i) }, `${c.title} (${c.language})`)));
  const teamSel = h('select', { class: 'oc-input', id: 'oc-teams' }, [2, 3, 4].map((n) => h('option', { value: String(n), selected: n === 2 }, plural('director.setup.teams_count', n))));
  main.append(
    h('label', { class: 'oc-field' }, t('director.setup.case'), caseSel),
    h('label', { class: 'oc-field' }, t('director.setup.teams'), teamSel),
    h('button', { class: 'oc-btn', type: 'button', id: 'oc-start', onclick: async () => {
      const c = cases[+caseSel.value];
      game = { slug: c.slug, lang: c.language, version: c.version, teams: 'ABCD'.slice(0, +teamSel.value).split(''), seq: 0, log: [], created: Date.now() };
      await loadCase();
      await save();
      target = [game.teams[0]];
      render();
    } }, t('director.setup.start')));
}

async function loadCase() {
  [teamJson, directorJson] = await Promise.all([json(caseUrl('team.json')), json(caseUrl('director.json'))]);
  await loadStrings(game.lang);
  document.title = t('director.page_title');
  dgame = createGame(teamJson, directorJson);
  if (!game.play) game.play = newBook();
  checkVersion();
  if (game.room && !room) startRoom();     // a reload: the room opens again with the same PIN and the same devices
}

// --- The live room --------------------------------------------------------------------------------------------

async function startRoom() {
  let known = new Set(game.room ? game.room.devices ? Object.keys(game.room.devices).filter((id) => game.room.devices[id].status === 'pending') : [] : []);
  room = new DirectorRoom({ game, save, onChange: () => {
    const fresh = room.pending().filter((d) => !known.has(d.id));
    for (const d of fresh) { known.add(d.id); if (tab !== 'room') toast(t('room.tab_pending', { n: room.pending().length })); }
    if (tab === 'room') render(); else refreshRoomTab();
  } });
  room.onMessage = (team, from, m) => onTeamMessage(team, from, m);
  room.onOnline = (team, id) => sendBalance(team, id);
  stopAwake = keepAwake();
  await room.start();
  await save();
  if (tab === 'room') render();
}

// --- Requests (F4b) -------------------------------------------------------------------------------------------

// The balance and the answered requests of a team, to one of its phones or to all that are connected.
async function sendBalance(team, to = null) {
  if (!room || !game.play) return;
  await room.sendTeam(team, { k: 'bal', ...balanceFor(dgame, game.play, team, game.log) }, to);
  await save();
}

// A phone of a team asks for something: it goes in the register once (it is sent again until answered) and the team is told
// the balance, so the phone that sent it sees that it arrived.
async function onTeamMessage(team, from, m) {
  if (!m || m.k !== 'req' || !game.play) return;
  const device = room.r.devices[from];
  const got = receiveRequest(dgame, game.play, team, device, m.r);
  if (!got) return;
  if (got.fresh) {
    room.log.append('request', { device: from, team, id: got.record.id, kind: got.record.req.kind });
    await save();
    if (tab !== 'requests') toast(t('requests.panel.new', { team, n: pendingList(game.play).length }));
    render();
  } else if (got.record.status === 'done') sendBalance(team, from);
}

async function answerRequest(rec, button, options) {
  const res = answerOne(dgame, game.play, rec, button, options, game.log);
  if (!res.ok) { toast(t(`requests.panel.error.${res.error}`)); return; }
  choices.delete(rec.id);
  room?.log.append('answer', { team: rec.team, id: rec.id, answer: button, charged: res.charged });
  await save();
  if (res.items.length) await handOut(rec.team, res.items);
  await sendBalance(rec.team);
  render();
}

function refreshRoomTab() {
  const b = document.getElementById('oc-tab-room');
  if (b && room) b.textContent = room.pending().length ? t('room.tab_pending', { n: room.pending().length }) : t('room.tab');
}

const roomUrl = () => roomLink(new URL('../equipo/', location.href).href, room.pin);
const time = (ms) => new Date(ms).toLocaleTimeString(language(), { hour: '2-digit', minute: '2-digit' });
const deviceName = (d) => d.name || t('room.unnamed', { id: d.id.slice(0, 4) });

function roomView() {
  if (!room) {
    return h('div', { class: 'oc-card' }, h('h3', {}, t('room.create_title')), h('p', {}, t('room.create_text')),
      h('button', { class: 'oc-btn', type: 'button', id: 'oc-room-create', onclick: async () => { await startRoom(); render(); } }, t('room.create')));
  }
  const link = roomUrl();
  const qr = drawQr(link);
  const kinds = room.vestibule ? room.vestibule.kinds.join(' + ') : '';
  const pending = room.pending();
  return h('div', {},
    h('section', { class: 'oc-card' },
      h('p', { class: 'oc-muted' }, t('room.share_help')),
      h('p', {}, t('room.pin'), ': ', h('strong', { id: 'oc-room-pin', style: 'font-size:2rem;letter-spacing:.18em;font-family:var(--mono,monospace)' }, room.pin)),
      qr ? h('div', { class: 'oc-qr' }, qr) : null,
      h('code', { class: 'oc-link', id: 'oc-room-link' }, link),
      h('div', { class: 'oc-row' }, h('button', { class: 'oc-btn oc-btn--small', type: 'button', onclick: () => copy(link) }, t('room.copy'))),
      kinds ? h('p', { class: 'oc-muted' }, t('room.transport', { kinds })) : null),
    h('h3', {}, t('room.pending_title')),
    pending.length ? pending.map((d) => h('section', { class: 'oc-card', dataset: { device: d.id } },
      h('p', {}, h('strong', {}, deviceName(d)), ' ', h('small', { class: 'oc-muted' }, room.seenInVestibule(d.id) ? t('room.online', { time: time(d.joined) }) : t('room.offline'))),
      h('div', { class: 'oc-chips' },
        game.teams.map((tm) => h('button', { class: `oc-chip oc-team-${tm}`, type: 'button', dataset: { approve: tm }, onclick: () => room.approve(d.id, tm) }, t('room.approve_to', { team: tm }))),
        h('button', { class: 'oc-chip', type: 'button', dataset: { deny: '1' }, onclick: () => room.deny(d.id) }, t('room.deny'))))) : h('p', { class: 'oc-muted', id: 'oc-room-none' }, t('room.pending_none')),
    game.teams.map((tm) => {
      const members = room.members(tm);
      return h('section', { class: `oc-card oc-team-${tm}`, dataset: { team: tm } },
        h('h3', {}, teamBadge(tm), ' ', t('room.team_title', { team: tm })),
        members.length ? members.map((d) => h('div', { class: 'oc-row', dataset: { device: d.id, online: String(room.isOnline(d.id)) } },
          h('span', {}, h('strong', {}, deviceName(d)), ' · ', room.isOnline(d.id) ? t('room.online', { time: time(room.online.get(d.id)) }) : t('room.offline')),
          h('span', { class: 'oc-grow' }),
          game.teams.filter((x) => x !== tm).map((x) => h('button', { class: 'oc-btn oc-btn--small oc-btn--ghost', type: 'button', onclick: () => room.approve(d.id, x) }, t('room.move_to', { team: x }))),
          h('button', { class: 'oc-btn oc-btn--small oc-btn--ghost', type: 'button', onclick: () => room.deny(d.id) }, t('room.remove')))) : h('p', { class: 'oc-muted' }, t('room.nobody')));
    }),
    h('p', { class: 'oc-muted' }, t('room.qr_help')));
}

// Is the case on the site newer than the one this game started with? (Pages replaces the whole site on every deployment.)
async function checkVersion() {
  try {
    const index = await json(new URL('cases/index.json', PLAY_ROOT));
    const entry = index.cases.find((c) => c.slug === game.slug && c.language === game.lang);
    if (!entry || entry.version === game.version) { outdated = null; return; }
    const manifest = await json(new URL(`${entry.path}manifest.json`, PLAY_ROOT));
    outdated = { version: entry.version, sameFormat: manifest.schema_version === teamJson.schema_version };
    render();
  } catch (e) { /* offline: nothing to check */ }
}

// --- Main screen ----------------------------------------------------------------------------------------------

function topBar() {
  return h('header', { class: 'oc-top' }, h('div', { class: 'oc-top__in' },
    h('span', { class: 'oc-brand' }, 'Open Case'),
    h('span', { class: 'oc-badge' }, t('director.badge')),
    teamJson ? h('span', { class: 'oc-case' }, teamJson.texts.title) : null,
    h('span', { class: 'oc-grow' }),
    game ? h('button', { class: 'oc-btn oc-btn--small oc-btn--ghost', type: 'button', onclick: endGame }, t('director.end')) : null));
}

async function endGame() {
  if (!confirm(t('director.end_confirm'))) return;
  await store.del('game');
  if (room) { await room.stop(); room = null; }
  if (stopAwake) { stopAwake(); stopAwake = null; }
  game = teamJson = directorJson = dgame = null; picked.clear(); choices.clear();
  setupScreen();
}

function render() {
  if (!game) return setupScreen();
  // a field being typed in keeps the cursor when the panel is drawn again (a request arrives, a phone connects…)
  const active = document.activeElement && document.activeElement.dataset && document.activeElement.dataset.focus;
  const caret = active ? document.activeElement.selectionStart : null;
  draw();
  if (active) {
    const el = document.querySelector(`[data-focus="${active}"]`);
    if (el) { el.focus(); try { el.setSelectionRange(caret, caret); } catch (e) { /* not a text field */ } }
  }
}

function draw() {
  clear(app);
  app.append(topBar());
  const main = h('main', { class: 'oc-wrap' });
  app.append(main);
  if (!store.store.persistent) main.append(h('div', { class: 'oc-notice' }, t('director.no_storage')));
  if (outdated) main.append(h('div', { class: `oc-notice${outdated.sameFormat ? '' : ' oc-notice--bad'}` }, outdated.sameFormat ? t('director.outdated.same') : t('director.outdated.format')));
  const mk = (id, text) => h('button', { class: 'oc-tab', id: `oc-tab-${id}`, role: 'tab', type: 'button', 'aria-selected': String(tab === id), onclick: () => { tab = id; render(); } }, text);
  main.append(h('div', { class: 'oc-tabs', role: 'tablist' }, mk('requests', game.play && pendingList(game.play).length ? t('requests.panel.tab_pending', { n: pendingList(game.play).length }) : t('requests.panel.tab')), mk('give', t('director.tab.give')), mk('teams', t('director.tab.teams')), mk('room', room && room.pending().length ? t('room.tab_pending', { n: room.pending().length }) : t('room.tab')), mk('kit', t('director.tab.kit')), mk('register', t('requests.panel.register')), mk('log', t('director.tab.log'))));
  main.append(tab === 'requests' ? queueView(panelUi()) : tab === 'register' ? registerView(panelUi()) : tab === 'give' ? giveView() : tab === 'room' ? roomView() : tab === 'teams' ? teamsView() : tab === 'kit' ? kitView() : logView());
}

const panelUi = () => ({ dgame, book: game.play, teamJson, log: game.log, choices, answer: answerRequest, redraw: () => render() });

const teamBadge = (letter) => h('span', { class: `oc-badge oc-team-${letter}` }, letter);

function teamPicker() {
  return h('div', { class: 'oc-chips', role: 'group', 'aria-label': t('director.give.to') },
    game.teams.map((tm) => h('button', { class: `oc-chip oc-team-${tm}`, type: 'button', dataset: { team: tm }, 'aria-pressed': String(target.includes(tm)), onclick: () => {
      target = target.includes(tm) ? target.filter((x) => x !== tm) : [...target, tm];
      render();
    } }, t('director.give.team', { team: tm }))),
    h('button', { class: 'oc-chip', type: 'button', onclick: () => { target = target.length === game.teams.length ? [] : [...game.teams]; render(); } }, t('director.give.all')));
}

// Everything that can be handed out: the sheets and the cards of the case, with the envelope they belong to.
function candidates() {
  const sheets = directorJson.sheets.map((s) => ({ file: s.file, code: s.code, label: s.title, kind: 'sheet', note: s.envelope ? t('director.give.in_envelope', { n: s.envelope }) : '' }));
  const cards = directorJson.cards.filter((c) => c.file).map((c) => ({ file: c.file, code: c.code, label: c.who || c.headline || c.question || '', kind: 'card', note: c.type, attach: c.attach || [] }));
  return [...sheets, ...cards];
}

function giveView() {
  const all = candidates();
  const q = search.trim().toLowerCase();
  const list = all.filter((c) => !q || `${c.code} ${c.label} ${c.note}`.toLowerCase().includes(q))
    .sort((a, b) => (a.kind === b.kind ? naturalCompare(a.code, b.code) : a.kind === 'sheet' ? -1 : 1));
  const envelopes = teamJson.envelopes.filter((e) => e.number > 1);
  const box = h('div', {},
    h('p', { class: 'oc-muted' }, t('director.give.help')),
    teamPicker(),
    envelopes.length ? h('div', { class: 'oc-row' }, envelopes.map((e) => h('button', { class: 'oc-btn oc-btn--ghost oc-btn--small', type: 'button', dataset: { envelope: String(e.number) }, onclick: () => {
      for (const s of e.sections) for (const it of s.items) picked.set(it.file, it.code);
      render();
    } }, t('director.give.envelope', { n: e.number })))) : null,
    h('label', { class: 'oc-field' }, t('director.give.search'), h('input', { class: 'oc-input', type: 'search', id: 'oc-search', value: search, oninput: (e) => { search = e.target.value; const pos = e.target.selectionStart; render(); const el = document.getElementById('oc-search'); el.focus(); el.setSelectionRange(pos, pos); } })));
  const ul = h('div', { class: 'oc-selectlist' });
  for (const c of list) {
    ul.append(h('label', { class: 'oc-sel', dataset: { file: c.file } },
      h('input', { type: 'checkbox', checked: picked.has(c.file), onchange: (e) => { e.target.checked ? picked.set(c.file, c.code) : picked.delete(c.file); updateGiveButton(); } }),
      h('span', {}, h('strong', {}, c.code), ' ', c.kind === 'card' ? `· ${t('director.give.card')} ` : '', c.label, c.note ? h('small', {}, ` · ${c.note}`) : null)));
  }
  box.append(ul, h('div', { class: 'oc-row', style: 'position:sticky;bottom:0;padding:10px 0;background:var(--mesa)' },
    h('button', { class: 'oc-btn', type: 'button', id: 'oc-give', onclick: give }, ''),
    h('button', { class: 'oc-btn oc-btn--ghost', type: 'button', onclick: () => { picked.clear(); render(); } }, t('director.give.clear'))));
  queueMicrotask(updateGiveButton);
  return box;
}

function updateGiveButton() {
  const b = document.getElementById('oc-give');
  if (!b) return;
  b.textContent = t('director.give.button', { n: picked.size });
  b.disabled = !picked.size || !target.length;
}

// Puts items in a team's folder: in the game's log, in what the team holds (for the rules) and on its phones if any is connected.
// Returns the delivery when the team has no phone connected (the director shows its QR).
async function handOut(team, items, quiet = false) {
  game.seq += 1;
  game.log.push({ seq: game.seq, team, items, at: Date.now() });
  if (game.play && game.play.states[team]) game.play.states[team] = holdItems(game.play.states[team], items);
  await save();
  const n = room ? room.reach(team) : 0;
  if (n) {
    room.deliver(team, items, game.seq);
    if (!quiet) toast(plural('room.sent', n, { team }));
    return null;
  }
  const d = { team, items, seq: game.seq };
  if (!quiet) showDeliveries([d]);
  return d;
}

async function give() {
  const items = [...picked].map(([file, code]) => [file, code]);
  if (!items.length || !target.length) return;
  picked.clear();
  // Teams with a phone connected get it over the network; the QR is for the others (and is always in Teams).
  const byQr = [];
  for (const team of [...target].sort()) {
    const d = await handOut(team, items, true);
    if (d) byQr.push(d); else toast(plural('room.sent', room.reach(team), { team }));
  }
  if (byQr.length) showDeliveries(byQr);
  render();
}

// One QR (and its link) per team that gets the delivery.
function showDeliveries(deliveries) {
  const close = () => modal.remove();
  const cards = deliveries.map((d) => deliveryCard(d));
  const modal = h('div', { class: 'oc-modal', id: 'oc-delivery' }, h('div', { class: 'oc-modal__box' },
    h('h2', {}, t('director.delivery.title')), ...cards,
    h('button', { class: 'oc-btn', type: 'button', id: 'oc-delivery-close', onclick: close }, t('director.delivery.done'))));
  document.body.append(modal);
}

function deliveryCard(d) {
  const link = teamLink(d.team, d.items);
  const qr = drawQr(link);
  return h('section', { class: `oc-card oc-team-${d.team}`, dataset: { team: d.team } },
    h('h3', {}, teamBadge(d.team), ' ', plural('director.delivery.count', d.items.length), ' ', h('small', { class: 'oc-muted' }, d.items.map((i) => i[1]).join(', '))),
    qr ? h('div', { class: 'oc-qr' }, qr) : h('div', { class: 'oc-notice' }, t('director.delivery.too_big')),
    h('code', { class: 'oc-link' }, link),
    h('div', { class: 'oc-row' },
      h('button', { class: 'oc-btn oc-btn--small', type: 'button', onclick: () => copy(link) }, t('director.delivery.copy')),
      h('a', { class: 'oc-btn oc-btn--small oc-btn--ghost', href: link, target: '_blank', rel: 'noopener', dataset: { open: d.team } }, t('director.delivery.open'))));
}

async function copy(text) {
  try { await navigator.clipboard.writeText(text); toast(t('director.delivery.copied')); }
  catch (e) { toast(t('director.delivery.copy_failed')); }
}

function teamsView() {
  return h('div', {}, game.teams.map((tm) => {
    const got = new Map();
    for (const e of game.log) if (e.team === tm) for (const [f, c] of e.items) got.set(f, c);
    const join = teamLink(tm, []);
    const qr = drawQr(join);
    return h('section', { class: `oc-card oc-team-${tm}`, dataset: { team: tm } },
      h('h3', {}, teamBadge(tm), ' ', t('director.teams.title', { team: tm })),
      h('p', { class: 'oc-muted' }, t('director.teams.join_help')),
      qr ? h('div', { class: 'oc-qr' }, qr) : null,
      h('code', { class: 'oc-link' }, join),
      h('div', { class: 'oc-row' },
        h('button', { class: 'oc-btn oc-btn--small', type: 'button', onclick: () => copy(join) }, t('director.delivery.copy')),
        h('a', { class: 'oc-btn oc-btn--small oc-btn--ghost', href: join, target: '_blank', rel: 'noopener', dataset: { join: tm } }, t('director.delivery.open')),
        got.size ? h('button', { class: 'oc-btn oc-btn--small oc-btn--ghost', type: 'button', onclick: () => showDeliveries([{ team: tm, items: [...got], seq: game.seq }]) }, t('director.teams.resend')) : null),
      h('p', { class: 'oc-muted' }, got.size ? t('director.teams.has', { codes: [...got.values()].sort(naturalCompare).join(', ') }) : t('director.teams.nothing')));
  }));
}

function kitView() {
  const ul = h('ul', { class: 'oc-list' });
  const items = teamJson.kit.map((k) => ({ url: caseUrl(k.file).href, title: k.title }));
  items.forEach((it, i) => ul.append(h('li', { class: 'oc-item' }, h('button', { class: 'oc-item__open', type: 'button', onclick: () => openViewer({
    items, index: i,
    labels: { close: t('team.viewer.close'), prev: t('team.viewer.prev'), next: t('team.viewer.next'), zoomIn: t('team.viewer.zoom_in'), zoomOut: t('team.viewer.zoom_out'), fit: t('team.viewer.fit') },
  }) }, it.title))));
  const guide = h('div', { class: 'oc-card' }, h('h3', {}, t('director.kit.guide_title')), h('p', {}, t('director.kit.guide_text')), h('span', { id: 'oc-guide-link' }));
  findGuideZip().then((href) => { if (href) document.getElementById('oc-guide-link')?.replaceWith(h('a', { class: 'oc-btn oc-btn--small', href }, t('director.kit.guide_download'))); });
  return h('div', {}, h('p', { class: 'oc-muted' }, t('director.kit.help')), ul, guide);
}

// The guide is a PDF in the site's downloads (cases.json); the site root is the parent of play/.
async function findGuideZip() {
  try {
    const data = await json(new URL('../cases.json', PLAY_ROOT));
    const c = data.cases.find((x) => x.slug === game.slug);
    const z = c && c.languages[game.lang] && c.languages[game.lang].director_zip;
    return z ? new URL(`../${z.file}`, PLAY_ROOT).href : null;
  } catch (e) { return null; }
}

function logView() {
  if (!game.log.length) return h('p', { class: 'oc-muted' }, t('director.log.empty'));
  return h('ul', { class: 'oc-list' }, [...game.log].reverse().map((e) => h('li', { class: `oc-item oc-team-${e.team}`, style: 'border-left-color:var(--team);padding:10px 12px' },
    h('span', {}, `#${e.seq} · `, teamBadge(e.team), ` ${new Date(e.at).toLocaleTimeString(language())} · `, e.items.map((i) => i[1]).join(', ')))));
}

// --- Start ----------------------------------------------------------------------------------------------------

async function main() {
  await loadStrings(navigator.language.slice(0, 2));
  document.title = t('director.page_title');
  await registerWorker();
  game = (await store.get('game')) || null;
  if (game) {
    try { await loadCase(); target = [game.teams[0]]; }
    catch (e) { toast(t('director.error.load'), 6000); game = null; }
  }
  render();
}

main();
