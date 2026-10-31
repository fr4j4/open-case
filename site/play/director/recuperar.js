// The director's side of recovering a game (F6a): the backup file, and getting the game back from the teams' phones when the
// director's own device is lost. The accounts are js/recover.js (pure); this draws and wires.
//
//   backupCard(ui)       the "Backup" card of the Room tab: download, last copy, load
//   recoverBox(ui)       the form of the setup screen: paste or scan the codes of the teams, or load a backup file
//   Recovery             what the new device collects while the phones tell their registro, and the screen to choose
import { h } from '../js/dom.js';
import { t, plural, language } from '../js/i18n.js';
import { scanCamera } from '../js/qr.js';
import { Assembler, checkRegistro, completeness, differences, rebuild } from '../js/recover.js';
import { newRequestId } from '../js/requests.js';

const time = (ms) => new Date(ms).toLocaleTimeString(language(), { hour: '2-digit', minute: '2-digit' });

// --- Backup ---------------------------------------------------------------------------------------------------------

/** ui = { lastBackup (ms or null), download(), load(text) } */
export function backupCard(ui) {
  const file = h('input', { type: 'file', accept: '.json,application/json', id: 'oc-backup-file', class: 'oc-input', onchange: async (e) => {
    const f = e.target.files && e.target.files[0];
    if (f) ui.load(await f.text());
    e.target.value = '';
  } });
  return h('section', { class: 'oc-card', id: 'oc-backup' },
    h('h3', {}, t('recover.backup.title')),
    h('p', { class: 'oc-muted' }, t('recover.backup.text')),
    h('p', { id: 'oc-backup-last', dataset: { at: String(ui.lastBackup || '') } }, ui.lastBackup ? t('recover.backup.last', { time: time(ui.lastBackup) }) : t('recover.backup.never')),
    h('div', { class: 'oc-row' }, h('button', { class: 'oc-btn oc-btn--small', type: 'button', id: 'oc-backup-download', onclick: () => ui.download() }, t('recover.backup.download'))),
    h('label', { class: 'oc-field' }, t('recover.backup.load'), file));
}

// --- The form of the setup screen --------------------------------------------------------------------------------------

/** ui = { initial (text), start(text), load(text) } */
export function recoverBox(ui) {
  const area = h('textarea', { class: 'oc-input', id: 'oc-rec-codes', rows: '4', placeholder: 'https://…/play/director/#recuperar.oc1r.…', value: ui.initial || '' }, ui.initial || '');
  const file = h('input', { type: 'file', accept: '.json,application/json', id: 'oc-rec-backup', class: 'oc-input', onchange: async (e) => {
    const f = e.target.files && e.target.files[0];
    if (f) ui.load(await f.text());
    e.target.value = '';
  } });
  const scan = h('div', { id: 'oc-rec-scan' });
  const startScan = async () => {
    const video = h('video', { class: 'oc-video', muted: true });
    const stopBtn = h('button', { class: 'oc-btn oc-btn--small oc-btn--ghost', type: 'button', onclick: () => { stop(); scan.replaceChildren(); } }, t('recover.start.scan_stop'));
    scan.replaceChildren(video, stopBtn);
    let stop = () => {};
    try {
      stop = await scanCamera(video, (text) => {
        if (/oc1r\./.test(text) && !area.value.includes(text)) { area.value = `${area.value.trim()}\n${text}`.trim(); }
      });
    } catch (e) { scan.replaceChildren(h('p', { class: 'oc-muted' }, t('recover.start.no_camera'))); }
  };
  return h('details', { class: 'oc-card', id: 'oc-recover', open: !!ui.initial },
    h('summary', {}, t('recover.start.title')),
    h('p', { class: 'oc-muted' }, t('recover.start.text')),
    h('label', { class: 'oc-field' }, t('recover.start.codes'), area),
    h('div', { class: 'oc-row' },
      h('button', { class: 'oc-btn', type: 'button', id: 'oc-rec-start', onclick: () => ui.start(area.value) }, t('recover.start.go')),
      h('button', { class: 'oc-btn oc-btn--ghost', type: 'button', onclick: startScan }, t('recover.start.scan'))),
    scan,
    h('p', { class: 'oc-muted' }, t('recover.start.or_backup')),
    h('label', { class: 'oc-field' }, t('recover.backup.load'), file));
}

// --- Recovering from the teams -----------------------------------------------------------------------------------------

export class Recovery {
  /** ctx = { room() (DirectorRoom), rg() (rules game), game(), now(), done(result, teams), cancel(), redraw(), replay(team, from, msg) } */
  constructor(ctx) {
    this.ctx = ctx;
    this.parts = new Assembler();
    this.regs = {};          // team -> Map(device id -> checked registro)
    this.picks = {};         // team -> device id the director chose
    this.held = [];          // messages that came meanwhile (requests, sheets): they are handled once the game is back
    this.asked = new Set();
  }

