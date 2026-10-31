// The decision rules of F0, as code, so the lab applies them to the field data and the CI tests them
// with made-up data. The rules (docs/web-network-test.md) are applied in this order and the first
// that holds wins:
//   1. The relay bus alone reaches >= 95 % in every network       -> bus first, WebRTC optional.
//   2. WebRTC reaches >= 90 % at home and on the hotspot, and the bus covers the rest with >= 95 %
//                                                                  -> WebRTC first, bus as backup.
//   3. Neither                                                     -> plan B (Firebase or Supabase), to decide with fr4j4.
// A decision needs data: at least 10 attempts per transport and network, in two different days, with
// at least 4 kinds of network, 3 phones, an iPhone and an Android.

export const RULES = {
  minAttempts: 10,
  minDays: 2,
  minNetworks: 4,
  minDevices: 3,
  busMin: 0.95,
  webrtcMin: 0.90,
  connectMs: 10000,
  burstSize: 100,
};

export const NETWORKS = [
  { id: 'wifi-casa', label: 'Wi-Fi de casa' },
  { id: 'wifi-institucional', label: 'Wi-Fi institucional' },
  { id: 'datos-mixto', label: 'Datos móviles mezclados con Wi-Fi' },
  { id: 'hotspot', label: 'Hotspot del director' },
  { id: 'otra', label: 'Otra red' },
];

// One attempt = one phone trying one transport once.
// {transport, network, device, os, date, ok, connectMs, burst:{got, dup, ordered}, ...}
export function isSuccess(a, rules = RULES) {
  return Boolean(a.connectMs != null && a.connectMs < rules.connectMs && a.burst &&
    a.burst.got === rules.burstSize && !a.burst.dup && a.burst.ordered !== false);
}

export function median(xs) {
  if (!xs.length) return null;
  const s = [...xs].sort((x, y) => x - y);
  const m = s.length >> 1;
  return s.length % 2 ? s[m] : (s[m - 1] + s[m]) / 2;
}

export function percentile(xs, p) {
  if (!xs.length) return null;
  const s = [...xs].sort((x, y) => x - y);
  return s[Math.min(s.length - 1, Math.ceil(p * s.length) - 1)];
}

// Groups attempts by transport and network.
export function summarize(attempts, rules = RULES) {
  const by = new Map();
  for (const a of attempts) {
    const key = `${a.transport}|${a.network}`;
    if (!by.has(key)) by.set(key, { transport: a.transport, network: a.network, attempts: 0, ok: 0, connect: [], rtt: [], lockTried: 0, lockOk: 0 });
    const g = by.get(key);
    g.attempts++;
    if (isSuccess(a, rules)) g.ok++;
    if (a.connectMs != null) g.connect.push(a.connectMs);
    if (a.rtt && a.rtt.length) g.rtt.push(...a.rtt);
    if (a.lock) { g.lockTried++; if (a.lock.recovered) g.lockOk++; }
  }
  return [...by.values()].map((g) => ({
    transport: g.transport,
    network: g.network,
    attempts: g.attempts,
    ok: g.ok,
    rate: g.attempts ? g.ok / g.attempts : 0,
    connectMedianMs: median(g.connect),
    rttMedianMs: median(g.rtt),
    rttP95Ms: percentile(g.rtt, 0.95),
    lockTried: g.lockTried,
    lockOk: g.lockOk,
  }));
}

function kindOfDevice(a) {
  return (a.os || '').toLowerCase();
}

// What is missing before the numbers mean anything.
export function missingData(attempts, rules = RULES) {
  const missing = [];
  const days = new Set(attempts.map((a) => a.date));
  if (days.size < rules.minDays) missing.push(`faltan días de prueba: hay ${days.size} y se piden ${rules.minDays}`);
  const networks = new Set(attempts.map((a) => a.network));
  if (networks.size < rules.minNetworks) missing.push(`faltan tipos de red: hay ${networks.size} y se piden ${rules.minNetworks}`);
  const devices = new Set(attempts.map((a) => a.device));
  if (devices.size < rules.minDevices) missing.push(`faltan teléfonos: hay ${devices.size} y se piden ${rules.minDevices}`);
  const oses = new Set(attempts.map(kindOfDevice));
  if (!oses.has('ios')) missing.push('falta un iPhone');
  if (!oses.has('android')) missing.push('falta un Android');
  const rows = summarize(attempts, rules);
  const transports = new Set(rows.map((r) => r.transport));
  for (const t of transports) {
    for (const n of networks) {
      const r = rows.find((x) => x.transport === t && x.network === n);
      const have = r ? r.attempts : 0;
      if (have < rules.minAttempts) missing.push(`${t} en ${n}: ${have} intentos de ${rules.minAttempts}`);
    }
  }
  return missing;
}

const rateOf = (rows, transport, network) => rows.find((r) => r.transport === transport && r.network === network)?.rate ?? 0;

// Returns {rule, text, config, missing, rows}. `rule` is 1, 2, 3 or null when no rule holds with the data
// there is. `config` is what to write into transport/config.js.
export function decide(attempts, rules = RULES) {
  const rows = summarize(attempts, rules);
  const missing = missingData(attempts, rules);
  const networks = [...new Set(attempts.map((a) => a.network))];
  const webrtc = [...new Set(rows.map((r) => r.transport))].filter((t) => t.startsWith('trystero-'));
  const out = { rows, missing, complete: missing.length === 0 };

  const busEverywhere = networks.length > 0 && networks.every((n) => rateOf(rows, 'relay', n) >= rules.busMin);
  if (busEverywhere) {
    return { ...out, rule: 1, text: 'Bus por relé primero; WebRTC opcional (menos piezas que mantener).',
      config: { primary: 'relay', fallback: webrtc[0] || null } };
  }

  // The best WebRTC strategy: the one that reaches the required rate at home and on the hotspot.
  const good = webrtc.filter((t) => rateOf(rows, t, 'wifi-casa') >= rules.webrtcMin && rateOf(rows, t, 'hotspot') >= rules.webrtcMin);
  // Rule 2: the bus only has to cover the networks where WebRTC falls short.
  if (good.length) {
    const rest = networks.filter((n) => rateOf(rows, good[0], n) < rules.webrtcMin);
    if (rest.every((n) => rateOf(rows, 'relay', n) >= rules.busMin)) {
      return { ...out, rule: 2, text: `WebRTC primero (${good[0]}) y el bus por relé de respaldo.`,
        config: { primary: good[0], fallback: 'relay' } };
    }
  }
  if (!attempts.length) return { ...out, rule: null, text: 'Sin datos.', config: null };
  return { ...out, rule: 3, text: 'Ninguno llega a las cifras: plan B (Firebase o Supabase en F3, a decidir con fr4j4) o quedarse en F2, que no necesita red.', config: null };
}
