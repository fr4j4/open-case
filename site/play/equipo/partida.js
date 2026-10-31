// What a team sees of the game (F5): the phase and its clock, and the sheets it hands to the director (the accusation and the
// discard sheet, with the fields of the kit). It draws; the clock is js/clock.js and the sending is done by app.js.
// The team never sees the minute at which a notice is suggested: only the phase and the time left in it.
// `ui` = { team (team.json), clock ({phase, running, elapsed, since} or null), forms ({id: {values, sent, at}}), connected, save(id, values), submit(id), redraw() }.
import { h } from '../js/dom.js';
import { t } from '../js/i18n.js';
import { remainingMs, elapsedMs, format, minutesOf, canRequest } from '../js/clock.js';

/** The phase strip: where the game is and how long is left (it says so when the director has not started it). */
export function clockBar(ui, now = Date.now()) {
  const c = ui.clock;
  if (!c) return h('div', { class: 'oc-notice', id: 'oc-clock', dataset: { phase: '' } }, t('game.clock.not_started'));
  const left = remainingMs(ui.team.figures, c, now);
  return h('div', { class: 'oc-notice oc-clock', id: 'oc-clock', dataset: { phase: c.phase, running: String(c.running), asking: String(canRequest(c)) } },
    h('strong', {}, t(`game.phase.${c.phase}`)), ' · ',
    h('span', { id: 'oc-clock-time' }, left >= 0 ? t('game.clock.left', { time: format(left) }) : t('game.clock.over', { time: format(-left) })),
    c.running ? null : h('small', {}, ' · ', t('game.clock.paused')),
    canRequest(c) ? null : h('div', { class: 'oc-muted', id: 'oc-clock-blocked' }, t('game.clock.no_requests', { phase: t(`game.phase.${c.phase}`).toLowerCase() })));
}

/** Refreshes only the countdown (once a second), without drawing the page again. */
export function tick(ui, now = Date.now()) {
  const el = document.getElementById('oc-clock-time');
  if (!el || !ui.clock) return;
  const left = remainingMs(ui.team.figures, ui.clock, now);
  el.textContent = left >= 0 ? t('game.clock.left', { time: format(left) }) : t('game.clock.over', { time: format(-left) });
}

export { elapsedMs, minutesOf };

const MAX = 2000;

function fieldsPart(ui, form, part, rec, locked) {
  return part.items.map((f, i) => {
    const key = `f${form.parts.indexOf(part)}.${i}`;
    const value = (rec.values && rec.values[key]) || '';
    const attrs = { class: 'oc-input', 'data-field': key, maxlength: String(MAX), disabled: locked, oninput: (e) => { rec.values[key] = e.target.value; ui.save(form.id, rec.values); } };
    return h('label', { class: 'oc-field' }, f.label, f.type === 'box' ? h('textarea', { ...attrs, rows: '4' }, value) : h('input', { ...attrs, value }));
  });
}

function tablePart(ui, form, part, rec, locked) {
  const p = form.parts.indexOf(part);
  return h('div', { class: 'oc-formtable' }, part.rows.map((row, r) => h('div', { class: 'oc-card' },
    h('strong', {}, row),
    part.columns.slice(1).map((col, c) => {
      const key = `t${p}.${r}.${c}`;
      return h('label', { class: 'oc-field' }, col, h('textarea', { class: 'oc-input', rows: '2', 'data-field': key, maxlength: String(MAX), disabled: locked,
        oninput: (e) => { rec.values[key] = e.target.value; ui.save(form.id, rec.values); } }, (rec.values && rec.values[key]) || ''));
    }))));
}

/** The "Hand in" tab: one card per sheet of the kit that the team fills in; what they write is kept on the phone while they type. */
export function formsView(ui) {
  const forms = ui.team.forms || [];
  if (!forms.length) return h('p', { class: 'oc-muted' }, t('game.forms.none'));
  return h('div', {},
    h('p', { class: 'oc-muted' }, t('game.forms.help')),
    ui.connected ? null : h('div', { class: 'oc-notice', id: 'oc-forms-offline' }, t('game.forms.offline')),
    forms.map((form) => {
      const rec = ui.forms[form.id] || (ui.forms[form.id] = { values: {}, sent: false, at: null });
      const locked = rec.sent;
      return h('section', { class: 'oc-card oc-form', dataset: { form: form.id, sent: String(rec.sent), queued: String(!!rec.queued) } },
        h('h3', {}, form.title),
        h('p', { class: 'oc-muted' }, h('a', { href: '#', onclick: (e) => { e.preventDefault(); ui.openSheet(form.file, form.title); } }, t('game.forms.read_sheet'))),
        ...form.parts.map((part) => (part.kind === 'fields' ? fieldsPart(ui, form, part, rec, locked) : tablePart(ui, form, part, rec, locked))),
        rec.sent
          ? h('div', { class: 'oc-row' }, h('span', { class: 'oc-badge', id: `oc-form-sent-${form.id}` }, t('game.forms.sent')), h('button', { class: 'oc-btn oc-btn--small oc-btn--ghost', type: 'button', dataset: { reopen: form.id }, onclick: () => ui.reopen(form.id) }, t('game.forms.edit')))
          : h('div', { class: 'oc-row' }, h('button', { class: 'oc-btn', type: 'button', dataset: { submit: form.id }, onclick: () => ui.submit(form.id) }, rec.queued ? t('game.forms.queued') : t('game.forms.submit'))));
    }));
}
