// The clock of the phases (F5), as a pure module: no DOM, no network, and no clock of its own (every function takes `now`).
// The phases and their minutes are the engine's and the case's (`figures.phases`, `closing_minutes`, `notice_minutes` in
// team.json and director.json); nothing here is a number of the game. The director runs it (start, pause, advance, jump to a
// phase, shift the time) and tells the phones `wire(clock, now)`; each phone counts from there with its own clock, so nothing
// depends on how long the network takes.
//
//   let c = newClock(figures);                    // the first phase, stopped
//   c = start(c, now); c = toPhase(c, 'investigation', now); c = shift(c, +60_000, now);
//   remainingMs(figures, c, now);  investigationMinute(c, now);  due(figures, notices, c, now);

export const INVESTIGATION = 'investigation';   // the only phase in which a team may ask (rule 1 of the kit)
export const CLOSING = 'closing';                // after the accusation: score, confession and closing of the story

/** The phases in order, with their minutes: those of `figures.phases`, then `closing` (the first of `closing_minutes`). */
export function phases(figures) {
  const list = Object.entries(figures.phases || {}).map(([key, minutes]) => ({ key, minutes: Number(minutes) }));
  const closing = (figures.closing_minutes || [])[0];
  if (closing != null) list.push({ key: CLOSING, minutes: Number(closing) });
  return list;
}

export const newClock = (figures) => ({ phase: phases(figures)[0].key, running: false, elapsed: 0, since: null });

export const elapsedMs = (c, now) => Math.max(0, c.elapsed + (c.running && c.since != null ? now - c.since : 0));

export const start = (c, now) => (c.running ? c : { ...c, running: true, since: now });
export const pause = (c, now) => (c.running ? { ...c, elapsed: elapsedMs(c, now), running: false, since: null } : c);

/** Moves to `phase` and starts counting from 0 (the director chose it; there is no automatic jump). */
export function toPhase(figures, c, phase, now) {
  if (!phases(figures).some((p) => p.key === phase)) return c;
  return { phase, running: true, elapsed: 0, since: now };
}

/** The next phase, or the same one at the end. */
export function next(figures, c, now) {
  const list = phases(figures);
  const i = list.findIndex((p) => p.key === c.phase);
  return i >= 0 && i < list.length - 1 ? toPhase(figures, c, list[i + 1].key, now) : c;
}

/** Moves the time of the phase by `deltaMs` (positive: the phase is further along; "advance"). It never goes below 0. */
export function shift(c, deltaMs, now) {
  const base = elapsedMs(c, now) + deltaMs;
  return { ...c, elapsed: Math.max(0, base), since: c.running ? now : null };
}

export const minutesOf = (figures, phase) => (phases(figures).find((p) => p.key === phase) || { minutes: 0 }).minutes;

/** Milliseconds left in the phase (negative: it ran over; the director decides when to move on). */
export const remainingMs = (figures, c, now) => minutesOf(figures, c.phase) * 60000 - elapsedMs(c, now);

/** Minutes of the investigation gone by (0 is when the director moved to the investigation), or null in another phase. */
export function investigationMinute(c, now) {
  return c.phase === INVESTIGATION ? elapsedMs(c, now) / 60000 : null;
}

/** May a team ask for something now? Only in the investigation (the scene is for reading and the accusation for writing). */
export const canRequest = (c) => !!c && c.phase === INVESTIGATION;

/** The notices (`director.notices`) whose suggested minute has come and that were not read yet. `done` is a set of `n`.
 * They are only a suggestion for the director: nothing is sent by itself. */
export function due(notices, c, now, done = []) {
  const m = investigationMinute(c, now);
  if (m == null) return [];
  return notices.filter((n) => !done.includes(n.n) && n.minute != null && n.minute <= m);
}

/** What travels to the phones: the phase, whether it runs and how much of it has gone by. */
export const wire = (c, now) => ({ phase: c.phase, running: c.running, elapsedMs: Math.round(elapsedMs(c, now)) });

/** What a phone makes of it, counting from its own clock. null when it is not well formed. */
export function fromWire(figures, w, now) {
  if (!w || typeof w !== 'object' || !phases(figures).some((p) => p.key === w.phase)) return null;
  const elapsed = Number(w.elapsedMs);
  if (!Number.isFinite(elapsed) || elapsed < 0 || elapsed > 24 * 3600 * 1000) return null;
  return { phase: w.phase, running: !!w.running, elapsed, since: w.running ? now : null };
}

/** "m:ss" of a number of milliseconds (a minus sign when it ran over). */
export function format(ms) {
  const neg = ms < 0;
  const s = Math.floor(Math.abs(ms) / 1000);
  return `${neg ? '−' : ''}${Math.floor(s / 60)}:${String(s % 60).padStart(2, '0')}`;
}
