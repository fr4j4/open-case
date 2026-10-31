"""Follow-ups and witnesses (opencase/followups.py, opencase/witnesses.py): the box on the card, the guide's
tables drawn from cards.yaml, and the checks of follow_up, unlocked_by and appears_in."""
import pytest

from opencase.documents import build_documents
from opencase.loader import CaseError, load_case
from opencase.markup import use_strings

from test_validate import case_dir, cards_file, edit_yaml, write  # noqa: F401  (the fixture and helpers)


def add_cards(root, lang="es"):
    """A1 enables the follow-up A1+, which also needs E02; Rosa (two questions) appears in E01 and Kevin,
    whom E01 calls "el nieto", hands out E02."""
    def change(d):
        d["groups"][0]["cards"][0]["follow_up"] = "A1+"
        d["groups"][0]["cards"].append({"code": "A1+", "type": "follow-up", "question": "¿Qué dibujo?",
                                        "answer": "Ninguno.", "unlocked_by": "E02", "guide_note": "[false] Miente."})
        d["groups"].append({"title": "Testigos", "type": "witness", "cards": [
            {"code": "R1", "who": "Rosa Soto, vecina", "question": "¿Qué oyó?", "answer": "Nada.", "appears_in": "E01"},
            {"code": "R2", "who": "Rosa Soto, vecina", "question": "¿Qué vio?", "answer": "Un auto."},
            {"code": "K1", "who": "Kevin Soto", "question": "¿Y usted?", "answer": "Volé un dron.", "attach": "E02",
             "appears_in": ["E01"], "aliases": ["el nieto"]}]})
    edit_yaml(cards_file(root).parent.parent / lang / "cards.yaml", change)
    write(root / "languages" / lang / "dossier" / "E01.md",
          "---\ncode: E01\ninstitution: Fiscalía de prueba\ntitle: Parte policial\n---\n\n"
          "La vecina Rosa Soto puede ser entrevistada. El nieto vio luces.\n")
    return root


def docs(root, lang="es"):
    case = load_case(root, lang)
    use_strings(case.strings)
    return case, {d.key: d.html for d in build_documents(case)}


def test_card_box_shows_code_cost_and_condition_but_not_the_question(case_dir):
    case, html = docs(add_cards(case_dir))
    assert case.warnings == []
    cards = html["cards"]
    assert "Seguimiento A1+ · 1 ficha · si ya tienen E02" in cards
    box = cards[cards.index("oc-tarjeta__seguimiento"):]
    assert "¿Qué dibujo?" not in box[:box.index("</div>")]


def test_engine_off_keeps_the_old_line(case_dir):
    edit_yaml(case_dir / "case.yaml", lambda d: d.update(engine_sheets=False))
    case, html = docs(add_cards(case_dir))
    assert "Seguimiento disponible: A1+" in html["cards"] and "oc-tarjeta__seguimiento" not in html["cards"]


@pytest.mark.parametrize("lang", ["es", "en"])
def test_guide_tables(case_dir, lang):
    root = add_cards(case_dir)
    if lang == "en":
        edit_yaml(root / "case.yaml", lambda d: d.update(base_language="en", languages=["en"]))
        (root / "languages" / "es").rename(root / "languages" / "en")
    write(root / "languages" / lang / "guide" / "06-answers.md",
          "---\ntitle: Answers\n---\n\n```follow-ups\n```\n\n```witnesses\nothers: {names: Otros, appears_in: [E01], "
          "card: NADA QUE APORTAR}\n```\n\n````columns 230\n```quick-follow-ups\n```\n===\n```quick-witnesses\n```\n````\n")
    case, html = docs(root, lang)
    guide = html["guide"]
    assert "¿Qué dibujo?" in guide and "[false]" not in guide          # the question, and the pill drawn
    assert "A1, " + ("con" if lang == "es" else "with") + " E02" in guide
    assert "Rosa Soto, vecina" in guide and "Kevin Soto" in guide
    assert ("Tarjetas R1 y R2" if lang == "es" else "Cards R1 and R2") in guide
    assert "K1 + E02" in guide and '"Nada que aportar"' in guide
    assert "{{" not in guide and "```" not in guide


def test_follow_up_to_a_missing_card(case_dir):
    edit_yaml(cards_file(case_dir), lambda d: d["groups"][0]["cards"][0].update(follow_up="A9+"))
    with pytest.raises(CaseError, match="A9\\+"):
        load_case(case_dir)


def test_unlocked_by_must_exist(case_dir):
    add_cards(case_dir)
    edit_yaml(cards_file(case_dir), lambda d: d["groups"][0]["cards"][1].update(unlocked_by="E77"))
    with pytest.raises(CaseError, match="E77"):
        load_case(case_dir)


def test_unlocked_by_only_on_follow_ups(case_dir):
    edit_yaml(cards_file(case_dir), lambda d: d["groups"][0]["cards"][0].update(unlocked_by="E01"))
    with pytest.raises(CaseError, match="only follow-up cards"):
        load_case(case_dir)


def test_orphan_follow_up_is_a_warning(case_dir):
    add_cards(case_dir)
    edit_yaml(cards_file(case_dir), lambda d: d["groups"][0]["cards"][0].pop("follow_up"))
    assert any("enabled by no card" in w for w in load_case(case_dir).warnings)


def test_appears_in_must_exist(case_dir):
    add_cards(case_dir)
    edit_yaml(cards_file(case_dir), lambda d: d["groups"][1]["cards"][0].update(appears_in="E55"))
    with pytest.raises(CaseError, match="E55"):
        load_case(case_dir)


def test_invisible_witness_and_missing_appears_in_are_warnings(case_dir):
    add_cards(case_dir)

    def change(d):
        d["groups"][1]["cards"][2]["aliases"] = []        # "Kevin Soto" is not written in E01
        d["groups"][1]["cards"][0].pop("appears_in")      # Rosa: nowhere
    edit_yaml(cards_file(case_dir), change)
    warnings = load_case(case_dir).warnings
    assert any("Kevin Soto is invisible" in w for w in warnings)
    assert any("Rosa Soto, vecina (R1, R2) has no appears_in" in w for w in warnings)
