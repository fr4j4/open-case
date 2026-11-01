"""site/play/js/rules.js against the engine: the JS gives the same cards, sheets and costs as the data that
pytest works out from the loaded case (tests/web_expected/), and the tokens follow rules 1 to 6 of the kit.
The JS tests are in rules.test.mjs and run with `node --test`; without node these tests are skipped."""
import json
import shutil
import subprocess
from pathlib import Path

import pytest
import yaml

from opencase import web

REPO = Path(__file__).resolve().parent.parent.parent
CASES = REPO / "cases"
CASE = "chupacabras-labranza"
EXPECTED = REPO / "tests" / "web_expected" / f"{CASE}.json"
CONFRONTATIONS = REPO / "tests" / "web_expected" / f"{CASE}-confrontations.json"
NODE = shutil.which("node")

pytestmark = pytest.mark.skipif(NODE is None, reason="node is not installed")


def _compile(case_dir, out):
    entries = web.build_cases([case_dir], out)
    return out / "play" / next(e for e in entries if e["language"] == "es")["path"]


def _node(version_folder, expected):
    env = {"OC_WEB_DIR": str(version_folder), "OC_EXPECTED": str(expected), "OC_CONFRONTATIONS": str(CONFRONTATIONS), "PATH": str(Path(NODE).parent)}
    return subprocess.run([NODE, "--test", str(REPO / "tests" / "web" / "rules.test.mjs")], cwd=REPO, env=env,
                          capture_output=True, text=True)


def test_rules_js_agrees_with_the_engine(tmp_path):
    folder = _compile(CASES / CASE, tmp_path)
    done = _node(folder, EXPECTED)
    assert done.returncode == 0, done.stdout[-6000:] + done.stderr[-2000:]


def test_a_changed_cost_reaches_the_json_the_kit_and_the_cards(tmp_path):
    """The costs are figures (defaults.yaml): a case that changes them changes the app, the kit and the follow-up box."""
    case = tmp_path / "case"
    shutil.copytree(CASES / CASE, case)
    data = yaml.safe_load((case / "case.yaml").read_text(encoding="utf-8"))
    data["costs"] = {"question": 2, "follow_up": 3}
    (case / "case.yaml").write_text(yaml.safe_dump(data, allow_unicode=True, sort_keys=False), encoding="utf-8")
    folder = _compile(case, tmp_path / "site")
    team = json.loads((folder / "team.json").read_text(encoding="utf-8"))
    assert team["rules"]["costs"] == {"question": 2, "witness": 1, "confrontation": 1, "follow_up": 3}
    assert team["rules"]["requests"]["question"]["cost"] == 2
    assert {f["cost"] for f in team["follow_ups"]} == {3}
    kit = (folder / "sheets" / "kit-oc-20-rules.html").read_text(encoding="utf-8")
    assert "Cada pregunta cuesta <strong>2 fichas</strong>" in kit
    assert "cuesta 1 ficha" in kit   # the witness' question, still 1
    card = (folder / "cards" / "B1.html").read_text(encoding="utf-8")
    assert "Seguimiento B1+ · 3 fichas" in card


def test_the_wildcard_roles_are_in_the_json_and_the_cards_exist(tmp_path):
    folder = _compile(CASES / CASE, tmp_path)
    director = json.loads((folder / "director.json").read_text(encoding="utf-8"))
    wild = director["rules"]["wildcards"]
    codes = {c["code"] for c in director["cards"]}
    assert wild == {"no_findings": "SIN HALLAZGOS", "unavailable": "TESTIGO", "nothing_to_add": "NADA QUE APORTAR",
                    "confrontation_failed": "◆ ✕"}
    assert set(wild.values()) <= codes


def test_a_wrong_role_stops_the_export(tmp_path):
    case = tmp_path / "case"
    shutil.copytree(CASES / CASE, case)
    cards = case / "languages" / "es" / "cards.yaml"
    cards.write_text(cards.read_text(encoding="utf-8").replace("role: no_findings", "role: nothing"), encoding="utf-8")
    with pytest.raises(Exception, match="role 'nothing'"):
        web.build_cases([case], tmp_path / "site")
