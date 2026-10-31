// The director's side of the game (F5): the clock of the phases, the notices and the hints, and the score (the sheets the teams
// handed in, the points of each team, the ranking and the final report). It draws; the clock is js/clock.js, the points are
// js/score.js (over figures.score) and what is handed out goes through the same delivery as the rest (app.js `handOut`).
// `ui` = { dgame, book, teamJson, teams, log, clock actions…, redraw() } — see app.js.
import { h } from '../js/dom.js';
import { t, plural, language } from '../js/i18n.js';
import * as clock from '../js/clock.js';
import * as score from '../js/score.js';
import { teamState } from '../js/requests.js';

const teamBadge = (letter) => h('span', { class: `oc-badge oc-team-${letter}` }, letter);
const num = (n) => (Math.round(n * 100) / 100).toLocaleString(language());
const stamp = (ms) => new Date(ms).toLocaleTimeString(language(), { hour: '2-digit', minute: '2-digit' });

// --- The clock ---------------------------------------------------------------------------------------------------

export function clockCard(ui, now = Date.now()) {
  const figures = ui.teamJson.figures;
  const c = ui.book.clock;
  const list = clock.phases(figures);
  const left = clock.remainingMs(figures, c, now);
  return h('section', { class: 'oc-card', id: 'oc-clock-card', dataset: { phase: c.phase, running: String(c.running) } },
    h('div', { class: 'oc-row' }, h('strong', {}, t('game.clock.title')), h('span', { class: 'oc-grow' }),
      h('span', { class: 'oc-muted' }, t('game.clock.session', { min: (figures.session_minutes || []).join('–') }))),
    h('div', { class: 'oc-chips', role: 'group', 'aria-label': t('game.clock.phases') }, list.map((p) => h('button', {
      class: 'oc-chip', type: 'button', 'aria-pressed': String(c.phase === p.key), dataset: { phase: p.key },
      onclick: () => ui.clockDo('phase', p.key) }, `${t(`game.phase.${p.key}`)} · ${p.minutes} min`))),
    h('p', {}, h('strong', { id: 'oc-clock-time', style: 'font-size:2rem;font-family:var(--mono,monospace)' }, left >= 0 ? clock.format(left) : `${t('game.clock.over_short')} ${clock.format(-left)}`),
      ' ', h('span', { class: 'oc-muted' }, c.running ? t('game.clock.running') : t('game.clock.paused'))),
    c.phase === clock.INVESTIGATION ? h('p', { class: 'oc-muted', id: 'oc-clock-minute' }, t('game.clock.minute', { n: Math.floor(clock.investigationMinute(c, now)) })) : null,
    h('p', { class: 'oc-muted' }, clock.canRequest(c) ? t('game.clock.asking_open') : t('game.clock.asking_closed')),
    h('div', { class: 'oc-row' },
      c.running ? h('button', { class: 'oc-btn oc-btn--small', type: 'button', id: 'oc-clock-pause', onclick: () => ui.clockDo('pause') }, t('game.clock.pause'))
        : h('button', { class: 'oc-btn oc-btn--small', type: 'button', id: 'oc-clock-start', onclick: () => ui.clockDo('start') }, t('game.clock.start')),
      h('button', { class: 'oc-btn oc-btn--small oc-btn--ghost', type: 'button', id: 'oc-clock-next', onclick: () => ui.clockDo('next') }, t('game.clock.next')),
      h('button', { class: 'oc-btn oc-btn--small oc-btn--ghost', type: 'button', dataset: { shift: '-60' }, onclick: () => ui.clockDo('shift', -60000) }, t('game.clock.back')),
      h('button', { class: 'oc-btn oc-btn--small oc-btn--ghost', type: 'button', dataset: { shift: '60' }, onclick: () => ui.clockDo('shift', 60000) }, t('game.clock.forward'))));
}

/** Refreshes only the numbers of the clock card (once a second). */
export function tickClock(ui, now = Date.now()) {
  const figures = ui.teamJson.figures;
  const c = ui.book.clock;
  const el = document.getElementById('oc-clock-time');
  if (!el) return;
  const left = clock.remainingMs(figures, c, now);
  el.textContent = left >= 0 ? clock.format(left) : `${t('game.clock.over_short')} ${clock.format(-left)}`;
  const m = document.getElementById('oc-clock-minute');
  if (m && c.phase === clock.INVESTIGATION) m.textContent = t('game.clock.minute', { n: Math.floor(clock.investigationMinute(c, now)) });
}

