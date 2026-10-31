// The device's memory (IndexedDB): one small key/value store. The team's folder and the director's game live here,
// so a reload, a closed tab or a lost connection loses nothing. If IndexedDB is not available (a private window
// of some browsers) it falls back to memory and `store.persistent` is false, so the app can warn.
const DB_NAME = 'opencase-play';
const STORE = 'kv';

let dbPromise = null;
const memory = new Map();
export const store = { persistent: true };

function open() {
  if (!dbPromise) {
    dbPromise = new Promise((resolve, reject) => {
      try {
        const req = indexedDB.open(DB_NAME, 1);
        req.onupgradeneeded = () => req.result.createObjectStore(STORE);
        req.onsuccess = () => resolve(req.result);
        req.onerror = () => reject(req.error);
        req.onblocked = () => reject(new Error('blocked'));
      } catch (e) { reject(e); }
    }).catch(() => { store.persistent = false; return null; });
  }
  return dbPromise;
}

function run(mode, fn) {
  return open().then((db) => {
    if (!db) return fn(null);
    return new Promise((resolve, reject) => {
      const tx = db.transaction(STORE, mode);
      const res = fn(tx.objectStore(STORE));
      tx.oncomplete = () => resolve(res && 'result' in res ? res.result : undefined);
      tx.onerror = () => reject(tx.error);
      tx.onabort = () => reject(tx.error);
    });
  });
}

export async function get(key) {
  const db = await open();
  if (!db) return memory.get(key);
  return run('readonly', (s) => s.get(key));
}

export async function set(key, value) {
  const db = await open();
  if (!db) { memory.set(key, structuredClone(value)); return; }
  await run('readwrite', (s) => s.put(value, key));
}

export async function del(key) {
  const db = await open();
  if (!db) { memory.delete(key); return; }
  await run('readwrite', (s) => s.delete(key));
}

export async function ready() { await open(); return store.persistent; }
