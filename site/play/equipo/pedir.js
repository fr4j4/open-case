// A team's requests (F4b): the balance of tokens, the form to ask the director for something, what is waiting and the
// history ("what we spent each token on"). It draws; the rules are in js/requests.js and js/rules.js and the sending is
// done by app.js. `ui` = { team (team.json), game (rules), bal, pending, held (codes the team has), send(requests), redraw() }.
import { h, toast } from '../js/dom.js';
import { t, plural } from '../js/i18n.js';
import { describe, canAsk, available, newRequestId, KINDS } from '../js/requests.js';
import { norm } from '../js/rules.js';

const FORM_KINDS = ['question', 'follow_up', 'witness', 'confrontation', 'procedure'];
const form = { kind: 'question', code: '', suspect: '', text: '', who: '', detail: '', evidence: new Map(), target: '', alibi: false };
let procedureCode = '';

const val = (id) => (document.getElementById(id) || {}).value || '';
const holds = (ui, code) => [...ui.held].some((x) => norm(x) === norm(code));

/** The saldo strip: numbers and alibi tokens, with what the pending requests hold back. */
export function balanceBar(ui) {
  const left = available(ui.game, ui.bal, ui.pending);
  const held = { tokens: ui.bal.tokens - left.tokens, alibi: ui.bal.alibi - left.alibi };
  const box = h('div', { class: 'oc-balance', id: 'oc-balance', dataset: { tokens: String(ui.bal.tokens), alibi: String(ui.bal.alibi), free: String(left.tokens) } },
    h('span', { class: 'oc-balance__n', id: 'oc-balance-tokens' }, String(left.tokens)), ' ', h('span', {}, t('requests.tokens')),
    ui.game.rules.alibi_tokens_per_team ? h('span', { class: 'oc-balance__alibi' }, ' · ', h('b', { id: 'oc-balance-alibi' }, String(left.alibi)), ' ', t('requests.alibi')) : null,
    held.tokens || held.alibi ? h('small', { class: 'oc-muted' }, ' · ', t('requests.reserved', { n: held.tokens + held.alibi })) : null);
  return box;
}

/** The request the form describes, or { error } when it is not complete. For `each` procedures, one request per line. */
function build(ui) {
  const f = form;
  const base = { kind: f.kind };
  if (f.kind === 'question') {
    if (f.code) return [{ ...base, id: newRequestId(), code: f.code }];
    if (!f.suspect || !f.text.trim()) return { error: 'incomplete' };
    return [{ ...base, id: newRequestId(), suspect: f.suspect, text: f.text.trim() }];
  }
  if (f.kind === 'follow_up') return f.code ? [{ ...base, id: newRequestId(), code: f.code }] : { error: 'incomplete' };
  if (f.kind === 'witness') {
    if (!f.who.trim()) return { error: 'incomplete' };
    return [{ ...base, id: newRequestId(), who: f.who.trim(), detail: f.detail.trim(), text: f.text.trim() }];
  }
  if (f.kind === 'confrontation') {
    if (!f.suspect || !f.evidence.size) return { error: 'incomplete' };
    return [{ ...base, id: newRequestId(), suspect: f.suspect, evidence: [...f.evidence].map(([code, text]) => [code, text]) }];
  }
  const p = ui.team.procedures.find((x) => x.code === procedureCode);
  if (!p) return { error: 'incomplete' };
  if (p.targets.length && !f.target) return { error: 'incomplete' };
  const lines = p.each && !p.targets.length ? f.text.split('\n').map((s) => s.trim()).filter(Boolean) : [f.text.trim()];
  if (!lines.length) return { error: 'incomplete' };
  return lines.map((text) => ({ kind: 'procedure', id: newRequestId(), code: p.code, ...(p.targets.length ? { target: f.target } : {}), text, ...(f.alibi ? { alibi: 1 } : {}) }));
}

function reset() {
  Object.assign(form, { code: '', suspect: '', text: '', who: '', detail: '', evidence: new Map(), target: '', alibi: false });
  procedureCode = '';
}

function sendButton(ui) {
  const built = build(ui);
  const requests = Array.isArray(built) ? built : [];
  // a request is checked against what is still free after the ones that go before it in the same form
  let reason = built.error || null;
  let total = { min: 0, max: 0 };
  const pending = [...ui.pending];
  for (const r of requests) {
    const ok = canAsk(ui.game, ui.bal, pending, r);
    if (!ok.ok) { reason = ok.reason; break; }
    total = { min: total.min + ok.cost.min, max: total.max + ok.cost.max };
    pending.push(r);
  }
  const price = total.min === total.max ? String(total.max) : `${total.min}–${total.max}`;
  const button = h('button', { class: 'oc-btn', type: 'button', id: 'oc-req-send', disabled: !requests.length || !!reason,
    onclick: async () => {
      const again = build(ui);
      if (!Array.isArray(again)) return;
      reset();
      await ui.send(again);
      toast(plural('requests.sent', again.length));
      ui.redraw();
    } }, requests.length && !reason ? t('requests.send_cost', { cost: price }) : t('requests.send'));
  return h('div', {}, button, reason && reason !== 'incomplete' ? h('p', { class: 'oc-notice oc-notice--bad', id: 'oc-req-why' }, t(`requests.why.${reason}`)) : null);
}

