"""F4b · the pages: teams ask from their phones with a balance of tokens and the director answers from the panel.

The scripted game is the v8 simulation of three teams (tests/web/partidas/v8_tres_equipos.json, rounds 1 to 3: 21 requests).
Every request is made in the form of the team's page and answered with a button of the panel, over the real `relay`
transport against a Nostr relay written in Python (as in test_room.py). At the end each team's folder and tokens are the ones
the simulation ended with. The rules themselves are tested in test_requests.py and test_rules.py."""
import json
import re
from pathlib import Path

import pytest

from test_room import LocalRelay, _approve, _context, _director, _phone, _state, _wait  # noqa: F401  (fixtures and helpers)

pytestmark = pytest.mark.web

GAME = json.loads((Path(__file__).parent / "partidas" / "v8_tres_equipos.json").read_text(encoding="utf-8"))


@pytest.fixture
def relay():
    return LocalRelay()


def _norm(code):
    return re.sub(r"[\s·\-.]+", "", code).lower()


def _fill_form(page, req):
    page.click("#oc-tab-ask")
    page.click(f'.oc-chip[data-kind="{req["kind"]}"]')
    if req["kind"] == "procedure":
        page.select_option("#oc-p-code", req["code"])
        if req.get("target"):
            page.select_option("#oc-p-target", req["target"])
        page.fill("#oc-p-text", req.get("text", ""))
        if req.get("alibi"):
            page.check("#oc-p-alibi")
    elif req["kind"] == "witness":
        page.fill("#oc-w-who", req["who"])
        page.fill("#oc-w-detail", req.get("detail", ""))
        page.fill("#oc-w-text", req.get("text", ""))
    elif req["kind"] == "confrontation":
        page.select_option("#oc-c-suspect", req["suspect"])
        for code, points in req["evidence"]:
            page.check(f'[data-evidence="{code}"]')
            page.fill(f'[data-point="{code}"]', points)
    else:
        raise AssertionError(req["kind"])


def _balance(page):
    box = page.locator("#oc-balance")
    return int(box.get_attribute("data-tokens")), int(box.get_attribute("data-alibi"))


