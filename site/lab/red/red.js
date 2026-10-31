// The screens of the network lab. The measuring is in lab.js, the decision rules in decision.js and the
// transports in ../../play/js/transport/.
//
//   ?rol=director        start as the director (otherwise the page asks)
//   ?sala=K7QX2          room code; a phone that opens a link with it joins as a team
//   ?control=relay       transport of the control channel (relay by default; broadcast for same-browser tests)
//   ?transports=a,b      transports offered (default: the three Trystero strategies and the relay bus)
//   ?auto=1              director: start the full test as soon as `esperar` phones are connected
//   ?intentos=10&esperar=3&red=wifi-casa   presets for the director's form

import { crearTransporte, TRANSPORTS } from '../../play/js/transport/index.js';
import { intentoDirector, intentoEquipo, deviceInfo } from './lab.js';
import { NETWORKS, decide, RULES } from './decision.js';
import { qrcode } from '../../play/vendor/qrcode-generator.js';

const $ = (id) => document.getElementById(id);
const params = new URLSearchParams(location.search);
const CODE_CHARS = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789';
const randomCode = () => Array.from(crypto.getRandomValues(new Uint8Array(5)), (b) => CODE_CHARS[b % CODE_CHARS.length]).join('');
const STORE = 'oc-lab-results';
const DEFAULT_TRANSPORTS = TRANSPORTS.filter((t) => t !== 'broadcast');

const state = { sala: null, attempts: [], ctl: null, stop: false, running: false };
window.__lab = state;          // the CI reads the results from here

function load() {
  try { return JSON.parse(localStorage.getItem(STORE) || '[]'); } catch (_) { return []; }
}
function save() {
  try { localStorage.setItem(STORE, JSON.stringify(state.attempts)); } catch (_) { /* private mode */ }
}

function fillNetworks(select, selected) {
  select.innerHTML = '';
  for (const n of NETWORKS) {
    const o = document.createElement('option');
    o.value = n.id;
    o.textContent = n.label;
    if (n.id === selected) o.selected = true;
    select.appendChild(o);
  }
}

function setPill(el, ok, text) {
  el.textContent = text;
  el.className = `pill ${ok ? 'ok' : 'bad'}`;
}

async function joinControl(role, name, onMessage) {
  const kind = params.get('control') || 'relay';
  const ctl = crearTransporte(kind, { room: `${state.sala}~ctl`, name, role });
  ctl.on('message', onMessage);
  await ctl.connect();
  return ctl;
}

// ---- boot --------------------------------------------------------------------------------------
function boot() {
  const sala = (params.get('sala') || '').toUpperCase();
  const rol = params.get('rol');
  if (rol === 'director') return startDirector(sala || randomCode());
  if (sala) return startEquipo(sala);
  $('inicio').hidden = false;
  $('soy-director').onclick = () => { $('inicio').hidden = true; startDirector(randomCode()); };
  $('soy-equipo').onclick = () => {
    const s = $('sala-in').value.trim().toUpperCase();
    if (!s) { $('sala-in').focus(); return; }
    $('inicio').hidden = true;
    startEquipo(s);
  };
}