const field = (label, control) => h('label', { class: 'oc-field' }, label, control);
const select = (id, options, value, onchange) => h('select', { class: 'oc-input', id, onchange: (e) => onchange(e.target.value) },
  options.map(([v, text, extra]) => h('option', { value: v, selected: v === value, disabled: extra === 'disabled' }, text)));
const input = (id, value, set, tag = 'input', attrs = {}) => h(tag, { class: 'oc-input', id, value, oninput: (e) => { set(e.target.value); }, ...attrs }, tag === 'textarea' ? value : null);

const suspectName = (ui, s) => s.short_name || s.name;

function questionForm(ui) {
  const menu = ui.team.menu.map((m) => [m.code, `${m.code} · ${suspectName(ui, ui.team.suspects.find((s) => s.letter === m.suspect) || { name: m.suspect })} — ${m.question}`]);
  const off = !form.code;
  return h('div', {},
    field(t('requests.question.menu'), select('oc-q-code', [['', t('requests.question.off_menu')], ...menu], form.code, (v) => { form.code = v; ui.redraw(); })),
    off ? [
      field(t('requests.question.suspect'), select('oc-q-suspect', [['', '—'], ...ui.team.suspects.map((s) => [s.letter, suspectName(ui, s)])], form.suspect, (v) => { form.suspect = v; ui.redraw(); })),
      field(t('requests.question.text'), input('oc-q-text', form.text, (v) => { form.text = v; refreshSend(ui); }, 'textarea', { rows: '3' })),
    ] : null);
}

function followUpForm(ui) {
  const options = ui.team.follow_ups.map((f) => {
    const ok = !f.unlocked_by.length || f.unlocked_by.some((c) => holds(ui, c));
    return [f.code, ok ? `${f.code} · ${plural('requests.tokens_n', f.cost)}` : `${f.code} · ${t('requests.follow_up.needs', { codes: f.unlocked_by.join(' / ') })}`, ok ? '' : 'disabled'];
  });
  return h('div', {}, h('p', { class: 'oc-muted' }, t('requests.follow_up.help')),
    field(t('requests.follow_up.code'), select('oc-f-code', [['', '—'], ...options], form.code, (v) => { form.code = v; refreshSend(ui); })));
}

function witnessForm(ui) {
  return h('div', {}, h('p', { class: 'oc-muted' }, t('requests.witness.help')),
    field(t('requests.witness.who'), input('oc-w-who', form.who, (v) => { form.who = v; refreshSend(ui); }, 'input', { maxlength: '80', autocomplete: 'off' })),
    field(t('requests.witness.detail'), input('oc-w-detail', form.detail, (v) => { form.detail = v; }, 'input', { maxlength: '200', autocomplete: 'off' })),
    field(t('requests.witness.text'), input('oc-w-text', form.text, (v) => { form.text = v; }, 'textarea', { rows: '2' })));
}

function confrontationForm(ui) {
  const folder = ui.folder.filter((i) => i.code);
  const pieces = folder.length ? folder.map((i) => {
    const on = form.evidence.has(i.code);
    return h('div', { class: 'oc-evidence', dataset: { code: i.code } },
      h('label', { class: 'oc-sel' }, h('input', { type: 'checkbox', checked: on, 'data-evidence': i.code, onchange: (e) => { if (e.target.checked) form.evidence.set(i.code, ''); else form.evidence.delete(i.code); ui.redraw(); } }),
        h('span', {}, h('strong', {}, i.code), i.label && i.label !== i.code ? ` · ${i.label}` : '')),
      on ? h('input', { class: 'oc-input', 'data-point': i.code, placeholder: t('requests.confrontation.points'), value: form.evidence.get(i.code), maxlength: '200', oninput: (e) => form.evidence.set(i.code, e.target.value) }) : null);
  }) : [h('p', { class: 'oc-muted' }, t('requests.confrontation.no_evidence'))];
  return h('div', {}, h('p', { class: 'oc-muted' }, t('requests.confrontation.help')),
    field(t('requests.confrontation.suspect'), select('oc-c-suspect', [['', '—'], ...ui.team.suspects.map((s) => [s.letter, suspectName(ui, s)])], form.suspect, (v) => { form.suspect = v; refreshSend(ui); })),
    h('h3', {}, t('requests.confrontation.evidence')), ...pieces);
}

