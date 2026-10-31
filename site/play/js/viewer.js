// Shows one page of the case (a sheet, a card) full screen, with zoom. The pages are whole HTML documents, so they
// go in an iframe; the service worker serves them (and their styles, fonts and photos) from the cache offline.
import { h } from './dom.js';

// items: [{url, title}]; labels: {close, prev, next, zoomIn, zoomOut, fit, loading}
export function openViewer({ items, index = 0, labels, onShow }) {
  let i = index, scale = 1, fit = true, natW = 0, natH = 0;
  const frame = h('iframe', { class: 'oc-viewer__frame', title: '' });
  const inner = h('div', { class: 'oc-viewer__inner' }, frame);
  const body = h('div', { class: 'oc-viewer__body' }, inner);
  const title = h('div', { class: 'oc-viewer__title' });
  const count = h('div', { class: 'oc-viewer__count' });
  const btn = (text, label, fn) => h('button', { type: 'button', class: 'oc-btn oc-btn--ghost', 'aria-label': label, title: label, onclick: fn }, text);
  const prev = btn('‹', labels.prev, () => go(-1));
  const next = btn('›', labels.next, () => go(1));
  const root = h('div', { class: 'oc-viewer', role: 'dialog', 'aria-modal': 'true' },
    h('div', { class: 'oc-viewer__bar' },
      btn('✕', labels.close, close), h('div', { class: 'oc-viewer__heading' }, title, count),
      prev, next,
      btn('−', labels.zoomOut, () => zoom(1 / 1.25)), btn('+', labels.zoomIn, () => zoom(1.25)), btn('⤢', labels.fit, () => { fit = true; layout(); })),
    body);

  // The page is laid out as wide as the screen (up to a sheet's width), so its text is read at its own size; the
  // zoom buttons and the pinch scale it from there. Content wider than that (a table) is shrunk to fit.
  const layoutWidth = () => Math.min(Math.max(body.clientWidth - 16, 280), 820);
  function layout() {
    if (!natH) return;
    if (fit) scale = Math.min(layoutWidth() / natW, 1);
    frame.style.width = natW + 'px';
    frame.style.height = natH + 'px';
    frame.style.transform = `scale(${scale})`;
    inner.style.width = natW * scale + 'px';
    inner.style.height = natH * scale + 'px';
  }
  function zoom(f) { fit = false; scale = Math.min(Math.max(scale * f, 0.2), 5); layout(); }
  function measure() {
    try {
      const d = frame.contentDocument;
      natW = Math.max(layoutWidth(), d.documentElement.scrollWidth);
      natH = Math.max(d.documentElement.scrollHeight, d.body ? d.body.scrollHeight : 0, 100);
    } catch (e) { natW = layoutWidth(); natH = 1000; }
    layout();
  }
  function show() {
    const it = items[i];
    natW = natH = 0;
    fit = true;
    frame.removeAttribute('style');
    frame.style.width = layoutWidth() + 'px';
    frame.src = it.url;
    frame.title = it.title;
    title.textContent = it.title;
    count.textContent = `${i + 1} / ${items.length}`;
    prev.disabled = i === 0;
    next.disabled = i === items.length - 1;
    body.scrollTo(0, 0);
    if (onShow) onShow(items[i], i);
  }
  function go(d) { const j = i + d; if (j >= 0 && j < items.length) { i = j; show(); } }
  function close() { window.removeEventListener('keydown', key); window.removeEventListener('resize', layout); root.remove(); document.body.classList.remove('oc-noscroll'); }
  function key(e) {
    if (e.key === 'Escape') close();
    else if (e.key === 'ArrowLeft') go(-1);
    else if (e.key === 'ArrowRight') go(1);
  }
  frame.addEventListener('load', () => { measure(); setTimeout(measure, 300); setTimeout(measure, 1500); });   // fonts and photos change the height
  window.addEventListener('keydown', key);
  window.addEventListener('resize', layout);
  document.body.classList.add('oc-noscroll');
  document.body.append(root);
  show();
  return { close };
}