// ---- director ----------------------------------------------------------------------------------
async function startDirector(sala) {
  state.sala = sala;
  state.attempts = load();
  $('director').hidden = false;
  $('sala-dir').textContent = sala;

  const join = new URL(location.href);
  join.search = `?sala=${sala}${params.get('control') ? `&control=${params.get('control')}` : ''}`;
  join.hash = '';
  $('url-unir').textContent = join.href;
  try {
    const q = qrcode(0, 'M');
    q.addData(join.href);
    q.make();
    $('qr').innerHTML = q.createSvgTag({ scalable: true, margin: 1 });
  } catch (e) {
    $('qr').textContent = 'No se pudo dibujar el QR; usa el enlace.';
  }

  fillNetworks($('red'), params.get('red') || 'wifi-casa');
  if (params.get('intentos')) $('intentos').value = params.get('intentos');
  if (params.get('esperar')) $('esperar').value = params.get('esperar');
  const offered = (params.get('transports') || '').split(',').filter(Boolean);
  const list = offered.length ? offered : DEFAULT_TRANSPORTS;
  $('transportes').innerHTML = '';
  for (const t of list) {
    const l = document.createElement('label');
    l.innerHTML = `<input type="checkbox" value="${t}" checked> ${t}`;
    $('transportes').appendChild(l);
  }

  try {
    state.ctl = await joinControl('director', 'director', () => {});
    state.ctl.on('peer', refreshPhones).on('peerleave', refreshPhones);
    setPill($('ctl-estado'), true, 'conectado');
  } catch (e) {
    setPill($('ctl-estado'), false, `sin control (${e.message}); usa el modo manual de los teléfonos`);
  }
  setInterval(refreshPhones, 2000);
  refreshPhones();
  render();

  $('run-full').onclick = () => runFull(false);
  $('run-one').onclick = () => runOne(false);
  $('run-lock').onclick = () => runOne(true);
  $('run-stop').onclick = () => { state.stop = true; setStatus('Deteniendo al terminar la ronda…'); };
  $('copiar').onclick = async () => { try { await navigator.clipboard.writeText(exportJson()); setStatus('JSON copiado.'); } catch (_) { setStatus('No se pudo copiar; usa Descargar.'); } };
  $('bajar').onclick = download;
  $('limpiar').onclick = () => { if (confirm('¿Borrar todos los resultados guardados en este teléfono?')) { state.attempts = []; save(); render(); } };
  $('fusionar').onclick = merge;

  if (params.get('auto') === '1') {
    const want = Number($('esperar').value);
    const timer = setInterval(() => {
      if (phones().length >= want) { clearInterval(timer); runFull(false); }
    }, 250);
  }
}

const phones = () => (state.ctl ? state.ctl.peers().filter((p) => p.role === 'equipo') : []);

function refreshPhones() {
  const list = phones();
  $('n-tel').textContent = String(list.length);
  $('telefonos').innerHTML = '';
  for (const p of list) {
    const li = document.createElement('li');
    li.textContent = p.name;
    $('telefonos').appendChild(li);
  }
}

function setStatus(text) { $('estado').textContent = text; }

function selectedTransports() {
  return Array.from($('transportes').querySelectorAll('input:checked'), (i) => i.value);
}

async function round(transport, n, lock) {
  const names = phones().map((p) => p.name);
  const { rows } = await intentoDirector({
    sala: state.sala, transport, n, expect: Number($('esperar').value), expectedDevices: names,
    network: $('red').value, ctl: state.ctl, lock, onStatus: (t) => setStatus(`${transport} · intento ${n} · ${t}`),
  });
  state.attempts.push(...rows);
  save();
  render();
}

async function runOne(lock) {
  if (state.running) return;
  state.running = true;
  state.stop = false;
  const t = selectedTransports()[0];
  if (!t) { setStatus('Elige un transporte.'); state.running = false; return; }
  const n = state.attempts.filter((a) => a.transport === t && a.network === $('red').value).length + 1;
  await round(t, n, lock);
  setStatus('Ronda lista.');
  state.running = false;
}

async function runFull(lock) {
  if (state.running) return;
  state.running = true;
  state.stop = false;
  const per = Number($('intentos').value);
  for (const t of selectedTransports()) {
    for (let i = 1; i <= per && !state.stop; i++) {
      const n = state.attempts.filter((a) => a.transport === t && a.network === $('red').value).length + 1;
      await round(t, n, lock);
    }
  }
  setStatus(state.stop ? 'Detenido.' : 'Prueba completa lista.');
  state.running = false;
  state.done = true;
}

function pct(x) { return `${Math.round(x * 100)} %`; }
const ms = (x) => (x == null ? '–' : `${Math.round(x)} ms`);

function render() {
  const d = decide(state.attempts);
  const label = (id) => (NETWORKS.find((n) => n.id === id) || { label: id }).label;
  let html = '<table><thead><tr><th>Transporte</th><th>Red</th><th>Intentos</th><th>Éxito</th><th>Conecta (mediana)</th><th>Ida y vuelta (mediana / p95)</th><th>Bloqueo 30 s</th></tr></thead><tbody>';
  for (const r of d.rows) {
    html += `<tr><td>${r.transport}</td><td>${label(r.network)}</td><td>${r.attempts}</td><td>${pct(r.rate)}</td><td>${ms(r.connectMedianMs)}</td><td>${ms(r.rttMedianMs)} / ${ms(r.rttP95Ms)}</td><td>${r.lockTried ? `${r.lockOk}/${r.lockTried}` : '–'}</td></tr>`;
  }
  html += '</tbody></table>';
  $('tabla').innerHTML = d.rows.length ? html : '<p class="small">Todavía no hay resultados.</p>';
  const ruleText = d.rule ? `Regla ${d.rule}: ${d.text}` : d.text;
  const miss = d.missing.length ? `<p>${d.complete ? '' : 'Todavía no vale como decisión. Falta:'}</p><ul>${d.missing.map((m) => `<li>${m}</li>`).join('')}</ul>` : '<p>Datos completos según el protocolo.</p>';
  $('veredicto').innerHTML = `<strong>Lectura de las reglas con estos datos</strong><p>${ruleText}</p>${miss}<p class="small">Éxito = conectó en menos de ${RULES.connectMs / 1000} s y recibió los ${RULES.burstSize} mensajes sin pérdidas, repetidos ni desorden.</p>`;
}

