"""Procedures and places (opencase/procedures.py): the kit's menu, the guide's tables and the control sheet drawn
from procedures.yaml and locations.yaml, the checks of their data, and the codes shown with their middle dot."""
import pytest
import yaml

from opencase.documents import build_documents
from opencase.loader import CaseError, compare_languages, load_case
from opencase.markup import use_strings

from test_validate import case_dir, cards_file, edit_yaml, sheet, write  # noqa: F401  (the fixture and helpers)

NEUTRAL = {"procedures": [
    {"code": "DG1", "kind": "report", "gives": "E03"},
    {"code": "DG4", "kind": "phone_towers", "alibi": True, "targets": {"A": "E04-A", "other": "none"}},
    {"code": "DG7", "kind": "cameras", "alibi": True, "targets": {"shop": "E05", "bar": "none"}},
    {"code": "DG9", "kind": "other", "targets": {"safe": {"gives": "E06", "cost": 2}, "other": "material"}},
]}
PLACES = {"locations": [{"id": "shop", "sources": ["camera"]}, {"id": "bar", "sources": []}]}
TEXTS = {"es": {"names": {"A": "Ana"}, "procedures": {
             "DG1": {"label": "Informe del Servicio Agrícola y Ganadero (SAG)", "short": "Informe SAG"},
             "DG7": {"notes": {"bar": "no tiene cámaras"}},
             "DG9": {"targets": {"safe": "caja fuerte"}}}},
         "en": {"names": {"A": "Ana"}, "procedures": {
             "DG1": {"label": "Report from the Agriculture and Livestock Service (SAG)", "short": "SAG report"},
             "DG7": {"notes": {"bar": "it has no cameras"}},
             "DG9": {"targets": {"safe": "safe"}}}}}
PLACE_TEXTS = {"es": {"locations": {"shop": {"name": "almacén"}, "bar": {"name": "bar", "note": "cierra a las 22"}}},
               "en": {"locations": {"shop": {"name": "shop"}, "bar": {"name": "bar", "note": "closes at 22"}}}}


def dump(path, data):
    write(path, yaml.safe_dump(data, allow_unicode=True, sort_keys=False))


def add_procedures(root, lang="es"):
    """Four procedures of four kinds (one result, letters with `none`, places, a cost of its own and `material`),
    two places, and the sheets they hand out in a section without envelope."""
    dump(root / "procedures.yaml", NEUTRAL)
    dump(root / "locations.yaml", PLACES)
    dump(root / "languages" / lang / "procedures.yaml", TEXTS[lang])
    dump(root / "languages" / lang / "locations.yaml", PLACE_TEXTS[lang])
    edit_yaml(root / "languages" / lang / "case.yaml", lambda d: d.update(glossary={"SAG": "Servicio Agrícola y Ganadero"}))
    edit_yaml(root / "case.yaml", lambda d: (d.update(alibi_tokens_per_team=2), d["dossier"]["sections"].append(
        {"id": "procedures", "items": ["E03", "E04-A", "E05", "E06"]})))
    for code, sid in (("E03", "E03"), ("E04 · A", "E04-A"), ("E05", "E05"), ("E06", "E06")):
        write(root / "languages" / lang / "dossier" / f"{sid}.md", sheet(code, "Hoja " + code))
    write(root / "languages" / lang / "kit" / "03-diligencias.md", "---\ntitle: Diligencias\n---\n\n```procedures\n```\n")
    write(root / "languages" / lang / "guide" / "06-respuestas.md",
          "---\ntitle: Respuestas\n---\n\n```procedure-answers\n```\n\n```locations\n```\n\n"
          "````columns 230\n```quick-procedures\n```\n````\n\n```control\n```\n")
    return root


def english(root):
    edit_yaml(root / "case.yaml", lambda d: d.update(base_language="en", languages=["en"]))
    (root / "languages" / "es").rename(root / "languages" / "en")
    for name in ("procedures.yaml", "locations.yaml"):
        p = root / "languages" / "en" / name
        if p.exists():
            key = "procedures" if name == "procedures.yaml" else "locations"
            dump(p, TEXTS["en"] if key == "procedures" else PLACE_TEXTS["en"])
    return root


