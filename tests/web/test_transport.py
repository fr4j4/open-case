"""F0 · the transport interface: delivery over BroadcastChannel, the contract against a lossy channel,
and the decision rules of the network lab. The `trystero` and `relay` transports need real relays, so
they are only tried in the field (docs/web-network-test.md); here they must at least load and keep the
interface."""
import json

HOST = "lab/red/index.html"          # any page of the site is a valid origin to import the modules from


def open_page(context, url):
    page = context.new_page()
    page.on("pageerror", lambda e: (_ for _ in ()).throw(AssertionError(f"page error: {e}")))
    page.goto(url)
    return page


def test_broadcast_one_director_three_teams_100_of_100(context, site_url):
    """1 director and 3 teams: the director sends 100 messages to each team; every one arrives, in order, once."""
    boot = """
      async ([role, name]) => {
        const { crearTransporte } = await import('/play/js/transport/index.js');
        const t = crearTransporte('broadcast', { room: 'prueba-100', role, name });
        window.t = t; window.got = [];
        t.on('message', (_f, p) => window.got.push(p.i));
        await t.connect();
      }"""
    teams = []
    for i in range(3):
        page = open_page(context, site_url + HOST)
        page.evaluate(boot, ["equipo", f"equipo-{i}"])
        teams.append(page)
    director = open_page(context, site_url + HOST)
    sent = director.evaluate("""
      async () => {
        const { crearTransporte } = await import('/play/js/transport/index.js');
        const t = crearTransporte('broadcast', { room: 'prueba-100', role: 'director', name: 'director' });
        await t.connect();
        const limit = Date.now() + 15000;
        while (t.peers().length < 3 && Date.now() < limit) await new Promise((r) => setTimeout(r, 20));
        const results = [];
        for (const p of t.peers()) {
          const sends = [];
          for (let i = 0; i < 100; i++) sends.push(t.send(p.id, { i }));
          results.push((await Promise.allSettled(sends)).filter((r) => r.status === 'fulfilled').length);
        }
        return { peers: t.peers().length, acked: results, stats: t.stats };
      }""")
    assert sent["peers"] == 3
    assert sent["acked"] == [100, 100, 100]
    for page in teams:
        page.wait_for_function("window.got.length >= 100", timeout=15000)
        got = page.evaluate("window.got")
        assert got == list(range(100))


def test_contract_over_broadcast(context, site_url):
    page = open_page(context, site_url + HOST)
    out = page.evaluate("""
      async () => {
        const { contract } = await import('/__tests__/contract.js');
        const { crearTransporte } = await import('/play/js/transport/index.js');
        return contract(
          () => crearTransporte('broadcast', { room: 'contrato', role: 'director', name: 'd' }),
          () => crearTransporte('broadcast', { room: 'contrato', role: 'equipo', name: 't' }));
      }""")
    assert out["teamOk"] and out["directorOk"], out
    assert out["rejected"] == 0


def test_contract_over_a_channel_that_loses_and_repeats(context, site_url):
    """The simulated channel drops 30 % of the frames, repeats 30 % and delays them: the ids, acks and retries
    must still deliver every message once and in order."""
    page = open_page(context, site_url + HOST)
    out = page.evaluate("""
      async () => {
        const { contract } = await import('/__tests__/contract.js');
        const { Hub, SimuladoTransporte } = await import('/play/js/transport/simulado.js');
        const hub = new Hub({ loss: 0.3, dup: 0.3, maxDelayMs: 30, seed: 7 });
        const rel = { retryMs: 60, maxTries: 40, gapMs: 3000, helloMs: 100, keepAliveMs: 300 };
        const out = await contract(
          () => new SimuladoTransporte({ hub, room: 'x', role: 'director', name: 'd', reliability: rel }),
          () => new SimuladoTransporte({ hub, room: 'x', role: 'equipo', name: 't', reliability: rel }));
        out.hub = { sent: hub.sent, dropped: hub.dropped, duplicated: hub.duplicated };
        return out;
      }""")
    assert out["hub"]["dropped"] > 50 and out["hub"]["duplicated"] > 50, out["hub"]   # the channel really misbehaved
    assert out["teamOk"] and out["directorOk"], out
    assert out["rejected"] == 0
    assert out["stats"]["d"]["retries"] > 0
    assert out["stats"]["t"]["dupes"] > 0       # repeated frames were dropped, not delivered twice


