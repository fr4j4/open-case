// Recovering a game (F6a), as a pure module: no DOM, no network and no clock of its own (every function takes `now`).
//
// Two ways to get a game back when the director's device is lost:
//   1. The BACKUP FILE: the director's whole saved game as JSON (`makeBackup`, `readBackup`, `cleanPlay`). It is the only thing that
//      also keeps what the teams never see: the marks of the score sheet.
//   2. The REGISTRO of the teams: each phone keeps what it was told (its folder, the answered requests with their cost, the
//      balance, the sheets and the clock). A new director device reads them (`buildRegistro` on the phone, `Assembler` and
//      `checkRegistro` on the director) and `rebuild` makes the game from them. Two phones of one team may not agree: `differences`
//      shows it and the director picks one registro per team; they are never merged by themselves.
// Nothing here has a rule of its own: balances, held sheets and hints come from rules.js and requests.js.
import { newState, hold } from './rules.js';
import { sanitize, holdItems, rulesRequest } from './requests.js';
import { newClock, fromWire, phases, wire } from './clock.js';
import { cleanMarks } from './score.js';
import { checkItems } from './delivery.js';

export const BACKUP_FORMAT = 'opencase-backup';
export const BACKUP_VERSION = 1;
const PIN = /^[A-HJKMNP-Z2-9]{6}$/;             // the alphabet of room.js (no 0 O 1 I L)
const TEAM_ROOM = /^oc-t-[a-z0-9]{20}$/;
const ID = /^[a-z0-9]{6,24}$/;
const TEAM = /^[A-D]$/;
const MAX_FORM_TEXT = 2000;
const clone = (x) => JSON.parse(JSON.stringify(x));
const isInt = (n, max = 1e9) => Number.isInteger(n) && n >= 0 && n <= max;
const num = (n) => (Number.isFinite(n) ? n : 0);
const text = (v, n) => (typeof v === 'string' ? v.slice(0, n) : '');

// --- The backup file -------------------------------------------------------------------------------------------------

export const makeBackup = (game, now) => JSON.stringify({ format: BACKUP_FORMAT, version: BACKUP_VERSION, at: now, game }, null, 1);
export const backupName = (slug, now) => `${slug}-${new Date(now).toISOString().slice(0, 16).replace(/[-:]/g, '').replace('T', '-')}.opencase.json`;

/** The game of a backup file, checked: { ok, game, at } or { ok: false, error } (`format`, `version`, `shape`). Nothing in it is
 * trusted: the fields that decide where the app fetches from are matched against their patterns. `cleanPlay` finishes the job
 * once the case is loaded (it needs the rules). */
export function readBackup(raw) {
  let b;
  try { b = typeof raw === 'string' ? JSON.parse(raw) : raw; } catch (e) { return { ok: false, error: 'format' }; }
  if (!b || typeof b !== 'object' || b.format !== BACKUP_FORMAT || !b.game || typeof b.game !== 'object') return { ok: false, error: 'format' };
  if (b.version !== BACKUP_VERSION) return { ok: false, error: 'version' };
  const g = b.game;
  const bad = { ok: false, error: 'shape' };
  if (typeof g.slug !== 'string' || !/^[A-Za-z0-9_-]{1,60}$/.test(g.slug)) return bad;
  if (typeof g.lang !== 'string' || !/^[a-z]{2}(-[A-Za-z]{2})?$/.test(g.lang)) return bad;
  if (typeof g.version !== 'string' || !/^[0-9a-f]{12}$/.test(g.version)) return bad;
  if (!Array.isArray(g.teams) || g.teams.length < 1 || g.teams.length > 4 || !g.teams.every((t, i) => TEAM.test(t) && g.teams.indexOf(t) === i)) return bad;
  if (!isInt(g.seq) || !Array.isArray(g.log)) return bad;
  const log = [];
  for (const e of g.log) {
    if (!e || !isInt(e.seq) || !g.teams.includes(e.team) || !Array.isArray(e.items)) return bad;
    const items = checkItems(e.items);
    if (!items) return bad;
    log.push({ seq: e.seq, team: e.team, items, at: num(e.at) });
  }
  const game = { slug: g.slug, lang: g.lang, version: g.version, teams: [...g.teams], seq: g.seq, log, created: num(g.created) || Date.now(), play: g.play && typeof g.play === 'object' ? g.play : null };
  if (g.room != null) {
    const r = g.room;
    if (!r || typeof r !== 'object' || !PIN.test(r.pin) || !ID.test(r.id || '') || !r.teamRooms || typeof r.teamRooms !== 'object' || !r.devices || typeof r.devices !== 'object') return bad;
    const teamRooms = {};
    for (const [t, name] of Object.entries(r.teamRooms)) if (g.teams.includes(t) && TEAM_ROOM.test(name)) teamRooms[t] = name;
    const devices = {};
    for (const [id, d] of Object.entries(r.devices)) {
      if (!ID.test(id) || !d || typeof d !== 'object') continue;
      const status = ['pending', 'approved', 'denied'].includes(d.status) ? d.status : 'pending';
      const team = status === 'approved' && g.teams.includes(d.team) ? d.team : null;
      devices[id] = { id, name: text(d.name, 40), team, status: status === 'approved' && !team ? 'pending' : status, joined: num(d.joined), seen: num(d.seen) };
    }
    game.room = { pin: r.pin, id: r.id, teamRooms, devices, adopt: (Array.isArray(r.adopt) ? r.adopt : []).filter((t) => g.teams.includes(t)) };
  }
  return { ok: true, game, at: num(b.at) };
}

