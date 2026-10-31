"""Follow-up questions (codes ending in +): the box on the card that enables them, the rows of the
guide's tables and their checks.

A follow-up is a card of type follow-up. The cards that enable it name it in `follow_up` (its "mother"
cards). If its question names something the mother card does not say and that comes from another piece
of evidence, the follow-up card says which in `unlocked_by` (one or several codes of the dossier or of
cards; any one of them is enough). The team's card only shows the code, the cost and that condition:
the full question is in the director's guide.
"""
from .loader import CaseError, as_list, normalize_code
from .markup import e

KIND = "follow-up"


def _kind(c, g):
    return str(c.get("type", g.get("type", "answer"))).lower()


def _cards(case):
    return [(c, g) for g in case.card_groups for c in g.get("cards", []) or []]


def index(case):
    """Follow-up cards by normalized code."""
    return {normalize_code(c["code"]): c for c, g in _cards(case) if _kind(c, g) == KIND and c.get("code")}


def card_box(c, case):
    """The boxes at the bottom of a card that enables follow-ups: "Seguimiento H2+ · 1 ficha · si ya tienen E13b".
    A case that turns the engine off keeps the old line ("Seguimiento disponible: H2+")."""
    codes = as_list(c.get("follow_up"))
    if not codes:
        return ""
    if not case.uses_engine:
        return "".join(f'<div class="oc-tarjeta__pie oc-tarjeta__pie--seg">{e(case.t("cards.follow_up_available"))}: '
                       f'{e(code)}</div>' for code in codes)
    found = index(case)
    out = []
    for code in codes:
        text = case.t("follow_up.box", code=code)
        target = found.get(normalize_code(code))
        unlock = as_list(target.get("unlocked_by")) if target else []
        if unlock:
            text += " · " + case.t("follow_up.box_condition", codes=join_or(case, unlock))
        out.append(f'<div class="oc-tarjeta__seguimiento">{e(text)}</div>')
    return "".join(out)


def join_or(case, codes):
    codes = [str(x) for x in codes]
    if len(codes) == 1:
        return codes[0]
    return ", ".join(codes[:-1]) + case.t("follow_up.or_word") + codes[-1]


def follow_ups(case):
    """Every follow-up of the case, in the order of cards.yaml, for the guide's tables (templates)."""
    mothers = {}
    for c, g in _cards(case):
        for code in as_list(c.get("follow_up")):
            mothers.setdefault(normalize_code(code), []).append(str(c["code"]))
    out = []
    for c, g in _cards(case):
        if _kind(c, g) != KIND:
            continue
        out.append({
            "code": str(c["code"]),
            "question": c.get("question", ""),
            "mothers": mothers.get(normalize_code(c["code"]), []),
            "unlocked_by": [str(x) for x in as_list(c.get("unlocked_by"))],
            "attach": [str(x) for x in as_list(c.get("attach"))],
            "note": c.get("guide_note", ""),
        })
    return out


def check(case):
    """follow_up and unlocked_by point to things that exist; a follow-up nobody enables is only a warning."""
    cards_file = case.lang_root / "cards.yaml"
    cards = _cards(case)
    card_codes = {normalize_code(c["code"]) for c, g in cards if c.get("code")}
    evidence = {normalize_code(s.get("code", s.id)) for s in case.dossier.values()} | {normalize_code(s) for s in case.dossier}
    found = index(case)
    enabled = set()
    for c, g in cards:
        for code in as_list(c.get("follow_up")):
            if normalize_code(code) not in card_codes:
                raise CaseError(f"card {c['code']} enables the follow-up {code}, but no card has that code", cards_file)
            if normalize_code(code) not in found:
                case.warnings.append(f"card {c['code']} enables {code} as a follow-up, but {code} is not of type follow-up")
            enabled.add(normalize_code(code))
        unlock = as_list(c.get("unlocked_by"))
        if unlock and _kind(c, g) != KIND:
            raise CaseError(f"card {c['code']} has unlocked_by, which only follow-up cards use", cards_file)
        for ref in unlock:
            if normalize_code(ref) not in evidence | card_codes:
                raise CaseError(f"the follow-up {c['code']} is unlocked by {ref}, which is neither a sheet of the dossier "
                                "nor a card", cards_file)
    for code, c in found.items():
        if code not in enabled:
            case.warnings.append(f"the follow-up {c['code']} is enabled by no card (add it to the follow_up of its "
                                 "mother card)")
