// A channel to the other devices of a room, made of the transport chosen in transport/config.js and, if that one does
// not connect, the backup one (config.js `fallback`). Same interface as a Transporte, so the rest of the app does not
// care which one carries the messages:
//   const c = new Canal({room, name, role, id, mode})
//   await c.connect()           never throws: a transport that does not open is skipped (c.errors says why)
//   c.on('peer'|'peerleave'|'message', fn)   same arguments as Transporte
//   c.send(to, payload)          Promise; tries the other transport if the first one fails
//   c.peers(), c.broadcast(payload), await c.close()
//
// mode 'listen' (the director) opens both transports at once, so a phone that only reaches the backup finds it.
// mode 'dial' (a phone) opens the main one and adds the backup if nobody answers within connectTimeoutMs.
import { CONFIG, TRANSPORTS } from './transport/config.js';
import { crearTransporte } from './transport/index.js';

// ?transport=broadcast (tests, the network lab): that transport alone, no backup. ?relays=wss://a,wss://b sets the
// relays of the `relay` transport (a local one in the tests).
export function chosenTransports() {
  try {
    const q = new URLSearchParams(location.search);
    const urls = (q.get('relays') || '').split(',').filter((u) => /^wss?:\/\//.test(u));
    const name = q.get('transport');
    if (name && TRANSPORTS.includes(name)) return { primary: name, fallback: null, urls };
    if (urls.length) return { primary: CONFIG.primary, fallback: CONFIG.fallback, urls };
  } catch (e) { /* no location: the defaults */ }
  return { primary: CONFIG.primary, fallback: CONFIG.fallback, urls: [] };
}

export class Canal {
  constructor({ room, name = '', role = 'equipo', id, mode = 'dial', primary, fallback, timeoutMs } = {}) {
    const chosen = chosenTransports();
    this.opts = { room, name, role, id };
    this.urls = chosen.urls;
    this.mode = mode;
    this.primary = primary || chosen.primary;
    this.fallback = fallback === undefined ? chosen.fallback : fallback;
    this.timeoutMs = timeoutMs || CONFIG.connectTimeoutMs;
    this.transports = [];
    this.errors = [];
    this.id = id;
    this._peers = new Map();       // peer id -> {info, via: Set of transports}
    this._handlers = { peer: [], peerleave: [], message: [] };
    this._timer = null;
    this._closed = false;
  }

  on(type, fn) { this._handlers[type].push(fn); return this; }
  off(type, fn) { const l = this._handlers[type]; const i = l.indexOf(fn); if (i >= 0) l.splice(i, 1); return this; }
  _emit(type, ...a) { for (const fn of this._handlers[type]) { try { fn(...a); } catch (e) { console.error(e); } } }

  async connect() {
    const first = await this._add(this.primary);
    if (!this.fallback || this.fallback === this.primary) return this;
    if (this.mode === 'listen' || !first) { await this._add(this.fallback); return this; }
    this._timer = setTimeout(() => {
      if (!this._closed && !this._peers.size) this._add(this.fallback);
    }, this.timeoutMs);
    return this;
  }

  async _add(kind) {
    if (this._closed || this.transports.some((t) => t.name_ === kind)) return null;
    let t;
    try {
      t = crearTransporte(kind, kind === 'relay' && this.urls.length ? { ...this.opts, urls: this.urls } : this.opts);
      t.name_ = kind;
      t.on('peer', (p) => this._peer(t, p));
      t.on('peerleave', (p) => this._leave(t, p));
      t.on('message', (from, payload) => this._emit('message', from, payload));
      await t.connect();
    } catch (e) {
      this.errors.push({ transport: kind, error: String(e && e.message || e) });
      return null;
    }
    if (this._closed) { t.close(); return null; }
    this.transports.push(t);
    return t;
  }

  _peer(t, p) {
    let e = this._peers.get(p.id);
    if (!e) { e = { info: p, via: new Set() }; this._peers.set(p.id, e); e.via.add(t); this._emit('peer', p); return; }
    e.info = p;
    e.via.add(t);
  }

  _leave(t, p) {
    const e = this._peers.get(p.id);
    if (!e) return;
    e.via.delete(t);
    if (!e.via.size) { this._peers.delete(p.id); this._emit('peerleave', p); }
  }

  peers() { return [...this._peers.values()].map((e) => e.info); }
  get kinds() { return this.transports.map((t) => t.name_); }

  async send(to, payload) {
    const e = this._peers.get(to);
    if (!e) throw new Error('sin-par');
    let last = null;
    for (const t of [...e.via]) {
      try { return await t.send(to, payload); } catch (err) { last = err; }
    }
    throw last || new Error('sin-par');
  }

  broadcast(payload) { return Promise.allSettled(this.peers().map((p) => this.send(p.id, payload))); }

  async close() {
    this._closed = true;
    clearTimeout(this._timer);
    await Promise.allSettled(this.transports.map((t) => t.close()));
    this.transports = [];
    this._peers.clear();
  }
}
