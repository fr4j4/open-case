// Tabs of the same browser talking through a BroadcastChannel. For tests and demos: it never touches
// the network, so it says nothing about real networks.
import { Transporte } from './transport.js';

export class BroadcastTransporte extends Transporte {
  constructor(opts) {
    super(opts);
    this.kind = 'broadcast';
  }

  async _open() {
    this._bc = new BroadcastChannel(`open-case:${this.room}`);
    this._bc.onmessage = (ev) => this._recv(ev.data);
  }

  async _close() {
    if (this._bc) this._bc.close();
  }

  _raw(_to, frame) {
    this._bc.postMessage(frame);     // everybody gets it; _recv() ignores what is not addressed to this peer
  }
}
