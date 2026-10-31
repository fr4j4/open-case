"""loader.load_case and loader.validate on a minimal case written in a temporary folder: what stops
the export (CaseError) and what is only a warning."""
import shutil

import pytest
import yaml

from opencase.documents import build_documents
from opencase.loader import CaseError, compare_languages, load_case, normalize_code
from opencase.markup import use_strings

# A 1x1 transparent PNG, for the tests with images.
PNG = bytes.fromhex("89504e470d0a1a0a0000000d4948445200000001000000010806000000"
                    "1f15c4890000000d49444154789c6360000002000154a24f5d0000000049454e44ae426082")


def write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def sheet(code, title, body="Texto."):
    return f"---\ncode: {code}\ninstitution: Fiscalía de prueba\ntitle: {title}\n---\n\n{body}\n"


@pytest.fixture
def case_dir(tmp_path):
    """The smallest case that exports: two dossier sheets in one envelope, one suspect, one card,
    one kit sheet and one guide sheet."""
    root = tmp_path / "minimal"
    neutral = {
        "paper": "letter", "base_language": "es", "languages": ["es"],
        "teams": ["A", "B"], "tokens_per_team": 10,
        "dossier": {"sections": [{"id": "start", "envelope": 1, "items": ["E01", "E02"]}]},
    }
    write(root / "case.yaml", yaml.safe_dump(neutral, allow_unicode=True))
    lang = root / "languages" / "es"
    write(lang / "case.yaml", yaml.safe_dump({"title": "Caso mínimo",
                                              "dossier": {"sections": {"start": {"title": "Inicio"}}}},
                                             allow_unicode=True))
    write(lang / "suspects.yaml", yaml.safe_dump({"suspects": [{"letter": "A", "name": "Ana Pérez", "role": "vecina"}]},
                                                 allow_unicode=True))
    write(lang / "cards.yaml", yaml.safe_dump({"groups": [{"title": "Ana Pérez", "suspect": "A", "cards": [
        {"code": "A1", "menu": True, "question": "¿Dónde estaba?", "answer": "En mi casa."}]}]}, allow_unicode=True))
    write(lang / "kit" / "01-mision.md", "---\ntitle: Misión\n---\n\nAveriguar qué pasó.\n")
    write(lang / "guide" / "01-solucion.md", "---\ntitle: Solución\n---\n\nFue el gato.\n")
    write(lang / "dossier" / "E01.md", sheet("E01", "Parte policial"))
    write(lang / "dossier" / "E02.md", sheet("E02", "Croquis"))
    return root


def edit_yaml(path, change):
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    change(data)
    path.write_text(yaml.safe_dump(data, allow_unicode=True), encoding="utf-8")


def cards_file(root):
    return root / "languages" / "es" / "cards.yaml"


def test_minimal_case_loads_without_warnings(case_dir):
    case = load_case(case_dir)
    assert case.title == "Caso mínimo"
    assert case.lang == "es"
    assert list(case.dossier) == ["E01", "E02"]
    assert case.warnings == []


def test_minimal_case_builds_every_document(case_dir):
    case = load_case(case_dir)
    use_strings(case.strings)
    keys = [d.key for d in build_documents(case)]
    assert keys[:2] == ["kit", "envelopes:1"]
    assert "evidence" not in keys   # every sheet is in an envelope: there is no Evidence file
    assert {"guide", "cards", "card-backs", "suspects", "badges", "tokens", "requests"} <= set(keys)


def test_no_case_yaml(tmp_path):
    with pytest.raises(CaseError, match="no case.yaml"):
        load_case(tmp_path)


def test_unknown_language(case_dir):
    with pytest.raises(CaseError, match="has no 'en' language"):
        load_case(case_dir, "en")


def test_missing_title(case_dir):
    write(case_dir / "languages" / "es" / "case.yaml", "version: 1\n")
    with pytest.raises(CaseError, match="'title' is missing"):
        load_case(case_dir)


def test_invalid_yaml_reports_the_line(case_dir):
    write(case_dir / "languages" / "es" / "suspects.yaml", "suspects:\n  - letter: A\n   name: [\n")
    with pytest.raises(CaseError, match=r"suspects.yaml:\d+: invalid YAML"):
        load_case(case_dir)


def test_times_stay_text(case_dir):
    """YAML 1.1 would read 07:12 as a number and `no` as False; a case is full of both."""
    write(cards_file(case_dir), "groups:\n  - title: Ana\n    cards:\n      - code: A1\n        question: no\n"
                                "        answer: 07:12\n")
    card = load_case(case_dir).card_groups[0]["cards"][0]
    assert card["answer"] == "07:12" and card["question"] == "no"


