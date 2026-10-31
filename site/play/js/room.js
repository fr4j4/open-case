// The live room (F3): the director opens it, phones come in with a PIN or a link, the director approves each one and
// assigns it to a team, and from then on the deliveries go over the network (the QR stays as the backup).
//
//   vestibule   room `oc-v-<PIN>`. Anybody who knows the PIN is here. The director sends it only `wait`, `approved`
//               or `denied`: nothing about the game.
//   team room   room `oc-t-<random>`, one per team. Its name is sent only to the devices the director approved, and
//               the relay bus encrypts with a key made from that name, so a phone that was not approved cannot read it.
//
// Messages (JSON, on top of the Transporte layer that numbers, acknowledges and repeats them):
//   phone → director (vestibule)  {k:'join', name}
//   director → phone (vestibule)  {k:'wait'} | {k:'approved', team, room, c, l, v} | {k:'denied'}
//   director → phone (team room)  {k:'sync'|'deliver', c, l, v, t, s, i}    same shape as the QR's message (delivery.js)
//                                 {k:'room', room}  the team room changed    {k:'out'}  the director took the phone out
//
// Nothing here is a secret that protects the game from a determined player (the PIN is short and the site is public):
// what it does is keep a device that nobody approved from receiving what the director hands out.
import { Canal } from './canal.js';
import { validate } from './delivery.js';
import { openLog } from './log.js';

export const PIN_ALPHABET = 'ABCDEFGHJKMNPQRSTUVWXYZ23456789';   // no 0/O, 1/I/L
const rand = (n, alphabet) => {
  const a = new Uint8Array(n);
  crypto.getRandomValues(a);
  return Array.from(a, (b) => alphabet[b % alphabet.length]).join('');
};
const ID_CHARS = 'abcdefghijklmnopqrstuvwxyz0123456789';

// Waits for an acknowledgement, but not for long: the phone may close the room it is leaving right after reading.
const quick = (promise, ms = 2000) => Promise.race([promise.catch(() => {}), new Promise((r) => setTimeout(r, ms))]);

export const newPin = () => rand(6, PIN_ALPHABET);
export const newId = () => rand(8, ID_CHARS);
export const normalizePin = (text) => String(text || '').toUpperCase().replace(/[^A-Z0-9]/g, '').slice(0, 6);
export const validPin = (pin) => typeof pin === 'string' && pin.length === 6 && [...pin].every((c) => PIN_ALPHABET.includes(c));
export const vestibuleRoom = (pin) => `oc-v-${pin}`;
export const newTeamRoom = () => `oc-t-${rand(20, ID_CHARS)}`;

// The link that opens the phone's app with the PIN already in: play/equipo/#sala.<PIN>
export const roomLink = (base, pin) => `${base}#sala.${pin}`;
export function pinFromHash(hash) {
  const m = /^#?sala\.([A-Za-z0-9]{6})$/.exec(String(hash || '').trim());
  if (!m) return null;
  const pin = m[1].toUpperCase();
  return validPin(pin) ? pin : null;
}

// The screen of the phone stays on while the room is open (iOS and Android turn it off otherwise, and the connection goes with it).
export function keepAwake() {
  let lock = null;
  const ask = async () => {
    try { if ('wakeLock' in navigator && document.visibilityState === 'visible' && !lock) { lock = await navigator.wakeLock.request('screen'); lock.addEventListener('release', () => { lock = null; }); } }
    catch (e) { lock = null; }
  };
  document.addEventListener('visibilitychange', ask);
  ask();
  return () => { document.removeEventListener('visibilitychange', ask); if (lock) lock.release().catch(() => {}); };
}

// ---- The director's side ---------------------------------------------------------------------------------------------

// `game` is the director's saved game; the room lives in game.room and is saved through `save()` on every change:
//   room = {pin, id, teamRooms: {A: 'oc-t-…'}, devices: {<id>: {id, name, team, status: 'pending'|'approved'|'denied', joined, seen}}}
export class DirectorRoom {
  constructor({ game, save, onChange = () => {} }) {
    this.game = game;
    this.save = save;
    this.onChange = onChange;
    this.vestibule = null;
    this.teams = new Map();      // team letter -> Canal
    this.online = new Map();     // device id -> since (ms) while it is connected to its team room
    this.log = openLog(`director-${game.created || 0}`);
    if (!game.room) game.room = { pin: newPin(), id: newId(), teamRooms: {}, devices: {} };
    this.r = game.room;
  }

