// A message bus over public Nostr relays. Every message is an ephemeral Nostr event (kind 2xxxx, which
// relays pass on and do not store) whose content is encrypted with AES-GCM using a key derived from the
// room name: the relays carry text they cannot read, and anybody who knows the room name can join.
// Several relays are kept open at once, so one down does not break the bus. Events are signed with a
// throwaway key made for each page (the Schnorr code is the one Trystero uses, copied to ../../vendor/).
import { Transporte } from './transport.js';
import { CONFIG } from './config.js';

const enc = new TextEncoder();
const hex = (buf) => Array.from(new Uint8Array(buf), (b) => b.toString(16).padStart(2, '0')).join('');
const b64 = (bytes) => btoa(String.fromCharCode(...bytes));
const unb64 = (s) => Uint8Array.from(atob(s), (c) => c.charCodeAt(0));

async function sha256(text) { return crypto.subtle.digest('SHA-256', enc.encode(text)); }

export class RelayTransporte extends Transporte {
  constructor(opts) {
    super(opts);
    this.kind = 'relay';
    this.urls = opts.urls || [];
    this.sockets = new Map();       // url -> {ws, open, tries}
    this.seenEvents = new Set();
    this.relayStats = { opened: 0, errors: 0, rejected: 0 };
  }

  async _open() {
    const [nobleMod, nostr] = await Promise.all([
      import('../../vendor/noble-secp256k1.js'),
      import('../../vendor/trystero-nostr.js'),
    ]);
    this._noble = nobleMod;
    const urls = (this.urls.length ? this.urls : CONFIG.relay.urls.length ? CONFIG.relay.urls : nostr.defaultRelayUrls)
      .slice(0, Math.max(1, CONFIG.relay.redundancy));
    this._secret = nobleMod.utils.randomSecretKey();
    this._pubkey = hex(nobleMod.schnorr.getPublicKey(this._secret));
    this._topic = hex(await sha256(`oc-topic|${this.room}`)).slice(0, 32);
    this._key = await crypto.subtle.importKey('raw', await sha256(`oc-key|${this.room}`), 'AES-GCM', false, ['encrypt', 'decrypt']);
    this._subId = `oc${Math.random().toString(36).slice(2, 10)}`;
    for (const url of urls) this._connectSocket(url);
    // Ready as soon as one relay is open (or fail after the connect timeout).
    await new Promise((resolve, reject) => {
      const t0 = Date.now();
      const check = () => {
        if (this._closed) return reject(new Error('cerrado'));
        if ([...this.sockets.values()].some((s) => s.open)) return resolve();
        if (Date.now() - t0 > CONFIG.connectTimeoutMs) return reject(new Error('ningún relé abrió'));
        setTimeout(check, 100);
      };
      check();
    });
  }

  openRelays() { return [...this.sockets.values()].filter((s) => s.open).length; }

  _connectSocket(url) {
    const st = this.sockets.get(url) || { ws: null, open: false, tries: 0 };
    this.sockets.set(url, st);
    if (this._closed) return;
    let ws;
    try { ws = new WebSocket(url); } catch (_) { this.relayStats.errors++; return; }
    st.ws = ws;
    ws.onopen = () => {
      st.open = true;
      st.tries = 0;
      this.relayStats.opened++;
      ws.send(JSON.stringify(['REQ', this._subId, { kinds: [CONFIG.relay.kind], '#t': [this._topic], since: Math.floor(Date.now() / 1000) - 5 }]));
    };
    ws.onmessage = (ev) => this._onSocketMessage(ev.data);
    ws.onerror = () => { this.relayStats.errors++; };
    ws.onclose = () => {
      st.open = false;
      if (this._closed) return;
      st.tries++;
      setTimeout(() => this._connectSocket(url), Math.min(1000 * 2 ** st.tries, 15000));
    };
  }

  async _onSocketMessage(data) {
    let msg;
    try { msg = JSON.parse(data); } catch (_) { return; }
    if (msg[0] === 'OK' && msg[2] === false) { this.relayStats.rejected++; return; }
    if (msg[0] !== 'EVENT' || msg[1] !== this._subId) return;
    const ev = msg[2];
    if (!ev || ev.pubkey === this._pubkey || this.seenEvents.has(ev.id)) return;
    this.seenEvents.add(ev.id);
    if (this.seenEvents.size > 5000) this.seenEvents.clear();
    try {
      const raw = unb64(ev.content);
      const plain = await crypto.subtle.decrypt({ name: 'AES-GCM', iv: raw.slice(0, 12) }, this._key, raw.slice(12));
      this._recv(JSON.parse(new TextDecoder().decode(plain)));
    } catch (_) { /* not ours, or damaged */ }
  }

  async _raw(_to, frame) {
    const iv = crypto.getRandomValues(new Uint8Array(12));
    const body = new Uint8Array(await crypto.subtle.encrypt({ name: 'AES-GCM', iv }, this._key, enc.encode(JSON.stringify(frame))));
    const content = b64(new Uint8Array([...iv, ...body]));
    const ev = { kind: CONFIG.relay.kind, tags: [['t', this._topic]], created_at: Math.floor(Date.now() / 1000), content, pubkey: this._pubkey };
    const id = new Uint8Array(await sha256(JSON.stringify([0, ev.pubkey, ev.created_at, ev.kind, ev.tags, ev.content])));
    ev.id = hex(id);
    ev.sig = hex(await this._noble.schnorr.signAsync(id, this._secret));
    const text = JSON.stringify(['EVENT', ev]);
    for (const s of this.sockets.values()) if (s.open && s.ws.readyState === 1) s.ws.send(text);
  }

  async _close() {
    for (const s of this.sockets.values()) {
      try { s.ws.send(JSON.stringify(['CLOSE', this._subId])); } catch (_) { /* already closed */ }
      try { s.ws.close(); } catch (_) { /* already closed */ }
    }
  }
}
