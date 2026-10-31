// The event log of a device, in IndexedDB: the director's holds every join, approval and delivery; a team's holds what
// it received. It is only a record (the state that matters is kept apart), so a full or missing store never stops the game.
import * as store from './store.js';

const MAX = 2000;

export function openLog(name) {
  const key = `log:${name}`;
  let entries = null;
  let chain = Promise.resolve();
  const load = async () => { if (!entries) entries = (await store.get(key)) || []; return entries; };
  return {
    // Adds {id, at, type, ...data}. The id grows by one, so an entry is never mixed up with another.
    append(type, data = {}) {
      chain = chain.then(async () => {
        const list = await load();
        const last = list.length ? list[list.length - 1].id : 0;
        list.push({ id: last + 1, at: Date.now(), type, ...data });
        if (list.length > MAX) list.splice(0, list.length - MAX);
        try { await store.set(key, list); } catch (e) { /* the log is not worth stopping for */ }
      }).catch(() => {});
      return chain;
    },
    async all() { await chain; return [...(await load())]; },
    async clear() { await chain; entries = []; await store.del(key); },
  };
}
