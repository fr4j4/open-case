"""F6a · the pages: the director loses its device in the middle of a game and a new one gets the game back.

Two ways, both over the real `relay` transport against a Nostr relay written in Python (as in test_room.py):
  - from the TEAMS: the phones show a recovery link; the new device reads them, asks each phone for its registro and rebuilds the
    game (balances, folders, the queue, the hint, the clock). The game finishes with the score the figures give.
  - from the BACKUP FILE: the director downloaded it before; the new device loads it and finds the room, the requests and the marks."""
import json

import pytest

from opencase.loader import load_defaults
from test_room import QS, LocalRelay, _approve, _context, _director, _phone, _state, _wait  # noqa: F401  (fixtures and helpers)
from test_requests_ui import _balance as _balance_in_view, _fill_form, _start_investigation

pytestmark = pytest.mark.web


@pytest.fixture
def relay():
    return LocalRelay()


def _balance(page):
    """The tokens a phone shows (they are on its Ask tab)."""
    page.click("#oc-tab-ask")
    return _balance_in_view(page)


def _game_in_progress(site, browser, relay):
    """A director and two phones, a few requests answered, one waiting, a sheet and a hint handed out. Returns what was seen."""
    folder, base = site
    version = next((folder / "play" / "cases" / "chupacabras-labranza" / "es").iterdir())
    director_json = json.loads((version / "director.json").read_text(encoding="utf-8"))
    director_ctx = _context(browser, relay)
    director, pin = _director(director_ctx, base, teams=2)
    phones = {}
    for team in "AB":
        ctx = _context(browser, relay)
        phones[team] = (ctx, _phone(ctx, base, pin, f"Tel-{team}"))
    for team in "AB":
        _wait(lambda t=team: phones[t][1].query_selector('#oc-room-status[data-status="waiting"]'), what=f"{team} waiting")
        _approve(director, f"Tel-{team}", team)
    for team in "AB":
        _wait(lambda t=team: (_state(phones[t][1]) or {}).get("team") == t, what=f"{team} folder")
        phones[team][1].wait_for_selector("#oc-tab-ask")
    a, b = phones["A"][1], phones["B"][1]
    director.click("#oc-tab-room")
    _wait(lambda: len(director.query_selector_all('[data-online="true"]')) == 2, what="2 phones online")
    _start_investigation(director, a, b)

    start = {"A": _balance(a), "B": _balance(b)}
    for phone, req in ((a, {"kind": "procedure", "code": "DG2", "text": "llamadas"}), (b, {"kind": "procedure", "code": "DG2", "text": "llamadas B"})):
        _fill_form(phone, req)
        phone.click("#oc-req-send")
    director.click("#oc-tab-requests")
    for team in "AB":
        director.wait_for_selector(f'.oc-request[data-team="{team}"]', timeout=30000)
        director.click(f'.oc-request[data-team="{team}"] [data-answer="give"]')
    _wait(lambda: _balance(a)[0] == start["A"][0] - 1 and _balance(b)[0] == start["B"][0] - 1, what="balances after the answers")
    # a request that nobody answers (it is waiting in the queue)
    _fill_form(b, {"kind": "procedure", "code": "DG7", "target": "P", "text": "ropa de Pía"})
    b.click("#oc-req-send")
    director.wait_for_selector('.oc-request[data-team="B"]', timeout=30000)
    # a hint to A
    hint = director_json["hints"][0]
    director.click("#oc-tab-game")
    director.click('[data-give-hint="A"]')
    hint_file = next(c["file"] for c in director_json["cards"] if c["code"] == hint["code"])
    _wait(lambda: hint_file in ((_state(a) or {}).get("items") or {}), what="the hint reaches A")
    return {"base": base, "pin": pin, "director_ctx": director_ctx, "director": director, "phones": phones, "start": start,
            "hint_file": hint_file, "director_json": director_json}


def _links(phones):
    out = []
    for team in "AB":
        page = phones[team][1]
        page.click("#oc-tab-room")
        out.append(page.locator("#oc-recover-code").text_content().strip())
    return out