def test_section_lists_a_missing_sheet(case_dir):
    edit_yaml(case_dir / "case.yaml", lambda d: d["dossier"]["sections"][0]["items"].append("E99"))
    with pytest.raises(CaseError, match="lists 'E99'"):
        load_case(case_dir)


def test_sheet_in_two_sections(case_dir):
    edit_yaml(case_dir / "case.yaml",
              lambda d: d["dossier"]["sections"].append({"id": "more", "items": ["E01"]}))
    with pytest.raises(CaseError, match="'E01' is in two sections"):
        load_case(case_dir)


def test_sheet_in_no_section_is_a_warning(case_dir):
    write(case_dir / "languages" / "es" / "dossier" / "E03.md", sheet("E03", "Suelta"))
    case = load_case(case_dir)
    assert any("E03.md is in no section" in w for w in case.warnings)


def test_card_without_code(case_dir):
    edit_yaml(cards_file(case_dir), lambda d: d["groups"][0]["cards"].append({"question": "¿Y?", "answer": "Nada."}))
    with pytest.raises(CaseError, match="has no code"):
        load_case(case_dir)


def test_card_warnings(case_dir):
    def change(d):
        cards = d["groups"][0]["cards"]
        cards.append({"code": "A1", "question": "¿Otra vez?", "answer": "Sí."})
        cards.append({"code": "A2", "question": "¿Y esto?", "answer": "Mire.", "attach": "E01, E7"})
        cards.append({"code": "A3", "question": "¿Larga?", "answer": "x" * 421})
    edit_yaml(cards_file(case_dir), change)
    warnings = load_case(case_dir).warnings
    assert any("A1 appears twice" in w for w in warnings)
    assert any("A2 attaches E7" in w for w in warnings)
    assert not any("attaches E01" in w for w in warnings)
    assert any("A3 has 421 characters" in w for w in warnings)


def test_missing_image(case_dir):
    write(case_dir / "languages" / "es" / "dossier" / "E02.md",
          sheet("E02", "Croquis", "![croquis](diagrams/croquis.png)"))
    with pytest.raises(CaseError, match="'diagrams/croquis.png' does not exist"):
        load_case(case_dir)


def test_image_from_case_or_language_folder(case_dir):
    (case_dir / "photos").mkdir()
    (case_dir / "photos" / "foto.png").write_bytes(PNG)
    (case_dir / "languages" / "es" / "diagrams").mkdir()
    (case_dir / "languages" / "es" / "diagrams" / "plano.png").write_bytes(PNG)
    write(case_dir / "languages" / "es" / "dossier" / "E02.md",
          sheet("E02", "Croquis", "![foto](photos/foto.png)\n\n![plano](diagrams/plano.png)"))
    assert load_case(case_dir).warnings == []


def test_missing_portrait(case_dir):
    edit_yaml(case_dir / "languages" / "es" / "suspects.yaml",
              lambda d: d["suspects"][0].update(portrait="photos/ana.jpg"))
    with pytest.raises(CaseError, match="portrait 'photos/ana.jpg'"):
        load_case(case_dir)


def test_unclosed_block_reports_the_line(case_dir):
    write(case_dir / "languages" / "es" / "dossier" / "E02.md", sheet("E02", "Croquis", "Hola\n\n```note\nsin cerrar"))
    with pytest.raises(CaseError, match=r"E02.md:\d+: the ```note block is never closed"):
        load_case(case_dir)


def test_translation_missing_pieces(case_dir):
    edit_yaml(case_dir / "case.yaml", lambda d: d.update(languages=["es", "en"]))
    shutil.copytree(case_dir / "languages" / "es", case_dir / "languages" / "en")
    en = case_dir / "languages" / "en"
    (en / "dossier" / "E02.md").unlink()
    edit_yaml(en / "cards.yaml", lambda d: d["groups"][0]["cards"][0].update(code="A9"))
    edit_yaml(en / "suspects.yaml", lambda d: d["suspects"][0].update(letter="B"))
    # E02 is still listed in the neutral case.yaml, so the English side fails on its own...
    with pytest.raises(CaseError, match="lists 'E02'"):
        load_case(case_dir, "en")
    # ...and once it is out of the order, the comparison lists what the translation lacks.
    edit_yaml(case_dir / "case.yaml", lambda d: d["dossier"]["sections"][0]["items"].remove("E02"))
    es, en_case = load_case(case_dir, "es"), load_case(case_dir, "en")
    problems = compare_languages(es, en_case)
    assert "languages/en/dossier/E02.md is missing" in problems
    assert any("card A1 is missing" in p for p in problems)
    assert any("card A9 does not exist" in p for p in problems)
    assert any("suspects" in p for p in problems)


@pytest.mark.parametrize("code", ["E17·B", "E17 · B", "E17-B", "e17 - b"])
def test_normalize_code(code):
    assert normalize_code(code) == "E17·B"
