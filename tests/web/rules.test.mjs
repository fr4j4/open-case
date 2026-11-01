// Tests of site/play/js/rules.js against the engine. Run by tests/web/test_rules.py (node --test), with
//   OC_WEB_DIR   the folder of a compiled version (team.json, director.json)
//   OC_EXPECTED  tests/web_expected/<case>.json, written by pytest from the loaded case
import { test } from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { createGame, newState, hold, answers, resolve, quote, checkState, spareTokenScore, spent, norm, matchConfrontation } from '../../site/play/js/rules.js';

const read = (f) => JSON.parse(fs.readFileSync(f, 'utf8'));
const team = read(path.join(process.env.OC_WEB_DIR, 'team.json'));
const director = read(path.join(process.env.OC_WEB_DIR, 'director.json'));
const expected = read(process.env.OC_EXPECTED);
const game = createGame(team, director);
const fresh = () => newState(game);
const costs = expected.costs;

const allSheets = [...new Set([...director.sheets.map((s) => s.code), ...director.cards.flatMap((c) => c.attach),
  ...director.procedures.flatMap((p) => [p.gives, ...p.targets].filter(Boolean).flatMap((r) => r.sheets))])];
const everything = () => hold(fresh(), { sheets: allSheets, cards: director.cards.map((c) => c.code) });
/** A state that satisfies what a request needs (the card that enables a follow-up, the place where a witness appears). */
function ready(r) {
  let s = fresh();
  if (r.kind === 'follow_up') s = hold(s, { cards: r.mothers, sheets: r.unlocked_by.slice(0, 1) });
  if (r.kind === 'witness') s = hold(s, { sheets: r.appears_in.slice(0, 1) });
  return s;
}
const req = (r) => ({ kind: r.kind, code: r.code, suspect: r.suspect, card: r.card, who: r.who, target: r.target ?? undefined });
const same = (a, b) => assert.deepEqual(a.map(norm), b.map(norm));

// --- Parity with the engine ----------------------------------------------------------------------

test('the expected file lists every question, follow-up, witness, confrontation and procedure target', () => {
  const kinds = new Set(expected.requests.map((r) => r.kind));
  assert.deepEqual([...kinds].sort(), ['confrontation', 'follow_up', 'procedure', 'question', 'witness']);
  assert.equal(expected.requests.filter((r) => r.kind === 'question').length, expected.menu.length);
  assert.equal(expected.requests.filter((r) => r.kind === 'follow_up').length, Object.keys(expected.follow_ups).length);
  assert.equal(expected.requests.filter((r) => r.kind === 'witness').length, expected.witnesses.length);
  assert.equal(expected.requests.filter((r) => r.kind === 'confrontation').length, expected.cards.confrontation.length);
});

for (const [i, r] of expected.requests.entries()) {
  const name = `${r.kind} ${r.code ?? r.who ?? r.card}${r.target ? ' ' + r.target : ''}`;
  test(`parity: ${name} (#${i}) hands out and costs what the engine says`, () => {
    if (r.kind === 'witness') {
      let s = ready(r);
      for (const step of r.sequence) {
        const before = s.tokens;
        const res = resolve(game, s, req(r), 'give');
        assert.ok(res.ok, `${r.who}: ${res.error}`);
        same(res.delivers.cards, step.cards);
        same(res.delivers.sheets, step.sheets);
        assert.equal(before - res.state.tokens, r.cost);
        s = res.state;
      }
      const end = answers(game, s, req(r));
      assert.equal(end.find((a) => a.answer === 'give').available, false, 'no card left: a witness has nothing to add');
      assert.equal(end.find((a) => a.answer === 'nothing_to_add').available, true);
      return;
    }
    const s = ready(r);
    const q = quote(game, req(r));
    assert.deepEqual([q.min, q.max], [r.cost, r.cost], 'the quote');
    if (r.kind === 'procedure' && r.special) {   // "sin hallazgos" or an open request: it cannot hand out a fixed sheet
      assert.equal(answers(game, s, req(r)).find((a) => a.answer === 'give').available, false);
      const res = resolve(game, s, req(r), 'nothing_found');
      assert.ok(res.ok, res.error);
      assert.equal(res.cost, r.cost);
      assert.equal(s.tokens - res.state.tokens, r.cost);
      return;
    }
    const before = s.tokens;
    const res = resolve(game, s, req(r), 'give');
    assert.ok(res.ok, res.error);
    same(res.delivers.cards, r.cards ?? []);
    same(res.delivers.sheets, r.sheets);
    assert.equal(res.cost, r.cost);
    assert.equal(before - res.state.tokens, r.cost);
    // holding it already, the same request is answered without charging
    const again = answers(game, res.state, req(r));
    assert.equal(again.find((a) => a.answer === 'give').available, false);
    assert.equal(again.find((a) => a.answer === 'already_have').available, true);
  });
}

