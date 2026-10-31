"""The glossary of a case (languages/<lang>/case.yaml) and the check of acronyms: a bad glossary stops the
export, an acronym used before its long form or a word in no glossary is only a warning, and the director's
guide and the ```acronyms block draw the table."""
import pytest

from opencase.documents import build_documents
from opencase.loader import CaseError, load_case
from opencase.markup import use_strings

from test_validate import case_dir, edit_yaml, sheet, write  # noqa: F401  (the fixture and helpers)

SAG = "Servicio Agrícola y Ganadero"


def lang_case(root):
    return root / "languages" / "es" / "case.yaml"


def build(root):
    case = load_case(root)
    use_strings(case.strings)
    docs = {d.key: d.html for d in build_documents(case)}
    return case, docs


def with_glossary(root, glossary, **extra):
    edit_yaml(lang_case(root), lambda d: d.update(glossary=glossary, **extra))


def warnings_of(case):
    return [w for w in case.warnings if "acronym" in w or "long form" in w or "glossary" in w]


def test_no_glossary_no_sheet_and_no_warning(case_dir):
    case, docs = build(case_dir)
    assert "Siglas del caso" not in docs["guide"]
    assert warnings_of(case) == []


def test_written_out_first_is_fine(case_dir):
    write(case_dir / "languages" / "es" / "dossier" / "E01.md", sheet("E01", "Parte", f"El {SAG} (SAG) informa. Luego el SAG."))
    with_glossary(case_dir, {"SAG": SAG})
    case, _ = build(case_dir)
    assert warnings_of(case) == []


def test_acronym_beside_its_long_form_is_fine(case_dir):
    write(case_dir / "languages" / "es" / "dossier" / "E01.md", sheet("E01", "Parte", f"El SAG ({SAG}) informa."))
    with_glossary(case_dir, {"SAG": SAG})
    case, _ = build(case_dir)
    assert warnings_of(case) == []


def test_acronym_before_its_long_form_warns_once(case_dir):
    write(case_dir / "languages" / "es" / "dossier" / "E01.md", sheet("E01", "Parte", "El SAG informa."))
    write(case_dir / "languages" / "es" / "dossier" / "E02.md", sheet("E02", "Croquis", f"{SAG}. El SAG otra vez."))
    with_glossary(case_dir, {"SAG": SAG})
    case, _ = build(case_dir)
    late = [w for w in case.warnings if "SAG is used" in w]
    assert len(late) == 1 and "E01" in late[0]


def test_reading_order_is_the_kit_first(case_dir):
    write(case_dir / "languages" / "es" / "kit" / "01-mision.md", f"---\ntitle: Misión\n---\n\nPregunten al SAG.\n")
    write(case_dir / "languages" / "es" / "dossier" / "E01.md", sheet("E01", "Parte", f"{SAG} (SAG)."))
    with_glossary(case_dir, {"SAG": SAG})
    case, _ = build(case_dir)
    assert any("SAG is used in kit" in w for w in case.warnings)


def test_what_a_person_says_is_not_checked(case_dir):
    chat = "```quote\nHay PDI y cinta amarilla.\n```\n"
    write(case_dir / "languages" / "es" / "dossier" / "E02.md", sheet("E02", "Croquis", chat))
    with_glossary(case_dir, {"PDI": "Policía de Investigaciones"})
    case, _ = build(case_dir)
    assert warnings_of(case) == []


def test_expand_false_needs_no_long_form(case_dir):
    write(case_dir / "languages" / "es" / "dossier" / "E01.md", sheet("E01", "Parte", "Una SUV blanca."))
    with_glossary(case_dir, {"SUV": {"long": "vehículo utilitario deportivo", "expand": False}})
    case, docs = build(case_dir)
    assert warnings_of(case) == []
    assert "vehículo utilitario deportivo" in docs["guide"]


def test_a_card_is_checked_against_what_the_teams_read(case_dir):
    write(case_dir / "languages" / "es" / "dossier" / "E01.md", sheet("E01", "Parte", "Nada."))
    edit_yaml(case_dir / "languages" / "es" / "cards.yaml",
              lambda d: d["groups"][0]["cards"][0].update(answer="Llamé al SAG.", ))
    with_glossary(case_dir, {"SAG": SAG})
    case, _ = build(case_dir)
    assert any("SAG is used in card A1" in w for w in case.warnings)
    # ... unless it is something the person says
    edit_yaml(case_dir / "languages" / "es" / "cards.yaml",
              lambda d: d["groups"][0]["cards"][0].update(answer='"Llamé al SAG."'))
    case, _ = build(case_dir)
    assert not any("SAG is used" in w for w in case.warnings)


def test_a_word_in_no_glossary_warns(case_dir):
    write(case_dir / "languages" / "es" / "dossier" / "E01.md", sheet("E01", "Parte", "Informa la PDI."))
    case, _ = build(case_dir)
    assert any("PDI in envelope E01 looks like an acronym" in w for w in case.warnings)
    with_glossary(case_dir, {}, glossary_ignore=["PDI"])
    case, _ = build(case_dir)
    assert warnings_of(case) == []


def test_capitals_headings_and_code_prefixes_are_not_acronyms(case_dir):
    write(case_dir / "languages" / "es" / "dossier" / "E01.md", sheet("E01", "Parte", "TESTIGO NO DISPONIBLE\n\nVer E02 y E01."))
    case, _ = build(case_dir)
    assert warnings_of(case) == []


def test_unused_entry_warns(case_dir):
    with_glossary(case_dir, {"SAG": SAG})
    case, _ = build(case_dir)
    assert any("SAG is never used" in w for w in case.warnings)


@pytest.mark.parametrize("bad", ["PDI", {"pdi": "x"}, {"PDI": ""}, {"PDI": {"long": "x", "expand": "no"}},
                                 {"PDI": {"long": "x", "extra": 1}}, {"PDI": 3}])
def test_a_bad_glossary_stops_the_export(case_dir, bad):
    with_glossary(case_dir, bad)
    with pytest.raises(CaseError, match="glossary"):
        load_case(case_dir)


def test_guide_table_and_block(case_dir):
    write(case_dir / "languages" / "es" / "kit" / "01-mision.md",
          "---\ntitle: Misión\n---\n\nAveriguar qué pasó.\n\n```acronyms\nonly: [SAG]\n```\n")
    with_glossary(case_dir, {"SAG": SAG, "PDI": "Policía de Investigaciones"})
    case, docs = build(case_dir)
    assert "Siglas del caso" in docs["guide"] and "Policía de Investigaciones" in docs["guide"]
    kit = docs["kit"]
    assert SAG in kit and "Policía de Investigaciones" not in kit


def test_block_with_an_unknown_acronym_stops_the_export(case_dir):
    write(case_dir / "languages" / "es" / "kit" / "01-mision.md",
          "---\ntitle: Misión\n---\n\n```acronyms\nonly: [XYZ]\n```\n")
    with_glossary(case_dir, {"SAG": SAG})
    with pytest.raises(CaseError):
        build(case_dir)