  get pin() { return this.r.pin; }
  devices() { return Object.values(this.r.devices); }
  pending() { return this.devices().filter((d) => d.status === 'pending'); }
  members(team) { return this.devices().filter((d) => d.status === 'approved' && d.team === team); }
  isOnline(id) { return this.online.has(id); }
  seenInVestibule(id) { return !!(this.vestibule && this.vestibule.peers().some((p) => p.id === id)); }

  async start() {
    this.vestibule = new Canal({ room: vestibuleRoom(this.r.pin), name: 'director', role: 'director', id: this.r.id, mode: 'listen' });
    this.vestibule.on('peer', (p) => this._joined(p));
    this.vestibule.on('message', (from, m) => this._vestibuleMessage(from, m));
    this.vestibule.on('peerleave', () => this.onChange());
    await this.vestibule.connect();
    await Promise.all(this.game.teams.filter((t) => this.members(t).length).map((t) => this._openTeam(t)));
    this.onChange();
    return this;
  }

  async stop() {
    await this.vestibule?.close();
    await Promise.all([...this.teams.values()].map((c) => c.close()));
    this.teams.clear();
    this.online.clear();
  }

  _changed() { this.save(); this.onChange(); }

  // Somebody with the PIN is in the vestibule.
  _joined(p) {
    if (p.role === 'director') return;
    let d = this.r.devices[p.id];
    if (!d) {
      d = { id: p.id, name: p.name || '', team: null, status: 'pending', joined: Date.now(), seen: Date.now() };
      this.r.devices[p.id] = d;
      this.log.append('join', { device: p.id, name: d.name });
    } else { d.seen = Date.now(); if (p.name) d.name = p.name; }
    this._answer(d);
    this._changed();
  }

  _vestibuleMessage(from, m) {
    const d = this.r.devices[from];
    if (!d || !m || typeof m !== 'object') return;
    if (m.k === 'join' && typeof m.name === 'string') { d.name = m.name.slice(0, 40); this._changed(); }
  }

  // The reply to a phone in the vestibule: wait, the room it was approved into, or no.
  _answer(d) {
    const v = this.vestibule;
    if (!v) return;
    const msg = d.status === 'approved' ? this._approvedMessage(d) : d.status === 'denied' ? { k: 'denied' } : { k: 'wait' };
    v.send(d.id, msg).catch(() => {});
  }

  _approvedMessage(d) {
    const g = this.game;
    return { k: 'approved', team: d.team, room: this.r.teamRooms[d.team], c: g.slug, l: g.lang, v: g.version };
  }

  async approve(id, team) {
    const d = this.r.devices[id];
    if (!d || !this.game.teams.includes(team)) return;
    const moved = d.status === 'approved' && d.team !== team;
    const previous = d.team;
    d.status = 'approved';
    d.team = team;
    if (!this.r.teamRooms[team]) this.r.teamRooms[team] = newTeamRoom();
    this.log.append(moved ? 'move' : 'approve', { device: id, team, from: moved ? previous : undefined });
    if (moved) {                           // the phone is in the old team's room: it is told there where to go
      const oldCanal = this.teams.get(previous);
      if (oldCanal) await quick(oldCanal.send(id, this._approvedMessage(d)));
      await this._rotate(previous, id);
    }
    await this._openTeam(team);
    this._answer(d);
    this._changed();
  }

  async deny(id) {
    const d = this.r.devices[id];
    if (!d) return;
    const was = d.status === 'approved' ? d.team : null;
    d.status = 'denied';
    d.team = null;
    this.log.append('deny', { device: id });
    if (was) await this._rotate(was, id, true);
    this._answer(d);
    this._changed();
  }

