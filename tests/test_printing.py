"""The print plan (opencase/printing.py): which documents, how many copies and in what order, counted
from the data. tools/check_print.py checks it against real PDFs; these tests check it without a browser."""
from pathlib import Path

import pytest

from opencase import printing
from opencase.cli import use_teams
from opencase.documents import REPO_ROOT, build_documents
from opencase.loader import CaseError, Sheet, load_case
from opencase.markup import use_strings

CHUPACABRAS = REPO_ROOT / "cases" / "chupacabras-labranza"


def load(teams=None, chat=False):
    case = load_case(CHUPACABRAS, "es")
    if teams is not None:
        use_teams(case, teams)
    if chat:
        case.data["_chat"] = True
    use_strings(case.strings)
    return case


@pytest.fixture(scope="module")
def built():
    case = load()
    return case, build_documents(case), printing.plan(case)


def test_every_document_is_in_the_plan(built):
    case, docs, plan = built
    assert sorted(d.file for d in docs) == sorted(i.file for i in plan)
    folders = {d.file: d.folder for d in docs}
    assert all(folders[i.file] == i.folder for i in plan)


def test_packages_follow_the_design(built):
    case, docs, plan = built
    keys = [i.key for i in plan]
    assert keys == ["badges", "tokens", "requests", "suspects", "kit", "envelopes:1", "envelopes:2",
                    "guide", "evidence", "cards", "card-backs", "labels"]
    by_key = {i.key: i for i in plan}
    assert {i.key for i in plan if i.package == "team"} == {"badges", "tokens", "requests", "suspects", "kit",
                                                            "envelopes:1", "envelopes:2"}
    assert by_key["requests"].pages == 3 and by_key["requests"].optional   # ceil(19 / 8): 24 slips for 19 tokens
    assert by_key["tokens"].pages == 8 and by_key["tokens"].per_team       # one sheet + back for each of 4 teams
    assert by_key["evidence"].copies == 4 and by_key["cards"].copies == 4
    assert by_key["card-backs"].copies == by_key["cards"].pages * 4
    assert by_key["labels"].folder == "director"
    assert "dossier" not in keys   # the complete dossier is gone


def test_evidence_is_ordered_by_code(built):
    case, docs, plan = built
    ids = printing.evidence_ids(case)
    assert len(ids) == 52
    assert ids[:4] == ["E08", "E09", "E10", "E11"] and ids[-1] == "E31"
    assert ids.index("E13b") < ids.index("E13b-2") < ids.index("E13c")
    assert ids.index("E15-B") < ids.index("E15-C") < ids.index("E16")
    evidence = next(d for d in docs if d.key == "evidence").html
    assert evidence.index('id="E14"') < evidence.index('id="E20"') < evidence.index('id="E30"')


def test_the_kit_has_no_cover_and_the_guide_ends_with_the_index(built):
    case, docs, plan = built
    html = {d.key: d.html for d in docs}
    assert "oc-tapa" not in html["kit"]
    assert html["guide"].rfind('id="index-1"') > html["guide"].rfind('id="09-confesion-y-cierre"')
    assert "Pruebas</td>" in html["guide"] and "Sobre 1</td>" in html["guide"]


def test_notices_are_only_cards(built):
    case, docs, plan = built
    html = {d.key: d.html for d in docs}
    assert not any(h.get("notice") for h in case.dossier.values())
    assert "Aviso 1 · min 10" in html["guide"] and "Toto intentó irse" in html["guide"]   # the control sheet


def test_each_team_gets_its_own_token_sheet(built):
    case, docs, plan = built
    tokens = next(d for d in docs if d.key == "tokens").html
    sheets = tokens.split('<section class="oc-pliego oc-pliego--fichas">')[1:]
    assert len(sheets) == 8
    for team, front in zip("ABCD", sheets[::2]):
        assert f"Equipo {team}" in front and front.count("oc-ficha--coartada") == 3
        assert all(f"Equipo {other}" not in front for other in "ABCD" if other != team)


def test_fewer_teams():
    case = load(teams=2)
    plan = {i.key: i for i in printing.plan(case)}
    assert plan["badges"].pages == 2 and plan["tokens"].pages == 4 and plan["evidence"].copies == 2
    docs = {d.key: d.html for d in build_documents(case)}
    assert "Equipo C" not in docs["tokens"] and "Equipo C" not in docs["labels"]
    assert "Con 2 equipos" in docs["guide"]


def test_teams_out_of_range():
    case = load_case(CHUPACABRAS, "es")
    with pytest.raises(CaseError, match="--teams 5"):
        use_teams(case, 5)


def test_chat_mode_prints_no_evidence():
    paper, chat = load(), load(chat=True)
    by_key = {i.key: i for i in printing.plan(chat)}
    assert by_key["evidence"].copies == 0
    assert printing.totals(printing.plan(paper))["bond"] - printing.totals(printing.plan(chat))["bond"] == 4 * by_key["evidence"].pages


def test_readme_lists_every_pdf(built):
    case, docs, plan = built
    text = printing.readme(case, "2026-10-31", "modo")
    for d in docs:
        assert f"{d.folder}/{d.file}.pdf" in text


@pytest.mark.parametrize("value", [0, "dos", 1.5, True])
def test_pages_must_be_a_whole_number(value):
    with pytest.raises(CaseError, match="pages"):
        printing.sheet_pages(Sheet("E01", Path("E01.md"), {"pages": value}))


def test_natural_order():
    codes = ["E10", "E9", "E13b", "E13a", "E15 · C", "E15 · B", "E2"]
    assert sorted(codes, key=printing.natural_key) == ["E2", "E9", "E10", "E13a", "E13b", "E15 · B", "E15 · C"]