test('parity: the team device quotes a procedure by its code, from team.json alone', () => {
  const teamGame = createGame(team, null);
  for (const [code, p] of Object.entries(expected.procedures)) {
    const q = quote(teamGame, { kind: 'procedure', code });
    assert.deepEqual([q.min, q.max], [Math.min(...p.costs), Math.max(...p.costs)], code);
  }
  assert.deepEqual(answers(teamGame, fresh(), { kind: 'question', code: 'B1' }), { error: 'no_director' });
});

// --- What a request needs ------------------------------------------------------------------------

test('a follow-up needs a card that enables it and, when it has them, one of its unlocked_by sheets', () => {
  for (const r of expected.requests.filter((x) => x.kind === 'follow_up')) {
    assert.equal(answers(game, fresh(), req(r)).find((a) => a.answer === 'give').why, 'locked', r.code);
    if (r.unlocked_by.length) {
      const onlyCard = hold(fresh(), { cards: r.mothers });
      assert.equal(answers(game, onlyCard, req(r)).find((a) => a.answer === 'give').available, false, `${r.code}: the card alone`);
      for (const one of r.unlocked_by) {   // any one is enough
        const s = hold(fresh(), { cards: r.mothers, sheets: [one] });
        assert.equal(answers(game, s, req(r)).find((a) => a.answer === 'give').available, true, `${r.code} with ${one}`);
      }
    }
  }
});

test('a witness can be interviewed only when their name has appeared', () => {
  const isCard = (code) => director.cards.some((k) => k.code === code);
  for (const r of expected.requests.filter((x) => x.kind === 'witness')) {
    const a = answers(game, fresh(), req(r));
    assert.equal(a.find((x) => x.answer === 'give').why, 'unavailable', r.who);
    assert.equal(a.find((x) => x.answer === 'unavailable').available, true);
    for (const where of r.appears_in) {   // a sheet or a card, any one is enough
      const s = hold(fresh(), isCard(where) ? { cards: [where] } : { sheets: [where] });
      assert.equal(answers(game, s, req(r)).find((x) => x.answer === 'give').available, true, `${r.who} after ${where}`);
    }
  }
});

test('a confrontation hands out one card, can be repeated with another, and a wrong one is charged', () => {
  const [c1, c2] = expected.requests.filter((x) => x.kind === 'confrontation' && x.suspect === 'B');
  let s = fresh();
  const one = resolve(game, s, req(c1), 'give');
  const two = resolve(game, one.state, req(c2), 'give');
  assert.ok(one.ok && two.ok);
  assert.equal(spent(two.state).tokens, 2 * costs.confrontation);
  assert.equal(resolve(game, two.state, req(c1), 'give').error, 'already_have');
  const wrong = resolve(game, s, { kind: 'confrontation', suspect: 'B' }, 'failed');
  assert.ok(wrong.ok);
  same(wrong.delivers.cards, ['B✕']);
  assert.equal(wrong.cost, costs.confrontation);
  // a suspect with no failed card of their own gets the engine's wildcard
  const generic = resolve(game, s, { kind: 'confrontation', suspect: 'H' }, 'failed');
  same(generic.delivers.cards, [game.rules.wildcards.confrontation_failed]);
});

test('a request for what they already have, or with no basis, is not charged; "sin hallazgos" is', () => {
  const s = fresh();
  const none = { kind: 'procedure', code: 'DG11', target: 'karaoke' };
  const r = resolve(game, s, none, 'nothing_found');
  assert.equal(r.cost, 1);
  same(r.delivers.cards, [game.rules.wildcards.no_findings]);
  assert.equal(resolve(game, s, { kind: 'procedure', code: 'DG11', target: 'copec' }, 'nothing_found').error, 'there_is_something');
  const nb = resolve(game, s, { kind: 'procedure', code: 'DG11', target: 'copec' }, 'no_basis');
  assert.equal(nb.state.tokens, s.tokens);
  const held = hold(s, { sheets: ['E28'] });
  assert.equal(resolve(game, held, { kind: 'procedure', code: 'DG11', target: 'copec' }, 'give').error, 'already_have');
  assert.equal(resolve(game, held, { kind: 'procedure', code: 'DG11', target: 'copec' }, 'already_have').state.tokens, s.tokens);
});