def test_three_teams_play_the_v8_rounds_through_the_forms_and_the_panel(site, browser, relay):
    folder, base = site
    director_ctx = _context(browser, relay)
    director, pin = _director(director_ctx, base, teams=3)
    phones = {}
    for team in "ABC":
        ctx = _context(browser, relay)
        phones[team] = (ctx, _phone(ctx, base, pin, f"Tel-{team}"))
    for team in "ABC":
        _wait(lambda t=team: phones[t][1].query_selector('#oc-room-status[data-status="waiting"]'), what=f"{team} waiting")
        _approve(director, f"Tel-{team}", team)
    for team in "ABC":
        _wait(lambda t=team: (_state(phones[t][1]) or {}).get("team") == t, what=f"{team} folder")
        phones[team][1].wait_for_selector("#oc-tab-ask")
        _wait(lambda t=team: phones[t][1].query_selector('#oc-room-status[data-connected="true"]') or phones[t][1].query_selector("#oc-tab-ask"), what="connected")
    director.click("#oc-tab-room")
    _wait(lambda: len(director.query_selector_all('[data-online="true"]')) == 3, what="3 phones online")
    director.click("#oc-tab-requests")

    start = {}
    for team in "ABC":
        phones[team][1].click("#oc-tab-ask")
        start[team] = _balance(phones[team][1])
    assert start["A"] == start["B"] == start["C"] and start["A"][0] > 10

    spent = {t: [0, 0] for t in "ABC"}
    asked = {t: 0 for t in "ABC"}
    for i, step in enumerate(GAME["steps"]):
        team, req = step["team"], step["request"]
        page = phones[team][1]
        _fill_form(page, req)
        send = page.locator("#oc-req-send")
        assert send.is_enabled(), f"step {i + 1}: the phone lets the team send {req}"
        send.click()
        asked[team] += 1
        card = director.locator(f'.oc-request[data-team="{team}"]')
        card.wait_for(timeout=30000)
        choice = step.get("choice") or {}
        if choice.get("card"):
            director.locator(f'.oc-request[data-team="{team}"] [data-card="{choice["card"]}"] input').check()
        director.locator(f'.oc-request[data-team="{team}"] [data-answer="{step["button"]}"]').click(timeout=15000)
        director.wait_for_selector(f'.oc-request[data-team="{team}"]', state="detached", timeout=15000)
        cost = 0 if step["button"] == "no_basis" else 1
        if req.get("alibi"):
            spent[team][1] += cost
        else:
            spent[team][0] += cost
        want = (start[team][0] - spent[team][0], start[team][1] - spent[team][1])
        _wait(lambda p=page, w=want: _balance(p) == w, seconds=20, what=f"step {i + 1}: balance of {team} is {want}")

    # the folders and the tokens the simulation ended with
    expected_tokens = {"A": (start["A"][0] - 7, start["A"][1] - 2), "B": (start["B"][0] - 4, start["B"][1] - 2), "C": (start["C"][0] - 6, start["C"][1])}
    for team in "ABC":
        page = phones[team][1]
        assert _balance(page) == expected_tokens[team], team
        wanted = {_norm(c) for s in GAME["steps"] if s["team"] == team for c in s["gives"]}
        _wait(lambda p=page, w=wanted: w <= {_norm(i.get("code", "")) for i in (_state(p) or {}).get("items", {}).values()}, seconds=30,
              what=f"folder of {team}")
        page.click("#oc-tab-history")
        assert page.locator("#oc-hist li").count() == asked[team]
        assert str(sum(expected_tokens and (start[team][0] - expected_tokens[team][0], start[team][1] - expected_tokens[team][1]))) in page.inner_text("#oc-hist-total")
    director.click("#oc-tab-register")
    assert director.locator("#oc-register li").count() == len(GAME["steps"])
    assert "s" in director.inner_text("#oc-register-median")
    for ctx, _ in phones.values():
        ctx.close()
    director_ctx.close()


def test_a_request_made_while_the_director_is_away_waits_and_arrives_when_it_returns(site, browser, relay):
    folder, base = site
    director_ctx = _context(browser, relay)
    director, pin = _director(director_ctx, base)
    ctx = _context(browser, relay)
    phone = _phone(ctx, base, pin, "Tel-A")
    _wait(lambda: phone.query_selector('#oc-room-status[data-status="waiting"]'), what="waiting")
    _approve(director, "Tel-A", "A")
    _wait(lambda: (_state(phone) or {}).get("team") == "A", what="folder")
    phone.wait_for_selector("#oc-tab-ask")
    director.close()                                               # the director's page goes away; its game stays in IndexedDB
    _wait(lambda: phone.query_selector("#oc-room-status[data-connected='false']"), seconds=40, what="the phone sees the director leave")
    _fill_form(phone, {"kind": "procedure", "code": "DG2", "text": "llamadas"})
    phone.click("#oc-req-send")
    before = _balance(phone)
    phone.wait_for_selector("#oc-req-waiting li")
    assert phone.locator("#oc-req-offline").count() == 1
    assert phone.locator("#oc-balance-tokens").inner_text() == str(before[0] - 1), "the token is held back while it waits"
    director = director_ctx.new_page()
    director.goto(base + "play/director/?transport=relay&relays=wss://relay.test/")
    director.wait_for_selector(".oc-tabs")
    director.click("#oc-tab-requests")
    director.wait_for_selector('.oc-request[data-team="A"]', timeout=60000)
    director.click('.oc-request[data-team="A"] [data-answer="give"]')
    _wait(lambda: _balance(phone)[0] == before[0] - 1, seconds=30, what="the balance after the answer")
    assert phone.locator("#oc-req-waiting li").count() == 0
    ctx.close()
    director_ctx.close()