/** The `play` of a saved game made well formed against the rules of the case: requests are checked again like a request that
 * arrives from the network, and a number or a code that does not make sense is dropped. Returns a book the app can use. */
export function cleanPlay(raw, rg, teams, now = Date.now()) {
  const p = raw && typeof raw === 'object' ? raw : {};
  const out = { states: {}, requests: [], clock: null, notices: {}, hints: {}, forms: {}, marks: {} };
  for (const team of teams) {
    const s = p.states && p.states[team];
    if (s && typeof s === 'object') {
      const base = newState(rg, team);
      const list = (v) => (Array.isArray(v) ? v.filter((x) => typeof x === 'string').slice(0, 400) : []);
      const tokens = isInt(s.tokens, base.initial.tokens) ? s.tokens : base.tokens;
      const alibi = isInt(s.alibi, base.initial.alibi) ? s.alibi : base.alibi;
      const asked = {};
      for (const [k, v] of Object.entries(s.asked && typeof s.asked === 'object' ? s.asked : {})) if (isInt(v, 99)) asked[k.slice(0, 80)] = v;
      out.states[team] = { ...base, tokens, alibi, held: { sheets: list(s.held && s.held.sheets), cards: list(s.held && s.held.cards) }, asked, log: Array.isArray(s.log) ? clone(s.log).slice(0, 500) : [] };
    }
    const forms = p.forms && p.forms[team];
    if (forms && typeof forms === 'object') out.forms[team] = cleanForms(forms, rg);
    const marks = p.marks && p.marks[team];
    if (marks) out.marks[team] = cleanMarks(marks);
    const hints = p.hints && p.hints[team];
    if (Array.isArray(hints)) out.hints[team] = hints.filter((n) => isInt(n, 99));
  }
  for (const r of Array.isArray(p.requests) ? p.requests : []) {
    if (!r || typeof r !== 'object' || !teams.includes(r.team)) continue;
    const req = sanitize(r.req, rg.team);
    if (!req) continue;
    const rec = { ...clone(r), id: req.id, req, status: r.status === 'done' ? 'done' : 'pending', at: num(r.at), device: text(r.device, 24), name: text(r.name, 40) };
    if (rec.status === 'done' && !(r.charged && isInt(r.charged.tokens, 99) && isInt(r.charged.alibi, 99))) continue;
    out.requests.push(rec);
  }
  if (p.clock && typeof p.clock === 'object' && phases(rg.figures).some((x) => x.key === p.clock.phase)) {
    out.clock = { phase: p.clock.phase, running: !!p.clock.running, elapsed: Math.max(0, num(p.clock.elapsed)), since: p.clock.running ? num(p.clock.since) || now : null };
  }
  for (const [code, at] of Object.entries(p.notices && typeof p.notices === 'object' ? p.notices : {})) if (Number.isFinite(at)) out.notices[code.slice(0, 40)] = at;
  return out;
}

function cleanForms(forms, rg) {
  const out = {};
  const known = new Set(((rg.team && rg.team.forms) || []).map((f) => f.id));
  for (const [id, rec] of Object.entries(forms)) {
    if (!known.has(id) || !rec || typeof rec.values !== 'object' || !rec.values) continue;
    out[id] = { values: cleanValues(rec.values), at: num(rec.at), device: text(rec.device, 24) };
  }
  return out;
}