  get teams() { return this.ctx.game().recovery.teams; }

  // A phone of a team is in the room: ask for its registro (one request per connection of the phone).
  ask(team, id) {
    this.ctx.room().sendTeam(team, { k: 'recover', rid: newRequestId() }, id).catch(() => {});
    this.ctx.redraw();
  }

  // Everything a phone says while the game is being recovered: its registro is kept; the rest waits.
  onMessage(team, from, m) {
    if (!m || typeof m !== 'object') return;
    if (m.k !== 'reg') { if (this.held.length < 500) this.held.push([team, from, m]); return; }
    const raw = this.parts.add(from, m);
    if (!raw) return;
    const reg = checkRegistro(raw, this.ctx.rg(), team);
    if (!reg || reg.device !== from) return;                      // a phone speaks only for itself
    const mine = (this.regs[team] = this.regs[team] || new Map());
    mine.set(from, { ...reg, name: reg.name || (this.ctx.room().r.devices[from] || {}).name || '' });
    if (!this.picks[team] || !mine.has(this.picks[team])) this.picks[team] = this.best(team);
    this.ctx.redraw();
  }

  best(team) {
    const list = [...(this.regs[team] || new Map()).values()].sort((a, b) => completeness(b) - completeness(a));
    return list[0] ? list[0].device : null;
  }

  chosen() {
    const out = {};
    for (const team of this.teams) {
      const reg = this.picks[team] && this.regs[team] && this.regs[team].get(this.picks[team]);
      if (reg) out[team] = reg;
    }
    return out;
  }

  apply() {
    const picks = this.chosen();
    if (!Object.keys(picks).length) return;
    const game = this.ctx.game();
    const result = rebuild(this.ctx.rg(), picks, { teams: game.teams, now: this.ctx.now() });
    this.ctx.done(result, this.teams, this.held.splice(0));
  }

  view() {
    const game = this.ctx.game();
    const room = this.ctx.room();
    const picks = this.chosen();
    const missing = this.teams.filter((tm) => !picks[tm]);
    return h('div', { id: 'oc-recovery' },
      h('h1', {}, t('recover.panel.title')),
      h('p', {}, t('recover.panel.help')),
      this.teams.map((team) => this.teamCard(team, room)),
      h('div', { class: 'oc-notice' }, t('recover.panel.marks_lost')),
      missing.length ? h('div', { class: 'oc-notice', id: 'oc-rec-missing' }, t('recover.panel.missing', { teams: missing.join(', ') })) : null,
      h('div', { class: 'oc-row' },
        h('button', { class: 'oc-btn', type: 'button', id: 'oc-rec-apply', disabled: !Object.keys(picks).length, onclick: () => this.apply() }, t('recover.panel.apply')),
        h('button', { class: 'oc-btn oc-btn--ghost', type: 'button', id: 'oc-rec-cancel', onclick: () => this.ctx.cancel() }, t('recover.panel.cancel'))),
      h('small', { class: 'oc-muted' }, game.slug));
  }

  teamCard(team, room) {
    const regs = [...(this.regs[team] || new Map()).values()];
    const online = room.members(team).filter((d) => room.isOnline(d.id)).length;
    const diff = regs.length > 1 ? differences(regs) : null;
    const name = (reg) => reg.name || t('room.unnamed', { id: reg.device.slice(0, 4) });
    return h('section', { class: `oc-card oc-team-${team}`, dataset: { team, regs: String(regs.length) } },
      h('h3', {}, h('span', { class: `oc-badge oc-team-${team}` }, team), ' ', t('room.team_title', { team })),
      h('p', { class: 'oc-muted' }, regs.length ? plural('recover.panel.phones', online, { read: regs.length }) : online ? t('recover.panel.reading') : t('recover.panel.waiting')),
      regs.map((reg) => {
        const only = diff && diff.phones.find((p) => p.device === reg.device).only;
        return h('label', { class: 'oc-sel', dataset: { device: reg.device, picked: String(this.picks[team] === reg.device) } },
          h('input', { type: 'radio', name: `pick-${team}`, checked: this.picks[team] === reg.device, onchange: () => { this.picks[team] = reg.device; this.ctx.redraw(); } }),
          h('span', {}, h('strong', {}, name(reg)), ' · ', t('recover.panel.counts', { delivered: reg.delivered.length, answered: reg.hist.length, pending: reg.pending.length, tokens: reg.bal ? reg.bal.tokens : '?' }),
            only && (only.delivered.length || only.hist.length || only.pending.length)
              ? h('small', { class: 'oc-muted', dataset: { only: reg.device } }, ' · ', t('recover.panel.only', { delivered: only.delivered.length, answered: only.hist.length, pending: only.pending.length })) : null));
      }),
      diff && !diff.same ? h('div', { class: 'oc-notice oc-notice--bad', dataset: { differ: team } }, t('recover.panel.differ')) : null);
  }
}