test('asking whether a place has a camera is free and the answer follows the case', () => {
  for (const place of director.locations) {
    const a = answers(game, fresh(), { kind: 'source', code: 'DG11', place: place.id });
    assert.equal(a.find((x) => x.answer === 'yes').suggested, place.sources.length > 0, place.id);
    assert.ok(a.every((x) => x.cost === 0 && !x.charge));
  }
  assert.equal(answers(game, fresh(), { kind: 'source', code: 'DG9', place: 'copec' }).error, 'no_source_procedure');
});

// --- Tokens (rules 1 to 6 of the kit) --------------------------------------------------------------

function everyRequest() {
  const out = [];
  for (const r of expected.requests) out.push(req(r));
  for (const s of team.suspects) out.push({ kind: 'question', suspect: s.letter }, { kind: 'confrontation', suspect: s.letter });
  for (const p of expected.procedures ? Object.keys(expected.procedures) : []) {
    for (const loc of director.locations) out.push({ kind: 'source', code: p, place: loc.id });
  }
  return out;
}

test('every kind of request with every button charges what the rules say', () => {
  const seen = new Set();
  // nothing held; everything held; everything but the follow-ups (they can be asked); and that with every witness exhausted
  const noFollowUps = hold(fresh(), { sheets: allSheets, cards: director.cards.filter((c) => c.type !== 'follow-up').map((c) => c.code) });
  const exhausted = { ...noFollowUps, asked: Object.fromEntries(director.witnesses.map((w) => [w.who, w.cards.length])) };
  const states = [fresh(), everything(), noFollowUps, exhausted];
  for (const request of everyRequest()) {
    for (const s of states) {
      const list = answers(game, s, request);
      if (list.error) continue;
      for (const a of list) {
        const rule = game.rules.requests[request.kind].answers[a.answer];
        assert.ok(rule, `${request.kind}: ${a.answer} is not in rules.requests`);
        assert.equal(a.charge, rule.charge);
        if (!a.available) {
          assert.equal(resolve(game, s, request, a.answer).ok, false);
          continue;
        }
        seen.add(`${request.kind}:${a.answer}`);
        const r = resolve(game, s, request, a.answer);
        assert.ok(r.ok, `${request.kind} ${a.answer}: ${r.error}`);
        assert.equal(s.tokens - r.state.tokens, a.charge ? a.cost : 0, `${request.kind}:${a.answer}`);
        assert.deepEqual(checkState(r.state), []);
        assert.equal(r.state.tokens + spent(r.state).tokens, r.state.initial.tokens);
      }
    }
  }
  const want = Object.entries(game.rules.requests).flatMap(([k, r]) => Object.keys(r.answers).map((a) => `${k}:${a}`));
  assert.deepEqual(want.filter((x) => !seen.has(x)), [], 'a button that no request ever offers');
});

test('the balance never goes negative: a charged answer without tokens is refused and nothing changes', () => {
  let s = fresh();
  const q = { kind: 'confrontation', suspect: 'B' };
  for (let i = 0; i < s.initial.tokens; i++) s = resolve(game, s, q, 'failed').state;
  assert.equal(s.tokens, 0);
  const r = resolve(game, s, q, 'failed');
  assert.deepEqual([r.ok, r.error], [false, 'not_enough_tokens']);
  assert.equal(resolve(game, s, { kind: 'question', suspect: 'B' }, 'obvious').ok, true, 'a free answer does not need tokens');
  assert.deepEqual(checkState(s), []);
  // a request that costs 2 with 1 token left
  const one = { ...fresh(), tokens: 1 };
  const dear = resolve(game, one, { kind: 'procedure', code: 'DG10', target: 'deleted_message' }, 'give');
  assert.equal(dear.error, 'not_enough_tokens');
});

