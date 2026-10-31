"""The engine's templates (opencase/templates/<lang>/) and figures (opencase/defaults.yaml): every language
has the same files, every template draws in every language with and without alibi tokens, a value no
YAML defines stops the export, and the case's engine_sheets settings place or leave out the sheets."""
import re
from pathlib import Path

import pytest
import yaml

from opencase import templates
from opencase.documents import build_documents
from opencase.loader import DEFAULTS_FILE, CaseError, load_case
from opencase.markup import use_strings

from test_validate import case_dir, edit_yaml, write  # noqa: F401  (the fixture and helpers)

TEMPLATES = templates.TEMPLATES_DIR
LANGS = sorted(p.name for p in TEMPLATES.iterdir() if p.is_dir())


def files(lang):
    return sorted(str(p.relative_to(TEMPLATES / lang)) for p in (TEMPLATES / lang).rglob("*") if p.is_file())


def test_base_and_english_exist():
    assert {"es", "en"} <= set(LANGS)


@pytest.mark.parametrize("lang", [l for l in LANGS if l != "es"])
def test_same_files_in_every_language(lang):
    assert files(lang) == files("es")


def test_every_figure_is_used():
    """A figure of defaults.yaml that no template, component or card reads is dead weight."""
    text = "\n".join(p.read_text(encoding="utf-8") for p in TEMPLATES.rglob("*") if p.is_file())
    text += "\n".join(p.read_text(encoding="utf-8") for p in Path(templates.__file__).parent.glob("*.py"))
    defaults = yaml.safe_load(DEFAULTS_FILE.read_text(encoding="utf-8"))
    unused = []
    for key, value in defaults.items():
        names = [f"{key}.{k}" for k in value] if isinstance(value, dict) else [key]
        for name in names:
            short = name.split(".")[-1]
            if not re.search(rf"\b{re.escape(short)}\b", text):
                unused.append(name)
    assert unused == []


def bilingual(root):
    """Adds an English copy of the minimal case, with a notice, a press card and two hints."""
    edit_yaml(root / "case.yaml", lambda d: d.update(languages=["es", "en"]))
    es = root / "languages" / "es"
    en = root / "languages" / "en"
    for f in es.rglob("*"):
        if f.is_file():
            write(en / f.relative_to(es), f.read_text(encoding="utf-8"))
    for lang in (es, en):
        edit_yaml(lang / "cards.yaml", lambda d: d["groups"].append({"title": "Notices", "cards": [
            {"code": "N1", "type": "notice", "answer": "News."},
            {"code": "P", "type": "press", "answer": "Headline."},
            {"code": "H1", "type": "hint", "answer": "Look again."},
            {"code": "H2", "type": "hint", "answer": "Look harder."}]}))
    edit_yaml(root / "case.yaml", lambda d: d.update(hint_penalties=[1, 2]))
    return root


def kit_and_guide(root, lang):
    case = load_case(root, lang)
    use_strings(case.strings)
    docs = {d.key: d.html for d in build_documents(case)}
    return case, docs["kit"], docs["guide"]


@pytest.mark.parametrize("lang", ["es", "en"])
@pytest.mark.parametrize("alibi", [0, 3])
def test_engine_sheets_draw(case_dir, lang, alibi):
    root = bilingual(case_dir)
    edit_yaml(root / "case.yaml", lambda d: d.update(alibi_tokens_per_team=alibi, score_bonus=2))
    for l in ("es", "en"):
        edit_yaml(root / "languages" / l / "case.yaml", lambda d: d.update(score_texts={"bonus": "Bonus line"}))
    case, kit, guide = kit_and_guide(root, lang)
    assert 'id="oc-20-rules"' in kit and 'id="oc-30-score"' in kit
    assert 'id="oc-10-running-the-game"' in guide and 'id="oc-90-request-log"' in guide
    assert "Bonus line" in kit
    dashed = {"es": "(borde punteado)", "en": "(dashed border)"}[lang]
    assert (dashed in kit) == bool(alibi)
    assert "{{" not in kit and "{%" not in kit and "{{" not in guide


def test_join_puts_how_to_play_on_the_first_sheet(case_dir):
    case, kit, guide = kit_and_guide(case_dir, "es")
    first = kit.index('id="01-mision"')
    assert kit.index("Cómo se juega") > first
    assert kit.index("Cómo se juega") < kit.index('id="oc-20-rules"')


