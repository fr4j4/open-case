"""Signatures drawn as pen strokes (opencase/signatures.py): the strokes come from the case's signatures.yaml,
a signer without strokes keeps the handwriting font, and bad data stops the export. Also the drawing tool
(tools/signatures.py), which writes the strokes of the signers of a case."""
import pytest
import yaml

import signatures as tool
from opencase.documents import build_documents
from opencase.loader import CaseError, load_case
from opencase.markup import use_strings

from test_validate import case_dir, sheet, write  # noqa: F401  (the fixture and helpers)

STROKES = {"signatures": {"A": {"name": "Ana Pérez", "width": 1.6, "viewbox": "0 0 90 40",
                                "strokes": ["M3 30C10 5 20 5 30 30", "M5 36L80 34", "M86 30h0.6"]}}}


def sign(root, *items):
    body = "```signature\n" + "".join(f"- {yaml.safe_dump(it, allow_unicode=True, default_flow_style=True).strip()}\n"
                                      for it in items) + "```"
    write(root / "languages" / "es" / "dossier" / "E01.md", sheet("E01", "Declaración", body))


def sheets_html(root):
    case = load_case(root)
    use_strings(case.strings)
    return "".join(d.html for d in build_documents(case) if d.kind == "sheets"), case


def test_signer_with_strokes_is_drawn(case_dir):
    write(case_dir / "signatures.yaml", yaml.safe_dump(STROKES, allow_unicode=True))
    sign(case_dir, {"signer": "A", "scrawl": "Ana Pérez", "label": "Firma del declarante"}, "Detective a cargo")
    html, case = sheets_html(case_dir)
    assert case.warnings == []
    assert '<svg class="oc-firma__svg" viewBox="0 0 90 40" role="img" aria-label="Firma de Ana Pérez">' in html
    assert 'stroke-width="1.6"' in html and html.count("<path d=") >= 3
    assert "oc-firma__trazo--svg" in html
    assert ">Ana Pérez</span>" not in html     # the font's scrawl is not printed as well


def test_signer_without_strokes_keeps_the_font(case_dir):
    sign(case_dir, {"signer": "A", "scrawl": "Ana Pérez", "label": "Firma del declarante"})
    html, _ = sheets_html(case_dir)
    assert '<span class="oc-firma__trazo">Ana Pérez</span>' in html
    assert "oc-firma__svg" not in html


def test_scrawl_without_signer_is_unchanged(case_dir):
    write(case_dir / "signatures.yaml", yaml.safe_dump(STROKES, allow_unicode=True))
    sign(case_dir, {"signer": "A", "label": "Declarante"}, {"scrawl": "I. Painemal", "label": "Comisario a cargo"})
    html, _ = sheets_html(case_dir)
    assert '<span class="oc-firma__trazo">I. Painemal</span>' in html
    assert 'aria-label="Firma de Ana Pérez"' in html   # the name comes from signatures.yaml when there is no scrawl


def test_signer_with_nothing_to_print(case_dir):
    sign(case_dir, {"signer": "Z", "label": "Firma del declarante"})
    with pytest.raises(CaseError, match="'Z' has no strokes in signatures.yaml and no scrawl"):
        load_case(case_dir)


def test_unused_signature_is_a_warning(case_dir):
    write(case_dir / "signatures.yaml", yaml.safe_dump(STROKES, allow_unicode=True))
    assert load_case(case_dir).warnings == ["signatures.yaml: 'A' signs no sheet"]


@pytest.mark.parametrize("entry, message", [
    ({"strokes": []}, "has no strokes"),
    ({"strokes": ["<path d='M0 0'/>"]}, "is not SVG path data"),
    ({"strokes": ["M0 0L1 1"], "viewbox": "0 0 90"}, "four numbers"),
    ({"strokes": ["M0 0L1 1"], "width": 0}, "above 0"),
])
def test_bad_strokes_stop_the_export(case_dir, entry, message):
    write(case_dir / "signatures.yaml", yaml.safe_dump({"signatures": {"A": entry}}))
    with pytest.raises(CaseError, match=message):
        load_case(case_dir)


def test_the_tool_draws_the_signers_of_the_case(case_dir, capsys):
    sign(case_dir, {"signer": "A", "scrawl": "Ana Pérez", "label": "Firma"}, {"signer": "B", "scrawl": "Bruno Soto"})
    tool.main([str(case_dir)])
    data = yaml.safe_load((case_dir / "signatures.yaml").read_text(encoding="utf-8"))["signatures"]
    assert list(data) == ["A", "B"]
    assert data["A"]["name"] == "Ana Pérez" and data["A"]["seed"] == 1
    assert data["A"]["family"] != data["B"]["family"]          # no two people of a case share a hand movement
    case = load_case(case_dir)                                  # what it writes is valid for the exporter
    assert set(case.signatures) == {"A", "B"}
    first = data["A"]["strokes"]
    tool.main([str(case_dir)])                                  # a second run leaves drawn signers alone
    assert yaml.safe_load((case_dir / "signatures.yaml").read_text(encoding="utf-8"))["signatures"]["A"]["strokes"] == first
    tool.main([str(case_dir), "--redo", "A"])
    again = yaml.safe_load((case_dir / "signatures.yaml").read_text(encoding="utf-8"))["signatures"]["A"]
    assert again["seed"] == 2 and again["strokes"] != first


def test_drawing_is_deterministic():
    assert tool.draw("Ana Pérez", 1, "flow") == tool.draw("Ana Pérez", 1, "flow")
    assert tool.draw("Ana Pérez", 1, "flow") != tool.draw("Ana Pérez", 2, "flow")
