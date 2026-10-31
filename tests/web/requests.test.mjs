// Tests of site/play/js/requests.js: what a team may ask for, how a request that comes from the network is checked, what the
// panel suggests and how an answer charges and hands out. Run by tests/web/test_requests.py (node --test), with
//   OC_WEB_DIR  the folder of a compiled version (team.json, director.json)
//   OC_PARTIDA  tests/web/partidas/<game>.json: a scripted game (the v8 simulation of three teams, rounds 1 to 3)
import { test } from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { createGame, checkState, norm } from '../../site/play/js/rules.js';
import { sanitize, canAsk, available, receive, suggest, answer, teamState, balanceFor, medianSeconds, newBook, matchWitness, describe, holdItems } from '../../site/play/js/requests.js';

const read = (f) => JSON.parse(fs.readFileSync(f, 'utf8'));
const team = read(path.join(process.env.OC_WEB_DIR, 'team.json'));
const director = read(path.join(process.env.OC_WEB_DIR, 'director.json'));
const partida = read(process.env.OC_PARTIDA);
const game = createGame(team, director);
const teamGame = createGame(team, null);
const device = (t) => ({ id: `phone-${t}`, name: `Teléfono ${t}` });
const rid = (i) => `req${String(i).padStart(5, '0')}`;
const codes = (d) => [...d.sheets, ...d.cards];
const sameSet = (a, b, msg) => assert.deepEqual(a.map(norm).sort(), b.map(norm).sort(), msg);
const tr = (k) => k;

function play(steps, book = newBook(), log = []) {
  const results = [];
  let now = 1_000_000;
  steps.forEach((s, i) => {
    now += 20_000;
    const got = receive(game, book, s.team, device(s.team), { id: rid(i), ...s.request }, now);
    assert.ok(got && got.fresh, `step ${i + 1}: the request is accepted (${JSON.stringify(s.request)})`);
    const state = teamState(game, book, s.team, log);
    const sg = suggest(game, state, got.record, s.choice || {});
    const res = answer(game, book, got.record, s.button, { card: s.choice?.card, who: s.choice?.who }, log, now + 4000);
    assert.ok(res.ok, `step ${i + 1} ${s.team}: ${res.error}`);
    results.push({ step: s, sg, res });
  });
  return results;
}

test('a request that arrives is checked against team.json: unknown codes, targets and kinds are refused', () => {
  const ok = { id: 'abcdef12', kind: 'procedure', code: 'DG3', target: 'B', text: 'x' };
  assert.deepEqual(sanitize(ok, team), { id: 'abcdef12', kind: 'procedure', code: 'DG3', target: 'B', text: 'x', detail: '' });
  const bad = [
    { ...ok, id: 'X' }, { ...ok, kind: 'cheat' }, { ...ok, code: 'DG99' }, { ...ok, target: 'nobody' },
    { ...ok, alibi: 1 },                                              // DG3 does not accept an alibi token
    { id: 'abcdef12', kind: 'question', code: 'ZZ9' }, { id: 'abcdef12', kind: 'question', suspect: 'B' },   // off the menu needs a text
    { id: 'abcdef12', kind: 'follow_up', code: 'B1' }, { id: 'abcdef12', kind: 'witness', who: '  ' },
    { id: 'abcdef12', kind: 'confrontation', suspect: 'B', evidence: [] }, { id: 'abcdef12', kind: 'confrontation', suspect: 'Z', evidence: [['E01', '']] },
    { id: 'abcdef12', kind: 'source', code: 'DG3', place: 'copec' }, { id: 'abcdef12', kind: 'source', code: 'DG11', place: 'mars' },
    null, 'x', {},
  ];
  for (const b of bad) assert.equal(sanitize(b, team), null, JSON.stringify(b));
  assert.equal(sanitize({ id: 'abcdef12', kind: 'procedure', code: 'DG9', target: 'B', alibi: 1 }, team).alibi, 1);
  const long = sanitize({ id: 'abcdef12', kind: 'witness', who: 'a'.repeat(500), text: 'b'.repeat(5000) }, team);
  assert.ok(long.who.length <= 80 && long.text.length <= 400, 'texts are cut');
  assert.equal(sanitize({ id: 'abcdef12', kind: 'question', code: 'B1', evil: '<script>' }, team).evil, undefined);
});

