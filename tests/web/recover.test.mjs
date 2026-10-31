// Tests of site/play/js/recover.js (F6a): the backup file, the codes a phone shows, the registro a phone tells and the game that is
// made again from them. Run by tests/web/test_recover.py (node --test) with
//   OC_WEB_DIR  the folder of a compiled version (team.json, director.json)
//   OC_PARTIDA  tests/web/partidas/<game>.json: the scripted game of the v8 simulation (3 teams, 21 requests)
// The check that matters: a game played, "lost" and rebuilt from what the phones hold has the same balances, the same folders,
// the same answered requests and a state that still adds up (rules.js checkState).
import { test } from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { createGame, checkState, norm } from '../../site/play/js/rules.js';
import { receive, answer, balanceFor, newBook, teamState, holdItems } from '../../site/play/js/requests.js';
import { newClock, toPhase, start, wire } from '../../site/play/js/clock.js';
import * as R from '../../site/play/js/recover.js';

const read = (f) => JSON.parse(fs.readFileSync(f, 'utf8'));
const team = read(path.join(process.env.OC_WEB_DIR, 'team.json'));
const director = read(path.join(process.env.OC_WEB_DIR, 'director.json'));
const partida = read(process.env.OC_PARTIDA);
const game = createGame(team, director);
const TEAMS = ['A', 'B', 'C'];
const rid = (i) => `req${String(i).padStart(5, '0')}`;
const sorted = (xs) => [...xs].map(norm).sort();

// The director's game as the app keeps it: the book, the log of what was handed out and the phones' view of it.
function playGame() {
  const book = newBook();
  const log = [];
  let seq = 0;
  let now = 1_000_000;
  const hand = (tm, items) => { seq += 1; log.push({ seq, team: tm, items, at: now }); book.states[tm] = holdItems(teamState(game, book, tm, log), items); };
  partida.steps.forEach((s, i) => {
    now += 20_000;
    const got = receive(game, book, s.team, { id: `phone-${s.team}`, name: s.team }, { id: rid(i), ...s.request }, now);
    const res = answer(game, book, got.record, s.button, { card: s.choice?.card, who: s.choice?.who }, log, now + 4000);
    assert.ok(res.ok, `step ${i + 1}: ${res.error}`);
    if (res.items.length) hand(s.team, res.items);
  });
  // a hint to A and the first notice to everybody
  const hint = director.hints[0];
  const hintCard = director.cards.find((c) => c.code === hint.code);
  hand('A', [[hintCard.file, hintCard.code]]);
  const notice = director.notices.find((n) => n.kind === 'notice');
  const noticeCard = director.cards.find((c) => c.code === notice.code);
  for (const tm of TEAMS) hand(tm, [[noticeCard.file, noticeCard.code]]);
  return { book, log, seq, hint, notice };
}

// What a team's phone holds: its folder in the order of the deliveries, and the last balance the director told it.
function phoneOf(played, tm, device, clock) {
  const items = {};
  const order = [];
  let last = 0;
  for (const e of played.log.filter((x) => x.team === tm)) for (const [file, code] of e.items) { if (!items[file]) { items[file] = { file, code, group: 'folder', origin: 'delivery' }; order.push(file); } last = e.seq; }
  const bal = balanceFor(game, played.book, tm, played.log);
  const state = { team: tm, slug: 'chupacabras-labranza', lang: 'es', version: 'a95544c93896', seq: last, items, order };
  const reqs = { pending: [], bal, clock: clock || null, forms: {} };
  return { state, reqs, deviceId: device, name: `Tel ${device}` };
}

const tell = (phone, now = 2_000_000) => {
  // through the messages: split, shuffled, put together and checked, as the director does
  const reg = R.buildRegistro({ ...phone, now });
  const parts = R.splitRegistro(reg, 'r1abc');
  const asm = new R.Assembler();
  let out = null;
  for (const p of [...parts].reverse()) out = asm.add(phone.deviceId, p) || out;
  assert.ok(out, 'the registro comes together');
  return { parts: parts.length, reg: R.checkRegistro(out, game, phone.state.team) };
};