function procedureForm(ui) {
  const p = ui.team.procedures.find((x) => x.code === procedureCode);
  const options = ui.team.procedures.map((x) => [x.code, `${x.code} · ${x.label}`]);
  const free = p && ui.game.rules.free_source_procedures.includes(p.code);
  const accepts = p && ui.game.rules.alibi_procedures.includes(p.code);
  return h('div', {},
    field(t('requests.procedure.code'), select('oc-p-code', [['', '—'], ...options], procedureCode, (v) => { procedureCode = v; form.target = ''; form.alibi = false; ui.redraw(); })),
    p && p.targets.length ? field(t('requests.procedure.target'), select('oc-p-target', [['', '—'], ...p.targets.map((x) => [x.key, x.label])], form.target, (v) => { form.target = v; ui.redraw(); })) : null,
    p ? field(p.each && !p.targets.length ? t('requests.procedure.each') : t('requests.procedure.text'), input('oc-p-text', form.text, (v) => { form.text = v; refreshSend(ui); }, 'textarea', { rows: p.each ? '4' : '3' })) : null,
    accepts ? h('label', { class: 'oc-sel' }, h('input', { type: 'checkbox', id: 'oc-p-alibi', checked: form.alibi, onchange: (e) => { form.alibi = e.target.checked; ui.redraw(); } }), h('span', {}, t('requests.procedure.alibi'), ' ', h('small', {}, t('requests.procedure.alibi_help')))) : null,
    free && form.target ? h('div', {}, h('button', { class: 'oc-btn oc-btn--ghost', type: 'button', id: 'oc-p-source', onclick: async () => {
      await ui.send([{ kind: 'source', id: newRequestId(), code: p.code, place: form.target }]);
      toast(t('requests.source_sent'));
      ui.redraw();
    } }, t('requests.procedure.source')), h('p', { class: 'oc-muted' }, t('requests.procedure.source_help'))) : null);
}

function refreshSend(ui) {
  const old = document.getElementById('oc-req-send');
  if (!old) return;
  const box = old.parentElement;
  box.replaceWith(sendButton(ui));
}

/** The "ask" tab. */
export function askView(ui) {
  const chips = h('div', { class: 'oc-chips', role: 'group' }, FORM_KINDS.map((k) => h('button', { class: 'oc-chip', type: 'button', 'aria-pressed': String(form.kind === k), dataset: { kind: k },
    onclick: () => { form.kind = k; reset(); ui.redraw(); } }, t(`requests.kind.${k}`))));
  const body = form.kind === 'question' ? questionForm(ui) : form.kind === 'follow_up' ? followUpForm(ui) : form.kind === 'witness' ? witnessForm(ui)
    : form.kind === 'confrontation' ? confrontationForm(ui) : procedureForm(ui);
  const waiting = ui.pending.length ? [h('h3', {}, t('requests.waiting')), h('ul', { class: 'oc-list', id: 'oc-req-waiting' }, ui.pending.map((r) => requestItem(ui, r, null)))] : null;
  return h('div', {}, balanceBar(ui), ui.connected ? null : h('div', { class: 'oc-notice', id: 'oc-req-offline' }, t('requests.offline')),
    chips, h('section', { class: 'oc-card' }, body, sendButton(ui)), waiting);
}

const ANSWER_CLASS = { give: 'ok', obvious: 'ok', yes: 'ok', already_have: 'nope', locked: 'nope', unavailable: 'nope', no_basis: 'nope' };

function requestItem(ui, req, entry) {
  const d = describe(ui.team, req, t);
  const spent = entry ? entry.charged.tokens + entry.charged.alibi : 0;
  return h('li', { class: `oc-item oc-req${entry ? ` oc-req--${ANSWER_CLASS[entry.answer] || 'other'}` : ''}`, dataset: { id: req.id, answer: entry ? entry.answer : 'pending' }, style: 'padding:10px 12px;display:block' },
    h('div', {}, h('strong', {}, d.kind), ' · ', d.what),
    d.extra ? h('div', { class: 'oc-muted' }, d.extra) : null,
    entry ? h('div', {}, h('span', { class: 'oc-req__answer' }, t(`requests.answer.${entry.answer}`)), ' · ',
      spent ? h('span', { class: 'oc-req__cost' }, plural('requests.spent', spent), entry.charged.alibi ? ` (${t('requests.of_alibi', { n: entry.charged.alibi })})` : '') : h('span', { class: 'oc-req__cost' }, t('requests.free')),
      entry.note ? h('div', { class: 'oc-req__note' }, entry.note) : null)
      : h('div', { class: 'oc-pending' }, t('requests.pending')));
}

/** The "history" tab: every answered request, newest first, with what it cost. */
export function historyView(ui) {
  const entries = [...(ui.bal.hist || [])].sort((a, b) => b.at - a.at);
  const total = entries.reduce((n, e) => n + e.charged.tokens + e.charged.alibi, 0);
  return h('div', {}, balanceBar(ui),
    h('p', { class: 'oc-muted', id: 'oc-hist-total' }, plural('requests.hist_total', total)),
    entries.length ? h('ul', { class: 'oc-list', id: 'oc-hist' }, entries.map((e) => requestItem(ui, e.req, e))) : h('p', { class: 'oc-muted' }, t('requests.hist_empty')));
}

export { KINDS };