const exportJson = () => JSON.stringify({ schema: 'oc-red-v1', created: new Date().toISOString(), rules: RULES, attempts: state.attempts }, null, 2);

function download() {
  const a = document.createElement('a');
  a.href = URL.createObjectURL(new Blob([exportJson()], { type: 'application/json' }));
  a.download = `open-case-red-${new Date().toISOString().slice(0, 10)}.json`;
  a.click();
  setTimeout(() => URL.revokeObjectURL(a.href), 1000);
}

function merge() {
  try {
    const data = JSON.parse($('pegar').value);
    if (data.schema !== 'oc-red-v1' || !Array.isArray(data.attempts)) throw new Error('formato');
    state.attempts.push(...data.attempts);
    save();
    render();
    $('pegar').value = '';
    setStatus(`Se sumaron ${data.attempts.length} intentos.`);
  } catch (_) {
    setStatus('Ese texto no es un JSON de esta prueba.');
  }
}

// ---- team phone --------------------------------------------------------------------------------
async function startEquipo(sala) {
  state.sala = sala;
  const device = deviceInfo();
  $('equipo').hidden = false;
  $('sala-eq').textContent = sala;
  $('disp').textContent = device.id;
  fillNetworks($('red-eq'), params.get('red') || 'wifi-casa');
  const sel = $('man-transporte');
  for (const t of (params.get('transports') || '').split(',').filter(Boolean).concat(params.get('transports') ? [] : DEFAULT_TRANSPORTS)) {
    const o = document.createElement('option');
    o.value = t;
    o.textContent = t;
    sel.appendChild(o);
  }
  const log = (t) => { $('log-eq').textContent += `${new Date().toLocaleTimeString()}  ${t}\n`; };
  let current = null;

  async function join(msg) {
    if (current) { await current.close(); current = null; }
    if (msg.network) $('red-eq').value = msg.network;
    $('estado-eq').textContent = `Ronda ${msg.key}: conectando…`;
    const h = await intentoEquipo({
      sala, transport: msg.transport, n: msg.n, device, ctl: state.ctl, lock: !!msg.lock,
      onStatus: (t) => { $('estado-eq').textContent = `Ronda ${msg.key}: ${t}`; },
    });
    current = { key: msg.key, close: h.close };
    const r = await h.result;
    log(`${msg.key}: ${r.error ? `falló (${r.error})` : `conectó en ${Math.round(r.connectMs)} ms`}`);
    $('estado-eq').textContent = r.error ? `Ronda ${msg.key}: ${r.error}` : `Ronda ${msg.key}: conectado en ${Math.round(r.connectMs)} ms`;
    state.last = r;
  }

  try {
    state.ctl = await joinControl('equipo', device.id, (_from, m) => {
      if (!m) return;
      if (m.k === 'start') join(m).catch((e) => log(`error: ${e.message}`));
      if (m.k === 'end' && current && current.key === m.key) { current.close(); current = null; $('estado-eq').textContent = 'Ronda terminada. Esperando la siguiente…'; }
    });
    setPill($('ctl-estado-eq'), true, 'conectado');
  } catch (e) {
    setPill($('ctl-estado-eq'), false, `sin control (${e.message})`);
  }
  $('man-unir').onclick = () => {
    const t = sel.value;
    const n = Number($('man-n').value);
    join({ key: `${t}~${n}`, transport: t, n, network: $('red-eq').value }).catch((e) => log(`error: ${e.message}`));
    $('man-n').value = String(n + 1);
  };
}

boot();