/** The answers written on a sheet: only the keys the sheets use (`f<part>.<item>`, `t<part>.<row>.<column>`), as texts of at most 2000 characters. */
export function cleanValues(values) {
  const out = {};
  for (const [k, v] of Object.entries(values).slice(0, 300)) if (/^[ft]\d+\.\d+(\.\d+)?$/.test(k) && typeof v === 'string') out[k] = v.slice(0, MAX_FORM_TEXT);
  return out;
}

// --- The code that opens the recovery: what a phone shows and the new director reads -----------------------------------

export const CODE_PREFIX = 'oc1r.';
const b64 = (s) => { const bytes = new TextEncoder().encode(s); let bin = ''; for (const b of bytes) bin += String.fromCharCode(b); return btoa(bin).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, ''); };
const unb64 = (s) => { const t = s.replace(/-/g, '+').replace(/_/g, '/'); return new TextDecoder().decode(Uint8Array.from(atob(t + '='.repeat((4 - (t.length % 4)) % 4)), (c) => c.charCodeAt(0))); };

/** What a phone shows to be recovered: the PIN and the name of its team room, and the case it plays. The name of the room is what
 * opens the team's room, so it is shown only on the team's own phone. */
export const recoveryCode = (session) => CODE_PREFIX + b64(JSON.stringify({ p: session.pin, t: session.team, r: session.room, c: session.c, l: session.l, v: session.v }));
export const recoveryLink = (base, session) => `${base}#recuperar.${recoveryCode(session)}`;

/** Every code in a text (a link, a fragment, a bare code; several, separated by anything). Returns { codes: [{pin, team, room, slug, lang, version}], bad } */
export function parseCodes(input) {
  const found = String(input || '').match(/oc1r\.[A-Za-z0-9_-]+/g) || [];
  const codes = [];
  let bad = 0;
  for (const f of found) {
    try {
      const m = JSON.parse(unb64(f.slice(CODE_PREFIX.length)));
      const ok = m && PIN.test(m.p) && TEAM.test(m.t) && TEAM_ROOM.test(m.r) && /^[A-Za-z0-9_-]{1,60}$/.test(m.c) && /^[a-z]{2}(-[A-Za-z]{2})?$/.test(m.l) && /^[0-9a-f]{12}$/.test(m.v);
      if (!ok) { bad++; continue; }
      if (!codes.some((c) => c.team === m.t && c.room === m.r)) codes.push({ pin: m.p, team: m.t, room: m.r, slug: m.c, lang: m.l, version: m.v });
    } catch (e) { bad++; }
  }
  return { codes, bad };
}

/** One game from the codes of its teams: they must agree on the PIN and on the case, and every team once. */
export function gameFromCodes(codes) {
  if (!codes.length) return { error: 'none' };
  const first = codes[0];
  if (codes.some((c) => c.pin !== first.pin || c.slug !== first.slug || c.lang !== first.lang)) return { error: 'mixed' };
  const rooms = {};
  for (const c of codes) { if (rooms[c.team] && rooms[c.team] !== c.room) return { error: 'twice' }; rooms[c.team] = c.room; }
  const top = Math.max(...codes.map((c) => 'ABCD'.indexOf(c.team)));
  const teams = 'ABCD'.slice(0, Math.max(2, top + 1)).split('');
  // the version of the oldest code: the folder of a newer one may have changed, and a phone keeps asking for what it was given
  return { slug: first.slug, lang: first.lang, version: first.version, pin: first.pin, teams, rooms };
}

// --- The registro: what a phone keeps and tells -----------------------------------------------------------------------

export const PART_SIZE = 7000;       // characters of one message: the relays of the network accept small events

/** What a phone knows of the game: its folder as the director handed it out (in order), the answered requests with what they cost,
 * the ones still waiting, the sheets and the clock. `state` is the phone's saved folder and `reqs` its saved requests. */
export function buildRegistro({ state, reqs, deviceId, name, now }) {
  const delivered = (state.order || []).filter((f) => state.items[f]).map((f) => [f, state.items[f].code || '']);
  const forms = {};
  for (const [id, rec] of Object.entries(reqs.forms || {})) forms[id] = { values: rec.values || {}, sent: !!rec.sent };
  return {
    device: deviceId, name: name || '', team: state.team, c: state.slug, l: state.lang, v: state.version, seq: state.seq || 0, at: now,
    delivered, hist: (reqs.bal && reqs.bal.hist) || [], pending: reqs.pending || [],
    bal: reqs.bal ? { tokens: reqs.bal.tokens, alibi: reqs.bal.alibi } : null,
    forms, clock: reqs.clock ? wire(reqs.clock, now) : null,
  };
}

