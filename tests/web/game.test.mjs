// Tests of site/play/js/clock.js and score.js (F5). Run by tests/web/test_game.py (node --test), with
//   OC_WEB_DIR  the folder of a compiled version (team.json, director.json)
//   OC_GAME     a JSON that pytest works out from opencase/defaults.yaml, apart from the JS: the phases and the scripted game
//               (marks and tokens left of three teams) with the total each must get
import { test } from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { createGame, newState } from '../../site/play/js/rules.js';
import * as clock from '../../site/play/js/clock.js';
import * as score from '../../site/play/js/score.js';
import { sanitize, canAsk, newBook, receive, answer, teamState } from '../../site/play/js/requests.js';

const read = (f) => JSON.parse(fs.readFileSync(f, 'utf8'));
const team = read(path.join(process.env.OC_WEB_DIR, 'team.json'));
const director = read(path.join(process.env.OC_WEB_DIR, 'director.json'));
const expected = read(process.env.OC_GAME);
const game = createGame(team, director);
const figures = team.figures;
const MIN = 60000;

test('the phases and their minutes are the figures of the case (defaults.yaml, plus what the case changes)', () => {
  assert.deepEqual(clock.phases(figures).map((p) => [p.key, p.minutes]), expected.phases);
  for (const [key, minutes] of expected.phases) assert.equal(clock.minutesOf(figures, key), minutes);
});

test('the clock counts, pauses, advances and jumps phases only when the director says so', () => {
  let c = clock.newClock(figures);
  assert.equal(c.phase, expected.phases[0][0]);
  assert.equal(c.running, false);
  assert.equal(clock.elapsedMs(c, 5 * MIN), 0, 'it does not count before it starts');
  c = clock.start(c, 0);
  assert.equal(clock.elapsedMs(c, 90_000), 90_000);
  c = clock.pause(c, 120_000);
  assert.equal(clock.elapsedMs(c, 9_999_999), 120_000, 'a pause stops it');
  c = clock.start(c, 1_000_000);
  assert.equal(clock.elapsedMs(c, 1_030_000), 150_000);
  c = clock.shift(c, 60_000, 1_030_000);
  assert.equal(clock.elapsedMs(c, 1_030_000), 210_000, 'advance moves it forward');
  c = clock.shift(c, -10 * MIN, 1_030_000);
  assert.equal(clock.elapsedMs(c, 1_030_000), 0, 'it never goes below 0');
  const inv = expected.phases.find(([k]) => k === 'investigation')[1];
  c = clock.toPhase(figures, c, 'investigation', 2_000_000);
  assert.equal(c.phase, 'investigation');
  assert.equal(clock.remainingMs(figures, c, 2_000_000), inv * MIN);
  assert.equal(clock.remainingMs(figures, c, 2_000_000 + 7 * MIN), (inv - 7) * MIN);
  assert.equal(Math.floor(clock.investigationMinute(c, 2_000_000 + 7.5 * MIN)), 7);
  assert.ok(clock.remainingMs(figures, c, 2_000_000 + (inv + 1) * MIN) < 0, 'it can run over: the director decides when to move on');
  assert.equal(clock.format(-61_000), '−1:01');
  const keys = expected.phases.map(([k]) => k);
  let n = clock.newClock(figures);
  for (let i = 1; i < keys.length; i++) { n = clock.next(figures, n, 0); assert.equal(n.phase, keys[i]); }
  assert.equal(clock.next(figures, n, 0).phase, keys[keys.length - 1], 'the last phase stays');
  assert.equal(clock.toPhase(figures, n, 'nope', 0), n);
});

test('a team may ask only in the investigation (rule 1 of the kit)', () => {
  const allowed = expected.phases.map(([k]) => [k, clock.canRequest({ ...clock.newClock(figures), phase: k })]).filter(([, ok]) => ok).map(([k]) => k);
  assert.deepEqual(allowed, ['investigation']);
  const bal = { tokens: 10, alibi: 0 };
  const menu = team.menu[0];
  const req = sanitize({ id: 'req00001', kind: 'question', code: menu.code }, team);
  assert.ok(canAsk(game, bal, [], req).ok);
  assert.deepEqual(canAsk(game, bal, [], req, false), { ok: false, reason: 'phase' });
  // the director refuses to answer outside the investigation, and answers inside it
  const book = newBook();
  const got = receive(game, book, 'A', { id: 'p', name: '' }, req, 1000);
  book.clock = { ...clock.newClock(figures), phase: 'scene' };
  assert.deepEqual(answer(game, book, got.record, 'give'), { ok: false, error: 'phase' });
  assert.equal(teamState(game, book, 'A').tokens, bal.tokens > 0 ? teamState(game, book, 'A').tokens : 0);
  const before = teamState(game, book, 'A').tokens;
  book.clock = clock.toPhase(figures, book.clock, 'investigation', 0);
  const ok = answer(game, book, got.record, 'give');
  assert.ok(ok.ok, ok.error);
  assert.equal(teamState(game, book, 'A').tokens, before - expected.question_cost);
});

test('notices are suggested at the minutes of the case, only in the investigation and only until they are read', () => {
  const only = director.notices.filter((n) => n.kind === 'notice');
  assert.deepEqual(only.map((n) => n.minute), expected.notice_minutes);
  let c = clock.toPhase(figures, clock.newClock(figures), 'scene', 0);
  assert.deepEqual(clock.due(only, c, 99 * MIN), [], 'not during the scene');
  c = clock.toPhase(figures, c, 'investigation', 0);
  assert.deepEqual(clock.due(only, c, 0), []);
  const first = expected.notice_minutes[0];
  assert.deepEqual(clock.due(only, c, first * MIN).map((n) => n.n), [1]);
  assert.deepEqual(clock.due(only, c, first * MIN, [1]), [], 'read: no longer suggested');
  assert.equal(clock.due(only, c, (expected.notice_minutes[1] + 1) * MIN, [1]).length, 1);
});

