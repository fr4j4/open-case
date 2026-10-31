// A transport double for the tests: peers in the same page joined by a hub that loses, duplicates and
// delays frames at random (with a seeded generator, so a run can be repeated). The contract tests run the
// reliability layer against it.
import { Transporte } from './transport.js';

function mulberry32(a) {
  return () => {
    a |= 0; a = (a + 0x6D2B79F5) | 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

export class Hub {
  constructor({ loss = 0, dup = 0, maxDelayMs = 0, seed = 1 } = {}) {
    this.loss = loss;
    this.dup = dup;
    this.maxDelayMs = maxDelayMs;
    this.rand = mulberry32(seed);
    this.members = new Set();
    this.sent = 0;
    this.dropped = 0;
    this.duplicated = 0;
  }

  deliver(from, frame) {
    for (const m of this.members) {
      if (m === from) continue;
      this.sent++;
      if (this.rand() < this.loss) { this.dropped++; continue; }
      const copies = this.rand() < this.dup ? 2 : 1;
      if (copies === 2) this.duplicated++;
      for (let i = 0; i < copies; i++) {
        const copy = JSON.parse(JSON.stringify(frame));
        const delay = this.maxDelayMs ? Math.floor(this.rand() * this.maxDelayMs) : 0;
        setTimeout(() => m._recv(copy), delay);
      }
    }
  }
}

export class SimuladoTransporte extends Transporte {
  constructor(opts) {
    super(opts);
    this.kind = 'simulado';
    this.hub = opts.hub;
  }

  async _open() { this.hub.members.add(this); }
  async _close() { this.hub.members.delete(this); }
  _raw(_to, frame) { this.hub.deliver(this, frame); }
}