/** The registro cut in messages of at most PART_SIZE characters: { rid, i, n, d }. */
export function splitRegistro(reg, rid) {
  const json = JSON.stringify(reg);
  const n = Math.max(1, Math.ceil(json.length / PART_SIZE));
  return Array.from({ length: n }, (_, i) => ({ rid, i, n, d: json.slice(i * PART_SIZE, (i + 1) * PART_SIZE) }));
}

/** Puts the messages of a registro back together, per phone. `add` returns the registro when the last part arrives. */
export class Assembler {
  constructor() { this.open = new Map(); }
  add(from, p) {
    if (!p || typeof p.rid !== 'string' || p.rid.length > 24 || !isInt(p.i, 400) || !isInt(p.n, 400) || p.n < 1 || p.i >= p.n || typeof p.d !== 'string' || p.d.length > PART_SIZE * 2) return null;
    let cur = this.open.get(from);
    if (!cur || cur.rid !== p.rid) { cur = { rid: p.rid, n: p.n, parts: new Map() }; this.open.set(from, cur); }
    if (cur.n !== p.n) return null;
    cur.parts.set(p.i, p.d);
    if (cur.parts.size < cur.n) return null;
    this.open.delete(from);
    try { return JSON.parse(Array.from({ length: cur.n }, (_, i) => cur.parts.get(i)).join('')); } catch (e) { return null; }
  }
}

/** A registro that came from the network, cleaned and checked against the case. Everything unknown is dropped; null if it is not a registro of this team. */
export function checkRegistro(raw, rg, team) {
  if (!raw || typeof raw !== 'object' || raw.team !== team || typeof raw.device !== 'string' || !ID.test(raw.device)) return null;
  const delivered = checkItems(Array.isArray(raw.delivered) ? raw.delivered : []);
  if (!delivered) return null;
  const hist = [];
  for (const e of Array.isArray(raw.hist) ? raw.hist.slice(0, 500) : []) {
    const req = e && sanitize(e.req, rg.team);
    const c = e && e.charged;
    if (!req || typeof e.answer !== 'string' || !/^[a-z_]{2,30}$/.test(e.answer) || !c || !isInt(c.tokens, 99) || !isInt(c.alibi, 99)) continue;
    hist.push({ id: req.id, req, answer: e.answer, charged: { tokens: c.tokens, alibi: c.alibi }, note: text(e.note, 400), at: num(e.at), asked: num(e.asked) });
  }
  const done = new Set(hist.map((e) => e.id));
  const pending = (Array.isArray(raw.pending) ? raw.pending.slice(0, 200) : []).map((r) => sanitize(r, rg.team)).filter((r) => r && !done.has(r.id));
  const forms = {};
  const known = new Set(((rg.team && rg.team.forms) || []).map((f) => f.id));
  for (const [id, f] of Object.entries(raw.forms && typeof raw.forms === 'object' ? raw.forms : {})) if (known.has(id) && f && typeof f.values === 'object' && f.values) forms[id] = { values: cleanValues(f.values), sent: !!f.sent };
  const bal = raw.bal && isInt(raw.bal.tokens, 99) && isInt(raw.bal.alibi, 99) ? { tokens: raw.bal.tokens, alibi: raw.bal.alibi } : null;
  const c = raw.clock && fromWire(rg.figures, raw.clock, 0) ? { phase: raw.clock.phase, running: !!raw.clock.running, elapsedMs: Math.round(Number(raw.clock.elapsedMs)) } : null;
  return { device: raw.device, name: text(raw.name, 40), team, seq: isInt(raw.seq) ? raw.seq : 0, delivered, hist, pending, bal, forms, clock: c };
}

/** How complete a registro is (to propose the best one by default; the director decides). */
export const completeness = (reg) => reg.hist.length * 1000 + reg.delivered.length * 10 + reg.pending.length;

/** What the registros of one team do not agree on: for each phone, what only it has. { same, phones: [{device, name, only: {delivered, hist, pending}, tokens}] }.
 * A registro of a phone that has the same as the others is not a difference. */
