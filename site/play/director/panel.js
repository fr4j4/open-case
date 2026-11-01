// The director's panel of requests (F4b): the queue of every team's requests in order of arrival, each with what the case
// suggests, and the register of all of them (it replaces the printed control sheet). It draws; what a request is worth and
// how it is answered is js/requests.js over js/rules.js. `ui` = { dgame, book, teamJson, log, choices, answer(rec, button, options), redraw() }.
import { h } from '../js/dom.js';
import { t, plural, language } from '../js/i18n.js';
import { describe, suggest, matchWitness, medianSeconds, teamState, confrontationCards } from '../js/requests.js';
import { acceptsAlibi, norm } from '../js/rules.js';

const time = (ms) => new Date(ms).toLocaleTimeString(language(), { hour: '2-digit', minute: '2-digit', second: '2-digit' });
const teamBadge = (letter) => h('span', { class: `oc-badge oc-team-${letter}` }, letter);
const BUTTONS = ['give', 'yes', 'no', 'obvious', 'nothing_found', 'no_basis', 'already_have', 'locked', 'unavailable', 'nothing_to_add', 'failed'];

export const pendingList = (book) => book.requests.filter((r) => r.status === 'pending').sort((a, b) => a.at - b.at);

/** What the card shows about one request: the choices the director makes (witness, card, sheets, alibi, note, what to hand out). */
function choiceOf(ui, rec) {
  if (!ui.choices.has(rec.id)) ui.choices.set(rec.id, {});
  return ui.choices.get(rec.id);
}

const field = (label, control) => h('label', { class: 'oc-field' }, label, control);

function suggestionText(ui, rec, sg) {
  if (sg.error) return t(`requests.panel.error.${sg.error}`);
  const b = sg.buttons.find((x) => x.answer === sg.suggested);
  if (!b) return t('requests.panel.no_suggestion');
  const gives = [...(b.delivers.sheets || []), ...(b.delivers.cards || [])];
  const what = describe(ui.teamJson, rec.req, t).what;
  const cost = b.charge ? plural('requests.tokens_n', b.cost) : t('requests.free');
  return gives.length
    ? t('requests.panel.suggest_gives', { what, gives: gives.join(', '), cost })
    : t('requests.panel.suggest_only', { what, answer: t(`requests.btn.${b.answer}`), cost });
}

function conditionsText(sg) {
  if (!sg.conditions.length) return null;
  const label = (c) => `${c.code} ${c.held ? '✓' : '✗'}`;
  const by = (role) => sg.conditions.filter((c) => c.role === role).map(label).join(' · ');
  return h('p', { class: 'oc-muted oc-conditions' },
    by('mother') ? [t('requests.panel.cond.mother'), ' ', by('mother'), ' ◦ '] : null,
    by('needs') ? [t('requests.panel.cond.needs'), ' ', by('needs'), ' ◦ '] : null,
    by('appears') ? [t('requests.panel.cond.appears'), ' ', by('appears')] : null);
}

