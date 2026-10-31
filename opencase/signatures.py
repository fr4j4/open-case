"""Signatures drawn as pen strokes.

The engine knows how to draw a signature: a few strokes of a ballpoint pen, in the ink colour, at the height
of the signature line. Each case brings the strokes of the people who sign its sheets, as SVG path data:

  cases/<case>/signatures.yaml        neutral: for each signer id, the strokes, the pen width and the viewbox

A ```signature block names the signer of an item with `signer: <id>`. When the case has no strokes for that
id, the item is printed with the handwriting font (its `scrawl:`), as before. tools/signatures.py draws the
strokes from the signer's name; the export only reads them.
"""
import re

from .loader import CaseError, read_yaml_file
from .markup import e

FILE = "signatures.yaml"
DEFAULT_WIDTH = 1.5
DEFAULT_VIEWBOX = "0 0 120 40"
PATH_DATA = re.compile(r"^\s*[Mm][\sMmLlHhVvCcSsQqTtAaZz0-9.,eE+\-]*$")


def load(case):
    """Reads signatures.yaml into case.signatures ({id: {"strokes", "width", "viewbox", "name"}}). Errors in the
    data stop the export here, so --check sees them too."""
    case.signatures = {}
    path = case.root / FILE
    if not path.exists():
        return
    data = read_yaml_file(path).get("signatures") or {}
    if not isinstance(data, dict):
        raise CaseError("'signatures' must be one entry per signer id (key: value fields)", path)
    for sid, sig in data.items():
        sid = str(sid)
        if not isinstance(sig, dict):
            raise CaseError(f"the signature of '{sid}' must have strokes:, and optionally width: and viewbox:", path)
        strokes = sig.get("strokes")
        if not isinstance(strokes, list) or not strokes:
            raise CaseError(f"the signature of '{sid}' has no strokes (a list of SVG path data)", path)
        for d in strokes:
            if not isinstance(d, str) or not PATH_DATA.match(d):
                raise CaseError(f"a stroke of '{sid}' is not SVG path data (it must start with M): {str(d)[:40]}", path)
        viewbox = str(sig.get("viewbox", DEFAULT_VIEWBOX))
        numbers = viewbox.replace(",", " ").split()
        try:
            ok = len(numbers) == 4 and float(numbers[2]) > 0 and float(numbers[3]) > 0
        except ValueError:
            ok = False
        if not ok:
            raise CaseError(f"the viewbox of '{sid}' must be four numbers: x y width height", path)
        width = sig.get("width", DEFAULT_WIDTH)
        if not isinstance(width, (int, float)) or width <= 0:
            raise CaseError(f"the width of '{sid}' must be a number above 0", path)
        case.signatures[sid] = {"strokes": strokes, "width": width, "viewbox": " ".join(numbers),
                                "name": str(sig.get("name", ""))}


def items(case):
    """(sheet, block, item) of every item of a ```signature block that names a signer."""
    from .components import read_items
    for sheet in case.kit + list(case.dossier.values()) + case.guide:
        for b in sheet.blocks:
            if b.type == "signature":
                for it in read_items(b, sheet):
                    if isinstance(it, dict) and it.get("signer") is not None:
                        yield sheet, b, it


def check(case):
    """A signer with no strokes in signatures.yaml needs its scrawl: to be printed with the font."""
    for sheet, b, it in items(case):
        sid = str(it["signer"])
        if sid not in case.signatures and not it.get("scrawl"):
            raise CaseError(f"the signer '{sid}' has no strokes in {FILE} and no scrawl: to print instead",
                            sheet.path, b.line)
    used = {str(it["signer"]) for _, _, it in items(case)}
    for sid in case.signatures:
        if sid not in used:
            case.warnings.append(f"{FILE}: '{sid}' signs no sheet")


def svg(case, sid, label):
    """The <svg> of a signer's strokes, or None when the case has none for that id."""
    sig = case.signatures.get(str(sid))
    if not sig:
        return None
    paths = "".join(f'<path d="{e(d)}"/>' for d in sig["strokes"])
    return (f'<svg class="oc-firma__svg" viewBox="{sig["viewbox"]}" role="img" aria-label="{e(label)}">'
            f'<g fill="none" stroke="currentColor" stroke-width="{sig["width"]}" stroke-linecap="round" '
            f'stroke-linejoin="round">{paths}</g></svg>')
