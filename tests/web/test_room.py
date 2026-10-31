"""F3 · the live room: the director opens a room, phones join with a PIN, the director approves them, and the
deliveries go over the network.

The phones are in separate browser contexts (own IndexedDB, as separate phones), so a BroadcastChannel cannot
join them. The `relay` transport does: a Nostr relay written here in Python stands in for the public ones
(Playwright's route_web_socket), shared by every context. The messages cross it encrypted and signed, as in
the field, so this runs the real transport code, only not the WebRTC one (that one needs real networks: field closing).
"""
import json
import time

import pytest

pytestmark = pytest.mark.web

RELAY = "wss://relay.test/"
QS = "?transport=relay&relays=" + RELAY


class LocalRelay:
    """The least of a Nostr relay: REQ subscribes, EVENT is passed to every subscription whose filter matches."""

    def __init__(self):
        self.subs = []          # (ws, sub id, filter)
        self.events = 0

    def attach(self, context):
        context.route_web_socket(RELAY, self._on_socket)

    def _on_socket(self, ws):
        ws.on_message(lambda text: self._on_message(ws, text))
        # no on_close: Playwright 1.64 raises KeyError('code') on a close the page started. A send to a closed socket is caught below.

    def _on_message(self, ws, text):
        try:
            msg = json.loads(text)
        except ValueError:
            return
        if msg[0] == "REQ":
            self.subs = [s for s in self.subs if not (s[0] is ws and s[1] == msg[1])]
            self.subs.append((ws, msg[1], msg[2]))
        elif msg[0] == "CLOSE":
            self.subs = [s for s in self.subs if not (s[0] is ws and s[1] == msg[1])]
        elif msg[0] == "EVENT":
            ev = msg[1]
            self.events += 1
            ws.send(json.dumps(["OK", ev["id"], True, ""]))
            topics = [t[1] for t in ev["tags"] if t[0] == "t"]
            for other, sub_id, flt in list(self.subs):
                if ev["kind"] in flt.get("kinds", [ev["kind"]]) and any(t in flt.get("#t", topics) for t in topics):
                    try:
                        other.send(json.dumps(["EVENT", sub_id, ev]))
                    except Exception:
                        pass


@pytest.fixture
def relay():
    return LocalRelay()


def _context(browser, relay):
    ctx = browser.new_context()
    relay.attach(ctx)
    return ctx


def _director(ctx, base, relay_url_qs=QS, teams=2):
    page = ctx.new_page()
    page.goto(base + "play/director/" + relay_url_qs)
    page.wait_for_selector("#oc-start")
    page.select_option("#oc-teams", str(teams))
    page.click("#oc-start")
    page.wait_for_selector(".oc-tabs")
    page.click("#oc-tab-room")
    page.click("#oc-room-create")
    page.wait_for_selector("#oc-room-pin")
    return page, page.inner_text("#oc-room-pin").strip()


def _phone(ctx, base, pin, name=""):
    page = ctx.new_page()
    page.goto(base + "play/equipo/" + QS)
    page.wait_for_selector("#oc-room-pin")
    page.fill("#oc-room-pin", pin)
    if name:
        page.fill("#oc-room-name", name)
    page.click("#oc-room-enter")
    return page


def _wait(fn, seconds=20, what="condition"):
    limit = time.time() + seconds
    while time.time() < limit:
        value = fn()
        if value:
            return value
        time.sleep(0.1)
    raise AssertionError(f"timed out waiting for {what}")


def _approve(director, name, team):
    director.click("#oc-tab-room")
    # the panel redraws on every change, so the button is looked up again on each try (a locator)
    director.locator(f'section[data-device]:has-text("{name}") [data-approve="{team}"]').click(timeout=20000)


def _state(page, key="team"):
    return page.evaluate("""(key) => new Promise((resolve) => {
        const r = indexedDB.open('opencase-play');
        r.onsuccess = () => { const q = r.result.transaction('kv').objectStore('kv').get(key); q.onsuccess = () => resolve(q.result || null); q.onerror = () => resolve(null); };
        r.onerror = () => resolve(null);
      })""", key)


def _files(page, team_letter=None):
    s = _state(page)
    return (s or {}).get("order", [])


def _pick(director, file):
    director.click("#oc-tab-give")
    director.check(f'[data-file="{file}"] input')
    director.click("#oc-give")
    # a team with phones connected gets it with no QR; one without opens the QR (closed at once)
    if director.query_selector("#oc-delivery-close"):
        director.click("#oc-delivery-close")


