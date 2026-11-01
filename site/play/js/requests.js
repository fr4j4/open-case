// The requests of a game (F4b), as pure functions: what a team can ask for, how a request is checked when it arrives, what
// the director's panel suggests for it and how one is answered. No DOM and no network, and no rule of its own: costs, buttons
// and charges all come from rules.js (F4a), which reads only what the engine publishes (docs/web-format.md).
//
//   a team's phone  → director   {k:'req', r: <request>}            one per request, with an id; sent again until answered
//   director → team's phones     {k:'bal', t, tokens, alibi, initial, hist:[<entry>], open:[ids]}
//
// <request> (what travels; every field is checked by `sanitize` before the director uses it):
//   { id, kind, code?, target?, suspect?, who?, place?, text?, detail?, evidence?: [[code, text]], alibi? }
//   kind: question {code | suspect + text}, follow_up {code}, witness {who, detail (where the name appeared), text},
//         confrontation {suspect, evidence}, procedure {code, target?, text, alibi?}, source {code, place}
import { createGame, newState, hold, quote, answers, resolve, acceptsAlibi, norm, matchConfrontation, confrontationCards } from './rules.js';
import { canRequest } from './clock.js';

export { createGame, quote, acceptsAlibi, confrontationCards };
export const KINDS = ['question', 'follow_up', 'witness', 'confrontation', 'procedure', 'source'];
export const MAX_TEXT = 400;
export const MAX_EVIDENCE = 12;

const clip = (v, n = MAX_TEXT) => (typeof v === 'string' ? v.trim().slice(0, n) : '');
const clone = (x) => JSON.parse(JSON.stringify(x));
const ID = /^[a-z0-9]{6,24}$/;

export function newRequestId() {
  const a = new Uint8Array(8);
  crypto.getRandomValues(a);
  return Array.from(a, (b) => 'abcdefghijklmnopqrstuvwxyz0123456789'[b % 36]).join('');
}

// --- Checking a request that comes from the network -----------------------------------------------------------------

/** The request cleaned up and checked against team.json (the public data), or null if it does not make sense.
 * Nothing in it is trusted: unknown fields are dropped, texts are cut, codes must exist. */
export function sanitize(raw, team) {
  if (!raw || typeof raw !== 'object' || typeof raw.id !== 'string' || !ID.test(raw.id) || !KINDS.includes(raw.kind)) return null;
  const r = { id: raw.id, kind: raw.kind };
  const procedure = () => (team.procedures || []).find((p) => p.code === raw.code);
  const suspect = (letter) => (team.suspects || []).some((s) => s.letter === letter);
  switch (raw.kind) {
    case 'question': {
      if (raw.code) {
        if (!(team.menu || []).some((m) => m.code === raw.code)) return null;
        r.code = raw.code;
      } else {
        if (!suspect(raw.suspect) || !clip(raw.text)) return null;
        r.suspect = raw.suspect;
        r.text = clip(raw.text);
      }
      break;
    }
    case 'follow_up':
      if (!(team.follow_ups || []).some((f) => f.code === raw.code)) return null;
      r.code = raw.code;
      break;
    case 'witness':
      if (!clip(raw.who, 80)) return null;
      r.who = clip(raw.who, 80);
      r.detail = clip(raw.detail);
      r.text = clip(raw.text);
      break;
    case 'confrontation': {
      if (!suspect(raw.suspect) || !Array.isArray(raw.evidence) || !raw.evidence.length || raw.evidence.length > MAX_EVIDENCE) return null;
      r.suspect = raw.suspect;
      r.evidence = raw.evidence.map((e) => (Array.isArray(e) ? [clip(String(e[0] ?? ''), 40), clip(e[1], 200)] : null));
      if (r.evidence.some((e) => !e || !e[0])) return null;
      break;
    }
    case 'procedure':
    case 'source': {
      const p = procedure();
      if (!p) return null;
      r.code = p.code;
      if (raw.kind === 'source') {
        if (!(team.rules.free_source_procedures || []).includes(p.code)) return null;
        if (!p.targets.some((x) => x.key === raw.place)) return null;
        r.place = raw.place;
        break;
      }
      if (p.targets.length) {
        if (!p.targets.some((x) => x.key === raw.target)) return null;
        r.target = raw.target;
      } else r.target = null;
      r.text = clip(raw.text);
      r.detail = clip(raw.detail);
      const alibi = Number(raw.alibi || 0);
      if (alibi) {
        if (!Number.isInteger(alibi) || alibi < 0 || alibi > 9 || !(team.rules.alibi_procedures || []).includes(p.code)) return null;
        r.alibi = alibi;
      }
      break;
    }
    default: return null;
  }
  return r;
}