// --- Notices and press -------------------------------------------------------------------------------------------

export function noticesCard(ui, now = Date.now()) {
  const notices = ui.dgame.director.notices;
  if (!notices.length) return null;
  const read = ui.book.notices || {};
  const only = notices.filter((n) => n.kind === 'notice');
  const due = clock.due(only, ui.book.clock, now, only.filter((n) => read[n.code]).map((n) => n.n)).map((n) => n.n);
  return h('section', { class: 'oc-card', id: 'oc-notices' },
    h('h3', {}, t('game.notices.title')), h('p', { class: 'oc-muted' }, t('game.notices.help')),
    notices.map((n, i) => {
      const read = ui.book.notices && ui.book.notices[n.code];
      const label = n.kind === 'press' ? t('game.notices.press') : t('game.notices.notice', { n: n.n });
      const isDue = !read && n.kind === 'notice' && due.includes(n.n);
      return h('div', { class: 'oc-row', dataset: { notice: n.code, due: String(isDue), read: String(!!read) }, style: 'align-items:flex-start;padding:6px 0' },
        h('div', { class: 'oc-grow' }, h('strong', {}, `${n.code} · ${label}`), ' ', h('small', { class: 'oc-muted' }, n.headline),
          h('div', { class: 'oc-muted' }, read ? t('game.notices.read_at', { time: stamp(read) }) : isDue ? t('game.notices.due', { minute: n.minute }) : t('game.notices.suggested', { minute: n.minute }))),
        h('button', { class: `oc-btn oc-btn--small${isDue ? '' : ' oc-btn--ghost'}`, type: 'button', dataset: { sendNotice: n.code }, onclick: () => ui.sendNotice(n) }, read ? t('game.notices.again') : t('game.notices.send')));
    }));
}

// --- Hints -------------------------------------------------------------------------------------------------------

export function hintsCard(ui) {
  const hints = ui.dgame.director.hints;
  if (!hints.length) return null;
  return h('section', { class: 'oc-card', id: 'oc-hints' }, h('h3', {}, t('game.hints.title')), h('p', { class: 'oc-muted' }, t('game.hints.help')),
    ui.teams.map((tm) => {
      const given = (ui.book.hints && ui.book.hints[tm]) || [];
      const nx = score.nextHint(ui.dgame, given);
      return h('div', { class: 'oc-row', dataset: { hintTeam: tm } }, teamBadge(tm),
        h('span', { class: 'oc-grow' }, plural('game.hints.given', given.length, { n: given.length, of: hints.length }),
          given.length ? h('small', { class: 'oc-muted' }, ` · ${t('game.hints.cost', { n: num(given.reduce((a, g) => a + score.hintPenalty(ui.dgame, g), 0)) })}`) : null),
        h('button', { class: 'oc-btn oc-btn--small oc-btn--ghost', type: 'button', disabled: !nx, dataset: { giveHint: tm }, onclick: () => ui.giveHint(tm, nx) },
          nx ? t('game.hints.give', { penalty: num(score.hintPenalty(ui.dgame, nx.n)) }) : t('game.hints.none_left')));
    }));
}

export function gameView(ui) {
  return h('div', {}, h('p', { class: 'oc-muted' }, t('game.help')), clockCard(ui), noticesCard(ui), hintsCard(ui));
}

// --- Score ---------------------------------------------------------------------------------------------------------

const formTitle = (ui, id) => ((ui.teamJson.forms || []).find((f) => f.id === id) || { title: id }).title;

/** What a team wrote in one sheet, as the sheet is laid out (the labels of the kit). */
function submitted(ui, team, form, rec) {
  const v = rec.values || {};
  const out = [];
  form.parts.forEach((part, p) => {
    if (part.kind === 'fields') part.items.forEach((f, i) => out.push(h('div', { class: 'oc-answerline' }, h('strong', {}, f.label), h('div', {}, v[`f${p}.${i}`] || h('em', { class: 'oc-muted' }, '—')))));
    else part.rows.forEach((row, r) => out.push(h('div', { class: 'oc-answerline' }, h('strong', {}, row),
      part.columns.slice(1).map((col, c) => h('div', {}, h('small', { class: 'oc-muted' }, `${col}: `), v[`t${p}.${r}.${c}`] || '—')))));
  });
  return out;
}