test('the same request sent again is the same request', () => {
  const book = newBook();
  const raw = { id: 'abcdef12', kind: 'follow_up', code: 'B1+' };
  assert.equal(receive(game, book, 'A', device('A'), raw).fresh, true);
  assert.equal(receive(game, book, 'A', device('A'), raw).fresh, false);
  assert.equal(book.requests.length, 1);
  assert.equal(receive(game, book, 'A', device('A'), { id: 'abcdef99', kind: 'bogus' }), null);
});

test('a team cannot ask without the tokens: what is waiting holds them back', () => {
  const book = newBook();
  const bal = () => balanceFor(game, book, 'A');
  const pending = [];
  const ask = (r) => canAsk(teamGame, bal(), pending, r);
  const q = { kind: 'procedure', code: 'DG3', target: 'B' };
  const n = bal().tokens;
  for (let i = 0; i < n; i++) { assert.ok(ask(q).ok, `request ${i + 1}`); pending.push({ ...q, id: rid(i) }); }
  assert.deepEqual(available(teamGame, bal(), pending), { tokens: 0, alibi: bal().alibi });
  assert.equal(ask(q).reason, 'tokens');
  assert.equal(ask({ kind: 'source', code: 'DG11', place: 'copec' }).ok, true, 'asking if the source exists is free');
  assert.equal(ask({ kind: 'procedure', code: 'DG9', target: 'B', alibi: 1 }).ok, true, 'an alibi token pays where it is accepted');
  assert.equal(ask({ kind: 'procedure', code: 'DG3', target: 'B', alibi: 1 }).reason, 'alibi', 'and only there');
  assert.equal(ask({ kind: 'procedure', code: 'DG9', target: 'B', alibi: 9 }).ok, false);
});

test('the scripted game of the v8 simulation ends with the folders and the tokens it ended with', () => {
  const book = newBook();
  const results = play(partida.steps, book);
  assert.equal(results.length, partida.steps.length);
  for (const { step, sg, res } of results) {
    sameSet(codes(res.record.delivered), step.gives, `${step.team} ${JSON.stringify(step.request)}`);
    assert.equal(sg.suggested, step.button, `the panel suggests the button the director pressed: ${JSON.stringify(step.request)}`);
  }
  for (const t of ['A', 'B', 'C']) assert.deepEqual(checkState(book.states[t]), [], `the tokens of ${t} add up`);
  const left = (t) => [book.states[t].tokens, book.states[t].alibi];
  const start = book.states.A.initial;
  assert.deepEqual(left('A'), [start.tokens - 7, start.alibi - 2]);
  assert.deepEqual(left('B'), [start.tokens - 4, start.alibi - 2]);
  assert.deepEqual(left('C'), [start.tokens - 6, start.alibi - 0]);
  for (const t of ['A', 'B', 'C']) {
    const gave = partida.steps.filter((s) => s.team === t).flatMap((s) => s.gives);
    sameSet(book.states[t].held.sheets.concat(book.states[t].held.cards), [...game.envelope(1), ...gave], `the folder of ${t}`);
  }
  assert.ok(medianSeconds(book) < 15, 'the register measures the time to answer');
});

test('the balance a team is told has its answered requests and no content', () => {
  const book = newBook();
  play(partida.steps, book);
  const b = balanceFor(game, book, 'A');
  assert.equal(b.hist.length, partida.steps.filter((s) => s.team === 'A').length);
  assert.deepEqual(b.open, []);
  assert.equal(b.tokens + b.hist.reduce((n, e) => n + e.charged.tokens, 0), b.initial.tokens, 'spent + left = initial');
  assert.ok(!JSON.stringify(b).includes('E26'), 'what was handed out does not travel with the balance');
});

test('the same request cannot be answered twice, and a charged answer without tokens is refused', () => {
  const book = newBook();
  const got = receive(game, book, 'A', device('A'), { id: 'abcdef12', kind: 'procedure', code: 'DG3', target: 'B' });
  const first = answer(game, book, got.record, 'give', {});
  assert.ok(first.ok);
  assert.equal(answer(game, book, got.record, 'give', {}).error, 'done');
  const poor = newBook();
  const state = teamState(game, poor, 'B');
  state.tokens = 0;
  state.initial = { ...state.initial };
  const r = receive(game, poor, 'B', device('B'), { id: 'abcdef34', kind: 'procedure', code: 'DG3', target: 'T' }).record;
  assert.equal(answer(game, poor, r, 'give', {}).error, 'not_enough_tokens');
  assert.equal(r.status, 'pending');
  assert.equal(poor.states.B.tokens, 0);
});