export function differences(regs) {
  const sets = regs.map((r) => ({ delivered: new Set(r.delivered.map((i) => i[1] || i[0])), hist: new Set(r.hist.map((e) => e.id)), pending: new Set(r.pending.map((q) => q.id)) }));
  const phones = regs.map((r, i) => {
    const only = {};
    for (const k of ['delivered', 'hist', 'pending']) {
      const others = new Set(sets.filter((_, j) => j !== i).flatMap((s) => [...s[k]]));
      only[k] = [...sets[i][k]].filter((x) => !others.has(x));
    }
    return { device: r.device, name: r.name, only, tokens: r.bal ? r.bal.tokens : null };
  });
  const same = regs.length < 2 || (phones.every((p) => !p.only.delivered.length && !p.only.hist.length && !p.only.pending.length)
    && new Set(regs.map((r) => (r.bal ? r.bal.tokens : null))).size === 1);
  return { same, phones };
}

// --- The game from the registros ---------------------------------------------------------------------------------------

/** The game of the director from one registro per team (`picks`: {A: registro, …}, already through checkRegistro).
 * `rg` is the rules game (createGame(team, director)). Returns { seq, log, play, warnings }; `play` has the same shape as the book
 * the app keeps, so the panel, the register and the score work on it as before. What no phone knows is left blank: the marks. */
export function rebuild(rg, picks, { teams, now }) {
  const log = [];
  const play = { states: {}, requests: [], clock: null, notices: {}, hints: {}, forms: {}, marks: {} };
  const warnings = [];
  let seq = 0;
  const delivered = new Map();
  for (const team of teams) {
    const reg = picks[team];
    let s = newState(rg, team);
    s = hold(s, { sheets: rg.envelope(1) });
    if (!reg) { play.states[team] = s; continue; }          // a team nobody recovered starts as on the first minute
    if (reg.delivered.length) { log.push({ seq: reg.seq, team, items: reg.delivered, at: now }); seq = Math.max(seq, reg.seq); }
    s = holdItems(s, reg.delivered);
    delivered.set(team, new Set(reg.delivered.map((i) => String(i[1]).toLowerCase())));
    for (const e of reg.hist) {
      const request = rulesRequest(rg, { req: e.req });
      s.tokens -= e.charged.tokens;
      s.alibi -= e.charged.alibi;
      if (request.kind === 'witness' && e.answer === 'give' && request.who) s.asked = { ...s.asked, [request.who]: (s.asked[request.who] || 0) + 1 };
      s.log = [...s.log, { request, answer: e.answer, cost: e.charged.tokens + e.charged.alibi, charged: e.charged, delivers: { cards: [], sheets: [] } }];
      play.requests.push({ id: e.id, team, device: '', name: '', at: e.asked || e.at, req: e.req, status: 'done', answer: e.answer, charged: e.charged, note: e.note, doneAt: e.at, request, delivered: { cards: [], sheets: [] } });
    }
    if (s.tokens < 0 || s.alibi < 0) { warnings.push({ kind: 'negative', team }); s.tokens = Math.max(0, s.tokens); s.alibi = Math.max(0, s.alibi); }
    if (reg.bal && (reg.bal.tokens !== s.tokens || reg.bal.alibi !== s.alibi)) warnings.push({ kind: 'balance', team, expected: s.tokens, told: reg.bal.tokens });
    play.states[team] = s;
    for (const q of reg.pending) play.requests.push({ id: q.id, team, device: reg.device, name: reg.name, at: now, req: q, status: 'pending' });
    const forms = {};
    for (const [id, f] of Object.entries(reg.forms)) if (f.sent) forms[id] = { values: f.values, at: now, device: reg.device };
    if (Object.keys(forms).length) play.forms[team] = forms;
    // the hints given are the hint cards the team holds, in order; the notices read are those that reached any team
    const mine = delivered.get(team);
    const hints = ((rg.director && rg.director.hints) || []).filter((h) => mine.has(String(h.code).toLowerCase())).map((h) => h.n);
    if (hints.length) play.hints[team] = hints;
  }
  for (const n of (rg.director && rg.director.notices) || []) {
    if ([...delivered.values()].some((set) => set.has(String(n.code).toLowerCase()))) play.notices[n.code] = now;
  }
  play.requests.sort((a, b) => a.at - b.at);
  // the clock: the phone furthest along (a later phase, then more time in it)
  const order = phases(rg.figures).map((p) => p.key);
  const clocks = teams.map((t) => picks[t] && picks[t].clock).filter(Boolean)
    .sort((a, b) => order.indexOf(b.phase) - order.indexOf(a.phase) || b.elapsedMs - a.elapsedMs);
  play.clock = (clocks[0] && fromWire(rg.figures, clocks[0], now)) || newClock(rg.figures);
  return { seq, log, play, warnings };
}