def test_a_message_that_never_gets_through_fails_and_does_not_freeze_the_next(context, site_url):
    page = open_page(context, site_url + HOST)
    out = page.evaluate("""
      async () => {
        const { Hub, SimuladoTransporte } = await import('/play/js/transport/simulado.js');
        const hub = new Hub({ seed: 3 });
        const rel = { retryMs: 20, maxTries: 3, gapMs: 200, helloMs: 50, keepAliveMs: 200, readyMs: 2000 };
        const a = new SimuladoTransporte({ hub, room: 'x', role: 'director', name: 'a', reliability: rel });
        const b = new SimuladoTransporte({ hub, room: 'x', role: 'equipo', name: 'b', reliability: rel });
        const got = [];
        b.on('message', (_f, p) => got.push(p.i));
        await Promise.all([a.connect(), b.connect()]);
        while (!a.peers().length) await new Promise((r) => setTimeout(r, 10));
        const peer = a.peers()[0].id;
        await a.send(peer, { i: 0 });
        hub.loss = 1;                                      // the next one cannot get through
        const lost = await a.send(peer, { i: 1 }).then(() => 'ok', (e) => e.message);
        hub.loss = 0;
        await a.send(peer, { i: 2 });
        await new Promise((r) => setTimeout(r, 600));
        return { lost, got, gaps: b.stats.gaps };
      }""")
    assert out["lost"] == "sin-ack"
    assert out["got"] == [0, 2]                  # the lost one is skipped after gapMs
    assert out["gaps"] == 1


def test_all_transports_load_and_keep_the_interface(context, site_url):
    """trystero (three strategies) and relay cannot reach real relays here, but they must load and expose the API."""
    page = open_page(context, site_url + HOST)
    out = page.evaluate("""
      async () => {
        const { crearTransporte, TRANSPORTS, CONFIG } = await import('/play/js/transport/index.js');
        const res = {};
        for (const name of TRANSPORTS) {
          const t = crearTransporte(name, { room: 'api', role: 'equipo', name: 'x' });
          res[name] = ['connect', 'send', 'broadcast', 'peers', 'close', 'on', 'off'].every((m) => typeof t[m] === 'function');
        }
        for (const s of ['nostr', 'mqtt', 'torrent']) {
          const m = await import(`/play/vendor/trystero-${s}.js`);
          res[`vendor-${s}`] = typeof m.joinRoom === 'function' && typeof m.selfId === 'string';
        }
        const n = await import('/play/vendor/noble-secp256k1.js');
        res.noble = typeof n.schnorr.signAsync === 'function';
        res.primary = CONFIG.primary + '+' + CONFIG.fallback;
        return res;
      }""")
    assert all(v is True for k, v in out.items() if k != "primary"), out
    assert out["primary"] == "trystero-nostr+relay"