def docs(root, lang="es"):
    case = load_case(root, lang)
    use_strings(case.strings)
    return case, {d.key: d.html for d in build_documents(case)}


def test_kit_menu_from_the_data(case_dir):
    case, html = docs(add_procedures(case_dir))
    assert case.warnings == []
    kit = html["kit"]
    assert "Informe del Servicio Agrícola y Ganadero (SAG)" in kit
    assert "Tráfico de antenas del celular de una persona (indiquen de quién)" in kit   # the kind's label
    assert '<code class="oc-codigo--coartada">DG4</code>' in kit and '<code class="oc-codigo--coartada">DG1' not in kit
    assert "1 o 2" in kit and "borde punteado" in kit


def test_no_alibi_mark_without_alibi_tokens(case_dir):
    add_procedures(case_dir)
    edit_yaml(case_dir / "case.yaml", lambda d: d.update(alibi_tokens_per_team=0))
    case, html = docs(case_dir)
    assert "oc-codigo--coartada" not in html["kit"] and "borde punteado" not in html["kit"]
    assert any("DG4 has alibi: true, but the case has no alibi tokens" in w for w in case.warnings)


@pytest.mark.parametrize("lang", ["es", "en"])
def test_guide_tables(case_dir, lang):
    root = add_procedures(case_dir)
    if lang == "en":
        english(root)
    case, html = docs(root, lang)
    guide = html["guide"]
    es = lang == "es"
    assert ("Antenas: Ana · otra persona" if es else "Phone towers: Ana · someone else") in guide
    assert "E04·A · " + ('"Sin hallazgos"' if es else '"No findings"') in guide
    assert ("caja fuerte (2 fichas)" if es else "safe (2 tokens)") in guide
    assert ("(no tiene cámaras)" if es else "(it has no cameras)") in guide
    assert ("Almacén" if es else "Shop") in guide and ("cámara" if es else "camera") in guide
    assert ("Cierra a las 22" if es else "Closes at 22") in guide
    assert "DG4 → E04" in guide and "DG9 → E06" in guide and ("(·A)" in guide)
    assert "{{" not in guide and "```" not in guide


def test_control_sheet_separates_cards_from_procedures(case_dir):
    add_procedures(case_dir)
    edit_yaml(cards_file(case_dir), lambda d: d["groups"][0]["cards"][0].update(attach="E05"))
    case, html = docs(case_dir)
    guide = html["guide"]
    procedures, cards = guide.index("Diligencias</h3>"), guide.index("Pruebas que entregan las tarjetas")
    assert procedures < guide.index("DG7 → E05") < cards < guide.index("A1 → E05")


def test_control_rows_written_by_hand_still_work(case_dir):
    write(case_dir / "languages" / "es" / "guide" / "07-control.md",
          "---\ntitle: Control\n---\n\n```control\nrows:\n  - [X1 → E01, A mano, 1]\n```\n")
    case, html = docs(case_dir)
    assert "X1 → E01" in html["guide"] and "Pruebas que entregan las tarjetas" not in html["guide"]


@pytest.mark.parametrize("change, message", [
    (lambda d: d["procedures"][0].update(kind="tarot"), "kind 'tarot' does not exist"),
    (lambda d: d["procedures"][0].update(gives="E77"), "E77, which is not a sheet"),
    (lambda d: d["procedures"][0].update(targets={"A": "E03"}), "either gives"),
    (lambda d: d["procedures"][0].update(label="x"), "texts go in"),
    (lambda d: d["procedures"][1]["targets"].update(Z="E03"), "target 'Z'"),
    (lambda d: d["procedures"][0].update(cost=0), "whole number"),
    (lambda d: d["procedures"].append({"code": "DG1", "kind": "report", "gives": "E03"}), "DG1 is twice"),
])
def test_neutral_data_errors(case_dir, change, message):
    add_procedures(case_dir)
    edit_yaml(case_dir / "procedures.yaml", change)
    with pytest.raises(CaseError, match=message):
        load_case(case_dir)


