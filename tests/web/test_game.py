"""F5 · site/play/js/clock.js and score.js, and the pages: the phases, the notices, the hints, the sheets handed in and the score.

The pure modules are tested with node (tests/web/game.test.mjs) against numbers that this file works out apart from the JS,
from opencase/defaults.yaml and the case: the minutes of the phases, the notices and the points of a scripted game of three
teams. The pages (director and phones over the real `relay` transport) are in test_game_ui.py."""
import json
import shutil
import subprocess
from pathlib import Path

import pytest
import yaml

from opencase import web
from opencase.loader import load_defaults

REPO = Path(__file__).resolve().parent.parent.parent
CASES = REPO / "cases"
CASE = "chupacabras-labranza"
NODE = shutil.which("node")

pytestmark = pytest.mark.skipif(NODE is None, reason="node is not installed")

# What each team of the scripted game achieved (the director ticks it) and how many numbered tokens it had left.
GAME = {
    "A": {"marks": {"accusation": "culprit", "how": True, "why": True, "window": True, "bonus": True, "contradiction": True,
                    "discard_two": 3, "discard_one": 1, "discard_blank": 1, "red_herring": 2}, "tokens_left": 4, "hints": [1, 4]},
    "B": {"marks": {"accusation": "wrong", "how": True, "discard_two": 1}, "tokens_left": 9, "hints": []},
    "C": {"marks": {"accusation": "culprit_no_evidence", "why": True, "discard_two": 2, "discard_blank": 2}, "tokens_left": 2, "hints": [2]},
    "D": {"marks": {}, "tokens_left": 11, "hints": []},
}


def expected_total(figures, bonus, team):
    """The printed score sheet, added up by hand from the figures (an independent account of what score.js does)."""
    s, m = figures["score"], team["marks"]
    if not m:
        return team["tokens_left"] * s["spare_token"]
    total = {"culprit": s["culprit"], "culprit_no_evidence": s["culprit_no_evidence"], "wrong": 0}[m["accusation"]]
    total += (s["how"] if m.get("how") else 0) + (s["why"] if m.get("why") else 0) + (s["window"] if m.get("window") else 0)
    total += (bonus if m.get("bonus") else 0) + (s["contradiction"] if m.get("contradiction") else 0)
    total += m.get("discard_two", 0) * s["discard_two"] + m.get("discard_one", 0) * s["discard_one"]
    total += m.get("discard_blank", 0) * s["discard_blank"] + m.get("red_herring", 0) * s["red_herring"]
    if m["accusation"] == "wrong":
        total += s["wrong_accusation"]
    total += team["tokens_left"] * s["spare_token"]
    total -= sum(figures["hint_penalties"][n - 1] for n in team["hints"])
    return total


figures = load_defaults()


def _compile(case_dir, out):
    entries = web.build_cases([case_dir], out)
    return out / "play" / next(e for e in entries if e["language"] == "es")["path"]


def _node(folder, scenario, tmp_path):
    f = tmp_path / "game.json"
    f.write_text(json.dumps(scenario), encoding="utf-8")
    env = {"OC_WEB_DIR": str(folder), "OC_GAME": str(f), "PATH": str(Path(NODE).parent)}
    return subprocess.run([NODE, "--test", str(REPO / "tests" / "web" / "game.test.mjs")], cwd=REPO, env=env, capture_output=True, text=True)


def scenario(case_figures, bonus):
    teams = [{"team": k, "marks": v["marks"], "tokens_left": v["tokens_left"], "hints": v["hints"],
              "total": expected_total(case_figures, bonus, v), "can_win": v["marks"].get("accusation") in ("culprit", "culprit_no_evidence")}
             for k, v in GAME.items()]
    order = sorted((t for t in teams), key=lambda t: (not t["can_win"], -t["total"], 16 - t["tokens_left"], t["team"]))
    phases = [[k, v] for k, v in case_figures["phases"].items()] + [["closing", case_figures["closing_minutes"][0]]]
    return {"phases": phases, "teams": teams, "ranking": [t["team"] for t in order], "question_cost": case_figures["costs"]["question"],
            "notice_minutes": case_figures["notice_minutes"][:2], "lines": ["culprit", "how", "why", "window", "bonus", "contradiction",
                                                                              "discard_two", "discard_one", "discard_blank", "red_herring"]}


def test_clock_and_score_js_agree_with_the_figures(tmp_path):
    folder = _compile(CASES / CASE, tmp_path / "site")
    bonus = yaml.safe_load((CASES / CASE / "case.yaml").read_text(encoding="utf-8")).get("score_bonus") or 0
    done = _node(folder, scenario(figures, bonus), tmp_path)
    assert done.returncode == 0, done.stdout[-6000:] + done.stderr[-2000:]


def test_changing_a_figure_of_the_case_changes_the_app_without_touching_js(tmp_path):
    """phases.investigation, notice_minutes and score are figures of case.yaml: the compiled JSON carries them and the same JS
    (clock.js, score.js) gives the new times and points."""
    case = tmp_path / "case"
    shutil.copytree(CASES / CASE, case)
    data = yaml.safe_load((case / "case.yaml").read_text(encoding="utf-8"))
    data["phases"] = {"investigation": 22}
    data["score"] = {"how": 3, "spare_token": 0.5}
    data["notice_minutes"] = [8, 16]
    (case / "case.yaml").write_text(yaml.safe_dump(data, allow_unicode=True, sort_keys=False), encoding="utf-8")
    folder = _compile(case, tmp_path / "site")
    team = json.loads((folder / "team.json").read_text(encoding="utf-8"))
    assert team["figures"]["phases"]["investigation"] == 22
    assert team["figures"]["phases"]["scene"] == figures["phases"]["scene"]   # nested figures merge one by one
    merged = {**figures, "phases": {**figures["phases"], "investigation": 22}, "score": {**figures["score"], "how": 3, "spare_token": 0.5},
              "notice_minutes": [8, 16]}
    bonus = data.get("score_bonus") or 0
    done = _node(folder, scenario(merged, bonus), tmp_path)
    assert done.returncode == 0, done.stdout[-6000:] + done.stderr[-2000:]
