// What travels in a QR or a link: only codes. The message goes in the #fragment, which the browser never sends to a
// server, so the page that opens it (play/equipo/) is the only one that reads it.
//
//   #oc1.<base64url of JSON>   {c: case slug, l: language, v: version, t: team letter, s: delivery number,
//                               i: [[file, code], …]}   an empty `i` is the link that joins a team
export const PREFIX = 'oc1.';
const FILE = /^(sheets|cards|suspects)\/[A-Za-z0-9_-]{1,100}\.html$/;

export function encode(msg) {
  const json = JSON.stringify({ c: msg.slug, l: msg.lang, v: msg.version, t: msg.team, s: msg.seq || 0, i: msg.items || [] });
  const bytes = new TextEncoder().encode(json);
  let bin = '';
  for (const b of bytes) bin += String.fromCharCode(b);
  return PREFIX + btoa(bin).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
}

// Accepts a whole link, the #fragment or the bare text. Returns the checked message or null.
export function decode(text) {
  if (!text) return null;
  let s = String(text).trim();
  const hash = s.indexOf('#');
  if (hash >= 0) s = s.slice(hash + 1);
  if (!s.startsWith(PREFIX)) return null;
  try {
    const b64 = s.slice(PREFIX.length).replace(/-/g, '+').replace(/_/g, '/');
    const bin = atob(b64 + '='.repeat((4 - (b64.length % 4)) % 4));
    const raw = JSON.parse(new TextDecoder().decode(Uint8Array.from(bin, (c) => c.charCodeAt(0))));
    return validate(raw);
  } catch (e) { return null; }
}

// Anything that comes from a link is untrusted: only these shapes pass, and a file is only ever a page of the
// case folder, so a made-up link cannot make the app fetch something else.
export function validate(m) {
  if (!m || typeof m !== 'object') return null;
  if (typeof m.c !== 'string' || !/^[A-Za-z0-9_-]{1,60}$/.test(m.c)) return null;
  if (typeof m.l !== 'string' || !/^[a-z]{2}(-[A-Za-z]{2})?$/.test(m.l)) return null;
  if (typeof m.v !== 'string' || !/^[0-9a-f]{12}$/.test(m.v)) return null;
  if (typeof m.t !== 'string' || !/^[A-Z]$/.test(m.t)) return null;
  const out = checkItems(Array.isArray(m.i) ? m.i : []);
  if (!out) return null;
  return { slug: m.c, lang: m.l, version: m.v, team: m.t, seq: Number.isInteger(m.s) ? m.s : 0, items: out };
}

// A list of [file, code] checked: at most 300, each file a page of the case folder. null if any is not.
export function checkItems(items) {
  if (!Array.isArray(items) || items.length > 300) return null;
  const out = [];
  for (const it of items) {
    if (!Array.isArray(it) || typeof it[0] !== 'string' || !FILE.test(it[0])) return null;
    out.push([it[0], typeof it[1] === 'string' ? it[1].slice(0, 40) : '']);
  }
  return out;
}

export function kindOf(file) {
  return file.startsWith('cards/') ? 'card' : file.startsWith('suspects/') ? 'suspect' : 'sheet';
}

// B2 before B10, E9 before E10, E13b after E13.
export function naturalCompare(a, b) {
  const pa = String(a).match(/\d+|\D+/g) || [];
  const pb = String(b).match(/\d+|\D+/g) || [];
  for (let i = 0; i < Math.min(pa.length, pb.length); i++) {
    const x = pa[i], y = pb[i];
    if (/^\d/.test(x) && /^\d/.test(y)) { if (+x !== +y) return +x - +y; }
    else if (x !== y) return x < y ? -1 : 1;
  }
  return pa.length - pb.length;
}
