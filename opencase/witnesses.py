"""Witnesses: the people who are not suspects, the rows of the guide's tables and the check that none
of them is invisible.

A witness is one or several cards of type witness with the same `who` ("Luis Riquelme, conserje"; the
name is what comes before the comma). Each witness says where the teams can read their name, in
`appears_in` (codes of the dossier or of cards), and other ways the material calls them, in `aliases`
("conserje", "la Maca"). Both can go on any of the person's cards; they add up. The teams may only
interview someone once their name has appeared in their material, so a witness whose name or alias is
in none of those places cannot be found and the case gets a warning.
"""
import re

from .loader import CaseError, as_list, card_kind as _kind, display_code, iter_cards as _cards, normalize_code
from .markup import plain_text

KIND = "witness"


def name_of(who):
    return str(who).split(",")[0].strip()


def witnesses(case):
    """The witnesses in the order of cards.yaml, each with all its cards, for the guide's tables (templates)."""
    people = {}
    for c, g in _cards(case):
        if _kind(c, g) != KIND:
            continue
        who = str(c.get("who") or g.get("who") or c["code"])
        w = people.setdefault(who, {"who": who, "name": name_of(who), "cards": [], "attach": [],
                                    "appears_in": [], "aliases": [], "note": ""})
        w["cards"].append(str(c["code"]))
        for key in ("attach", "appears_in", "aliases"):
            w[key] += [str(x) for x in _list(c.get(key)) if str(x) not in w[key]]
        if c.get("guide_note"):
            w["note"] = (w["note"] + " " + c["guide_note"]).strip()
    for w in people.values():
        w["appears_in_shown"] = [display_code(case, x) for x in w["appears_in"]]
        w["attach"] = [display_code(case, x) for x in w["attach"]]
    return list(people.values())


def _list(v):
    """Like as_list, but an alias may hold commas only when written as a YAML list."""
    return list(v) if isinstance(v, (list, tuple)) else as_list(v)


def source_text(case, ref):
    """The text the teams read in a dossier code (all its sheets: E13b can take two) or a card, or None if
    the code is neither."""
    n = normalize_code(ref)
    sheets = [s for sheet_id, s in case.dossier.items()
              if n in (normalize_code(sheet_id), normalize_code(s.get("code", sheet_id)))]
    if sheets:
        return "\n".join(s.path.read_text(encoding="utf-8") for s in sheets)
    for c, g in _cards(case):
        if normalize_code(c.get("code", "")) == n:
            return " ".join(plain_text(str(c.get(k, ""))) for k in ("question", "answer", "note"))
    return None


def check(case):
    """appears_in points to sheets or cards that exist; a witness with no appears_in, or whose name and aliases
    are in none of them, is a warning (the teams could never ask for them)."""
    cards_file = case.lang_root / "cards.yaml"
    for w in witnesses(case):
        if not w["appears_in"]:
            case.warnings.append(f"the witness {w['who']} ({', '.join(w['cards'])}) has no appears_in: say in "
                                 "cards.yaml where the teams can read their name")
            continue
        names = [w["name"]] + w["aliases"]
        seen = False
        for ref in w["appears_in"]:
            text = source_text(case, ref)
            if text is None:
                raise CaseError(f"the witness {w['who']} appears in {ref}, which is neither a sheet of the dossier "
                                "nor a card", cards_file)
            if any(n.casefold() in text.casefold() for n in names if n):
                seen = True
        if not seen:
            case.warnings.append(f"the witness {w['who']} is invisible: neither '{w['name']}' nor an alias appears "
                                 f"in {', '.join(w['appears_in'])} (add the alias the material uses)")