def test_text_errors(case_dir):
    add_procedures(case_dir)
    edit_yaml(case_dir / "languages" / "es" / "procedures.yaml", lambda d: d["procedures"].update(DG99={"label": "x"}))
    with pytest.raises(CaseError, match="DG99 is not a procedure"):
        load_case(case_dir)
    add_procedures(case_dir)
    edit_yaml(case_dir / "languages" / "es" / "procedures.yaml", lambda d: d.pop("names"))
    with pytest.raises(CaseError, match="no name for A"):
        load_case(case_dir)
    add_procedures(case_dir)
    edit_yaml(case_dir / "locations.yaml", lambda d: d["locations"][0].update(sources=["dron"]))
    with pytest.raises(CaseError, match="source 'dron'"):
        load_case(case_dir)


def test_warnings(case_dir):
    add_procedures(case_dir)

    def change(d):
        d["procedures"][0]["alibi"] = True                       # a report does not place anyone
        d["procedures"][2]["targets"]["bar"] = "E05"             # footage of a place with no camera
        d["procedures"][3]["targets"].pop("safe")                # nothing hands out E06 any more
    edit_yaml(case_dir / "procedures.yaml", change)
    edit_yaml(case_dir / "languages" / "es" / "procedures.yaml", lambda d: d["procedures"].pop("DG9"))
    warnings = load_case(case_dir).warnings
    assert any("DG1 has alibi: true, but a procedure of kind report" in w for w in warnings)
    assert any("hands out E05 for bar, but locations.yaml says the place has no camera" in w for w in warnings)
    assert any("no team can get E06" in w for w in warnings)


def test_unlocked_by_that_no_team_can_get(case_dir):
    add_procedures(case_dir)
    edit_yaml(case_dir / "procedures.yaml", lambda d: d["procedures"][3]["targets"].pop("safe"))
    edit_yaml(case_dir / "languages" / "es" / "procedures.yaml", lambda d: d["procedures"].pop("DG9"))

    def change(d):
        d["groups"][0]["cards"][0]["follow_up"] = "A1+"
        d["groups"][0]["cards"].append({"code": "A1+", "type": "follow-up", "question": "¿Y?", "answer": "No.",
                                        "unlocked_by": "E06"})
    edit_yaml(cards_file(case_dir), change)
    assert any("the follow-up A1+ needs E06 (unlocked_by), which no team can get" in w
               for w in load_case(case_dir).warnings)


def test_follow_up_box_shows_the_sheet_code_with_its_dot(case_dir):
    add_procedures(case_dir)

    def change(d):
        d["groups"][0]["cards"][0]["follow_up"] = "A1+"
        d["groups"][0]["cards"].append({"code": "A1+", "type": "follow-up", "question": "¿Y?", "answer": "No.",
                                        "unlocked_by": "E04-A"})
    edit_yaml(cards_file(case_dir), change)
    case, html = docs(case_dir)
    assert "si ya tienen E04·A" in html["cards"] and "E04-A" not in html["cards"]


def test_procedure_label_writes_the_acronym_out(case_dir):
    """The kit's menu writes SAG out (its label is in procedures.yaml), so a sheet read after it may say SAG."""
    add_procedures(case_dir)
    write(case_dir / "languages" / "es" / "dossier" / "E03.md", sheet("E03", "Informe", "El SAG revisó."))
    case, html = docs(case_dir)
    assert not [w for w in case.warnings if "SAG" in w]


def test_translation_missing_procedure_texts(case_dir):
    add_procedures(case_dir)
    edit_yaml(case_dir / "case.yaml", lambda d: d.update(languages=["es", "en"]))
    import shutil
    shutil.copytree(case_dir / "languages" / "es", case_dir / "languages" / "en")
    dump(case_dir / "languages" / "en" / "locations.yaml", PLACE_TEXTS["en"])
    edit_yaml(case_dir / "languages" / "en" / "procedures.yaml", lambda d: d["procedures"].pop("DG7"))
    problems = compare_languages(load_case(case_dir, "es"), load_case(case_dir, "en"))
    assert "procedures.yaml (en): DG7 notes.bar is missing" in problems
