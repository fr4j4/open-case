// The director's panel (minimal, F2): choose the case and the number of teams, hand out evidence and cards by
// showing a QR or copying a link, and read the kit. The game is kept in IndexedDB; nothing goes through a server.
import { h, clear, toast } from '../js/dom.js';
import { loadStrings, t, plural, registerWorker, PLAY_ROOT, language } from '../js/i18n.js';
import * as store from '../js/store.js';
import { encode, naturalCompare } from '../js/delivery.js';
import { drawQr } from '../js/qr.js';
import { openViewer } from '../js/viewer.js';
import { DirectorRoom, roomLink, keepAwake, newId } from '../js/room.js';
import { createGame, newBook, receive as receiveRequest, answer as answerOne, balanceFor, holdItems } from '../js/requests.js';
import { queueView, registerView, pendingList } from './panel.js';
import { gameView, scoreView, tickClock, reportText } from './partida.js';
import * as clock from '../js/clock.js';
import { cleanMarks } from '../js/score.js';
import { norm } from '../js/rules.js';
import { makeBackup, readBackup, backupName, cleanPlay, parseCodes, gameFromCodes } from '../js/recover.js';
import { backupCard, recoverBox, Recovery } from './recuperar.js';

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
let recovery = null;     // F6a: the collection of the teams' registros while a lost game is being recovered
let lastBackup = null;   // when the backup file was last downloaded (ms)
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
    } }, t('director.setup.start')),
    recoverBox({ initial: pendingCodes, start: startRecovery, load: loadBackup }));
  pendingCodes = '';
}

// --- Recovering a lost game (F6a) ----------------------------------------------------------------------------------

let pendingCodes = '';     // codes that came in the link of the page (#recuperar.…), shown in the form

// From the codes the teams' phones show: the game is made again with the same PIN and the same team rooms, and the phones are
// asked what they know. Nothing is sent to them until the director has chosen (recuperar.js).
async function startRecovery(text) {
  const { codes, bad } = parseCodes(text);
  const g = gameFromCodes(codes);
  if (g.error) return toast(t(`recover.start.error.${g.error}`), 6000);
  if (bad) toast(t('recover.start.bad_codes', { n: bad }), 5000);
  game = { slug: g.slug, lang: g.lang, version: g.version, teams: g.teams, seq: 0, log: [], created: Date.now(),
    room: { pin: g.pin, id: newId(), teamRooms: {}, devices: {}, adopt: [] }, recovery: { teams: Object.keys(g.rooms), rooms: g.rooms } };
  try { await loadCase(); } catch (e) { game = null; return toast(t('director.error.load'), 6000); }
  await save();
  target = [game.teams[0]];
  render();
}

function makeRecovery() {
  return new Recovery({ room: () => room, rg: () => dgame, game: () => game, now: () => Date.now(), redraw: () => render(), cancel: endGame,
    done: async (result, teams, held) => {
      game.log = result.log; game.seq = result.seq; game.play = result.play;
      delete game.recovery;
      recovery = null;
      await save();
      room.endRecovery(teams);                       // now the phones get their folder, balance and clock
      for (const [team, from, m] of held) await onTeamMessage(team, from, m);
      toast(t('recover.panel.done'), 6000);
      render();
    } });
}

// --- The backup file ---------------------------------------------------------------------------------------------------

async function downloadBackup() {
  if (!game) return;
  const now = Date.now();
  const { recovery: _r, ...saved } = game;
  const blob = new Blob([makeBackup(saved, now)], { type: 'application/json' });
  const a = h('a', { href: URL.createObjectURL(blob), download: backupName(game.slug, now) });
  document.body.append(a); a.click(); a.remove();
  lastBackup = now;
  await store.set('backupAt', now);
  toast(t('recover.backup.saved'));
  render();
}

// The game of a backup file replaces the one of this device (the room opens again with the same PIN and the same phones).
async function loadBackup(text) {
  const r = readBackup(text);
  if (!r.ok) return toast(t(`recover.backup.error.${r.error}`), 6000);
  if (game && !confirm(t('recover.backup.confirm'))) return;
  if (room) { await room.stop(); room = null; }
  if (stopAwake) { stopAwake(); stopAwake = null; }
  game = r.game; recovery = null;
  try { await loadCase(true); } catch (e) { game = null; await store.del('game'); toast(t('director.error.load'), 6000); return render(); }
  lastBackup = r.at || null;
  await store.set('backupAt', lastBackup);
  await save();
  target = [game.teams[0]];
  toast(t('recover.backup.loaded'), 5000);
  render();
}