def test_the_director_loses_its_device_and_the_teams_give_the_game_back(site, browser, relay):
    g = _game_in_progress(site, browser, relay)
    base, phones, figures = g["base"], g["phones"], load_defaults()
    a, b = phones["A"][1], phones["B"][1]
    before = {"A": _balance(a), "B": _balance(b)}
    files = {t: sorted(((_state(phones[t][1]) or {}).get("items") or {})) for t in "AB"}
    links = _links(phones)
    assert all("/play/director/#recuperar.oc1r." in link for link in links)

    # --- the director's device is lost: its page, its IndexedDB and its room are gone -------------------------------------------
    g["director_ctx"].close()
    _wait(lambda: a.query_selector("#oc-room-status[data-connected='false']"), seconds=40, what="the phones see the director leave")

    # --- a new device: it opens the link of one team (the code is prefilled) and pastes the other ---------------------------------
    ctx = _context(browser, relay)
    fresh = ctx.new_page()
    fresh.goto(base + "play/director/" + QS + "#" + links[0].split("#", 1)[1])
    fresh.wait_for_selector("#oc-rec-codes")
    assert "oc1r." in fresh.input_value("#oc-rec-codes")
    fresh.fill("#oc-rec-codes", "\n".join(links))
    fresh.click("#oc-rec-start")
    for team in "AB":
        fresh.wait_for_selector(f'#oc-recovery [data-team="{team}"][data-regs="1"]', timeout=40000)
    # nothing was sent to the phones while the director was choosing: their balances are the ones they had
    assert (_balance(a), _balance(b)) == (before["A"], before["B"])
    assert fresh.locator("#oc-rec-apply").is_enabled()
    fresh.click("#oc-rec-apply")
    fresh.wait_for_selector(".oc-tabs", timeout=20000)

    # --- the game is back: queue, register, clock, the phones' folders and balances ----------------------------------------------
    fresh.click("#oc-tab-requests")
    fresh.wait_for_selector('.oc-request[data-team="B"]', timeout=30000)
    assert fresh.locator('.oc-request[data-team="A"]').count() == 0, "A has nothing waiting"
    fresh.click("#oc-tab-register")
    fresh.wait_for_selector('[data-team="A"]')
    assert "DG2" in fresh.inner_text("#app")
    fresh.click("#oc-tab-game")
    fresh.wait_for_selector('#oc-clock-card[data-phase="investigation"]')
    assert (_balance(a), _balance(b)) == (before["A"], before["B"])
    assert {t: sorted(((_state(phones[t][1]) or {}).get("items") or {})) for t in "AB"} == files
    assert g["hint_file"] in files["A"]
    _wait(lambda: a.query_selector("#oc-room-status[data-connected='true']"), seconds=40, what="the phones see the new director")

    # the waiting request is answered by the new device and charged on the recovered balance
    fresh.click("#oc-tab-requests")
    fresh.click('.oc-request[data-team="B"] [data-answer="give"]')
    _wait(lambda: _balance(b)[0] == before["B"][0] - 1, seconds=30, what="B's balance after the answer")
    assert b.locator("#oc-req-waiting li").count() == 0

    # --- the score: the hint cost and the tokens that are left come out of the figures, as in a game that never lost anything ------
    s = figures["score"]
    left_a = _balance(a)[0]
    fresh.click("#oc-tab-score")
    fresh.click('[data-score-team="A"] [data-acc="culprit"]')
    fresh.check('[data-score-team="A"] [data-mark="how"]')
    want_a = s["culprit"] + s["how"] + left_a * s["spare_token"] - figures["hint_penalties"][0]
    _wait(lambda: float(fresh.locator('[data-score-team="A"] .oc-total').get_attribute("data-total")) == want_a, what="total of A")
    # the new device can back up what it now has, and the phones show their recovery code again for another loss
    with fresh.expect_download() as dl:
        fresh.click("#oc-backup-top")
    saved = json.loads(open(dl.value.path(), encoding="utf-8").read())
    assert saved["format"] == "opencase-backup" and saved["game"]["play"]["marks"]["A"]["accusation"] == "culprit"
    for c, _ in phones.values():
        c.close()
    ctx.close()


def test_a_backup_file_brings_back_the_room_the_requests_and_the_marks(site, browser, relay, tmp_path):
    g = _game_in_progress(site, browser, relay)
    base, phones = g["base"], g["phones"]
    a, b = phones["A"][1], phones["B"][1]
    before = {"A": _balance(a), "B": _balance(b)}
    director = g["director"]
    director.click("#oc-tab-score")
    director.click('[data-score-team="A"] [data-acc="culprit"]')
    director.check('[data-score-team="A"] [data-mark="why"]')
    with director.expect_download() as dl:
        director.click("#oc-backup-top")
    path = tmp_path / "backup.opencase.json"
    dl.value.save_as(path)
    assert dl.value.suggested_filename.endswith(".opencase.json")
    g["director_ctx"].close()

    ctx = _context(browser, relay)
    fresh = ctx.new_page()
    fresh.goto(base + "play/director/" + QS)
    fresh.wait_for_selector("#oc-rec-backup", state="attached")
    fresh.locator("#oc-recover summary").click()
    fresh.set_input_files("#oc-rec-backup", path)
    fresh.wait_for_selector(".oc-tabs", timeout=20000)
    # the same room: the phones that were approved come back by themselves, and their balances are untouched
    fresh.click("#oc-tab-room")
    assert fresh.inner_text("#oc-room-pin").strip() == g["pin"]
    _wait(lambda: len(fresh.query_selector_all('[data-online="true"]')) == 2, seconds=60, what="the phones reconnect")
    assert (_balance(a), _balance(b)) == (before["A"], before["B"])
    fresh.click("#oc-tab-requests")
    fresh.wait_for_selector('.oc-request[data-team="B"]')
    fresh.click("#oc-tab-score")
    assert fresh.locator('[data-score-team="A"] [data-mark="why"]').is_checked(), "the marks of the score come back"
    for c, _ in phones.values():
        c.close()
    ctx.close()