function formsOf(ui, team) {
  const got = (ui.book.forms && ui.book.forms[team]) || {};
  const forms = ui.teamJson.forms || [];
  if (!forms.length) return null;
  return h('div', {}, forms.map((form) => {
    const rec = got[form.id];
    return h('details', { class: 'oc-details', dataset: { form: form.id, received: String(!!rec) } },
      h('summary', {}, form.title, ' · ', rec ? t('game.score.received', { time: stamp(rec.at) }) : t('game.score.not_received')),
      rec ? submitted(ui, team, form, rec) : null);
  }));
}

function marksControls(ui, team, marks, total) {
  const game = ui.dgame;
  const set = (patch) => ui.setMarks(team, { ...marks, ...patch });
  const acc = h('div', { class: 'oc-chips', role: 'group', dataset: { accusation: team } }, score.ACCUSATIONS.map((a) => h('button', {
    class: 'oc-chip', type: 'button', 'aria-pressed': String(marks.accusation === a), dataset: { acc: a || 'none' },
    onclick: () => set({ accusation: a }) }, t(`game.score.acc.${a || 'none'}`))));
  const rows = score.lines(game).filter((l) => l.key !== 'culprit').map((l) => {
    const label = l.key === 'bonus' ? l.text : t(`game.score.line.${l.key}`);
    if (l.type === 'flag') {
      return h('label', { class: 'oc-sel', style: 'min-height:40px' }, h('input', { type: 'checkbox', checked: marks[l.key], dataset: { mark: l.key }, onchange: (e) => set({ [l.key]: e.target.checked }) }),
        h('span', {}, label, ' ', h('small', { class: 'oc-muted' }, t('game.score.each', { n: num(l.points) }))));
    }
    return h('label', { class: 'oc-field' }, `${label} (${t('game.score.each', { n: num(l.points) })})`,
      h('input', { class: 'oc-input', type: 'number', min: '0', max: String(l.max ?? 99), step: '1', value: String(marks[l.key]), dataset: { mark: l.key }, style: 'max-width:6rem',
        onchange: (e) => set({ [l.key]: e.target.value }) }));
  });
  return [acc, marks.accusation ? rows : h('p', { class: 'oc-muted' }, t('game.score.no_accusation'))];
}

function teamScore(ui, team) {
  const game = ui.dgame;
  const marks = score.cleanMarks(ui.book.marks && ui.book.marks[team]);
  const state = teamState(game, ui.book, team, ui.log);
  const given = (ui.book.hints && ui.book.hints[team]) || [];
  const s = score.compute(game, marks, state, given);
  const tokens = state.tokens;
  return h('section', { class: `oc-card oc-team-${team}`, dataset: { scoreTeam: team } },
    h('div', { class: 'oc-row' }, teamBadge(team), h('strong', {}, t('game.score.team', { team })), h('span', { class: 'oc-grow' }),
      h('strong', { class: 'oc-total', dataset: { total: String(s.total) } }, plural('game.score.points', s.total, { n: num(s.total) }))),
    formsOf(ui, team),
    marksControls(ui, team, marks, s.total),
    h('p', { class: 'oc-muted' }, t('game.score.spare', { tokens, each: num(game.figures.score.spare_token), pts: num(s.spare) })),
    given.length ? h('p', { class: 'oc-muted' }, t('game.score.hints', { n: given.length, pts: num(s.hints) })) : null,
    s.wrong ? h('p', { class: 'oc-notice oc-notice--bad' }, t('game.score.cannot_win')) : null);
}

export function ranking(ui) {
  const game = ui.dgame;
  const entries = ui.teams.map((team) => ({ team, marks: ui.book.marks && ui.book.marks[team], state: teamState(game, ui.book, team, ui.log), given: (ui.book.hints && ui.book.hints[team]) || [] }));
  return score.ranking(game, entries);
}