test('a game rebuilt from what the phones hold has the same balances, folders and answers, and still adds up', () => {
  const played = playGame();
  const clock = toPhase(team.figures, start(newClock(team.figures), 5_000), 'investigation', 5_000);
  const picks = {};
  for (const tm of TEAMS) {
    const { reg } = tell(phoneOf(played, tm, `dev${tm.toLowerCase()}000`, wire(clock, 2_000_000) && { phase: clock.phase, running: true, elapsed: 600_000, since: 1_000_000 }));
    assert.ok(reg, `the registro of ${tm} is accepted`);
    picks[tm] = reg;
  }
  const out = R.rebuild(game, picks, { teams: TEAMS, now: 3_000_000 });
  assert.deepEqual(out.warnings, [], 'nothing to warn about when the phones agree with their own balance');
  for (const tm of TEAMS) {
    const was = played.book.states[tm];
    const now = out.play.states[tm];
    assert.equal(now.tokens, was.tokens, `${tm}: tokens`);
    assert.equal(now.alibi, was.alibi, `${tm}: alibi tokens`);
    assert.deepEqual(sorted(now.held.sheets), sorted(was.held.sheets), `${tm}: sheets held`);
    assert.deepEqual(sorted(now.held.cards), sorted(was.held.cards), `${tm}: cards held`);
    assert.deepEqual(now.asked, was.asked, `${tm}: witnesses asked`);
    assert.deepEqual(checkState(now), [], `${tm}: the account adds up`);
    const ids = (b) => b.requests.filter((r) => r.team === tm).map((r) => [r.id, r.answer, r.charged.tokens, r.charged.alibi]);
    assert.deepEqual(ids(out.play), ids(played.book), `${tm}: the register of requests`);
    // the folder: every file handed out, once, in order
    const files = (log) => log.filter((e) => e.team === tm).flatMap((e) => e.items.map((i) => i[0]));
    assert.deepEqual([...new Set(out.log.filter((e) => e.team === tm).flatMap((e) => e.items.map((i) => i[0])))], [...new Set(files(played.log))]);
  }
  assert.equal(out.seq, played.seq - 0 || out.seq);
  assert.deepEqual(out.play.hints, { A: [played.hint.n] }, 'the hint given is the hint card the team holds');
  assert.ok(out.play.notices[played.notice.code], 'the notice that reached the teams is marked as read');
  assert.equal(out.play.clock.phase, 'investigation');
  assert.ok(out.play.clock.running);
  assert.deepEqual(out.play.marks, {}, 'the marks of the score are not in the phones');
  // the next request after the recovery is charged on the rebuilt state like on the original
  const next = { id: 'after0001', kind: 'procedure', code: 'DG2', text: 'otra' };
  const a = receive(game, played.book, 'C', { id: 'x', name: '' }, next, 9);
  const b = receive(game, out.play, 'C', { id: 'x', name: '' }, next, 9);
  const ra = answer(game, played.book, a.record, 'give', {}, played.log, 10);
  const rb = answer(game, out.play, b.record, 'give', {}, out.log, 10);
  assert.deepEqual([rb.ok, rb.charged], [ra.ok, ra.charged]);
  assert.equal(out.play.states.C.tokens, played.book.states.C.tokens);
});

test('a registro is cut in messages, put together in any order and checked: nothing forged gets in', () => {
  const played = playGame();
  const phone = phoneOf(played, 'A', 'phonea0001');
  const { parts, reg } = tell(phone);
  assert.equal(parts, 1, 'a short registro is one message');
  const big = phoneOf(played, 'A', 'phonea0002');
  for (let i = 0; i < 200; i++) { big.state.items[`cards/c${i}.html`] = { code: `C${i}` }; big.state.order.push(`cards/c${i}.html`); }
  const long = tell(big);
  assert.ok(long.parts >= 2, `a long registro goes in several messages (${long.parts})`);
  assert.equal(long.reg.delivered.length, big.state.order.length, 'and comes together whole');
  assert.equal(reg.hist.length, played.book.requests.filter((r) => r.team === 'A').length);
  // another team's registro, a made-up file, an unknown request and a bad device are dropped or refused
  const raw = R.buildRegistro({ ...phone, now: 1 });
  assert.equal(R.checkRegistro({ ...raw, team: 'B' }, game, 'A'), null, 'a registro for another team');
  assert.equal(R.checkRegistro({ ...raw, device: 'X' }, game, 'A'), null, 'a bad device id');
  assert.equal(R.checkRegistro({ ...raw, delivered: [['../../etc/passwd', 'x']] }, game, 'A'), null, 'a file outside the case folder');
  const forged = R.checkRegistro({ ...raw, hist: [{ id: 'abcdef12', req: { id: 'abcdef12', kind: 'procedure', code: 'DG99' }, answer: 'give', charged: { tokens: 1, alibi: 0 } },
    { id: 'abcdef13', req: { id: 'abcdef13', kind: 'procedure', code: 'DG3', target: 'B' }, answer: 'give', charged: { tokens: 99, alibi: 0 } }, { id: 'x', req: {}, answer: 'give', charged: 3 }] }, game, 'A');
  assert.equal(forged.hist.length, 1, 'only the request the case knows is kept');
  // a half registro never comes together, and a part with a wrong number is ignored
  const asm = new R.Assembler();
  const ps = R.splitRegistro({ ...raw, delivered: Array.from({ length: 250 }, (_, i) => [`cards/c${i}.html`, `C${i}`]) }, 'rid1');
  assert.ok(ps.length >= 2);
  assert.equal(asm.add('p', ps[0]), null);
  assert.equal(asm.add('p', { ...ps[0], i: 999 }), null);
  assert.equal(asm.add('p', { rid: 'r', i: 0, n: 1, d: 'not json' }), null);
});

