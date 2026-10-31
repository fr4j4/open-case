// Made-up field data for the decision rules: 12 attempts per transport and network, over two days and
// three phones (an iPhone and two Androids), of which round(rate * 12) are successes.
export const NETS = ['wifi-casa', 'wifi-institucional', 'datos-mixto', 'hotspot'];
const DEVICES = [['iphone-Safari-aaaa', 'ios'], ['pixel-Chrome-bbbb', 'android'], ['moto-Chrome-cccc', 'android']];

export function attempts(transport, network, rate, count = 12) {
  const okCount = Math.round(rate * count);
  return Array.from({ length: count }, (_, i) => {
    const [device, os] = DEVICES[i % 3];
    return {
      transport, network, device, os, date: i % 2 ? '2026-11-02' : '2026-11-01', n: i + 1,
      connectMs: 900, rtt: [40, 55, 70],
      burst: i < okCount ? { got: 100, dup: 0, ordered: true } : { got: 93, dup: 0, ordered: true },
    };
  });
}

// rates: {network: rate} or a number for every network
export function field(transport, rates) {
  return NETS.flatMap((n) => attempts(transport, n, typeof rates === 'number' ? rates : rates[n] ?? 0));
}
