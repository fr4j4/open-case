// The rules of the tokens, as a pure module: no DOM, no network, no clock. It applies what the engine publishes
// in the `rules` block of team.json and director.json (docs/web-format.md) to the cards, sheets, procedures and
// witnesses of director.json, so a request is charged and answered the way the kit and the guide say.
// Nothing here is copied from the case: a number or a code that is not in the JSON is not in this file.
// tests/web/test_rules.py checks it against the engine (tests/web_expected/<case>.json).
//
//   const game = createGame(team, director);          // `director` is null on a team's device: quote only
//   let state = newState(game);                        // tokens, alibi tokens, what the team holds
//   state = hold(state, { sheets: [...game.envelope(1)] });
//   const request = { kind: 'procedure', code: 'DG3', target: 'B' };
//   answers(game, state, request);                     // the buttons of the panel, each with its cost
//   const r = resolve(game, state, request, 'give');   // { ok, state, charged, delivers, error }
//
// A request is { kind, ... } with kind in rules.requests: question {code?, suspect?}, witness {who},
// follow_up {code}, confrontation {suspect, card?}, procedure {code, target?, sheets?} and source {code, place}.
// State is plain data (JSON), and every function returns a new one: nothing is changed in place.

const clone = (x) => JSON.parse(JSON.stringify(x));
/** A code as the engine compares it: E15·B, E15-B and "e15 b" are the same sheet. */
export const norm = (s) => String(s).toLowerCase().replace(/[\s·\-.]+/g, '');
const uniq = (list) => [...new Set(list)];
const has = (list, code) => list.some((x) => norm(x) === norm(code));

export function createGame(team, director = null) {
  const rules = team.rules;
  const by = (list, key) => new Map((list || []).map((x) => [key(x), x]));
  const game = {
    rules, figures: team.figures, team, director, teams: team.teams,
    teamProcedures: by(team.procedures, (p) => p.code),
    suspects: by(team.suspects, (s) => s.letter),
    envelopes: team.envelopes,
    cards: director ? by(director.cards, (c) => norm(c.code)) : new Map(),
    procedures: director ? by(director.procedures, (p) => p.code) : new Map(),
    locations: director ? by(director.locations, (l) => l.id) : new Map(),
    witnesses: director ? by(director.witnesses, (w) => w.who) : new Map(),
    followUps: director ? by(director.follow_ups, (f) => norm(f.code)) : new Map(),
  };
  /** The printed codes of the sheets of an envelope (1, 2…). */
  game.envelope = (n) => game.envelopes.filter((e) => e.number === Number(n))
    .flatMap((e) => e.sections.flatMap((s) => s.items.map((i) => i.code)));
  return game;
}

// --- State ---------------------------------------------------------------------------------------

/** A fresh team: all its tokens and nothing in its hands. `teamId` only matters when the case gives teams
 * different tokens (today all have the same). */
export function newState(game, teamId = null) {
  const t = (game.teams.find((x) => x.id === teamId) || game.teams[0] || {});
  const tokens = (t.tokens || []).length || game.rules.tokens_per_team;
  const alibi = (t.alibi_tokens || []).length ?? game.rules.alibi_tokens_per_team;
  return { team: teamId, tokens, alibi, initial: { tokens, alibi }, held: { sheets: [], cards: [] },
    asked: {}, log: [] };
}

/** The team now holds these sheets (an envelope, a procedure's result) and cards. */
export function hold(state, { sheets = [], cards = [] } = {}) {
  const s = clone(state);
  s.held.sheets = uniq([...s.held.sheets, ...sheets]);
  s.held.cards = uniq([...s.held.cards, ...cards]);
  return s;
}

/** The tokens spent, as { tokens, alibi }. The invariant of the game: spent + left = initial, never below 0. */
export function spent(state) {
  return { tokens: state.initial.tokens - state.tokens, alibi: state.initial.alibi - state.alibi };
}

export function checkState(state) {
  const problems = [];
  if (state.tokens < 0 || state.alibi < 0) problems.push('negative balance');
  const s = spent(state);
  if (s.tokens < 0 || s.alibi < 0) problems.push('more tokens than at the start');
  const log = state.log.reduce((a, e) => ({ tokens: a.tokens + e.charged.tokens, alibi: a.alibi + e.charged.alibi }),
    { tokens: 0, alibi: 0 });
  if (log.tokens !== s.tokens || log.alibi !== s.alibi) problems.push('the log does not add up to the tokens spent');
  return problems;
}

