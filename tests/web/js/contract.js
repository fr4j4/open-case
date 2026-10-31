// The contract every transport must keep, run by the tests against different transports:
// a director and a team exchange 100 numbered messages in each direction and every one arrives
// once, in order, whatever the channel loses or repeats underneath.
export async function contract(makeDirector, makeTeam, { count = 100, timeoutMs = 60000 } = {}) {
  const d = makeDirector();
  const t = makeTeam();
  const gotByTeam = [];
  const gotByDirector = [];
  t.on('message', (_f, p) => gotByTeam.push(p.i));
  d.on('message', (_f, p) => gotByDirector.push(p.i));
  await Promise.all([d.connect(), t.connect()]);
  const limit = Date.now() + timeoutMs;
  while ((!d.peers().length || !t.peers().length) && Date.now() < limit) await new Promise((r) => setTimeout(r, 20));
  const dTeam = d.peers()[0].id;
  const tDir = t.peers()[0].id;
  const sends = [];
  for (let i = 0; i < count; i++) { sends.push(d.send(dTeam, { i })); sends.push(t.send(tDir, { i })); }
  const results = await Promise.allSettled(sends);
  while ((gotByTeam.length < count || gotByDirector.length < count) && Date.now() < limit) await new Promise((r) => setTimeout(r, 20));
  const seq = Array.from({ length: count }, (_, i) => i);
  const out = {
    teamOk: JSON.stringify(gotByTeam) === JSON.stringify(seq),
    directorOk: JSON.stringify(gotByDirector) === JSON.stringify(seq),
    teamCount: gotByTeam.length,
    directorCount: gotByDirector.length,
    rejected: results.filter((r) => r.status === 'rejected').length,
    stats: { d: d.stats, t: t.stats },
  };
  await d.close();
  await t.close();
  return out;
}
