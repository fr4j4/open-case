// The test the lab runs, without any screen: one attempt of one transport, seen from the director and
// from a team's phone. red.js draws the screens and chains the attempts; the CI drives these functions
// with the `broadcast` transport and several pages.
//
// What one attempt does:
//   1. everybody joins the room "<sala>~<transport>~<n>" (the control channel tells them which);
//   2. each phone measures how long it took to see the director (< 10 s counts as connected);
//   3. the director sends 10 messages to each phone and times the acknowledgement (round trip);
//   4. the director sends 100 numbered messages in a row; the phone checks none is missing, repeated or
//      out of order and reports;
//   5. optionally, a lock test: the phone locks its screen 30 s and tells whether the room came back.

import { crearTransporte, CONFIG } from '../../play/js/transport/index.js';
import { median, percentile } from './decision.js';

export const PINGS = 10;
export const BURST = 100;

export const roomOf = (sala, transport, n) => `${sala}~${transport}~${n}`;
export const keyOf = (transport, n) => `${transport}~${n}`;

const wait = (ms) => new Promise((r) => setTimeout(r, ms));
const today = () => new Date().toISOString().slice(0, 10);

export function deviceInfo(storage = globalThis.localStorage) {
  const ua = navigator.userAgent || '';
  const os = /iPhone|iPad|iPod/.test(ua) ? 'ios' : /Android/.test(ua) ? 'android' : 'otro';
  const browser = /CriOS|Chrome\//.test(ua) ? 'Chrome' : /FxiOS|Firefox\//.test(ua) ? 'Firefox' : /Safari\//.test(ua) ? 'Safari' : 'navegador';
  let id = null;
  try { id = storage.getItem('oc-lab-device'); } catch (_) { /* private mode */ }
  if (!id) {
    id = `${os}-${browser}-${Math.random().toString(36).slice(2, 6)}`;
    try { storage.setItem('oc-lab-device', id); } catch (_) { /* private mode */ }
  }
  const c = navigator.connection || {};
  return { id, os, browser, connection: c.type || c.effectiveType || '' };
}

// ---- director's side ---------------------------------------------------------------------------

// expect: how many phones should show up. expectedDevices (optional): their device ids, from the control
// channel, to name the ones that did not.
export async function intentoDirector({
  sala, transport, n, expect, expectedDevices = [], network = 'otra', ctl = null, lock = false,
  crear = crearTransporte, waitMs = CONFIG.connectTimeoutMs + 8000, lockWaitMs = 90000, resultsWaitMs = 4000,
  onStatus = () => {}, signal = null,
}) {
  const key = keyOf(transport, n);
  const date = today();
  const reports = new Map();            // device -> {connectMs, error, os}
  const bursts = new Map();             // transport peer id -> burst report
  const locks = new Map();              // device -> lock result
  const onCtl = (_from, p) => {
    if (!p || p.key !== key) return;
    if (p.k === 'result') reports.set(p.device, p);
    if (p.k === 'lock') locks.set(p.device, p);
  };
  if (ctl) ctl.on('message', onCtl);

  const t0 = performance.now();
  const T = crear(transport, { room: roomOf(sala, transport, n), name: 'director', role: 'director' });
  const readyAt = new Map();            // peer id -> ms since t0
  T.on('peer', (p) => { if (p.role === 'equipo') readyAt.set(p.id, performance.now() - t0); });
  T.on('message', (from, p) => { if (p && p.k === 'breport') bursts.set(from, p); });

  if (ctl) ctl.broadcast({ k: 'start', key, transport, n, network, lock }).catch(() => {});
  let openError = null;
  try {
    await T.connect();
  } catch (e) {
    openError = String(e.message || e);
  }

  // 1. wait for the phones
  const want = Math.max(expect, expectedDevices.length);
  const limit = performance.now() + waitMs;
  onStatus(`Esperando a ${want} teléfono(s)…`);
  while (!openError && readyAt.size < want && performance.now() < limit && !(signal && signal.aborted)) await wait(100);

  // 2. round trip and burst, one phone at a time
  const rows = [];
  for (const peer of T.peers().filter((p) => p.role === 'equipo')) {
    onStatus(`Midiendo con ${peer.name}…`);
    const row = { transport, n, network, date, device: peer.name, os: null, connectMs: null, directorSeenMs: readyAt.get(peer.id) ?? null, rtt: [], burst: null, error: null };
    try {
      for (let i = 0; i < PINGS; i++) row.rtt.push(await T.send(peer.id, { k: 'ping', i }));
      const before = T.stats.retries;
      const tb = performance.now();
      const sends = [];
      for (let i = 0; i < BURST; i++) sends.push(T.send(peer.id, { k: 'b', i }).catch((e) => e));
      sends.push(T.send(peer.id, { k: 'bend' }).catch((e) => e));
      await Promise.all(sends);
      const ms = performance.now() - tb;
      const retries = T.stats.retries - before;
      const limitB = performance.now() + 15000;
      while (!bursts.has(peer.id) && performance.now() < limitB) await wait(50);
      const rep = bursts.get(peer.id);
      row.burst = rep ? { got: rep.got, dup: rep.dup, ordered: rep.ordered, ms, retries } : { got: 0, dup: 0, ordered: false, ms, retries };
    } catch (e) {
      row.error = String(e.message || e);
    }
    rows.push(row);
  }

  // 3. optional lock test: keep the room open while the phones lock their screens
  if (lock && rows.length) {
    onStatus('Prueba de bloqueo: bloqueen la pantalla 30 s y vuelvan.');
    const limitL = performance.now() + lockWaitMs;
    while (locks.size < rows.length && performance.now() < limitL && !(signal && signal.aborted)) await wait(250);
  }

  // 4. what the phones report about themselves
  if (ctl) {
    const limitR = performance.now() + resultsWaitMs;
    const names = new Set([...rows.map((r) => r.device), ...expectedDevices]);
    while ([...names].some((d) => !reports.has(d)) && performance.now() < limitR) await wait(100);
  }
  for (const row of rows) {
    const rep = reports.get(row.device);
    if (rep) { row.connectMs = rep.connectMs; row.os = rep.os || row.os; row.error = row.error || rep.error || null; }
    else row.connectMs = row.directorSeenMs;
    const lk = locks.get(row.device);
    if (lk) row.lock = { hiddenMs: lk.hiddenMs, recovered: lk.recovered, ms: lk.ms };
  }
  // Phones that were expected and never appeared.
  for (const d of expectedDevices) {
    if (rows.some((r) => r.device === d)) continue;
    const rep = reports.get(d);
    rows.push({ transport, n, network, date, device: d, os: rep ? rep.os : null, connectMs: rep ? rep.connectMs : null, directorSeenMs: null, rtt: [], burst: null, error: (rep && rep.error) || 'no llegó al director' });
  }
  if (openError) rows.forEach((r) => { r.error = r.error || openError; });
  if (openError && !rows.length) rows.push({ transport, n, network, date, device: '(director)', connectMs: null, rtt: [], burst: null, error: openError });

  const stats = { ...T.stats };
  if (ctl) { ctl.off('message', onCtl); ctl.broadcast({ k: 'end', key }).catch(() => {}); }
  await T.close();
  return { rows, stats, key };
}