function choices(ui, rec, sg, c) {
  const q = rec.req;
  const out = [];
  if (q.kind === 'witness') {
    const typed = matchWitness(ui.dgame, q.who);
    const value = c.who ?? (typed ? typed.who : '');
    out.push(field(t('requests.panel.witness'), h('select', { class: 'oc-input', 'data-choice': 'who', onchange: (e) => { c.who = e.target.value; c.keep = undefined; ui.redraw(); } },
      [h('option', { value: '' }, typed ? t('requests.panel.witness_other') : t('requests.panel.witness_none')), ...ui.dgame.director.witnesses.map((w) => h('option', { value: w.who, selected: w.who === value }, w.name))])));
  }
  if (q.kind === 'confrontation') {
    const state = teamState(ui.dgame, ui.book, rec.team, ui.log);
    const cards = confrontationCards(ui.dgame, q.suspect);
    const ruled = cards.some((x) => (x.opens_with || []).length);
    const m = sg.match;
    const verdict = !ruled || !m ? null
      : m.card ? t('confront.opens', { card: m.card })
        : m.candidates.length ? t('confront.ask', { cards: m.candidates.join(', ') }) : t('confront.none');
    out.push(h('div', { class: 'oc-confront' },
      h('h4', {}, t('requests.panel.confront_cards')),
      verdict ? h('p', { class: 'oc-muted', dataset: { match: m.card || '', candidates: m.candidates.join(',') } }, verdict) : null,
      cards.length ? cards.map((k) => {
        const had = state.held.cards.some((x) => norm(x) === norm(k.code));
        return h('label', { class: 'oc-sel', dataset: { card: k.code } },
          h('input', { type: 'radio', name: `card-${rec.id}`, value: k.code, checked: sg.request.card === k.code, 'data-choice': 'card', onchange: () => { c.card = k.code; c.keep = undefined; ui.redraw(); } }),
          h('span', {}, h('strong', {}, k.code), ' · ', k.question, had ? h('small', {}, ` · ${t('requests.panel.had')}`) : null, k.guide_note ? h('small', {}, ` · ${k.guide_note}`) : null));
      }) : h('p', { class: 'oc-muted' }, t('requests.panel.no_cards'))));
  }
  if (q.kind === 'procedure') {
    const p = ui.dgame.procedures.get(q.code);
    const target = p && p.targets.find((x) => x.key === q.target);
    if (target && target.special === 'material') {
      out.push(field(t('requests.panel.material'), h('input', { class: 'oc-input', 'data-choice': 'sheets', 'data-focus': `sheets-${rec.id}`, value: (c.sheets || []).join(', '), placeholder: 'E10, E11',
        onchange: (e) => { c.sheets = e.target.value.split(/[,\s]+/).filter(Boolean); c.keep = undefined; ui.redraw(); } })));
    }
    if (target && target.note) out.push(h('p', { class: 'oc-muted' }, t('requests.panel.target_note'), ' ', target.note));
  }
  return out;
}

function alibiChoice(ui, rec, sg, c) {
  const request = sg.request;
  if (!acceptsAlibi(ui.dgame, request) || rec.req.kind !== 'procedure') return null;
  const state = teamState(ui.dgame, ui.book, rec.team, ui.log);
  const max = Math.min(sg.cost || 1, state.alibi);
  if (!max && !(rec.req.alibi)) return null;
  const value = c.alibi ?? rec.req.alibi ?? 0;
  return field(t('requests.panel.alibi'), h('select', { class: 'oc-input', 'data-choice': 'alibi', onchange: (e) => { c.alibi = Number(e.target.value); ui.redraw(); } },
    Array.from({ length: Math.max(max, value) + 1 }, (_, n) => h('option', { value: String(n), selected: n === value }, n ? plural('requests.panel.alibi_n', n) : t('requests.panel.alibi_none')))));
}

function deliveryChoice(ui, sg, c) {
  const b = sg.buttons.find((x) => x.answer === sg.suggested);
  if (!b) return null;
  const items = [...(b.delivers.sheets || []).map((code) => ['sheets', code]), ...(b.delivers.cards || []).map((code) => ['cards', code])];
  if (!items.length) return null;
  const keep = c.keep || { sheets: b.delivers.sheets || [], cards: b.delivers.cards || [] };
  return h('div', { class: 'oc-handout' }, h('h4', {}, t('requests.panel.handout')),
    items.map(([kind, code]) => h('label', { class: 'oc-sel', style: 'min-height:40px' },
      h('input', { type: 'checkbox', checked: keep[kind].includes(code), 'data-keep': code, onchange: (e) => {
        const next = { sheets: [...keep.sheets], cards: [...keep.cards] };
        next[kind] = e.target.checked ? [...new Set([...next[kind], code])] : next[kind].filter((x) => x !== code);
        c.keep = next;
      } }), h('span', {}, h('strong', {}, code), kind === 'cards' ? ` · ${t('director.give.card')}` : ''))));
}

