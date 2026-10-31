// The words of the app: play/strings/<lang>.json, made from the `web:` section of opencase/strings/<lang>.yaml.
let words = {};
let current = 'es';

export async function loadStrings(lang, fallback = 'es') {
  for (const l of [lang, fallback]) {
    try {
      const r = await fetch(new URL(`../strings/${l}.json`, import.meta.url), { cache: 'no-cache' });
      if (!r.ok) continue;
      words = (await r.json()).web || {};
      current = l;
      document.documentElement.lang = l;
      return l;
    } catch (e) { /* offline and never cached: try the fallback */ }
  }
  words = {};
  return current;
}

export function t(key, vars) {
  let v = key.split('.').reduce((o, k) => (o == null ? o : o[k]), words);
  if (typeof v !== 'string') return key;
  if (vars) v = v.replace(/\{(\w+)\}/g, (m, name) => (name in vars ? vars[name] : m));
  return v;
}

export function plural(key, n, vars = {}) { return t(`${key}.${n === 1 ? 'one' : 'other'}`, { n, ...vars }); }
export const language = () => current;

// The directory of the app (…/play/), whatever the site is served under.
export const PLAY_ROOT = new URL('../', import.meta.url);

export function registerWorker() {
  if (!('serviceWorker' in navigator)) return Promise.resolve(null);
  return navigator.serviceWorker.register(new URL('../sw.js', import.meta.url), { scope: PLAY_ROOT.pathname })
    .then(async (reg) => {
      await navigator.serviceWorker.ready;
      if (!navigator.serviceWorker.controller) {   // the first visit: wait for the worker to take this page
        await new Promise((res) => {
          const done = () => res();
          navigator.serviceWorker.addEventListener('controllerchange', done, { once: true });
          setTimeout(done, 3000);
        });
      }
      return reg;
    })
    .catch(() => null);
}