export function scoreView(ui) {
  const rank = ranking(ui);
  const accused = rank.some((r) => r.canWin);
  const top = rank[0];
  return h('div', {}, h('p', { class: 'oc-muted' }, t('game.score.help')),
    h('section', { class: 'oc-card', id: 'oc-ranking' }, h('h3', {}, t('game.score.ranking')),
      rank.map((r, i) => h('div', { class: 'oc-row', dataset: { rank: String(i + 1), team: r.team, total: String(r.total), canWin: String(r.canWin) } }, `${i + 1}.`, teamBadge(r.team),
        h('span', { class: 'oc-grow' }, plural('game.score.points', r.total, { n: num(r.total) }), r.canWin ? '' : ` · ${t('game.score.no_win')}`)),
      ),
      accused ? (top.tie ? h('p', { class: 'oc-notice', id: 'oc-tie' }, t('game.score.tie')) : h('p', { id: 'oc-winner' }, t('game.score.winner', { team: top.team }))) : h('p', { class: 'oc-notice', id: 'oc-no-winner' }, t('game.score.nobody')),
      h('button', { class: 'oc-btn oc-btn--small', type: 'button', id: 'oc-report', onclick: () => ui.downloadReport() }, t('game.report.download'))),
    ui.teams.map((tm) => teamScore(ui, tm)));
}

// --- Final report ----------------------------------------------------------------------------------------------------

/** The report of the game, as Markdown: the score of each team, what it asked and what it was handed. A pure function of the
 * director's book and the game's log (and the words of the app). */
export function reportText(ui, now = Date.now()) {
  const game = ui.dgame;
  const L = [];
  L.push(`# ${t('game.report.title', { case: ui.teamJson.texts.title })}`, '', t('game.report.date', { date: new Date(now).toLocaleString(language()) }), '');
  const rank = ranking(ui);
  L.push(`## ${t('game.score.ranking')}`, '');
  rank.forEach((r, i) => L.push(`${i + 1}. ${t('game.score.team', { team: r.team })}: ${num(r.total)}${r.canWin ? '' : ` (${t('game.score.no_win')})`}`));
  L.push('');
  for (const tm of ui.teams) {
    const marks = score.cleanMarks(ui.book.marks && ui.book.marks[tm]);
    const state = teamState(game, ui.book, tm, ui.log);
    const given = (ui.book.hints && ui.book.hints[tm]) || [];
    const s = score.compute(game, marks, state, given);
    L.push(`## ${t('game.score.team', { team: tm })}`, '', `**${plural('game.score.points', s.total, { n: num(s.total) })}**`, '');
    L.push(`| ${t('game.report.line')} | ${t('game.report.times')} | ${t('game.report.points')} |`, '|---|---|---|');
    for (const r of s.rows) L.push(`| ${t(`game.score.line.${r.key}`) === `game.score.line.${r.key}` ? r.key : t(`game.score.line.${r.key}`)} | ${r.times} | ${num(r.subtotal)} |`);
    L.push(`| ${t('game.score.spare_short')} | ${state.tokens} | ${num(s.spare)} |`);
    if (s.hints) L.push(`| ${t('game.score.hints_short')} | ${given.length} | −${num(s.hints)} |`);
    L.push('');
    const reqs = ui.book.requests.filter((r) => r.team === tm);
    L.push(`### ${t('game.report.requests', { n: reqs.length })}`, '');
    for (const r of reqs.sort((a, b) => a.at - b.at)) {
      const spent = r.charged ? r.charged.tokens + r.charged.alibi : 0;
      L.push(`- ${stamp(r.at)} · ${r.req.kind} ${r.req.code || r.req.target || r.req.who || ''} → ${r.status === 'done' ? `${r.answer} (${spent})` : t('requests.pending')}`);
    }
    L.push('');
    const items = [];
    for (const e of ui.log) if (e.team === tm) for (const [, code] of e.items) if (code) items.push(code);
    L.push(`### ${t('game.report.handed')}`, '', items.length ? [...new Set(items)].join(', ') : '—', '');
    const got = (ui.book.forms && ui.book.forms[tm]) || {};
    for (const form of ui.teamJson.forms || []) {
      if (!got[form.id]) continue;
      L.push(`### ${form.title}`, '');
      for (const line of submitted(ui, tm, form, got[form.id])) L.push(`- ${line.textContent.replace(/\s+/g, ' ').trim()}`);
      L.push('');
    }
  }
  return L.join('\n');
}