function requestCard(ui, rec) {
  const c = choiceOf(ui, rec);
  const state = teamState(ui.dgame, ui.book, rec.team, ui.log);
  const sg = suggest(ui.dgame, state, rec, { who: c.who, card: c.card, sheets: c.sheets });
  const d = describe(ui.teamJson, rec.req, t);
  const request = sg.request;
  const press = (answer) => ui.answer(rec, answer, {
    who: c.who, card: c.card, sheets: c.sheets, alibi: c.alibi, note: c.note, keep: answer === sg.suggested ? c.keep : undefined });
  const buttons = BUTTONS.map((name) => sg.buttons.find((b) => b.answer === name)).filter(Boolean);
  return h('section', { class: `oc-card oc-request oc-team-${rec.team}`, dataset: { id: rec.id, team: rec.team, kind: rec.req.kind } },
    h('div', { class: 'oc-row' }, teamBadge(rec.team), h('strong', {}, d.kind), h('span', { class: 'oc-grow' }), h('small', { class: 'oc-muted' }, rec.name ? `${rec.name} · ` : '', time(rec.at))),
    h('p', {}, h('strong', {}, d.what), d.extra ? h('span', { class: 'oc-muted' }, ` — ${d.extra}`) : null),
    h('p', { class: 'oc-suggest', dataset: { suggested: sg.suggested || '' } }, h('strong', {}, t('requests.panel.suggested')), ' ', suggestionText(ui, rec, sg)),
    h('p', { class: 'oc-muted' }, t('requests.panel.balance', { tokens: state.tokens, alibi: state.alibi })),
    conditionsText(sg),
    ...choices(ui, rec, sg, c),
    alibiChoice(ui, rec, sg, c),
    deliveryChoice(ui, sg, c),
    field(t('requests.panel.note'), h('textarea', { class: 'oc-input', rows: '2', 'data-choice': 'note', 'data-focus': `note-${rec.id}`, oninput: (e) => { c.note = e.target.value; } }, c.note || '')),
    h('div', { class: 'oc-row oc-answers' }, buttons.map((b) => h('button', {
      class: `oc-btn oc-btn--small${b.answer === sg.suggested ? '' : ' oc-btn--ghost'}`, type: 'button', disabled: !b.available, dataset: { answer: b.answer },
      title: b.available ? '' : t(`requests.panel.error.${b.why}`),
      onclick: () => press(b.answer) },
    t(`requests.btn.${b.answer}`), b.charge && b.cost ? h('small', {}, ` −${b.cost}`) : null))),
    request.kind === 'witness' && !request.who ? h('p', { class: 'oc-muted' }, t('requests.panel.pick_witness')) : null);
}

/** The "requests" tab: the queue. */
export function queueView(ui) {
  const list = pendingList(ui.book);
  return h('div', { id: 'oc-queue' },
    h('p', { class: 'oc-muted' }, t('requests.panel.help')),
    list.length ? list.map((rec) => requestCard(ui, rec)) : h('p', { class: 'oc-muted', id: 'oc-queue-empty' }, t('requests.panel.empty')));
}

/** The "register" tab: every request with its answer and how long the answer took; it replaces the control sheet. */
export function registerView(ui) {
  const median = medianSeconds(ui.book);
  const rows = [...ui.book.requests].sort((a, b) => b.at - a.at);
  return h('div', {},
    h('p', { class: 'oc-muted', id: 'oc-register-median' }, median == null ? t('requests.panel.median_none') : t('requests.panel.median', { s: median.toFixed(1) })),
    rows.length ? h('ul', { class: 'oc-list', id: 'oc-register' }, rows.map((r) => {
      const d = describe(ui.teamJson, r.req, t);
      const spent = r.charged ? r.charged.tokens + r.charged.alibi : 0;
      return h('li', { class: `oc-item oc-team-${r.team}`, style: 'border-left-color:var(--team);display:block;padding:10px 12px', dataset: { id: r.id, team: r.team, answer: r.answer || 'pending' } },
        h('div', {}, teamBadge(r.team), ' ', time(r.at), ' · ', h('strong', {}, d.kind), ' · ', d.what),
        h('div', { class: 'oc-muted' }, r.status === 'done'
          ? [t(`requests.btn.${r.answer}`), ' · ', spent ? plural('requests.spent', spent) : t('requests.free'),
            r.delivered && (r.delivered.sheets.length + r.delivered.cards.length) ? ` · ${[...r.delivered.sheets, ...r.delivered.cards].join(', ')}` : '',
            ` · ${((r.doneAt - r.at) / 1000).toFixed(1)} s`]
          : t('requests.pending')));
    })) : h('p', { class: 'oc-muted' }, t('requests.panel.register_empty')));
}