  // A device left a team (moved or taken out): the team gets a new room name, so the one that left cannot listen to it.
  async _rotate(team, leavingId, tellLeaver = false) {
    const old = this.teams.get(team);
    const fresh = newTeamRoom();
    const keep = this.members(team).filter((d) => d.id !== leavingId);
    if (old) {
      await Promise.all(keep.map((d) => quick(old.send(d.id, { k: 'room', room: fresh }))));
      if (tellLeaver) await quick(old.send(leavingId, { k: 'out' }));
      await old.close();
      this.teams.delete(team);
    }
    for (const d of keep) this.online.delete(d.id);
    this.r.teamRooms[team] = fresh;
    if (keep.length) await this._openTeam(team);
  }

  async _openTeam(team) {
    if (this.teams.has(team)) return;
    if (!this.r.teamRooms[team]) this.r.teamRooms[team] = newTeamRoom();
    const c = new Canal({ room: this.r.teamRooms[team], name: `director-${team}`, role: 'director', id: this.r.id, mode: 'listen' });
    this.teams.set(team, c);
    c.on('peer', (p) => this._teamPeer(team, p));
    c.on('peerleave', (p) => { this.online.delete(p.id); this.log.append('offline', { device: p.id, team }); this.onChange(); });
    c.on('message', (from, m) => this._teamMessage(team, from, m));
    await c.connect();
  }

  // Only a device the director approved for this team gets anything from the team room.
  _teamPeer(team, p) {
    const d = this.r.devices[p.id];
    if (!d || d.status !== 'approved' || d.team !== team) return;
    d.seen = Date.now();
    this.online.set(d.id, Date.now());
    this.log.append('online', { device: d.id, team });
    this._sync(team, d.id);
    this.onOnline?.(team, d.id);
    this._changed();
  }

  _teamMessage(team, from, m) {
    const d = this.r.devices[from];
    if (!d || d.status !== 'approved' || d.team !== team) return;     // not one of ours: ignored
    d.seen = Date.now();
    this.onMessage?.(team, from, m);
  }

  // Everything the team was handed so far (a device that arrives, reloads or comes back from a cut gets what it missed).
  teamItems(team) {
    const got = new Map();
    for (const e of this.game.log) if (e.team === team) for (const [f, c] of e.items) got.set(f, c);
    return [...got];
  }

  _wire(team, k, seq, items) {
    const g = this.game;
    return { k, c: g.slug, l: g.lang, v: g.version, t: team, s: seq, i: items };
  }

  _sync(team, deviceId) {
    const c = this.teams.get(team);
    if (!c) return;
    c.send(deviceId, this._wire(team, 'sync', this.game.seq, this.teamItems(team))).catch(() => {});
  }

  // Any other message to the devices of a team (F4b: the balance and the answers). `to` is one device id or null for all
  // the connected ones. Returns how many it was sent to.
  async sendTeam(team, msg, to = null) {
    const c = this.teams.get(team);
    if (!c) return 0;
    const targets = this.members(team).filter((d) => this.online.has(d.id) && (!to || d.id === to));
    const results = await Promise.allSettled(targets.map((d) => c.send(d.id, msg)));
    return results.filter((r) => r.status === 'fulfilled').length;
  }

  // Sends a delivery to every connected device of the team. Returns how many it was sent to; the rest get it from the
  // sync when they connect (the delivery is already in game.log).
  async deliver(team, items, seq) {
    const c = this.teams.get(team);
    if (!c) return 0;
    const targets = this.members(team).filter((d) => this.online.has(d.id));
    this.log.append('deliver', { team, seq, codes: items.map((i) => i[1]), devices: targets.length });
    const results = await Promise.allSettled(targets.map((d) => c.send(d.id, this._wire(team, 'deliver', seq, items))));
    return results.filter((r) => r.status === 'fulfilled').length;
  }

  // The closest thing to "reached": connected devices of the team right now.
  reach(team) { return this.members(team).filter((d) => this.online.has(d.id)).length; }
}

// ---- A phone's side ----------------------------------------------------------------------------------------------------

// status: 'connecting' | 'waiting' | 'approved' | 'denied' | 'out'
export class DeviceRoom {
  // `session` is what survives a reload: {pin, team, room, c, l, v} (null before the first approval).
  constructor({ id, name, pin, session, onStatus = () => {}, onMessage = () => {}, onSession = () => {}, onData = () => {}, onDirector = () => {} }) {
    this.id = id;
    this.name = name;
    this.pin = pin;
    this.session = session || null;
    this.onStatus = onStatus;
    this.onMessage = onMessage;
    this.onSession = onSession;
    this.onData = onData;               // messages that are not deliveries (the balance: {k:'bal'})
    this.onDirector = onDirector;       // the director is connected in the team room (again): send what is pending
    this.status = 'connecting';
    this.vestibule = null;
    this.team = null;
    this.directorSeen = false;
  }

