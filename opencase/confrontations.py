"""Confrontations as data: which evidence opens which card (`opens_with` in cards.yaml).

A confrontation card (type confrontation, or a follow-up or failed card that a confrontation also hands out) can
list the rules that open it. A rule is a mapping with:

  all       codes the team must show together (every one)
  any       codes of which at least one must be shown
  none      codes that must NOT be among the evidence (the card is not for that route)
  held      cards the team must already hold (T7 comes only once the team has T6)
  priority  whole number, 0 by default: of all the cards whose rules fit, the highest wins
  shows     what the guide's table says under "if they show…" (it is generated from the codes when missing)
  note      what the table adds after the card ("(admits it…)", "La ficha se cobra.")

The rules of one card are alternatives. `match` is the reference the web app (site/play/js/rules.js) repeats; the
director's panel suggests the card it returns. When the best cards tie, nobody wins: the panel lists them and
the director asks the team what they point at (the guide has always said so).
"""
import re

from .loader import CaseError, as_list, card_kind as _kind, display_code, iter_cards as _cards, normalize_code
from .markup import plain_text

KINDS = ("confrontation", "follow-up", "failed")
FIELDS = ("all", "any", "none", "held", "priority", "shows", "note")


def _codes(value):
    if isinstance(value, (list, tuple)):
        return [str(x) for x in value]
    return [str(x) for x in as_list(value)]


def rules_of(case, c):
    """The normalized rules of a card: [{all, any, none, held, priority, shows, note}] with printed codes."""
    out = []
    for r in c.get("opens_with") or []:
        out.append({
            "all": [display_code(case, x) for x in _codes(r.get("all"))],
            "any": [display_code(case, x) for x in _codes(r.get("any"))],
            "none": [display_code(case, x) for x in _codes(r.get("none"))],
            "held": _codes(r.get("held")),
            "priority": int(r.get("priority", 0)),
            "shows": str(r.get("shows", "")).strip(),
            "note": str(r.get("note", "")).strip(),
        })
    return out


def _fits(rule, evidence, held):
    ev = {normalize_code(x) for x in evidence}
    hd = {normalize_code(x) for x in held}
    n = normalize_code
    return (all(n(x) in ev for x in rule["all"])
            and (not rule["any"] or any(n(x) in ev for x in rule["any"]))
            and not any(n(x) in ev for x in rule["none"])
            and all(n(x) in hd for x in rule["held"]))


def match(case, suspect, evidence, held=()):
    """The card the evidence opens for a suspect: {card, candidates}. `card` is the code of the only best card
    (None when no card fits or the best ones tie); `candidates` are the best cards, in the order of the file."""
    best, names = None, []
    for c, g in _cards(case):
        if _kind(c, g) not in ("confrontation", "follow-up") or str(c.get("suspect", g.get("suspect"))) != str(suspect):
            continue
        scores = [r["priority"] for r in rules_of(case, c) if _fits(r, evidence, held)]
        if not scores:
            continue
        score = max(scores)
        if best is None or score > best:
            best, names = score, [str(c["code"])]
        elif score == best:
            names.append(str(c["code"]))
    return {"card": names[0] if len(names) == 1 else None, "candidates": names}


def _join(case, codes, word):
    codes = list(codes)
    if len(codes) <= 1:
        return "".join(codes)
    return ", ".join(codes[:-1]) + case.t(f"confrontations.{word}") + codes[-1]


def default_shows(case, r):
    """The table's "if they show…" for a rule that does not write it: "E14 y E26·B juntas", "E08 o E28 junto con E17·B"."""
    if r["all"] and r["any"]:
        text = case.t("confrontations.with", any=_join(case, r["any"], "or_word"), all=_join(case, r["all"], "and_word"))
    elif r["all"]:
        text = _join(case, r["all"], "and_word") + (case.t("confrontations.together") if len(r["all"]) > 1 else "")
    else:
        text = _join(case, r["any"], "or_word")
    if r["none"]:
        text += case.t("confrontations.without", codes=_join(case, r["none"], "or_word"))
    if r["held"]:
        text += case.t("confrontations.already", cards=_join(case, r["held"], "and_word"))
    return text


