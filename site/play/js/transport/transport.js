// The Transporte interface and the layer every transport shares.
//
// A transport only has to move frames: it implements _open(), _close() and _raw(to, frame), and calls
// this._recv(frame) for every frame that arrives. Everything else lives here, so it behaves the same
// over a BroadcastChannel, WebRTC or a relay bus:
//
//   hello      who is here (id, name, role). A peer is "ready" once its hello arrives.
//   message    {n, p}: number n counted per destination, payload p (JSON).
//   ack        {n}: the receiver confirms n; the sender repeats the message until then.
//
// Messages are delivered once and in order: duplicates are dropped (but acknowledged again), an early
// message waits for the missing one, and a missing one is skipped after `gapMs` so one loss never
// freezes the conversation.
//
// Public API:
//   const t = new Subclass({room, name, role, reliability?})
//   await t.connect()                  open the channel and start saying hello
//   t.on('peer', fn)                   fn({id, name, role, sid}) when a peer becomes ready
//   t.on('peerleave', fn)              fn({id, ...})
//   t.on('message', fn)                fn(fromId, payload)
//   t.off(type, fn)                    undo on()
//   t.send(toId, payload)              Promise: resolves with the round trip (ms) once acknowledged
//   t.broadcast(payload)               send() to every ready peer; Promise.allSettled
//   t.peers()                          ready peers
//   t.stats                            counters (frames, retries, duplicates, gaps)
//   await t.close()

import { CONFIG } from './config.js';

const rid = (n = 8) => {
  const a = new Uint8Array(n);
  crypto.getRandomValues(a);
  return Array.from(a, (b) => (b % 36).toString(36)).join('');
};

export class Transporte {
  constructor({ room, name = '', role = 'equipo', id, reliability } = {}) {
    if (!room) throw new Error('Transporte: falta room');
    this.room = room;
    this.name = name;
    this.role = role;
    this.id = id || rid(8);
    this.sid = rid(6);                       // changes on every instance, so a reload is a new peer
    this.cfg = { ...CONFIG.reliability, ...(reliability || {}) };
    this.kind = 'base';
    this._peers = new Map();                 // id -> {id, name, role, sid, seen}
    this._outSeq = new Map();                // peer id -> last number sent
    this._pending = new Map();               // "to#n" -> {resolve, reject, frame, tries, t0, timer}
    this._in = new Map();                    // "from/sid" -> {next, buf: Map, gapTimer}
    this._handlers = { peer: [], peerleave: [], message: [], fail: [] };
    this._timers = new Set();
    this._closed = false;
    this.stats = { framesIn: 0, framesOut: 0, retries: 0, dupes: 0, gaps: 0, failed: 0, delivered: 0 };
  }

  // ---- what a transport implements -------------------------------------------------------------
  async _open() { throw new Error('not implemented'); }
  async _close() {}
  _raw(_to, _frame) { throw new Error('not implemented'); }   // to === null: everybody on the channel
  get sharedBus() { return true; }                              // false when the channel reports peers leaving itself

  // ---- public ----------------------------------------------------------------------------------
  on(type, fn) {
    if (!this._handlers[type]) throw new Error(`Transporte: evento desconocido ${type}`);
    this._handlers[type].push(fn);
    return this;
  }

  off(type, fn) {
    const list = this._handlers[type];
    const i = list ? list.indexOf(fn) : -1;
    if (i >= 0) list.splice(i, 1);
    return this;
  }

  _emit(type, ...args) {
    for (const fn of this._handlers[type]) {
      try { fn(...args); } catch (e) { console.error(e); }
    }
  }

  async connect() {
    await this._open();
    this._hello();
    this._loop(() => this._hello(), () => (this._peers.size ? this.cfg.keepAliveMs : this.cfg.helloMs));
    if (this.sharedBus) this._loop(() => this._expire(), () => 2000);
    return this;
  }

  peers() { return Array.from(this._peers.values()); }

  send(to, payload) {
    if (this._closed) return Promise.reject(new Error('cerrado'));
    return this._whenReady(to).then(() => this._sendReady(to, payload));
  }

  broadcast(payload) {
    return Promise.allSettled(this.peers().map((p) => this.send(p.id, payload)));
  }

  async close() {
    if (this._closed) return;
    try { this._raw(null, { t: 'b', f: this.id, s: this.sid }); } catch (_) { /* the channel may be gone */ }
    this._closed = true;
    for (const t of this._timers) clearTimeout(t);
    this._timers.clear();
    for (const p of this._pending.values()) { clearTimeout(p.timer); p.reject(new Error('cerrado')); }
    this._pending.clear();
    for (const st of this._in.values()) clearTimeout(st.gapTimer);
    await this._close();
  }

  // ---- internals -------------------------------------------------------------------------------
  _loop(fn, delay) {
    const tick = () => {
      if (this._closed) return;
      try { fn(); } catch (e) { console.error(e); }
      const t = setTimeout(tick, delay());
      this._timers.add(t);
    };
    const t = setTimeout(tick, delay());
    this._timers.add(t);
  }

  _hello() {
    this._rawSafe(null, { t: 'h', f: this.id, s: this.sid, name: this.name, role: this.role });
  }

  _rawSafe(to, frame) {
    if (this._closed) return;
    this.stats.framesOut++;
    try {
      const r = this._raw(to, frame);
      if (r && typeof r.catch === 'function') r.catch(() => {});
    } catch (_) { /* a lost frame is what the retries are for */ }
  }

