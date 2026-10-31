// The score sheet of a team (F5), as a pure module: the points are `figures.score` and `figures.hint_penalties` of the engine and
// the case's own line (`director.score.bonus`); the director marks what a team achieved (it is a judgement, as on the printed
// sheet) and this adds it up, with the numbered tokens that were left over and the hints that were asked for.
// Nothing here has a number of the game of its own. tests/web/score.test.mjs checks it against cifras that pytest works out
// from defaults.yaml.
//
//   const marks = newMarks();                       // what the director ticks for one team
//   const s = compute(game, marks, state, [1, 2]);  // { rows, total, canWin, spare, hints, … }
//   ranking(entries)                                 // [{ team, total, spent, … }] best first, with `tie`
import { spareTokenScore, spent as spentTokens } from './rules.js';

/** The accusation of a team: none, the culprit with a piece of evidence, the culprit without, or the wrong person. */
export const ACCUSATIONS = ['', 'culprit', 'culprit_no_evidence', 'wrong'];
const FLAGS = ['how', 'why', 'window', 'bonus', 'contradiction'];
const COUNTS = ['discard_two', 'discard_one', 'discard_blank', 'red_herring'];

export const newMarks = () => ({ accusation: '', how: false, why: false, window: false, bonus: false, contradiction: false,
  discard_two: 0, discard_one: 0, discard_blank: 0, red_herring: 0 });

/** Marks made well formed (a value that is not one of the expected is dropped), so a saved game with an old shape still works. */
export function cleanMarks(raw) {
  const m = newMarks();
  if (!raw || typeof raw !== 'object') return m;
  if (ACCUSATIONS.includes(raw.accusation)) m.accusation = raw.accusation;
  for (const k of FLAGS) m[k] = !!raw[k];
  for (const k of COUNTS) { const n = Math.floor(Number(raw[k])); m[k] = Number.isFinite(n) && n > 0 ? Math.min(n, 99) : 0; }
  return m;
}

/** The innocents of the case: its suspects less the culprit (the engine's rule: one suspect is guilty). */
export const innocents = (game) => Math.max(0, game.team.suspects.length - 1);

/** The lines of the sheet, in the order of the kit's score table: key, points each, and what is ticked (`flag`) or counted (`count`).
 * The case's own line (`bonus`) is only there when the case has one. */
export function lines(game) {
  const p = game.figures.score;
  const out = [
    { key: 'culprit', type: 'accusation', points: p.culprit, alt: p.culprit_no_evidence },
    { key: 'how', type: 'flag', points: p.how },
    { key: 'why', type: 'flag', points: p.why },
    { key: 'window', type: 'flag', points: p.window },
  ];
  const bonus = game.director && game.director.score && game.director.score.bonus;
  if (bonus) out.push({ key: 'bonus', type: 'flag', points: bonus.points, text: bonus.text });
  out.push({ key: 'contradiction', type: 'flag', points: p.contradiction },
    { key: 'discard_two', type: 'count', points: p.discard_two, max: innocents(game) },
    { key: 'discard_one', type: 'count', points: p.discard_one, max: innocents(game) },
    { key: 'discard_blank', type: 'count', points: p.discard_blank, max: innocents(game) },
    { key: 'red_herring', type: 'count', points: p.red_herring });
  return out;
}

/** The penalty of each hint asked for (`given`: the `n` of the hint cards, in the order they were handed out). A hint the case
 * has no penalty for (it has more cards than figures) cannot be asked for, so it costs nothing here. */
export function hintPenalty(game, n) {
  const hint = ((game.director && game.director.hints) || []).find((x) => x.n === n);
  const fromFigures = (game.figures.hint_penalties || [])[n - 1];
  const v = hint && hint.penalty != null ? hint.penalty : fromFigures;
  return Number.isFinite(Number(v)) ? Number(v) : 0;
}

/** Adds a sheet up. `state` is the team's rules state (its tokens), `given` the hints it asked for.
 * Returns { rows: [{key, points, times, subtotal}], spare, hints, wrong, total, canWin }.
 * - wrong accusation: `score.wrong_accusation` and the team cannot win;
 * - no accusation: only the tokens left over count (what the kit says: "solo suman las fichas que les sobren"); the hints still cost. */
export function compute(game, rawMarks, state, given = []) {
  const m = cleanMarks(rawMarks);
  const p = game.figures.score;
  const rows = [];
  const add = (key, points, times) => rows.push({ key, points, times, subtotal: points * times });
  if (m.accusation) {
    if (m.accusation === 'culprit') add('culprit', p.culprit, 1);
    if (m.accusation === 'culprit_no_evidence') add('culprit_no_evidence', p.culprit_no_evidence, 1);
    for (const l of lines(game)) {
      if (l.type === 'flag' && m[l.key]) add(l.key, l.points, 1);
      if (l.type === 'count' && m[l.key]) add(l.key, l.points, Math.min(m[l.key], l.max ?? 99));
    }
    if (m.accusation === 'wrong') add('wrong_accusation', p.wrong_accusation, 1);
  }
  const spare = state ? spareTokenScore(game, state) : 0;
  const hints = given.reduce((n, h) => n + hintPenalty(game, h), 0);
  const total = rows.reduce((n, r) => n + r.subtotal, 0) + spare - hints;
  return { rows, spare, hints, wrong: m.accusation === 'wrong', total, canWin: m.accusation === 'culprit' || m.accusation === 'culprit_no_evidence' };
}

/** The teams from first to last: those that can win first (more points, then fewer tokens spent), then the rest.
 * `tie` is true on the entry at the top when another team has the same points and spent the same: the clearest theory decides,
 * which only the director can judge. entries: [{ team, marks, state, given }]. */
export function ranking(game, entries) {
  const rows = entries.map((e) => {
    const s = compute(game, e.marks, e.state, e.given || []);
    return { team: e.team, ...s, spent: e.state ? spentTokens(e.state).tokens : 0 };
  });
  rows.sort((a, b) => (b.canWin - a.canWin) || (b.total - a.total) || (a.spent - b.spent) || a.team.localeCompare(b.team));
  const top = rows[0];
  rows.forEach((r, i) => { r.tie = i === 0 && !!top.canWin && rows.slice(1).some((x) => x.canWin && x.total === top.total && x.spent === top.spent); });
  return rows;
}

/** The hint a team gets next: the first card that it has not been given, or null when none is left. */
export function nextHint(game, given = []) {
  const hints = (game.director && game.director.hints) || [];
  return hints.find((h) => !given.includes(h.n)) || null;
}