test('the panel: conditions, a witness by name, the cards of a confrontation and an edited handout', () => {
  const book = newBook();
  const rec = (raw) => receive(game, book, 'A', device('A'), raw).record;
  // H2+ needs E13b (and the card that enables it)
  const f = rec({ id: 'fup00001', kind: 'follow_up', code: 'H2+' });
  const sg = suggest(game, teamState(game, book, 'A'), f);
  assert.equal(sg.suggested, 'locked');
  assert.ok(sg.conditions.some((c) => c.role === 'needs' && c.code === 'E13b' && c.held === false));
  // a typed name or alias finds the witness; the one that has not appeared is not available
  assert.equal(matchWitness(game, 'don Juan, el colectivero').who, 'Juan Cifuentes, colectivero');
  assert.equal(matchWitness(game, 'conserje').name, 'Luis Riquelme');
  assert.equal(matchWitness(game, 'nadie conocido'), null);
  const w = rec({ id: 'wit00001', kind: 'witness', who: 'Luis Riquelme', detail: '', text: '' });
  assert.equal(suggest(game, teamState(game, book, 'A'), w).suggested, 'unavailable');
  assert.deepEqual(suggest(game, teamState(game, book, 'A'), w).conditions.map((c) => c.code), ['B1']);
  // the witness the director names, whatever the team typed
  const unknown = rec({ id: 'wit00002', kind: 'witness', who: 'el señor de la esquina', detail: '', text: '' });
  assert.equal(suggest(game, teamState(game, book, 'A'), unknown).error, 'unknown_witness');
  assert.equal(answer(game, book, unknown, 'give', {}).error, 'unknown_witness');
  assert.equal(suggest(game, teamState(game, book, 'A'), unknown, { who: 'Rosa Huenchumilla' }).suggested, 'give');
  // a confrontation waits for the card the director picks
  const c = rec({ id: 'con00001', kind: 'confrontation', suspect: 'B', evidence: [['E26·B', 'se fue']] });
  assert.equal(suggest(game, teamState(game, book, 'A'), c).buttons.find((b) => b.answer === 'give').why, 'no_card');
  assert.equal(suggest(game, teamState(game, book, 'A'), c).suggested, 'failed');
  const failed = answer(game, book, c, 'failed', {});
  assert.ok(failed.ok);
  assert.deepEqual(codes(failed.record.delivered), ['B✕']);
  // an edited handout: the director keeps back one of the sheets
  const e = rec({ id: 'edi00001', kind: 'witness', who: 'Rosa Huenchumilla', detail: 'E01', text: '' });
  const full = suggest(game, teamState(game, book, 'A'), e);
  assert.equal(full.suggested, 'give');
  const kept = answer(game, book, e, 'give', { keep: { cards: [], sheets: [] } });
  assert.ok(kept.ok);
  assert.deepEqual(codes(kept.record.delivered), []);
  assert.equal(book.states.A.held.cards.includes('R1'), false, 'what was not handed out is not held');
  assert.equal(book.states.A.tokens, book.states.A.initial.tokens - 2, 'but the answer is charged');
});

test('asking if a place has a source is free, and a manual delivery is held for the rules', () => {
  const book = newBook();
  const s = receive(game, book, 'A', device('A'), { id: 'src00001', kind: 'source', code: 'DG11', place: 'copec' }).record;
  const sg = suggest(game, teamState(game, book, 'A'), s);
  assert.equal(sg.suggested, 'yes');
  const r = answer(game, book, s, 'yes', {});
  assert.deepEqual(r.charged, { tokens: 0, alibi: 0 });
  book.states.A = holdItems(book.states.A, [['sheets/E20.html', 'E20'], ['cards/B5.html', 'B5']]);
  assert.ok(book.states.A.held.sheets.includes('E20') && book.states.A.held.cards.includes('B5'));
});

test('describe gives words for every kind', () => {
  const kinds = { question: { kind: 'question', code: 'B1' }, off: { kind: 'question', suspect: 'B', text: 'x' }, follow: { kind: 'follow_up', code: 'B1+' },
    witness: { kind: 'witness', who: 'X', detail: 'd', text: 't' }, conf: { kind: 'confrontation', suspect: 'B', evidence: [['E01', 'p']] },
    proc: { kind: 'procedure', code: 'DG3', target: 'B', text: 'z' }, src: { kind: 'source', code: 'DG11', place: 'copec' } };
  for (const [name, r] of Object.entries(kinds)) {
    const d = describe(team, r, tr);
    assert.ok(d.kind && d.what, name);
  }
});
