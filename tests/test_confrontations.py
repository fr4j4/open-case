"""Confrontations as data (opencase/confrontations.py): `opens_with` in cards.yaml, the guide's table that comes from it,
the checks and the card each evidence opens. site/play/js/rules.js repeats `match`; tests/web/test_rules.py runs the
same cases through it."""
import json
from pathlib import Path

import pytest

from opencase.confrontations import match
from opencase.documents import build_documents
from opencase.loader import CaseError, load_case
from opencase.markup import use_strings

from test_validate import case_dir, cards_file, edit_yaml, write  # noqa: F401  (the fixture and helpers)

REPO = Path(__file__).resolve().parent.parent
GOLDEN = json.loads((REPO / "tests" / "web_expected" / "chupacabras-labranza-confrontations.json").read_text(encoding="utf-8"))["cases"]


def chupacabras():
    case = load_case(REPO / "cases" / "chupacabras-labranza", "es")
    use_strings(case.strings)
    return case


@pytest.mark.parametrize("g", GOLDEN, ids=lambda g: f"{g['suspect']}:{'+'.join(g['evidence']) or '-'}{'|held ' + ','.join(g['held']) if g['held'] else ''}")
def test_the_evidence_opens_the_card_the_old_table_said(g):
    got = match(chupacabras(), g["suspect"], g["evidence"], g["held"])
    assert got == {"card": g["card"], "candidates": g["candidates"]}


def test_the_chupacabras_loads_without_warnings_and_every_confrontation_has_rules():
    case = chupacabras()
    assert case.warnings == []
    from opencase.loader import card_kind, iter_cards
    for c, g in iter_cards(case):
        if card_kind(c, g) == "confrontation":
            assert c.get("opens_with"), c["code"]


def test_the_guide_table_comes_from_the_cards():
    case = chupacabras()
    guide = next(d.html for d in build_documents(case) if d.key == "guide")
    assert "Tarjeta B8, no B10: el vehículo sigue exigiendo E17·B" in guide
    assert "Tarjeta C5 + E11" in guide and "Tarjeta C6 + E22" in guide
    assert "Aviso 2 o E13b, cuando ya tienen la T6" in guide
    assert "Cualquier otra prueba" in guide


# --- a small case ---------------------------------------------------------------------------------------------

def add(root, rules, extra=None):
    """A1 is a confrontation of suspect A; E01 and E02 are the dossier sheets the rules can name."""
    def change(d):
        d["groups"][0]["suspect"] = "A"
        d["groups"][0]["cards"].append({"code": "A9", "type": "confrontation", "question": "¿Y esto?", "answer": "Ya.",
                                        "opens_with": rules, **(extra or {})})
    edit_yaml(cards_file(root), change)
    return root


def test_a_rule_names_things_that_exist(case_dir):
    with pytest.raises(CaseError, match="E77.*neither a sheet"):
        load_case(add(case_dir, [{"all": ["E77"]}]), "es")


def test_a_rule_needs_all_or_any(case_dir):
    with pytest.raises(CaseError, match="needs `all` or `any`"):
        load_case(add(case_dir, [{"none": ["E01"]}]), "es")


def test_unknown_fields_and_wrong_priority_stop_the_export(case_dir):
    with pytest.raises(CaseError, match="unknown fields: cuando"):
        load_case(add(case_dir, [{"all": ["E01"], "cuando": 1}]), "es")


def test_opens_with_is_only_for_confrontations_follow_ups_and_failed(case_dir):
    def change(d):
        d["groups"][0]["cards"][0]["opens_with"] = [{"all": ["E01"]}]
    edit_yaml(cards_file(case_dir), change)
    with pytest.raises(CaseError, match="only confrontation, follow-up and failed"):
        load_case(case_dir, "es")


def test_a_default_text_is_written_when_the_rule_has_none(case_dir):
    root = add(case_dir, [{"all": ["E01"], "any": ["E02"], "none": ["A1"], "priority": 2}])
    case = load_case(root, "es")
    use_strings(case.strings)
    from opencase.confrontations import rows
    assert rows(case)[0]["shows"] == "E02 junto con E01 (sin A1)"
    assert rows(case)[0]["mark"] == "A◆"


def test_a_text_that_forgets_a_code_is_a_warning(case_dir):
    case = load_case(add(case_dir, [{"all": ["E01"], "shows": "algo distinto"}]), "es")
    assert any("does not mention E01" in w for w in case.warnings)


def test_a_confrontation_without_rules_is_a_warning_only_when_the_case_uses_them(case_dir):
    root = add(case_dir, [{"all": ["E01"], "shows": "E01"}])
    def more(d):
        d["groups"][0]["cards"].append({"code": "A8", "type": "confrontation", "question": "?", "answer": "Sí."})
    edit_yaml(cards_file(root), more)
    case = load_case(root, "es")
    assert any("A8 has no opens_with" in w for w in case.warnings)


def test_a_tie_gives_no_card_and_a_higher_priority_wins(case_dir):
    root = add(case_dir, [{"any": ["E01"], "shows": "E01"}])
    def more(d):
        d["groups"][0]["cards"].append({"code": "A8", "type": "confrontation", "question": "?", "answer": "Sí.",
                                        "opens_with": [{"any": ["E01", "E02"], "shows": "E01 o E02"}]})
    edit_yaml(cards_file(root), more)
    case = load_case(root, "es")
    assert match(case, "A", ["E01"]) == {"card": None, "candidates": ["A9", "A8"]}
    assert match(case, "A", ["E02"]) == {"card": "A8", "candidates": ["A8"]}