def test_pin_and_link_helpers(context, site_url):
    page = context.new_page()
    page.goto(site_url + "play/equipo/")
    out = page.evaluate("""async () => {
      const r = await import('./../js/room.js');
      const pins = Array.from({ length: 200 }, () => r.newPin());
      return {
        all6: pins.every((p) => p.length === 6 && r.validPin(p)),
        distinct: new Set(pins).size > 190,
        link: r.roomLink('https://x.test/play/equipo/', 'ABC234'),
        parsed: r.pinFromHash('#sala.abc234'),
        bad: [r.pinFromHash('#sala.ABC23'), r.pinFromHash('#sala.ABC230'), r.pinFromHash('#oc1.xxx'), r.pinFromHash('')],
        norm: r.normalizePin(' ab-c2 34x '),
      };
    }""")
    assert out["all6"] and out["distinct"]
    assert out["link"] == "https://x.test/play/equipo/#sala.ABC234"
    assert out["parsed"] == "ABC234"
    assert out["bad"] == [None, None, None, None]
    assert out["norm"] == "ABC234"


def test_director_two_teams_four_phones_and_an_intruder_50_deliveries(site, browser, relay):
    folder, base = site
    director_ctx = _context(browser, relay)
    director, pin = _director(director_ctx, base)
    assert len(pin) == 6

    phones = {}
    for name in ("A1", "A2", "B1", "B2", "intruso"):
        phones[name] = (ctx := _context(browser, relay), _phone(ctx, base, pin, name))
    # everybody waits; the intruder never gets approved
    for name in phones:
        _wait(lambda n=name: phones[n][1].query_selector('#oc-room-status[data-status="waiting"]'), what=f"{name} waiting")
    _approve(director, "A1", "A")
    _approve(director, "A2", "A")
    _approve(director, "B1", "B")
    _approve(director, "B2", "B")

    # each approved phone opens its team's folder by itself and the director sees it online
    for name, team in (("A1", "A"), ("A2", "A"), ("B1", "B"), ("B2", "B")):
        _wait(lambda n=name: (_state(phones[n][1]) or {}).get("team"), what=f"{name} folder")
        assert _state(phones[name][1])["team"] == team
    director.click("#oc-tab-room")
    _wait(lambda: len(director.query_selector_all('[data-online="true"]')) == 4, what="4 phones online")
    assert _state(phones["intruso"][1]) is None

    # 50 deliveries to A, to B and to both
    director.click("#oc-tab-give")
    files = director.eval_on_selector_all("label.oc-sel", "els => els.map(e => e.dataset.file)")
    initial = set(_state(phones["A1"][1])["items"]) | set(_state(phones["B1"][1])["items"])
    files = [f for f in files if f not in initial][:50]
    assert len(files) == 50
    plan = [("A",)] * 20 + [("B",)] * 15 + [("A", "B")] * 15
    expect = {"A": [], "B": []}
    current = None
    for file, teams in zip(files, plan):
        if teams != current:
            director.click("#oc-tab-give")
            for tm in "AB":
                pressed = director.get_attribute(f'.oc-chip[data-team="{tm}"]', "aria-pressed") == "true"
                if pressed != (tm in teams):
                    director.click(f'.oc-chip[data-team="{tm}"]')
            current = teams
        _pick(director, file)
        for tm in teams:
            expect[tm].append(file)

    for name, team in (("A1", "A"), ("A2", "A"), ("B1", "B"), ("B2", "B")):
        _wait(lambda n=name, tm=team: len(_files(phones[n][1])) >= len(expect[tm]), seconds=45, what=f"{name} deliveries")
    for name, team in (("A1", "A"), ("A2", "A"), ("B1", "B"), ("B2", "B")):
        got = [f for f in _files(phones[name][1]) if f in files]
        assert got == expect[team], name                      # all of them, in order, once, and only its team's
        assert len(set(got)) == len(got)
    assert _state(phones["intruso"][1]) is None               # the intruder has the PIN, nothing else
    assert _state(phones["intruso"][1], "session") is None
    status = phones["intruso"][1].get_attribute("#oc-room-status", "data-status")
    assert status == "waiting"
    for ctx, _ in phones.values():
        ctx.close()
    director_ctx.close()