// --- What the team's phone shows ------------------------------------------------------------------------------------

/** Words for a request, in the language of `tr` (the app's `t`). { kind, what, extra } */
export function describe(team, req, tr) {
  const suspect = (l) => { const s = (team.suspects || []).find((x) => x.letter === l); return s ? s.short_name || s.name : l; };
  const out = { kind: tr(`requests.kind.${req.kind}`), what: '', extra: '' };
  if (req.kind === 'question') {
    const m = (team.menu || []).find((x) => x.code === req.code);
    out.what = m ? `${m.code} · ${suspect(m.suspect)}` : `${suspect(req.suspect)} · ${tr('requests.off_menu')}`;
    out.extra = m ? m.question : req.text;
  } else if (req.kind === 'follow_up') out.what = req.code;
  else if (req.kind === 'witness') { out.what = req.who; out.extra = [req.detail, req.text].filter(Boolean).join(' · '); }
  else if (req.kind === 'confrontation') {
    out.what = suspect(req.suspect);
    out.extra = req.evidence.map((e) => (e[1] ? `${e[0]}: ${e[1]}` : e[0])).join(' · ');
  } else {
    const p = (team.procedures || []).find((x) => x.code === req.code);
    const target = p && p.targets.find((x) => x.key === (req.place ?? req.target));
    out.what = `${req.code}${target ? ` · ${target.label}` : ''}`;
    out.extra = req.text || '';
  }
  return out;
}

/** The tokens a team can still use: what the director says it has minus what its pending requests hold back.
 * `pending` are requests the team has sent and nobody has answered yet. */
export function available(game, bal, pending) {
  let tokens = bal.tokens;
  let alibi = bal.alibi;
  for (const p of pending) {
    const q = quote(game, p);
    if (q.error) continue;
    const a = Math.min(p.alibi || 0, q.max);
    tokens -= q.max - a;
    alibi -= a;
  }
  return { tokens, alibi };
}

/** Whether a team can send this request now: { ok } or { ok: false, reason } (`tokens`, `alibi`, `unknown`). A request with
 * a cost it cannot pay is not sent at all (the saldo is also checked by the director). */
export function canAsk(game, bal, pending, req, open = true) {
  if (!open) return { ok: false, reason: 'phase' };
  const q = quote(game, req);
  if (q.error) return { ok: false, reason: 'unknown' };
  const a = req.alibi || 0;
  if (a && (!acceptsAlibi(game, req) || a > q.max)) return { ok: false, reason: 'alibi' };
  const left = available(game, bal, pending);
  if (q.max - a > left.tokens) return { ok: false, reason: 'tokens' };
  if (a > left.alibi) return { ok: false, reason: 'alibi' };
  return { ok: true, cost: q };
}

// --- The director's book: one rules state per team, and the register of requests ---------------------------------------

/** What the director's device keeps of the game's requests: { states: {A: <rules state>}, requests: [<record>] }. */
export const newBook = () => ({ states: {}, requests: [] });

/** The items [[file, code]] as sheets and cards the team holds. */
export function holdItems(state, items) {
  const sheets = [];
  const cards = [];
  for (const [file, code] of items) {
    if (!code) continue;
    if (file.startsWith('sheets/')) sheets.push(code);
    else if (file.startsWith('cards/')) cards.push(code);
  }
  return hold(state, { sheets, cards });
}

/** The rules state of a team, made on first use: all its tokens, envelope 1, and everything already delivered (`log` of the game). */
export function teamState(game, book, team, log = []) {
  if (!book.states[team]) {
    let s = newState(game, team);
    s = hold(s, { sheets: game.envelope(1) });
    for (const e of log) if (e.team === team) s = holdItems(s, e.items);
    book.states[team] = s;
  }
  return book.states[team];
}