async function loadCase(clean = false) {
  [teamJson, directorJson] = await Promise.all([json(caseUrl('team.json')), json(caseUrl('director.json'))]);
  await loadStrings(game.lang);
  document.title = t('director.page_title');
  dgame = createGame(teamJson, directorJson);
  if (clean) game.play = cleanPlay(game.play, dgame, game.teams);      // a backup file is checked against the rules of the case
  if (!game.play) game.play = newBook();
  // F5: the clock of the phases (it starts in the first one, stopped), what was read, the hints given, the sheets handed in and the marks
  const p = game.play;
  if (!p.clock) p.clock = clock.newClock(teamJson.figures);
  p.notices = p.notices || {}; p.hints = p.hints || {}; p.forms = p.forms || {}; p.marks = p.marks || {};
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
  room.onOnline = (team, id) => { sendBalance(team, id); sendClock(team, id); };
  stopAwake = keepAwake();
  if (game.recovery) {            // F6a: the phones' rooms are opened quietly; their registros are asked for one by one
    recovery = makeRecovery();
    room.onRecoverPeer = (team, id) => recovery.ask(team, id);
    for (const [tm, name] of Object.entries(game.recovery.rooms)) { room.r.teamRooms[tm] = name; room.quiet.add(tm); if (!room.r.adopt.includes(tm)) room.r.adopt.push(tm); }
  }
  await room.start();
  if (game.recovery) await room.recover(game.recovery.rooms);
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
  if (recovery && room.quiet.has(team)) return recovery.onMessage(team, from, m);     // the game is not back yet: first the registros
  if (m && m.k === 'form') return onForm(team, from, m);
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

// --- Phases, notices, hints and score (F5) ---------------------------------------------------------------------------

const MAX_FORM_TEXT = 2000;

// The clock goes to the phones as the phase, whether it runs and how much has gone by: each phone counts from there.
async function sendClock(team = null, to = null) {
  if (!room || !game.play) return;
  const w = { k: 'clock', ...clock.wire(game.play.clock, Date.now()) };
  for (const tm of team ? [team] : game.teams) await room.sendTeam(tm, w, team ? to : null);
}

async function clockDo(action, arg) {
  const p = game.play;
  const now = Date.now();
  const before = p.clock.phase;
  if (action === 'start') p.clock = clock.start(p.clock, now);
  else if (action === 'pause') p.clock = clock.pause(p.clock, now);
  else if (action === 'phase') p.clock = clock.toPhase(teamJson.figures, p.clock, arg, now);
  else if (action === 'next') p.clock = clock.next(teamJson.figures, p.clock, now);
  else if (action === 'shift') p.clock = clock.shift(p.clock, arg, now);
  room?.log.append('clock', { action, phase: p.clock.phase, from: before });
  await save();
  await sendClock();
  render();
}

// A sheet a team handed in (the accusation, the discard sheet): checked against the sheets of team.json and kept once per team and
// sheet (the last version wins). The phone is told it arrived.
async function onForm(team, from, m) {
  const form = (teamJson.forms || []).find((f) => f.id === m.id);
  if (!form || !game.play || !m.values || typeof m.values !== 'object') return;
  const values = {};
  for (const [k, v] of Object.entries(m.values).slice(0, 300)) if (/^[ft]\d+\.\d+(\.\d+)?$/.test(k) && typeof v === 'string') values[k] = v.slice(0, MAX_FORM_TEXT);
  (game.play.forms[team] = game.play.forms[team] || {})[form.id] = { values, at: Date.now(), device: from };
  room.log.append('form', { team, id: form.id, device: from });
  await save();
  await room.sendTeam(team, { k: 'formok', id: form.id }, from);
  if (tab !== 'score') toast(t('game.score.new_form', { team, title: form.title }));
  render();
}

function fileOfCode(code) {
  const c = dgame.cards.get(norm(code));
  if (c && c.file) return [c.file, c.code];
  const s = directorJson.sheets.find((x) => norm(x.code) === norm(code));
  return s ? [s.file, s.code] : null;
}

async function sendNotice(n) {
  const item = fileOfCode(n.code);
  if (!item) return toast(t('game.notices.missing', { code: n.code }));
  for (const tm of game.teams) await handOut(tm, [item], true);
  game.play.notices[n.code] = Date.now();
  await save();
  toast(t('game.notices.sent', { code: n.code }));
  render();
}

async function giveHint(team, hint) {
  const item = hint && fileOfCode(hint.code);
  if (!item) return;
  await handOut(team, [item], true);
  (game.play.hints[team] = game.play.hints[team] || []).push(hint.n);
  await save();
  toast(t('game.hints.sent', { team }));
  render();
}

async function setMarks(team, marks) {
  game.play.marks[team] = cleanMarks(marks);
  await save();
  render();
}

function downloadReport() {
  const blob = new Blob([reportText(partidaUi())], { type: 'text/markdown' });
  const a = h('a', { href: URL.createObjectURL(blob), download: `${game.slug}-${t('game.report.file')}.md` });
  document.body.append(a); a.click(); a.remove();
}

const partidaUi = () => ({ dgame, book: game.play, teamJson, teams: game.teams, log: game.log, clockDo, sendNotice, giveHint, setMarks, downloadReport, redraw: () => render() });

// Once a second: the numbers of the clock, and a notice that comes due (it is only a suggestion) is shown at once.
let dueKey = '';
setInterval(() => {
  if (!game || !game.play || !teamJson) return;
  if (tab === 'game') tickClock(partidaUi());
  const read = game.play.notices || {};
  const only = directorJson.notices.filter((n) => n.kind === 'notice');
  const key = clock.due(only, game.play.clock, Date.now(), only.filter((n) => read[n.code]).map((n) => n.n)).map((n) => n.code).join(',');
  if (key !== dueKey) { dueKey = key; if (key) { toast(t('game.notices.due_toast')); if (tab === 'game') render(); } }
}, 1000);

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
    return h('div', {}, h('div', { class: 'oc-card' }, h('h3', {}, t('room.create_title')), h('p', {}, t('room.create_text')),
      h('button', { class: 'oc-btn', type: 'button', id: 'oc-room-create', onclick: async () => { await startRoom(); render(); } }, t('room.create'))),
      backupCard({ lastBackup, download: downloadBackup, load: loadBackup }));
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
    h('p', { class: 'oc-muted' }, t('room.qr_help')),
    backupCard({ lastBackup, download: downloadBackup, load: loadBackup }));
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
    game && !game.recovery ? h('button', { class: 'oc-btn oc-btn--small oc-btn--ghost', type: 'button', id: 'oc-backup-top', onclick: downloadBackup }, t('recover.backup.button')) : null,
    game ? h('button', { class: 'oc-btn oc-btn--small oc-btn--ghost', type: 'button', onclick: endGame }, t('director.end')) : null));
}

