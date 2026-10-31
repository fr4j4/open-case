"""F5 · the pages: the phases, the notices, the hints, the sheets handed in and the score, with a director and two phones over the
real `relay` transport against a Nostr relay written in Python (as in test_room.py and test_requests_ui.py).

The game: nobody can ask before the investigation; the director moves the clock there; a team asks; the notice comes due at the
minute of the case and the director hands it out to everybody; a hint is given (and costs); each team fills the sheets of the kit;
closing the accusation sends what a team did not hand in; the director ticks the score and the totals are the ones worked out from
the figures of defaults.yaml."""
import json

import pytest

from opencase.loader import load_defaults
from test_room import LocalRelay, _approve, _context, _director, _phone, _state, _wait  # noqa: F401  (fixtures and helpers)
from test_requests_ui import _balance, _fill_form

pytestmark = pytest.mark.web


@pytest.fixture
def relay():
    return LocalRelay()


def test_a_whole_game_from_the_scene_to_the_score(site, browser, relay):
    folder, base = site
    version = next((folder / "play" / "cases" / "chupacabras-labranza" / "es").iterdir())
    director_json = json.loads((version / "director.json").read_text(encoding="utf-8"))
    team_json = json.loads((version / "team.json").read_text(encoding="utf-8"))
    figures = load_defaults()
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

    # --- the phases: the phone shows where the game is, and nobody can ask before the investigation ---------------------
    _wait(lambda: a.query_selector('#oc-clock[data-phase="setup"]'), what="the phone gets the clock")
    assert a.locator("#oc-clock").get_attribute("data-asking") == "false"
    _fill_form(a, {"kind": "procedure", "code": "DG2", "text": "llamadas"})
    assert a.locator("#oc-req-send").is_disabled()
    assert a.locator("#oc-req-why").count() == 1
    director.click("#oc-tab-game")
    director.click('#oc-clock-card [data-phase="scene"]')
    _wait(lambda: a.query_selector('#oc-clock[data-phase="scene"]'), what="scene")
    director.click('#oc-clock-card [data-phase="investigation"]')
    _wait(lambda: a.query_selector('#oc-clock[data-phase="investigation"][data-asking="true"]'), what="investigation on the phone")
    _wait(lambda: b.query_selector('#oc-clock[data-phase="investigation"]'), what="investigation on the other phone")

    # a team asks and the director answers (the full flow is tested in test_requests_ui.py)
    start = _balance(a)
    _fill_form(a, {"kind": "procedure", "code": "DG2", "text": "llamadas"})
    assert a.locator("#oc-req-send").is_enabled()
    a.click("#oc-req-send")
    director.click("#oc-tab-requests")
    director.wait_for_selector('.oc-request[data-team="A"]', timeout=30000)
    director.click('.oc-request[data-team="A"] [data-answer="give"]')
    _wait(lambda: _balance(a)[0] == start[0] - 1, seconds=20, what="balance after the answer")

    # --- notices: suggested at the minute of the case, handed out by the director to every team --------------------------
    notice = next(n for n in director_json["notices"] if n["kind"] == "notice")
    director.click("#oc-tab-game")
    row = director.locator(f'[data-notice="{notice["code"]}"]')
    assert row.get_attribute("data-due") == "false"
    for _ in range(notice["minute"]):
        director.click('[data-shift="60"]')
    _wait(lambda: director.query_selector(f'[data-notice="{notice["code"]}"][data-due="true"]'), what="the notice comes due")
    director.click(f'[data-send-notice="{notice["code"]}"]')
    card = next(c for c in director_json["cards"] if c["code"] == notice["code"])
    for team, page in (("A", a), ("B", b)):
        _wait(lambda p=page, f=card["file"]: f in ((_state(p) or {}).get("items") or {}), what=f"the notice reaches {team}")
    assert director.locator(f'[data-notice="{notice["code"]}"]').get_attribute("data-read") == "true"
    # what the teams see never has the minute at which a notice is suggested
    a.click("#oc-tab-folder")
    assert "Sugerido" not in a.inner_text("body") and "minuto" not in a.inner_text("#oc-clock").lower()

    # --- a hint costs points ---------------------------------------------------------------------------------------------
    hint = director_json["hints"][0]
    director.click('[data-give-hint="A"]')
    hint_file = next(c["file"] for c in director_json["cards"] if c["code"] == hint["code"])
    _wait(lambda: hint_file in ((_state(a) or {}).get("items") or {}), what="the hint reaches A")
    assert hint_file not in ((_state(b) or {}).get("items") or {})

    # --- the sheets: A hands in the accusation, B only writes the discard (it goes at the closing) ---------------------------
    forms = {f["id"]: f for f in team_json["forms"]}
    accusation, discard = list(forms)[:2]
    a.click("#oc-tab-forms")
    a.fill(f'[data-form="{accusation}"] [data-field="f0.0"]', "Hernán Carrasco")
    a.click(f'[data-submit="{accusation}"]')
    a.wait_for_selector(f"#oc-form-sent-{accusation}", timeout=20000)
    b.click("#oc-tab-forms")
    b.fill(f'[data-form="{discard}"] [data-field="t0.0.0"]', "En su casa, con testigos")
    director.click("#oc-tab-score")
    director.wait_for_selector(f'[data-score-team="A"] [data-form="{accusation}"][data-received="true"]', timeout=20000)
    assert director.locator(f'[data-score-team="B"] [data-form="{discard}"]').get_attribute("data-received") == "false"
    director.click("#oc-tab-game")
    director.click('#oc-clock-card [data-phase="accusation"]')
    director.click('#oc-clock-card [data-phase="closing"]')
    director.click("#oc-tab-score")
    director.wait_for_selector(f'[data-score-team="B"] [data-form="{discard}"][data-received="true"]', timeout=30000)
    director.locator(f'[data-score-team="B"] [data-form="{discard}"] summary').click()
    assert "En su casa, con testigos" in director.inner_text(f'[data-score-team="B"] [data-form="{discard}"]')
    b.wait_for_selector(f"#oc-form-sent-{discard}", timeout=20000)

    # --- the score: A names the culprit with evidence and explains how; B accuses the wrong person ---------------------------
    s = figures["score"]
    a.click("#oc-tab-ask")
    b.click("#oc-tab-ask")
    left_a = _balance(a)[0]
    left_b = _balance(b)[0]
    director.click('[data-score-team="A"] [data-acc="culprit"]')
    director.check('[data-score-team="A"] [data-mark="how"]')
    director.click('[data-score-team="B"] [data-acc="wrong"]')
    want_a = s["culprit"] + s["how"] + left_a * s["spare_token"] - figures["hint_penalties"][0]
    want_b = s["wrong_accusation"] + left_b * s["spare_token"]
    _wait(lambda: float(director.locator('[data-score-team="A"] .oc-total').get_attribute("data-total")) == want_a, what="total of A")
    _wait(lambda: float(director.locator('[data-score-team="B"] .oc-total').get_attribute("data-total")) == want_b, what="total of B")
    assert director.locator('#oc-ranking [data-rank="1"]').get_attribute("data-team") == "A"
    assert director.locator("#oc-winner").count() == 1
    assert director.locator('#oc-ranking [data-team="B"]').get_attribute("data-can-win") == "false"
    with director.expect_download() as dl:
        director.click("#oc-report")
    text = open(dl.value.path(), encoding="utf-8").read()
    assert "Equipo A" in text and "Equipo B" in text and "Hernán Carrasco" in text
    for ctx, _ in phones.values():
        ctx.close()
    director_ctx.close()