def test_engine_blocks_draw(case_dir):
    write(case_dir / "languages" / "es" / "guide" / "02-control.md",
          "---\ntitle: Control\n---\n\n```control\nrows:\n  - [A1 → E02, Croquis, 1]\n```\n\n```score-sheet\n```\n"
          "\n```hints\n```\n\n```notices\n```\n")
    write(case_dir / "languages" / "es" / "kit" / "02-descarte.md", "---\ntitle: Descarte\n---\n\n```discard-rule\n```\n")
    case, kit, guide = kit_and_guide(case_dir, "es")
    assert "A1 → E02" in guide and "Hoja de puntaje" in guide
    assert "Llénenla durante la investigación" in kit
    # The request log goes right after the sheet that holds the control block.
    assert guide.index('id="02-control"') < guide.index('id="oc-90-request-log"')


def test_engine_sheets_off(case_dir):
    edit_yaml(case_dir / "case.yaml", lambda d: d.update(engine_sheets=False))
    case, kit, guide = kit_and_guide(case_dir, "es")
    assert "oc-20-rules" not in kit and "Cómo se juega" not in kit and "oc-10-running" not in guide


def test_engine_sheets_skip_and_after(case_dir):
    write(case_dir / "languages" / "es" / "kit" / "02-menu.md", "---\ntitle: Menú\n---\n\nPreguntas.\n")
    edit_yaml(case_dir / "case.yaml", lambda d: d.update(engine_sheets={"kit": {"after": "02-menu", "skip": ["30-score"]},
                                                                        "guide": False}))
    case, kit, guide = kit_and_guide(case_dir, "es")
    assert "oc-30-score" not in kit and "oc-10-running" not in guide
    assert kit.index('id="02-menu"') < kit.index("Cómo se juega") < kit.index('id="oc-20-rules"')


def test_engine_sheets_bad_settings(case_dir):
    edit_yaml(case_dir / "case.yaml", lambda d: d.update(engine_sheets={"kit": {"skip": ["99-nothing"]}}))
    with pytest.raises(CaseError, match="99-nothing"):
        kit_and_guide(case_dir, "es")
    edit_yaml(case_dir / "case.yaml", lambda d: d.update(engine_sheets={"kit": {"after": "07-nothing"}}))
    with pytest.raises(CaseError, match="07-nothing"):
        kit_and_guide(case_dir, "es")


def test_figures_merge_and_override(case_dir):
    bilingual(case_dir)  # one notice card
    edit_yaml(case_dir / "case.yaml", lambda d: d.update(phases={"investigation": 22}, notice_minutes=[7, 14]))
    case, kit, guide = kit_and_guide(case_dir, "es")
    assert case.figures["phases"] == {"setup": 5, "scene": 10, "investigation": 22, "accusation": 15}
    assert case.figures["tokens_per_team"] == 10      # the minimal case's own value
    assert "**2 · Investigación** · 22 min" not in kit  # Markdown is drawn, so look for the drawn text
    assert "22 min" in kit and "se sugiere el minuto 7 para el aviso 1." in guide


def test_unknown_figure_stops_the_export(case_dir):
    edit_yaml(case_dir / "case.yaml", lambda d: d.update(score={"style": 3}))
    with pytest.raises(CaseError, match="score.style"):
        kit_and_guide(case_dir, "es")


def test_hint_without_penalty_stops_the_export(case_dir):
    bilingual(case_dir)
    edit_yaml(case_dir / "case.yaml", lambda d: d.update(hint_penalties=[1]))
    with pytest.raises(CaseError, match="2 hint cards but hint_penalties gives 1"):
        kit_and_guide(case_dir, "es")


def test_bonus_without_text_stops_the_export(case_dir):
    edit_yaml(case_dir / "case.yaml", lambda d: d.update(score_bonus=3))
    with pytest.raises(CaseError, match="score_texts.bonus"):
        kit_and_guide(case_dir, "es")