/** What a team's phones are told: its balance, and one entry per answered request. Never what was handed out (that travels as a delivery). */
export function balanceFor(game, book, team, log = []) {
  const s = teamState(game, book, team, log);
  const mine = book.requests.filter((r) => r.team === team);
  return {
    t: team, tokens: s.tokens, alibi: s.alibi, initial: s.initial,
    hist: mine.filter((r) => r.status !== 'pending').map((r) => ({ id: r.id, req: r.req, answer: r.answer, charged: r.charged, note: r.note || '', at: r.doneAt, asked: r.at })),
    open: mine.filter((r) => r.status === 'pending').map((r) => r.id),
  };
}

/** Puts a request that arrived in the register (once: a request that is sent again is the same). Returns the record or null. */
export function receive(game, book, team, device, raw, now = Date.now()) {
  const known = book.requests.find((r) => r.id === raw?.id && r.team === team);
  if (known) return { record: known, fresh: false };
  const req = sanitize(raw, game.team);
  if (!req) return null;
  const record = { id: req.id, team, device: device.id, name: device.name || '', at: now, req, status: 'pending' };
  book.requests.push(record);
  return { record, fresh: true };
}

// --- What to suggest to the director ------------------------------------------------------------------------------------

/** The witness a typed name means (their name, `who` or an alias), or null. */
export function matchWitness(game, typed) {
  const text = norm(typed || '');
  if (!text) return null;
  const list = game.director ? game.director.witnesses : [];
  const names = (w) => [w.who, w.name, ...(w.aliases || [])].map(norm).filter(Boolean);
  return list.find((w) => names(w).includes(text))
    || list.find((w) => names(w).some((n) => text.includes(n) || n.includes(text))) || null;
}

/** The request of the rules (rules.js) for a team's request; `choice` is what the director decides: { who, card, sheets }.
 * A confrontation the director has not chosen a card for takes the card its evidence opens (opens_with), if it is only one;
 * that needs the team's `state` (T7 comes only once T6 is held). */
export function rulesRequest(game, rec, choice = {}, state = null) {
  const q = rec.req;
  switch (q.kind) {
    case 'question': return { kind: 'question', ...(q.code ? { code: q.code } : { suspect: q.suspect }) };
    case 'follow_up': return { kind: 'follow_up', code: q.code };
    case 'witness': { const w = choice.who ? { who: choice.who } : matchWitness(game, q.who); return { kind: 'witness', who: w ? w.who : '' }; }
    case 'confrontation': {
      const card = choice.card || (state ? matchConfrontation(game, state, q.suspect, q.evidence).card : null);
      return { kind: 'confrontation', suspect: q.suspect, ...(card ? { card } : {}) };
    }
    case 'source': return { kind: 'source', code: q.code, place: q.place };
    default: return { kind: 'procedure', code: q.code, target: q.target, ...(choice.sheets ? { sheets: choice.sheets } : {}) };
  }
}

const PREFER = ['give', 'nothing_found', 'already_have', 'locked', 'unavailable', 'nothing_to_add', 'no_basis'];

/** What the panel proposes for a request: { request, buttons, suggested, cost, conditions }.
 * `buttons` are rules.js `answers` (one per button, each with its cost and whether it can be pressed); `suggested` is the one
 * to press; `conditions` are the codes that decide it, each with whether the team already holds it. */