// ---- the phones' side ----------------------------------------------------------------------------

// Joins the room of one attempt, answers the director's burst and measures how long it took to see the
// director. Returns {result, close()}; `result` settles when the director is seen or the time is over.
export async function intentoEquipo({
  sala, transport, n, device, ctl = null, lock = false, crear = crearTransporte,
  timeoutMs = CONFIG.connectTimeoutMs * 2, onStatus = () => {}, doc = globalThis.document,
}) {
  const key = keyOf(transport, n);
  const t0 = performance.now();
  const T = crear(transport, { room: roomOf(sala, transport, n), name: device.id, role: 'equipo' });
  let got = 0;
  let dup = 0;
  let ordered = true;
  let last = -1;
  const seen = new Set();
  let directorId = null;
  T.on('message', (from, p) => {
    if (!p) return;
    if (p.k === 'b') {
      got++;
      if (seen.has(p.i)) dup++;
      seen.add(p.i);
      if (p.i <= last) ordered = false;
      last = Math.max(last, p.i);
    } else if (p.k === 'bend') {
      T.send(from, { k: 'breport', got, dup, ordered }).catch(() => {});
    }
  });

  const found = new Promise((resolve) => {
    T.on('peer', (p) => {
      if (p.role === 'director') { directorId = p.id; resolve(performance.now() - t0); }
    });
  });
  let error = null;
  try {
    await T.connect();
  } catch (e) {
    error = String(e.message || e);
  }
  onStatus('Buscando al director…');
  const connectMs = error ? null : await Promise.race([found, wait(timeoutMs).then(() => null)]);
  if (!error && connectMs === null) error = 'no vio al director';
  const result = { k: 'result', key, device: device.id, os: device.os, connectMs, error };
  if (ctl) ctl.broadcast(result).catch(() => {});

  // Lock test: when the screen comes back after >= 20 s, ask the director to confirm the room is alive.
  let off = () => {};
  if (lock && doc && directorId) {
    let hiddenAt = null;
    const onVis = async () => {
      if (doc.visibilityState === 'hidden') { hiddenAt = Date.now(); return; }
      if (hiddenAt === null) return;
      const hiddenMs = Date.now() - hiddenAt;
      hiddenAt = null;
      if (hiddenMs < 20000) return;
      const tl = performance.now();
      let recovered = false;
      try { await T.send(directorId, { k: 'lockping' }); recovered = performance.now() - tl < 15000; } catch (_) { /* did not come back */ }
      const out = { k: 'lock', key, device: device.id, hiddenMs, recovered, ms: performance.now() - tl };
      if (ctl) ctl.broadcast(out).catch(() => {});
      onStatus(recovered ? `Volvió a conectar tras ${Math.round(hiddenMs / 1000)} s.` : 'No volvió a conectar.');
    };
    doc.addEventListener('visibilitychange', onVis);
    off = () => doc.removeEventListener('visibilitychange', onVis);
  }
  return { result, T, close: async () => { off(); await T.close(); } };
}

// ---- numbers for the screens -----------------------------------------------------------------------
export function rttOf(rows) {
  const all = rows.flatMap((r) => r.rtt || []);
  return { median: median(all), p95: percentile(all, 0.95), n: all.length };
}
