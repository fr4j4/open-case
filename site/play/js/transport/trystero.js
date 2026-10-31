// WebRTC through Trystero (the library is copied to ../../vendor/). Three strategies find the other
// peers: 'nostr', 'mqtt' and 'torrent'. They are loaded on demand: mqtt weighs 400 KB.
import { Transporte } from './transport.js';
import { CONFIG } from './config.js';

export class TrysteroTransporte extends Transporte {
  constructor(opts) {
    super(opts);
    this.strategy = opts.strategy || 'nostr';
    this.kind = `trystero-${this.strategy}`;
    this.joinErrors = [];
  }

  get sharedBus() { return false; }            // WebRTC reports peers leaving by itself

  async _open() {
    const mod = await import(`../../vendor/trystero-${this.strategy}.js`);
    const cfg = { appId: CONFIG.trystero.appId };
    if (CONFIG.trystero.relayUrls.length) cfg.relayConfig = { urls: CONFIG.trystero.relayUrls };
    if (CONFIG.trystero.iceServers.length) cfg.rtcConfig = { iceServers: CONFIG.trystero.iceServers };
    cfg.onJoinError = (d) => this.joinErrors.push(d);
    this._mod = mod;
    this._room = mod.joinRoom(cfg, this.room);
    this._action = this._room.makeAction('oc');
    this._action.onMessage = (frame) => this._recv(frame);
    this._room.onPeerJoin = () => this._hello();
    this._room.onPeerLeave = (peerId) => this._peerGone(peerId);   // our ids are Trystero's ids
    this.id = mod.selfId;                       // so the id matches the one Trystero shows for this peer
  }

  async _close() {
    if (this._room) await this._room.leave();
  }

  _raw(to, frame) {
    // Addressed frames travel to everybody in the room and the others drop them in _recv(): the room
    // has few peers, and it spares us a map from our ids to Trystero's.
    return this._action.send(frame);
  }
}
