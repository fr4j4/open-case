// The factory: transport(name, options) gives a Transporte of the kind named in config.js.
import { CONFIG, TRANSPORTS } from './config.js';
import { Transporte } from './transport.js';
import { BroadcastTransporte } from './broadcast.js';
import { TrysteroTransporte } from './trystero.js';
import { RelayTransporte } from './relay.js';

export { CONFIG, TRANSPORTS, Transporte };

export function crearTransporte(name, opts) {
  if (name === 'broadcast') return new BroadcastTransporte(opts);
  if (name === 'relay') return new RelayTransporte(opts);
  if (name.startsWith('trystero-')) return new TrysteroTransporte({ ...opts, strategy: name.slice('trystero-'.length) });
  throw new Error(`Transporte desconocido: ${name}`);
}