test('alibi tokens pay only a procedure the case marks, and spare numbered tokens score, alibi ones do not', () => {
  const s = fresh();
  const cam = { kind: 'procedure', code: 'DG11', target: 'copec' };
  const r = resolve(game, s, cam, 'give', { alibi: 1 });
  assert.ok(r.ok);
  assert.deepEqual([r.charged.tokens, r.charged.alibi], [0, 1]);
  assert.deepEqual([r.state.tokens, r.state.alibi], [s.tokens, s.alibi - 1]);
  for (const bad of [{ kind: 'procedure', code: 'DG3', target: 'B' }, { kind: 'question', code: 'B1' },
    { kind: 'confrontation', suspect: 'B', card: 'B5' }, { kind: 'witness', who: 'Rosa Huenchumilla' }]) {
    const t = hold(s, { sheets: ['E01'] });
    assert.equal(resolve(game, t, bad, 'give', { alibi: 1 }).error, 'alibi_not_accepted', bad.kind);
  }
  assert.equal(resolve(game, s, cam, 'no_basis', { alibi: 1 }).error, 'alibi_not_accepted', 'a free answer takes no token');
  assert.equal(resolve(game, s, cam, 'give', { alibi: 2 }).error, 'alibi_over_cost');
  assert.equal(resolve(game, { ...s, alibi: 0 }, cam, 'give', { alibi: 1 }).error, 'not_enough_tokens');
  // score: 16 numbered tokens left score 16 × spare_token; the alibi ones add nothing
  assert.equal(spareTokenScore(game, s), s.tokens * team.figures.score.spare_token);
  assert.equal(spareTokenScore(game, { ...s, alibi: 0 }), spareTokenScore(game, s));
});

test('random games: spent + left is always the starting tokens and the log adds up', () => {
  let seed = 7;
  const rnd = (n) => { seed = (seed * 1103515245 + 12345) & 0x7fffffff; return seed % n; };
  const requests = everyRequest();
  for (let g = 0; g < 40; g++) {
    let s = rnd(2) ? everything() : fresh();
    for (let step = 0; step < 120; step++) {
      const request = requests[rnd(requests.length)];
      const list = answers(game, s, request);
      if (list.error) continue;
      const a = list[rnd(list.length)];
      const alibi = a.charge && rnd(3) === 0 ? 1 : 0;
      const before = s;
      const r = resolve(game, s, request, a.answer, { alibi });
      if (r.ok) s = r.state; else assert.deepEqual(s, before, 'a refused request changes nothing');
      assert.deepEqual(checkState(s), []);
      assert.equal(s.tokens + spent(s).tokens, s.initial.tokens);
      assert.equal(s.alibi + spent(s).alibi, s.initial.alibi);
    }
  }
});

test('nothing is hard-coded: costs and alibi tokens come from rules', () => {
  const t2 = JSON.parse(JSON.stringify(team));
  const d2 = JSON.parse(JSON.stringify(director));
  for (const j of [t2, d2]) {
    j.rules.costs.question = 3;
    j.rules.requests.question.cost = 3;
    j.rules.alibi_procedures = ['DG3'];
  }
  const g2 = createGame(t2, d2);
  assert.equal(quote(g2, { kind: 'question', code: 'B1' }).min, 3);
  const r = resolve(g2, newState(g2), { kind: 'question', code: 'B1' }, 'give');
  assert.equal(r.cost, 3);
  assert.equal(resolve(g2, newState(g2), { kind: 'procedure', code: 'DG3', target: 'B' }, 'give', { alibi: 1 }).ok, true);
  assert.equal(resolve(g2, newState(g2), { kind: 'procedure', code: 'DG11', target: 'copec' }, 'give', { alibi: 1 }).error, 'alibi_not_accepted');
});

// --- Which card a confrontation opens (opens_with): the cases of the old guide table, written by hand ----------------

const golden = process.env.OC_CONFRONTATIONS ? read(process.env.OC_CONFRONTATIONS).cases : [];

test('the hand-written table of confrontations is there', () => {
  assert.ok(golden.length >= 50);
});

for (const g of golden) {
  test(`confrontation ${g.suspect}: ${g.evidence.join(' + ') || '(nothing)'}${g.held.length ? ` (holding ${g.held})` : ''} opens ${g.card ?? (g.candidates.join(' or ') || 'nothing')}`, () => {
    const state = hold(fresh(), { cards: g.held });
    const got = matchConfrontation(game, state, g.suspect, g.evidence.map((c) => [c, '']));
    assert.deepEqual(got, { card: g.card, candidates: g.candidates });
  });
}

test('a card the rules name is accepted by the confrontation, one of another suspect is not', () => {
  const state = fresh();
  assert.ok(answers(game, state, { kind: 'confrontation', suspect: 'B', card: 'B3+' }).find((a) => a.answer === 'give').available);
  assert.equal(answers(game, state, { kind: 'confrontation', suspect: 'B', card: 'B1+' }).error, 'unknown_card');
  assert.equal(answers(game, state, { kind: 'confrontation', suspect: 'B', card: 'H5' }).error, 'unknown_card');
});