  _whenReady(to) {
    if (this._peers.has(to)) return Promise.resolve();
    return new Promise((resolve, reject) => {
      const timer = setTimeout(() => { off(); reject(new Error('sin-par')); }, this.cfg.readyMs);
      const check = (p) => { if (p.id === to) { off(); resolve(); } };
      const off = () => {
        clearTimeout(timer);
        const i = this._handlers.peer.indexOf(check);
        if (i >= 0) this._handlers.peer.splice(i, 1);
      };
      this._handlers.peer.push(check);
    });
  }

  _sendReady(to, payload) {
    const n = (this._outSeq.get(to) || 0) + 1;
    this._outSeq.set(to, n);
    const frame = { t: 'm', f: this.id, s: this.sid, to, n, p: payload };
    return new Promise((resolve, reject) => {
      const key = `${to}#${n}`;
      const entry = { resolve, reject, frame, tries: 0, t0: performance.now(), timer: null, to };
      this._pending.set(key, entry);
      const attempt = () => {
        if (this._closed || !this._pending.has(key)) return;
        if (entry.tries >= this.cfg.maxTries) {
          this._pending.delete(key);
          this.stats.failed++;
          const err = new Error('sin-ack');
          this._emit('fail', { to, n, payload });
          reject(err);
          return;
        }
        if (entry.tries > 0) this.stats.retries++;
        entry.tries++;
        this._rawSafe(to, frame);
        entry.timer = setTimeout(attempt, this.cfg.retryMs * 1.5 ** (entry.tries - 1));
      };
      attempt();
    });
  }

  // Called by the subclass for every frame that arrives from the channel.
  _recv(frame) {
    if (this._closed || !frame || typeof frame !== 'object' || frame.f === this.id) return;
    if (frame.to && frame.to !== this.id) return;                   // addressed to somebody else on a shared bus
    this.stats.framesIn++;
    switch (frame.t) {
      case 'h': return this._onHello(frame);
      case 'b': return this._dropPeer(frame.f, frame.s);
      case 'a': return this._onAck(frame);
      case 'm': return this._onMessage(frame);
      default:
    }
  }

  _onHello(fr) {
    const known = this._peers.get(fr.f);
    if (known && known.sid !== fr.s) this._dropPeer(fr.f, known.sid);   // same id, new instance
    const peer = this._peers.get(fr.f);
    if (peer) { peer.seen = Date.now(); return; }
    const p = { id: fr.f, name: fr.name || '', role: fr.role || '', sid: fr.s, seen: Date.now() };
    this._peers.set(p.id, p);
    this._outSeq.set(p.id, 0);
    this._hello();            // answer at once, so the newcomer does not wait for the next tick
    this._emit('peer', p);
  }

  _touch(id) {
    const p = this._peers.get(id);
    if (p) p.seen = Date.now();
  }

  _dropPeer(id, sid) {
    const p = this._peers.get(id);
    if (!p || (sid && p.sid !== sid)) return;
    this._peers.delete(id);
    this._outSeq.delete(id);
    for (const [key, e] of this._pending) {
      if (e.to === id) { clearTimeout(e.timer); this._pending.delete(key); e.reject(new Error('par-salio')); }
    }
    for (const [key, st] of this._in) {
      if (key.startsWith(`${id}/`)) { clearTimeout(st.gapTimer); this._in.delete(key); }
    }
    this._emit('peerleave', p);
  }

  // Native "peer left" signals (WebRTC) call this.
  _peerGone(id) { this._dropPeer(id); }

  _expire() {
    const now = Date.now();
    for (const p of Array.from(this._peers.values())) {
      if (now - p.seen > this.cfg.peerTtlMs) this._dropPeer(p.id, p.sid);
    }
  }

  _onAck(fr) {
    if (fr.so !== this.sid) return;                          // for an earlier instance of this page
    this._touch(fr.f);
    const key = `${fr.f}#${fr.n}`;
    const e = this._pending.get(key);
    if (!e) return;                                          // an ack repeated by a second relay
    clearTimeout(e.timer);
    this._pending.delete(key);
    e.resolve(performance.now() - e.t0);
  }

  _onMessage(fr) {
    this._touch(fr.f);
    // Always acknowledge, even a duplicate: the first ack may be what was lost.
    this._rawSafe(fr.f, { t: 'a', f: this.id, s: this.sid, to: fr.f, so: fr.s, n: fr.n });
    const key = `${fr.f}/${fr.s}`;
    let st = this._in.get(key);
    if (!st) { st = { next: 1, buf: new Map(), gapTimer: null }; this._in.set(key, st); }
    if (fr.n < st.next || st.buf.has(fr.n)) { this.stats.dupes++; return; }
    st.buf.set(fr.n, fr.p);
    this._drain(fr.f, st);
    if (st.buf.size && !st.gapTimer) {
      st.gapTimer = setTimeout(() => {
        st.gapTimer = null;
        if (!st.buf.size || this._closed) return;
        this.stats.gaps++;
        st.next = Math.min(...st.buf.keys());                // skip what never arrived
        this._drain(fr.f, st);
      }, this.cfg.gapMs);
    }
  }

  _drain(from, st) {
    while (st.buf.has(st.next)) {
      const p = st.buf.get(st.next);
      st.buf.delete(st.next);
      st.next++;
      this.stats.delivered++;
      this._emit('message', from, p);
    }
    if (!st.buf.size && st.gapTimer) { clearTimeout(st.gapTimer); st.gapTimer = null; }
  }
}