test('what travels to the phones is the phase and the time gone by, counted from the phone own clock', () => {
  let c = clock.toPhase(figures, clock.newClock(figures), 'investigation', 5000);
  const w = clock.wire(c, 5000 + 3 * MIN);
  assert.deepEqual(w, { phase: 'investigation', running: true, elapsedMs: 3 * MIN });
  const p = clock.fromWire(figures, w, 777_000);
  assert.equal(clock.elapsedMs(p, 777_000 + MIN), 4 * MIN, 'the phone adds what passes on its own clock');
  assert.equal(clock.fromWire(figures, { phase: 'x', running: true, elapsedMs: 0 }, 0), null);
  assert.equal(clock.fromWire(figures, { phase: 'scene', running: true, elapsedMs: -5 }, 0), null);
  assert.equal(clock.fromWire(figures, { phase: 'scene', running: true, elapsedMs: 'a' }, 0), null);
  assert.equal(clock.fromWire(figures, null, 0), null);
});

const stateWith = (left) => ({ ...newState(game), tokens: left });

test('the score of the scripted game is the one worked out apart from the JS with the figures of defaults.yaml', () => {
  const rank = [];
  for (const s of expected.teams) {
    const got = score.compute(game, s.marks, stateWith(s.tokens_left), s.hints);
    assert.equal(got.total, s.total, `team ${s.team}`);
    assert.equal(got.canWin, s.can_win, `team ${s.team} can win`);
    rank.push({ team: s.team, marks: s.marks, state: stateWith(s.tokens_left), given: s.hints });
  }
  const order = score.ranking(game, rank);
  assert.deepEqual(order.map((r) => r.team), expected.ranking);
  assert.equal(order[0].tie, false);
});

test('ties: more points, then fewer tokens spent; the same of both is for the director to judge', () => {
  const marks = { ...score.newMarks(), accusation: 'culprit' };
  const mk = (team, left) => ({ team, marks, state: stateWith(left), given: [] });
  assert.deepEqual(score.ranking(game, [mk('A', 3), mk('B', 3)]).map((r) => r.tie), [true, false]);
  assert.deepEqual(score.ranking(game, [mk('A', 3), mk('B', 3 + 4)]).map((r) => [r.team, r.tie]), [['B', false], ['A', false]], 'more points win');
  // same points, different tokens spent: the cheaper one wins (spare tokens give points, so make the points equal with a mark)
  const a = { team: 'A', marks: { ...marks, how: true }, state: stateWith(10), given: [] };
  const spare = figures.score.spare_token;
  const b = { team: 'B', marks: marks, state: stateWith(10 + figures.score.how / spare), given: [] };
  const r = score.ranking(game, [a, b]);
  assert.equal(r[0].total, r[1].total);
  assert.equal(r[0].team, 'B', 'B spent fewer tokens');
  assert.equal(r[0].tie, false);
});

test('a wrong accusation cannot win; no accusation only counts the tokens left; marks that are not well formed are cleaned', () => {
  const wrong = score.compute(game, { ...score.newMarks(), accusation: 'wrong', how: true }, stateWith(4), []);
  assert.equal(wrong.canWin, false);
  assert.equal(wrong.total, figures.score.how + figures.score.wrong_accusation + 4 * figures.score.spare_token);
  const none = score.compute(game, { ...score.newMarks(), how: true, why: true }, stateWith(4), []);
  assert.equal(none.total, 4 * figures.score.spare_token);
  const rank = score.ranking(game, [{ team: 'A', marks: { accusation: 'wrong' }, state: stateWith(16), given: [] }, { team: 'B', marks: {}, state: stateWith(0), given: [] }]);
  assert.equal(rank.every((r) => !r.canWin), true, 'if everybody fails there is no winner');
  const m = score.cleanMarks({ accusation: 'nonsense', how: 'yes', discard_two: -3, discard_one: '2', red_herring: 1e9, extra: 1 });
  assert.deepEqual(m, { ...score.newMarks(), how: true, discard_one: 2, red_herring: 99 });
  assert.deepEqual(score.cleanMarks(null), score.newMarks());
  // the discard counts never go over the innocents of the case
  const all = score.compute(game, { ...score.newMarks(), accusation: 'culprit', discard_two: 50 }, stateWith(0), []);
  assert.equal(all.rows.find((r) => r.key === 'discard_two').times, score.innocents(game));
});

test('hints cost what the figures say, in order; the next hint is the first not given', () => {
  const pens = figures.hint_penalties;
  assert.deepEqual(director.hints.map((h) => score.hintPenalty(game, h.n)), pens.slice(0, director.hints.length));
  assert.equal(score.nextHint(game, []).n, 1);
  assert.equal(score.nextHint(game, [1, 2]).n, 3);
  assert.equal(score.nextHint(game, director.hints.map((h) => h.n)), null);
  const s = score.compute(game, score.newMarks(), stateWith(0), [1, 4]);
  assert.equal(s.hints, pens[0] + pens[3]);
});

test('the sheet lines are those of the engine and the case: the case line (bonus) only when the case has one', () => {
  const keys = score.lines(game).map((l) => l.key);
  assert.deepEqual(keys, expected.lines);
});