/** Points of the tokens left at the end: each numbered token scores `score.spare_token`, alibi tokens do not. */
export function spareTokenScore(game, state) {
  return state.tokens * game.figures.score.spare_token;
}

const holdsSheet = (state, code) => has(state.held.sheets, code);
const holdsCard = (state, code) => has(state.held.cards, code);
const holdsAny = (state, code) => holdsSheet(state, code) || holdsCard(state, code);

// --- What a request is worth ---------------------------------------------------------------------

function resultOf(game, request) {
  const p = game.procedures.get(request.code);
  if (!p) return { error: 'unknown_procedure' };
  if (p.gives) return { p, r: p.gives };
  const r = p.targets.find((t) => t.key === request.target);
  return r ? { p, r } : { error: 'unknown_target' };
}

/** What a request costs: { min, max } (equal when it is known). The team's device knows the cost of a
 * procedure by its code ("1 or 2"); the director's, by its target. */
export function quote(game, request) {
  const rule = game.rules.requests[request.kind];
  if (!rule) return { error: 'unknown_kind' };
  if (request.kind === 'source') return { min: 0, max: 0 };
  if (rule.cost !== null) return { min: rule.cost, max: rule.cost };
  if (game.director) {
    const { r, error } = resultOf(game, request);
    if (error) return { error };
    return { min: r.cost, max: r.cost };
  }
  const p = game.teamProcedures.get(request.code);
  if (!p) return { error: 'unknown_procedure' };
  return { min: Math.min(...p.costs), max: Math.max(...p.costs) };
}

/** Whether an alibi token can pay for this request: only a procedure the case marks `alibi`. */
export function acceptsAlibi(game, request) {
  return request.kind === 'procedure' && game.rules.alibi_procedures.includes(request.code);
}

// --- What each answer hands out and whether it can be given -------------------------------------

const out = (cards = [], sheets = []) => ({ cards: [...cards], sheets: [...sheets] });

function wildcard(game, role) {
  const code = game.rules.wildcards[role];
  return code ? [code] : [];
}

/** For each answer the director can press: { charge, cost, delivers, error }. `error` says why it cannot be given
 * now. Only the answers the engine lists in rules.requests[kind].answers exist, with the charge it says. */