export function suggest(game, state, rec, choice = {}) {
  const request = rulesRequest(game, rec, choice, state);
  const list = request.kind === 'witness' && !request.who ? { error: 'unknown_witness' } : answers(game, state, request);
  const out = { request, buttons: Array.isArray(list) ? list : [], error: Array.isArray(list) ? null : list.error, suggested: null, cost: 0, conditions: [], match: null };
  if (request.kind === 'confrontation') out.match = matchConfrontation(game, state, rec.req.suspect, rec.req.evidence);
  if (out.error) return out;
  const flagged = out.buttons.find((b) => b.suggested === true && b.available);
  const first = flagged || PREFER.map((a) => out.buttons.find((b) => b.answer === a && b.available)).find(Boolean)
    || out.buttons.find((b) => b.available);
  out.suggested = first ? first.answer : null;
  out.cost = (out.buttons.find((b) => b.answer === 'give') || out.buttons[0] || { cost: 0 }).cost;
  const held = (c) => state.held.sheets.some((x) => norm(x) === norm(c)) || state.held.cards.some((x) => norm(x) === norm(c));
  const cond = (codes) => codes.map((code) => ({ code, held: held(code) }));
  if (request.kind === 'follow_up') {
    const f = game.followUps.get(norm(request.code));
    if (f) out.conditions = [...cond(f.mothers).map((c) => ({ ...c, role: 'mother' })), ...cond(f.unlocked_by).map((c) => ({ ...c, role: 'needs' }))];
  } else if (request.kind === 'witness') {
    const w = game.witnesses.get(request.who);
    if (w) out.conditions = cond(w.appears_in).map((c) => ({ ...c, role: 'appears' }));
  }
  return out;
}

/** The items [[file, code]] of what an answer hands out ({cards, sheets}), to put in a delivery. Every sheet with that printed code. */
export function itemsOf(game, delivers) {
  const items = [];
  const seen = new Set();
  const push = (file, code) => { if (file && !seen.has(file)) { seen.add(file); items.push([file, code]); } };
  for (const code of delivers.sheets || []) for (const s of game.director.sheets.filter((x) => norm(x.code) === norm(code))) push(s.file, s.code);
  for (const code of delivers.cards || []) { const c = game.cards.get(norm(code)); if (c && c.file) push(c.file, c.code); }
  return items;
}

/** Answers one request of the register with a button of the panel.
 * options: { who, card, sheets (material), alibi, keep: {cards, sheets} (a part of the suggestion: what the director hands out), note }
 * Returns { ok: true, record, items, charged } and the book is changed, or { ok: false, error } and nothing is. */
export function answer(game, book, rec, button, options = {}, log = [], now = Date.now()) {
  if (rec.status !== 'pending') return { ok: false, error: 'done' };
  // rule 1 of the kit: only in the investigation. The app keeps the clock in `book.clock` (a book without one has no phases).
  if (book.clock && !canRequest(book.clock)) return { ok: false, error: 'phase' };
  const state = teamState(game, book, rec.team, log);
  const request = rulesRequest(game, rec, options, state);
  if (request.kind === 'witness' && !request.who) return { ok: false, error: 'unknown_witness' };
  // an alibi token pays only a charged answer, and never more than it costs
  const pressed = answers(game, state, request);
  const b = Array.isArray(pressed) ? pressed.find((x) => x.answer === button) : null;
  const wanted = Number(options.alibi ?? rec.req.alibi ?? 0);
  const alibi = b && b.charge && acceptsAlibi(game, request) ? Math.max(0, Math.min(wanted, b.cost)) : 0;
  const res = resolve(game, state, request, button, { alibi });
  if (!res.ok) return res;
  let next = res.state;
  let delivers = res.delivers;
  if (options.keep) {      // the director took something out of the suggestion: only what stays is handed out
    const keep = { cards: delivers.cards.filter((c) => options.keep.cards.includes(c)), sheets: delivers.sheets.filter((c) => options.keep.sheets.includes(c)) };
    next = clone(next);
    next.held = hold(state, keep).held;
    delivers = keep;
  }
  book.states[rec.team] = next;
  Object.assign(rec, { status: 'done', answer: button, charged: res.charged, note: clip(options.note || ''), doneAt: now, request, delivered: delivers });
  return { ok: true, record: rec, items: itemsOf(game, delivers), charged: res.charged };
}

/** Median seconds from arriving to answered, over the answered ones (the criterion of the field closing). */
export function medianSeconds(book) {
  const t = book.requests.filter((r) => r.status === 'done').map((r) => (r.doneAt - r.at) / 1000).sort((a, b) => a - b);
  if (!t.length) return null;
  const m = t.length >> 1;
  return t.length % 2 ? t[m] : (t[m - 1] + t[m]) / 2;
}