  _set(status) { this.status = status; this.onStatus(status, this); }

  async start() {
    if (this.session && this.session.room) { await this._openTeam(this.session.room); this._set('approved'); return this; }
    return this._openVestibule();
  }

  async _openVestibule() {
    this._set('connecting');
    this.vestibule = new Canal({ room: vestibuleRoom(this.pin), name: this.name, role: 'equipo', id: this.id, mode: 'dial' });
    this.vestibule.on('peer', (p) => {
      if (p.role !== 'director') return;
      this.directorSeen = true;
      if (this.status === 'connecting') this._set('waiting');
      this.vestibule.send(p.id, { k: 'join', name: this.name }).catch(() => {});
    });
    this.vestibule.on('peerleave', (p) => { if (p.role === 'director' && this.status === 'waiting') this._set('connecting'); });
    this.vestibule.on('message', (_from, m) => this._vestibuleMessage(m));
    await this.vestibule.connect();
    return this;
  }

  _vestibuleMessage(m) {
    if (!m || typeof m !== 'object') return;
    if (m.k === 'wait') return this._set('waiting');
    if (m.k === 'denied') return this._set('denied');
    if (m.k === 'approved') {
      const ok = /^[A-Z]$/.test(m.team || '') && typeof m.room === 'string' && /^oc-t-[a-z0-9]{20}$/.test(m.room);
      if (!ok) return;
      if (this.team && this.session && this.session.room === m.room) return;
      this.session = { pin: this.pin, team: m.team, room: m.room, c: m.c, l: m.l, v: m.v };
      this.onSession(this.session);
      this._openTeam(m.room).then(() => {
        this._set('approved');
        const v = this.vestibule;
        this.vestibule = null;
        if (v) setTimeout(() => v.close(), 1500);
      });
    }
  }

  async _openTeam(room) {
    const old = this.team;
    if (old) setTimeout(() => old.close(), 1500);       // the acknowledgement of the message that sent us here still has to leave
    this.team = new Canal({ room, name: this.name, role: 'equipo', id: this.id, mode: 'dial' });
    this.team.on('message', (_from, m) => this._teamMessage(m));
    this.team.on('peer', (p) => { if (p.role === 'director') { this.directorSeen = true; this.onStatus(this.status, this); this.onDirector(p); } });
    this.team.on('peerleave', () => this.onStatus(this.status, this));
    await this.team.connect();
  }

  _teamMessage(m) {
    if (!m || typeof m !== 'object') return;
    if (m.k === 'room' && /^oc-t-[a-z0-9]{20}$/.test(m.room || '')) {
      this.session = { ...this.session, room: m.room };
      this.onSession(this.session);
      this._openTeam(m.room);
      return;
    }
    if (m.k === 'approved') return this._vestibuleMessage(m);     // moved to another team
    if (m.k === 'out') { this.session = null; this.onSession(null); this.team?.close(); this.team = null; this._set('out'); return; }
    if (m.k === 'bal') { this.onData(m); return; }
    if (m.k === 'deliver' || m.k === 'sync') {
      const msg = validate({ c: m.c, l: m.l, v: m.v, t: m.t, s: m.s, i: m.i });
      if (!msg || (this.session && msg.team !== this.session.team)) return;      // a message for another team is never used
      this.onMessage(msg, m.k);
    }
  }

  get connected() { return !!(this.team && this.team.peers().some((p) => p.role === 'director')); }

  // A message to the director through the team room. Resolves true when it was sent, false when the director is not there.
  async sendToDirector(msg) {
    const dir = this.team && this.team.peers().find((p) => p.role === 'director');
    if (!dir) return false;
    try { await this.team.send(dir.id, msg); return true; } catch (e) { return false; }
  }

  async stop() { await this.vestibule?.close(); await this.team?.close(); }
}