function evaluate(game, state, request) {
  const { kind } = request;
  const rule = game.rules.requests[kind];
  if (!rule) return { error: 'unknown_kind' };
  const card = (code) => game.cards.get(norm(code));
  const res = {};
  let cost = rule.cost;
  const put = (name, delivers = out(), error = null, extra = {}) => {
    const a = rule.answers[name];
    if (a) res[name] = { charge: a.charge, cost: a.charge ? cost : 0, delivers, error, ...extra };
  };
  const heldCard = (c) => holdsCard(state, c.code);

  if (kind === 'question') {
    const c = request.code ? card(request.code) : null;
    if (request.code && (!c || c.type !== 'answer' || !c.menu)) return { error: 'unknown_card' };
    put('give', c ? out([c.code], c.attach) : out(), c && heldCard(c) ? 'already_have' : null);
    put('obvious');
    put('already_have', out(), c && heldCard(c) ? null : 'not_held');
  } else if (kind === 'witness') {
    const w = game.witnesses.get(request.who);
    if (!w) return { error: 'unknown_witness' };
    const next = card(w.cards[state.asked[w.who] || 0] ?? '');
    const appeared = w.appears_in.some((c) => holdsAny(state, c));
    put('give', next ? out([next.code], next.attach) : out(), !appeared ? 'unavailable' : (next ? null : 'nothing_to_add'));
    put('unavailable', out(wildcard(game, 'unavailable')), appeared ? 'available' : null);
    put('nothing_to_add', out(wildcard(game, 'nothing_to_add')), appeared && !next ? null : 'has_more');
  } else if (kind === 'follow_up') {
    const c = card(request.code);
    const f = game.followUps.get(norm(request.code));
    if (!c || !f) return { error: 'unknown_card' };
    // rule.unlock is "any": one of the sheets of `unlocked_by` is enough, besides having a card that enables it
    const locked = !f.mothers.some((m) => holdsCard(state, m))
      || (f.unlocked_by.length > 0 && !f.unlocked_by.some((x) => holdsAny(state, x)));
    put('give', out([c.code], c.attach), locked ? 'locked' : (heldCard(c) ? 'already_have' : null));
    put('locked', out(), locked ? null : 'not_locked');
    put('already_have', out(), heldCard(c) ? null : 'not_held');
  } else if (kind === 'confrontation') {
    if (!game.suspects.has(request.suspect)) return { error: 'unknown_suspect' };
    const c = request.card ? card(request.card) : null;
    if (request.card && (!c || c.type !== 'confrontation' || c.suspect !== request.suspect)) return { error: 'unknown_card' };
    put('give', c ? out([c.code], c.attach) : out(), !c ? 'no_card' : (heldCard(c) ? 'already_have' : null));
    const failed = [...game.cards.values()].find((x) => x.type === 'failed' && x.suspect === request.suspect);
    put('failed', failed ? out([failed.code]) : out(wildcard(game, 'confrontation_failed')));
    put('already_have', out(), c && heldCard(c) ? null : 'not_held');
  } else if (kind === 'procedure') {
    const found = resultOf(game, request);
    if (found.error) return { error: found.error };
    const r = found.r;
    cost = r.cost;
    // an open request ("material") hands out the sheets the director names in request.sheets
    const mine = r.special === 'material' ? (request.sheets || []) : r.sheets;
    const allHeld = mine.length > 0 && mine.every((x) => holdsSheet(state, x));
    put('give', out([], mine), allHeld ? 'already_have' : (r.special === 'none' ? 'nothing_there' : (mine.length ? null : 'no_sheets')));
    put('nothing_found', out(wildcard(game, 'no_findings')), r.special ? null : 'there_is_something');
    put('no_basis');
    put('already_have', out(), allHeld ? null : 'not_held');
  } else if (kind === 'source') {
    const place = game.locations.get(request.place);
    if (!game.rules.free_source_procedures.includes(request.code)) return { error: 'no_source_procedure' };
    if (!place) return { error: 'unknown_place' };
    const yes = place.sources.length > 0;
    put('yes', out(), yes ? null : 'has_none', { suggested: yes });
    put('no', out(), yes ? 'has_one' : null, { suggested: !yes });
  }
  return { answers: res };
}

/** The buttons of the panel for a request: [{ answer, charge, cost, available, why, suggested }]. */
export function answers(game, state, request) {
  if (!game.director) return { error: 'no_director' };
  const e = evaluate(game, state, request);
  if (e.error) return { error: e.error };
  return Object.entries(e.answers).map(([answer, a]) => ({
    answer, charge: a.charge ?? false, cost: a.cost, available: !a.error, why: a.error || null,
    delivers: a.delivers, suggested: a.suggested }));
}

/** Answers a request. `options.alibi`: how many of the tokens are alibi tokens (only where the case allows).
 * Returns { ok: true, state, charged: {tokens, alibi}, cost, delivers } or { ok: false, error } with the state
 * untouched. A charged answer that the team cannot pay is refused: the balance never goes below 0. */
export function resolve(game, state, request, answer, options = {}) {
  const list = answers(game, state, request);
  if (list.error) return { ok: false, error: list.error };
  const a = list.find((x) => x.answer === answer);
  if (!a) return { ok: false, error: 'unknown_answer' };
  if (!a.available) return { ok: false, error: a.why };
  const alibi = Number(options.alibi || 0);
  if (alibi < 0 || !Number.isInteger(alibi)) return { ok: false, error: 'bad_alibi' };
  if (alibi && (!a.charge || !acceptsAlibi(game, request))) return { ok: false, error: 'alibi_not_accepted' };
  if (alibi > a.cost) return { ok: false, error: 'alibi_over_cost' };
  const charged = a.charge ? { tokens: a.cost - alibi, alibi } : { tokens: 0, alibi: 0 };
  if (charged.tokens > state.tokens || charged.alibi > state.alibi) return { ok: false, error: 'not_enough_tokens' };
  const s = hold(state, a.delivers);
  s.tokens -= charged.tokens;
  s.alibi -= charged.alibi;
  if (request.kind === 'witness' && answer === 'give') s.asked = { ...s.asked, [request.who]: (s.asked[request.who] || 0) + 1 };
  s.log = [...s.log, { request, answer, cost: a.cost, charged, delivers: a.delivers }];
  return { ok: true, state: s, charged, cost: a.cost, delivers: a.delivers };
}