async function endGame() {
  if (!confirm(t('director.end_confirm'))) return;
  await store.del('game'); await store.del('backupAt');
  recovery = null; lastBackup = null;
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
  if (game.recovery) return main.append(recovery ? recovery.view() : h('p', { class: 'oc-muted' }, t('recover.panel.waiting')));
  if (!store.store.persistent) main.append(h('div', { class: 'oc-notice' }, t('director.no_storage')));
  if (outdated) main.append(h('div', { class: `oc-notice${outdated.sameFormat ? '' : ' oc-notice--bad'}` }, outdated.sameFormat ? t('director.outdated.same') : t('director.outdated.format')));
  const mk = (id, text) => h('button', { class: 'oc-tab', id: `oc-tab-${id}`, role: 'tab', type: 'button', 'aria-selected': String(tab === id), onclick: () => { tab = id; render(); } }, text);
  main.append(h('div', { class: 'oc-tabs', role: 'tablist' }, mk('game', t('game.tab')), mk('requests', game.play && pendingList(game.play).length ? t('requests.panel.tab_pending', { n: pendingList(game.play).length }) : t('requests.panel.tab')), mk('give', t('director.tab.give')), mk('teams', t('director.tab.teams')), mk('room', room && room.pending().length ? t('room.tab_pending', { n: room.pending().length }) : t('room.tab')), mk('kit', t('director.tab.kit')), mk('register', t('requests.panel.register')), mk('score', t('game.score.tab')), mk('log', t('director.tab.log'))));
  main.append(tab === 'game' ? gameView(partidaUi()) : tab === 'score' ? scoreView(partidaUi()) : tab === 'requests' ? queueView(panelUi()) : tab === 'register' ? registerView(panelUi()) : tab === 'give' ? giveView() : tab === 'room' ? roomView() : tab === 'teams' ? teamsView() : tab === 'kit' ? kitView() : logView());
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
  lastBackup = (await store.get('backupAt')) || null;
  if (location.hash.includes('oc1r.')) {              // a team's phone sent the code as a link
    pendingCodes = decodeURIComponent(location.hash);
    history.replaceState(null, '', location.pathname + location.search);
  }
  if (game) {
    try { await loadCase(); target = [game.teams[0]]; }
    catch (e) { toast(t('director.error.load'), 6000); game = null; }
  }
  render();
}

main();