def test_a_phone_that_was_off_gets_what_it_missed_and_a_reloaded_director_recovers_the_room(site, browser, relay):
    folder, base = site
    director_ctx = _context(browser, relay)
    director, pin = _director(director_ctx, base)
    phone_ctx = _context(browser, relay)
    phone = _phone(phone_ctx, base, pin, "A1")
    _approve(director, "A1", "A")
    _wait(lambda: (_state(phone) or {}).get("team") == "A", what="folder")
    files = director.eval_on_selector_all("label.oc-sel", "els => els.map(e => e.dataset.file)") if director.query_selector("label.oc-sel") else None
    director.click("#oc-tab-give")
    files = director.eval_on_selector_all("label.oc-sel", "els => els.map(e => e.dataset.file)")
    known = set(_state(phone)["items"])
    fresh = [f for f in files if f not in known]
    director.click("#oc-tab-room")
    _wait(lambda: director.query_selector('[data-online="true"]'), what="online")
    director.click("#oc-tab-give")
    director.click('.oc-chip[data-team="A"]') if director.get_attribute('.oc-chip[data-team="A"]', "aria-pressed") != "true" else None

    phone.close()                                             # the phone is off (the folder stays in its IndexedDB)
    director.click("#oc-tab-room")
    _wait(lambda: director.query_selector('[data-online="false"]'), what="phone seen leaving")
    _pick(director, fresh[0])                                 # nobody to send to: the QR is the way
    phone = phone_ctx.new_page()
    phone.goto(base + "play/equipo/" + QS)
    got = _wait(lambda: fresh[0] in ((_state(phone) or {}).get("items") or {}), seconds=15, what="the missed delivery after reconnecting")
    assert got
    assert _state(phone)["team"] == "A"                       # the same folder, not a new one

    # the director reloads: same PIN, same phones, and everything keeps flowing
    director.reload()
    director.wait_for_selector(".oc-tabs")
    director.click("#oc-tab-room")
    assert director.inner_text("#oc-room-pin").strip() == pin
    t0 = time.time()
    _wait(lambda: director.query_selector('[data-online="true"]'), seconds=15, what="the phone reconnecting to the reloaded director")
    assert time.time() - t0 < 15
    _pick(director, fresh[1])
    _wait(lambda: fresh[1] in ((_state(phone) or {}).get("items") or {}), seconds=15, what="a delivery after the director reloaded")
    phone_ctx.close()
    director_ctx.close()


def test_refused_and_moved_phones(site, browser, relay):
    folder, base = site
    director_ctx = _context(browser, relay)
    director, pin = _director(director_ctx, base)
    p1_ctx, p2_ctx, p3_ctx = (_context(browser, relay) for _ in range(3))
    p1 = _phone(p1_ctx, base, pin, "P1")
    p2 = _phone(p2_ctx, base, pin, "P2")
    p3 = _phone(p3_ctx, base, pin, "P3")
    _approve(director, "P1", "A")
    _approve(director, "P2", "A")
    director.click("#oc-tab-room")
    director.locator('section[data-device]:has-text("P3") [data-deny]').click(timeout=20000)
    _wait(lambda: p3.query_selector('#oc-room-status[data-status="denied"]'), what="P3 refused")
    assert _state(p3) is None

    for p in (p1, p2):
        _wait(lambda p=p: (_state(p) or {}).get("team") == "A", what="folder A")
    director.click("#oc-tab-room")
    _wait(lambda: len(director.query_selector_all('[data-online="true"]')) == 2, what="both online")
    # P2 moves to team B: its folder is replaced by B's, and it stops getting what goes to A
    team_a = director.query_selector('section[data-team="A"]')
    row = next(r for r in team_a.query_selector_all("[data-device]") if "P2" in r.inner_text())
    row.query_selector("button:has-text('B')").click()
    _wait(lambda: (_state(p2) or {}).get("team") == "B", seconds=20, what="P2 in team B")
    director.click("#oc-tab-give")
    files = director.eval_on_selector_all("label.oc-sel", "els => els.map(e => e.dataset.file)")
    known = set(_state(p1)["items"]) | set(_state(p2)["items"])
    fresh = [f for f in files if f not in known]
    for tm in "AB":
        pressed = director.get_attribute(f'.oc-chip[data-team="{tm}"]', "aria-pressed") == "true"
        if pressed != (tm == "A"):
            director.click(f'.oc-chip[data-team="{tm}"]')
    _wait(lambda: director.query_selector('[data-online="true"]') or True)
    director.click("#oc-tab-room")
    _wait(lambda: any(r.get_attribute("data-online") == "true" for r in director.query_selector_all('section[data-team="A"] [data-device]')), what="P1 still online")
    _pick(director, fresh[0])
    _wait(lambda: fresh[0] in ((_state(p1) or {}).get("items") or {}), seconds=20, what="P1 gets A's delivery")
    time.sleep(2)
    assert fresh[0] not in ((_state(p2) or {}).get("items") or {})
    for c in (p1_ctx, p2_ctx, p3_ctx, director_ctx):
        c.close()