def test_undefined_value_stops_the_export(case_dir, tmp_path, monkeypatch):
    """StrictUndefined: a template that reads a value no YAML defines fails with its file and line."""
    fake = tmp_path / "templates"
    for lang in LANGS:
        for p in (TEMPLATES / lang).rglob("*"):
            if p.is_file():
                write(fake / lang / p.relative_to(TEMPLATES / lang), p.read_text(encoding="utf-8"))
    write(fake / "es" / "kit" / "40-bad.md", "---\ntitle: Mala\n---\n\nUna línea.\n\nFichas: {{ f.tokens_per_tema }}\n")
    monkeypatch.setattr(templates, "TEMPLATES_DIR", fake)
    with pytest.raises(CaseError) as err:
        kit_and_guide(case_dir, "es")
    assert "40-bad.md:7" in str(err.value) and "tokens_per_tema" in str(err.value)


def test_language_without_templates(case_dir, monkeypatch, tmp_path):
    monkeypatch.setattr(templates, "TEMPLATES_DIR", tmp_path / "none")
    with pytest.raises(CaseError, match="no templates in 'es'"):
        kit_and_guide(case_dir, "es")


def test_counts_come_from_the_case(case_dir):
    """How many notices, press cards and hints the rules mention is the case's, not the figures'."""
    case, kit, guide = kit_and_guide(case_dir, "es")  # no notices, no press, no hints
    assert "Avisos</h3>" not in kit and "Pistas</h3>" not in kit and "se sugiere" not in guide
    assert "Pistas guiadas" not in guide
    bilingual(case_dir)  # one notice, a press card and two hints
    case, kit, guide = kit_and_guide(case_dir, "es")
    assert "lee un aviso con información nueva" in kit and "Hay 2 y restan puntos" in kit
    assert "el último viene con una tarjeta de prensa" in kit


def test_more_notices_than_minutes_stops_the_export(case_dir):
    edit_yaml(case_dir / "languages" / "es" / "cards.yaml", lambda d: d["groups"].append({"title": "Avisos", "cards": [
        {"code": f"N{i}", "type": "notice", "answer": "Algo."} for i in (1, 2, 3)]}))
    with pytest.raises(CaseError, match="3 notices but notice_minutes gives 2"):
        kit_and_guide(case_dir, "es")


def test_teams_never_see_the_suggested_minute(case_dir):
    """Notice cards and sheets go to the teams' tables: "aviso 1 de 2", never the minute (only the guide has it)."""
    write(case_dir / "languages" / "es" / "dossier" / "AV1.md", "---\ntitle: Aviso 1\nnotice: true\n---\n\nAlgo.\n")
    write(case_dir / "languages" / "es" / "dossier" / "AV2.md", "---\ntitle: Aviso 2\nnotice: true\n---\n\nOtra cosa.\n")
    edit_yaml(case_dir / "case.yaml", lambda d: d["dossier"]["sections"].append({"id": "notices", "items": ["AV1", "AV2"]}))
    edit_yaml(case_dir / "languages" / "es" / "cards.yaml", lambda d: d["groups"].append({"title": "Avisos", "cards": [
        {"code": "AVISO 1", "type": "notice", "answer": "Algo."}, {"code": "AVISO 2", "type": "notice", "answer": "Otra."},
        {"code": "PRENSA", "type": "press", "answer": "Titular."}]}))
    case = load_case(case_dir, "es")
    use_strings(case.strings)
    docs = {d.key: d.html for d in build_documents(case)}
    assert "Aviso · 1 de 2" in docs["cards"] and "Con el aviso 2" in docs["cards"]
    assert "Aviso para todos los equipos · 2 de 2" in docs["evidence"]
    assert "minuto" not in docs["cards"] and "minuto" not in docs["evidence"]
    assert "el minuto 10 para el aviso 1 y el 20 para el aviso 2" in docs["guide"]


def test_figures_only_in_the_neutral_case_yaml(case_dir):
    edit_yaml(case_dir / "languages" / "es" / "case.yaml", lambda d: d.update(tokens_per_team=99))
    with pytest.raises(CaseError, match="'tokens_per_team' is the same in every language"):
        kit_and_guide(case_dir, "es")


def test_misspelt_key_stops_the_export(case_dir):
    edit_yaml(case_dir / "case.yaml", lambda d: d.update(tokens_per_teams=12))
    with pytest.raises(CaseError, match="did you mean 'tokens_per_team'"):
        kit_and_guide(case_dir, "es")
