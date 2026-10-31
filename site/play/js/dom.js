// Tiny DOM helper: h('button', {class: 'x', onclick: fn}, 'text', child…). Text is always set as text, never as HTML.
export function h(tag, attrs, ...children) {
  const el = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs || {})) {
    if (v === false || v == null) continue;
    if (k.startsWith('on') && typeof v === 'function') el.addEventListener(k.slice(2), v);
    else if (k === 'class') el.className = v;
    else if (k === 'dataset') Object.assign(el.dataset, v);
    else el.setAttribute(k, v === true ? '' : v);
  }
  add(el, children);
  return el;
}

function add(el, children) {
  for (const c of children.flat(Infinity)) {
    if (c == null || c === false) continue;
    el.append(c.nodeType ? c : document.createTextNode(String(c)));
  }
}

export function clear(el) { el.replaceChildren(); return el; }

export function toast(text, ms = 3500) {
  let box = document.getElementById('oc-toasts');
  if (!box) { box = h('div', { id: 'oc-toasts', role: 'status', 'aria-live': 'polite' }); document.body.append(box); }
  const t = h('div', { class: 'oc-toast' }, text);
  box.append(t);
  setTimeout(() => t.remove(), ms);
}