test('two phones of a team that do not agree are shown as different and never merged', () => {
  const played = playGame();
  const full = tell(phoneOf(played, 'B', 'phoneb0001')).reg;
  const stale = phoneOf(played, 'B', 'phoneb0002');
  stale.reqs.bal = { ...stale.reqs.bal, hist: stale.reqs.bal.hist.slice(0, -1) };      // missed the last answer
  stale.state.order = stale.state.order.slice(0, -1);
  const behind = tell(stale).reg;
  const d = R.differences([full, behind]);
  assert.equal(d.same, false);
  assert.equal(d.phones[0].only.hist.length, 1, 'the complete one has an answer the other does not');
  assert.equal(d.phones[1].only.hist.length, 0);
  assert.ok(R.completeness(full) > R.completeness(behind), 'the one with more is proposed first');
  assert.equal(R.differences([full, tell(phoneOf(played, 'B', 'phoneb0003')).reg]).same, true, 'two phones that agree are not a difference');
  // what the director picks is what the game has: the stale registro gives one answer less
  const out = R.rebuild(game, { B: behind }, { teams: ['A', 'B'], now: 5 });
  assert.equal(out.play.requests.filter((r) => r.team === 'B').length, full.hist.length - 1);
  assert.deepEqual(out.play.states.A.tokens, game.rules.tokens_per_team ?? out.play.states.A.tokens, 'a team nobody recovered starts from scratch');
});

test('a request that was waiting comes back waiting, and a sheet handed in comes back handed in', () => {
  const played = playGame();
  const phone = phoneOf(played, 'C', 'phonec0001');
  phone.reqs.pending = [{ id: 'wait00001', kind: 'procedure', code: 'DG2', text: 'pendiente' }];
  phone.reqs.forms = { [team.forms[0].id]: { values: { 'f0.0': 'Hernán Carrasco', 'x.y': 'ignored' }, sent: true }, [team.forms[1].id]: { values: { 't0.0.0': 'borrador' }, sent: false } };
  const { reg } = tell(phone);
  const out = R.rebuild(game, { C: reg }, { teams: ['C'], now: 7 });
  const waiting = out.play.requests.find((r) => r.id === 'wait00001');
  assert.equal(waiting.status, 'pending');
  assert.equal(waiting.device, 'phonec0001');
  assert.deepEqual(Object.keys(out.play.forms.C), [team.forms[0].id], 'only the sheet that was handed in is a sheet handed in');
  assert.deepEqual(out.play.forms.C[team.forms[0].id].values, { 'f0.0': 'Hernán Carrasco' });
});