def test_relay_encrypts_and_signs_what_it_publishes(context, site_url):
    """With a fake WebSocket that records what goes out: the text is not readable and the Nostr event is
    signed (the signature verifies), and the receiving side can read it back."""
    page = open_page(context, site_url + HOST)
    out = page.evaluate("""
      async () => {
        const sent = [];
        const sockets = [];
        class FakeWS {
          constructor(url) { this.url = url; this.readyState = 0; sockets.push(this); setTimeout(() => { this.readyState = 1; this.onopen && this.onopen(); }, 5); }
          send(t) { sent.push({ url: this.url, t }); }
          close() {}
        }
        window.WebSocket = FakeWS;
        const { RelayTransporte } = await import('/play/js/transport/relay.js');
        const noble = await import('/play/vendor/noble-secp256k1.js');
        const a = new RelayTransporte({ room: 'sala-secreta', role: 'director', name: 'a', urls: ['wss://uno.test', 'wss://dos.test'] });
        const b = new RelayTransporte({ room: 'sala-secreta', role: 'equipo', name: 'b', urls: ['wss://uno.test'] });
        await a.connect(); await b.connect();
        await a._raw(null, { t: 'h', f: 'a', s: 'x', name: 'texto-secreto', role: 'director' });
        const events = sent.filter((s) => s.t.startsWith('["EVENT"')).map((s) => JSON.parse(s.t)[1]);
        const ev = events[events.length - 1];
        const hexToBytes = (h) => Uint8Array.from(h.match(/../g), (x) => parseInt(x, 16));
        const verified = await noble.schnorr.verifyAsync(hexToBytes(ev.sig), hexToBytes(ev.id), hexToBytes(ev.pubkey));
        // feed b with the event as a relay would
        const got = [];
        b.on('peer', (p) => got.push(p.name));
        const bs = [...b.sockets.values()][0].ws;
        const sub = JSON.parse(sent.find((s) => s.t.startsWith('["REQ"')).t)[1];
        await b._onSocketMessage(JSON.stringify(['EVENT', b._subId, ev]));
        await a.close(); await b.close();
        return {
          relaysUsed: new Set(events.map(() => 1)).size, copies: sent.filter((s) => s.t.startsWith('["EVENT"') && JSON.parse(s.t)[1].id === ev.id).length,
          readable: JSON.stringify(ev).includes('texto-secreto'), verified, kind: ev.kind, got,
        };
      }""")
    assert out["verified"] is True
    assert out["readable"] is False
    assert 20000 <= out["kind"] < 30000
    assert out["copies"] == 2                        # one per open relay
    assert out["got"] == ["texto-secreto"]


def test_decision_rules(context, site_url):
    page = open_page(context, site_url + HOST)

    def run(expr):
        return page.evaluate("""async () => {
          const { decide } = await import('/lab/red/decision.js');
          const { field } = await import('/__tests__/fixtures.js');
          return (%s);
        }""" % expr)

    # rule 1: the bus alone is >= 95 % everywhere -> bus first, WebRTC optional
    r1 = run("decide([...field('relay', 1), ...field('trystero-nostr', 0.5)])")
    assert r1["rule"] == 1 and r1["config"]["primary"] == "relay" and r1["complete"] is True
    # rule 2: WebRTC >= 90 % at home and on the hotspot; the bus covers the networks where it falls short
    r2 = run("decide([...field('relay', {'wifi-institucional': 1, 'datos-mixto': 1, 'wifi-casa': 0.5, hotspot: 0.5}),"
             " ...field('trystero-nostr', {'wifi-casa': 1, hotspot: 1, 'wifi-institucional': 0.2, 'datos-mixto': 0.2})])")
    assert r2["rule"] == 2 and r2["config"] == {"primary": "trystero-nostr", "fallback": "relay"}
    # rule 3: neither reaches the numbers
    r3 = run("decide([...field('relay', 0.5), ...field('trystero-nostr', 0.5)])")
    assert r3["rule"] == 3 and r3["config"] is None
    # both rule 1 and rule 2 hold: the order picks rule 1
    r5 = run("decide([...field('relay', 1), ...field('trystero-nostr', 1)])")
    assert r5["rule"] == 1
    # a WebRTC that is good at home but the bus does not cover the rest -> rule 3
    r6 = run("decide([...field('relay', 0.5), ...field('trystero-nostr', {'wifi-casa': 1, hotspot: 1, 'wifi-institucional': 0.2, 'datos-mixto': 0.2})])")
    assert r6["rule"] == 3
    # not enough data is flagged: one day, one phone, a few attempts
    r4 = run("decide(field('relay', 1).filter((a) => a.date === '2026-11-01' && a.os === 'android'))")
    assert r4["complete"] is False
    assert any("días" in m for m in r4["missing"]) and any("iPhone" in m for m in r4["missing"])
    # a success needs the 100 messages and a connection under 10 s
    ok = run("(async () => { const m = await import('/lab/red/decision.js'); const b = { got: 100, dup: 0, ordered: true };"
             " return [m.isSuccess({ connectMs: 900, burst: b }), m.isSuccess({ connectMs: 12000, burst: b }),"
             " m.isSuccess({ connectMs: 900, burst: { got: 99, dup: 0, ordered: true } }), m.isSuccess({ connectMs: 900, burst: { got: 100, dup: 1, ordered: true } })]; })()")
    assert ok == [True, False, False, False]
    json.dumps(r5)