def rows(case):
    """The rows of the guide's table, in the order of cards.yaml: code (B◆), what they show, card and its note;
    plus the card of the confrontation that proves nothing."""
    out = []
    for c, g in _cards(case):
        letter = c.get("suspect", g.get("suspect"))
        for r in rules_of(case, c):
            attach = [display_code(case, x) for x in as_list(c.get("attach"))]
            out.append({"mark": f"{letter}◆" if letter else "◆", "card": str(c["code"]), "attach": attach,
                        "shows": r["shows"] or default_shows(case, r), "note": r["note"],
                        "sep": "" if r["note"][:1] in (",", ".", ":", ";") else " "})
    return out


def failed_card(case):
    """The card the engine hands out for evidence that proves nothing (role confrontation_failed), as
    {code, text}, or None."""
    for c, g in _cards(case):
        if c.get("role") == "confrontation_failed":
            return {"code": str(c["code"]), "text": plain_text(str(c.get("answer", ""))).strip(' "“”,.')}
    return None


def has_rules(case):
    return any(c.get("opens_with") for c, g in _cards(case))


def _mentions(text, code):
    flat = re.sub(r"\s*[·\-]\s*", "·", str(text)).upper()
    return normalize_code(code) in flat


def check(case):
    """opens_with: the right cards, known fields, codes that exist; warnings for what the table would lose."""
    cards_file = case.lang_root / "cards.yaml"
    cards = _cards(case)
    card_codes = {normalize_code(c["code"]) for c, g in cards if c.get("code")}
    evidence = ({normalize_code(s.get("code", s.id)) for s in case.dossier.values()}
                | {normalize_code(s) for s in case.dossier})
    anyone = has_rules(case)
    for c, g in cards:
        raw = c.get("opens_with")
        code = c.get("code")
        if raw is None:
            if anyone and _kind(c, g) == "confrontation":
                case.warnings.append(f"the confrontation {code} has no opens_with, so the guide's table has no row for it "
                                     "and the panel never suggests it")
            continue
        if _kind(c, g) not in KINDS:
            raise CaseError(f"card {code} has opens_with, which only confrontation, follow-up and failed cards use", cards_file)
        if not c.get("suspect", g.get("suspect")):
            raise CaseError(f"card {code} has opens_with but no suspect (put `suspect` on it or on its group)", cards_file)
        if not isinstance(raw, list) or not raw or not all(isinstance(r, dict) for r in raw):
            raise CaseError(f"card {code}: opens_with is a list of rules, each with all and/or any", cards_file)
        for r in raw:
            unknown = set(r) - set(FIELDS)
            if unknown:
                raise CaseError(f"card {code}: opens_with has unknown fields: {', '.join(sorted(unknown))} "
                                f"(they are: {', '.join(FIELDS)})", cards_file)
            if not _codes(r.get("all")) and not _codes(r.get("any")):
                raise CaseError(f"card {code}: a rule of opens_with needs `all` or `any`", cards_file)
            if "priority" in r and (isinstance(r["priority"], bool) or not isinstance(r["priority"], int)):
                raise CaseError(f"card {code}: the priority of a rule is a whole number", cards_file)
            for key in ("all", "any", "none"):
                for ref in _codes(r.get(key)):
                    if normalize_code(ref) not in evidence | card_codes:
                        raise CaseError(f"card {code}: opens_with names {ref}, which is neither a sheet of the dossier "
                                        "nor a card", cards_file)
            for ref in _codes(r.get("held")):
                if normalize_code(ref) not in card_codes:
                    raise CaseError(f"card {code}: opens_with says the team must hold {ref}, which is not a card", cards_file)
        for r in rules_of(case, c):
            if r["shows"]:
                missing = [x for x in r["all"] + r["any"] if not _mentions(r["shows"], x)]
                if missing:
                    case.warnings.append(f"card {code}: the text `shows` of a rule does not mention {', '.join(missing)}, "
                                         "which the rule needs: the table and the panel would disagree")