test('the backup file: a game goes out and comes back the same, and a forged one is refused', () => {
  const played = playGame();
  const g = { slug: 'chupacabras-labranza', lang: 'es', version: 'a95544c93896', teams: TEAMS, seq: played.seq, log: played.log, created: 5,
    play: { ...played.book, clock: newClock(team.figures), notices: { 'Aviso 1': 9 }, hints: { A: [1] }, forms: {}, marks: { A: { accusation: 'culprit', how: true } } },
    room: { pin: 'ABC234', id: 'dirabcd1', teamRooms: { A: 'oc-t-' + 'a'.repeat(20) }, devices: { phone0001: { id: 'phone0001', name: 'Tel', team: 'A', status: 'approved', joined: 1, seen: 2 } }, adopt: ['A'] } };
  const back = R.readBackup(R.makeBackup(g, 99));
  assert.ok(back.ok);
  assert.equal(back.at, 99);
  assert.deepEqual(back.game.log, g.log);
  assert.deepEqual(back.game.room, g.room);
  const clean = R.cleanPlay(back.game.play, game, TEAMS);
  for (const tm of TEAMS) {
    assert.equal(clean.states[tm].tokens, played.book.states[tm].tokens);
    assert.deepEqual(clean.states[tm].held, played.book.states[tm].held);
  }
  assert.equal(clean.requests.length, played.book.requests.length);
  assert.deepEqual(clean.marks.A, { accusation: 'culprit', how: true, why: false, window: false, bonus: false, contradiction: false, discard_two: 0, discard_one: 0, discard_blank: 0, red_herring: 0 });
  assert.deepEqual(clean.hints, { A: [1] });
  assert.equal(clean.clock.phase, newClock(team.figures).phase);
  // refused
  const ok = JSON.parse(R.makeBackup(g, 1));
  const mutate = (fn) => { const c = JSON.parse(JSON.stringify(ok)); fn(c); return JSON.stringify(c); };
  assert.equal(R.readBackup('not json').error, 'format');
  assert.equal(R.readBackup(mutate((c) => { c.format = 'x'; })).error, 'format');
  assert.equal(R.readBackup(mutate((c) => { c.version = 7; })).error, 'version');
  assert.equal(R.readBackup(mutate((c) => { c.game.slug = '../evil'; })).error, 'shape');
  assert.equal(R.readBackup(mutate((c) => { c.game.version = 'zzz'; })).error, 'shape');
  assert.equal(R.readBackup(mutate((c) => { c.game.log[0].items = [['http://evil/x.html', 'x']]; })).error, 'shape');
  assert.equal(R.readBackup(mutate((c) => { c.game.room.pin = 'abc'; })).error, 'shape');
  assert.equal(R.readBackup(mutate((c) => { c.game.teams = ['A', 'A']; })).error, 'shape');
  // dirty parts of the book are dropped
  const dirty = R.cleanPlay({ ...back.game.play, requests: [...back.game.play.requests, { id: 'forged001', team: 'A', req: { id: 'forged001', kind: 'procedure', code: 'ZZ' }, status: 'done', charged: { tokens: 0, alibi: 0 } }, { id: 'forged002', team: 'Z' }],
    states: { A: { tokens: -5, alibi: 'x', held: { sheets: [1, 'E01'], cards: 'no' } } } }, game, TEAMS);
  assert.equal(dirty.requests.length, played.book.requests.length);
  assert.equal(dirty.states.A.tokens, dirty.states.A.initial.tokens, 'a bad balance goes back to the start');
  assert.deepEqual(dirty.states.A.held, { sheets: ['E01'], cards: [] });
});

test('the recovery code a phone shows opens one team room; codes of different games are not mixed', () => {
  const session = { pin: 'ABC234', team: 'B', room: 'oc-t-' + 'q'.repeat(20), c: 'chupacabras-labranza', l: 'es', v: 'a95544c93896' };
  const link = R.recoveryLink('https://x.test/play/director/', session);
  assert.ok(link.startsWith('https://x.test/play/director/#recuperar.oc1r.'));
  const other = { ...session, team: 'A', room: 'oc-t-' + 'w'.repeat(20) };
  const text = `mira: ${link}\n${R.recoveryCode(other)} y ${R.recoveryCode(session)} oc1r.AAAA oc1r.${Buffer.from('{"p":"bad"}').toString('base64url')}`;
  const { codes, bad } = R.parseCodes(text);
  assert.equal(codes.length, 2, 'the same code twice is one');
  assert.equal(bad, 2);
  const g = R.gameFromCodes(codes);
  assert.deepEqual([g.pin, g.slug, g.teams, Object.keys(g.rooms).sort()], ['ABC234', 'chupacabras-labranza', ['A', 'B'], ['A', 'B']]);
  assert.equal(R.gameFromCodes([codes[0], { ...codes[1], pin: 'ZZZ234' }]).error, 'mixed');
  assert.equal(R.gameFromCodes([codes[0], { ...codes[0], room: 'oc-t-' + 'e'.repeat(20) }]).error, 'twice');
  assert.equal(R.gameFromCodes([]).error, 'none');
  assert.equal(R.parseCodes(R.recoveryCode({ ...session, room: 'oc-t-short' })).codes.length, 0, 'the room name is checked');
});
