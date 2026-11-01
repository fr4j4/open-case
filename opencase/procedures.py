"""Procedures (diligencias): the requests of the team's menu, and the places of the case with the sources
they have.

The engine knows the KINDS of procedure (a phone, a bank statement, cameras…) and what each kind is; a case
lists its own procedures with its own codes (DG9 is the phone towers in one case and the cameras in another),
and says what each one hands out:

  cases/<case>/procedures.yaml        neutral: code, kind, cost, each, alibi, and gives or targets
  cases/<case>/locations.yaml         neutral: the places and the sources each one has (camera, register)
  languages/<lang>/procedures.yaml    texts: the names of the people of the targets, the label (kit) and the
                                      short name (guide) of each procedure, the labels of other targets and
                                      the notes for the director
  languages/<lang>/locations.yaml     texts: the name and the note of each place

A result is a dossier sheet (E12), several handed out together ([E29-J, E08]), `none` ("sin hallazgos": the
request makes sense but there is nothing to find, and the token is spent) or `material` (only for an open
request: hand out what the material has, if anything). A target is a suspect's letter, a place of
locations.yaml, `other` (anyone or anything else) or a key of the case's own with its label in the language
file. Whether a procedure can be paid with an alibi token is said explicitly with `alibi: true`, never worked
out from its results. A case without procedures.yaml keeps its menu written by hand.
"""
from .loader import (CaseError, as_list, card_kind, display_code, iter_cards, normalize_code, read_yaml_file)

# What each kind is, the same in every case. `target`: what the team names in the request (a person, a place
# or a thing). `locates`: it can show where someone was, so a case may let alibi tokens pay for it. `source`:
# it reads a source a place has (a camera, a register): asking whether the place has one is free.
# Their labels are in the strings (procedures.kinds.<kind>).
KINDS = {
    "report": {"target": "thing", "locates": False, "source": False},
    "phone": {"target": "person", "locates": False, "source": False},
    "bank_statement": {"target": "person", "locates": False, "source": False},
    "social_media": {"target": "person", "locates": False, "source": False},
    "vehicle": {"target": "person", "locates": False, "source": False},
    "area_search": {"target": "place", "locates": False, "source": False},
    "belongings": {"target": "person", "locates": False, "source": False},
    "premises_search": {"target": "place", "locates": False, "source": False},
    "phone_towers": {"target": "person", "locates": True, "source": False},
    "cameras": {"target": "place", "locates": True, "source": True},
    "other": {"target": "thing", "locates": False, "source": False},
}
SOURCES = ("camera", "register")
SPECIAL = ("none", "material")
NEUTRAL_KEYS = {"code", "kind", "cost", "each", "alibi", "gives", "targets"}
TEXT_KEYS = {"label", "short", "note", "targets", "notes"}


def _file(case, name, lang=False):
    return (case.lang_root if lang else case.root) / name


def has_procedures(case):
    return _file(case, "procedures.yaml").exists()


def _read(case, name, lang, key, kind):
    path = _file(case, name, lang)
    if not path.exists():
        return path, kind()
    data = read_yaml_file(path)
    value = data.get(key, kind())
    if not isinstance(value, kind):
        what = "a list (lines starting with '- ')" if kind is list else "key: value fields"
        raise CaseError(f"'{key}' must be {what}", path)
    return path, value


def load(case):
    """Reads and joins the four files. Sets case.procedures and case.locations (lists of dicts, in the order of
    the neutral files). Errors in the data stop the export here, so --check sees them too."""
    case.procedures, case.locations = [], []
    lpath, places = _read(case, "locations.yaml", False, "locations", list)
    ltpath, place_texts = _read(case, "locations.yaml", True, "locations", dict)
    seen = set()
    for p in places:
        if not isinstance(p, dict) or not p.get("id"):
            raise CaseError("every place needs an id", lpath)
        pid = str(p["id"])
        if pid in seen:
            raise CaseError(f"the place '{pid}' is twice", lpath)
        seen.add(pid)
        sources = [str(s) for s in as_list(p.get("sources"))]
        for s in sources:
            if s not in SOURCES:
                raise CaseError(f"the place '{pid}' has the source '{s}' (use {', '.join(SOURCES)})", lpath)
        text = place_texts.get(pid) or {}
        if isinstance(text, str):
            text = {"name": text}
        if not text.get("name"):
            raise CaseError(f"the place '{pid}' has no name in languages/{case.lang}/locations.yaml", ltpath)
        case.locations.append({"id": pid, "sources": sources, "name": str(text["name"]),
                               "note": str(text.get("note", "")), "procedures": [], "results": []})
    for pid in place_texts:
        if pid not in seen:
            raise CaseError(f"'{pid}' is not a place of locations.yaml", ltpath)

    if not has_procedures(case):
        return
    path, items = _read(case, "procedures.yaml", False, "procedures", list)
    tpath = _file(case, "procedures.yaml", True)
    texts = read_yaml_file(tpath) if tpath.exists() else {}
    names = texts.get("names", {}) or {}
    own_texts = texts.get("procedures", {}) or {}
    places_by_id = {p["id"]: p for p in case.locations}
    letters = {str(s.get("letter")) for s in case.suspects}
    codes = set()
    for item in items:
        if not isinstance(item, dict) or not item.get("code"):
            raise CaseError("every procedure needs a code", path)
        code = str(item["code"])
        if code in codes:
            raise CaseError(f"the procedure {code} is twice", path)
        codes.add(code)
        unknown = set(item) - NEUTRAL_KEYS
        if unknown:
            raise CaseError(f"{code}: '{sorted(unknown)[0]}' is not a field of a procedure (the texts go in "
                            f"languages/<lang>/procedures.yaml)", path)
        kind = str(item.get("kind", ""))
        if kind not in KINDS:
            raise CaseError(f"{code}: the kind '{kind}' does not exist (the engine has: {', '.join(KINDS)})", path)
        cost = _cost(item.get("cost", 1), code, path)
        if ("gives" in item) == ("targets" in item):
            raise CaseError(f"{code} needs either gives (one result) or targets (one result per person or place)", path)
        text = own_texts.get(code) or {}
        unknown = set(text) - TEXT_KEYS
        if unknown:
            raise CaseError(f"{code}: '{sorted(unknown)[0]}' is not a text of a procedure (use "
                            f"{', '.join(sorted(TEXT_KEYS))})", tpath)
        kind_text = lambda k: case.t(f"procedures.kinds.{kind}.{k}")  # noqa: E731
        proc = {"code": code, "kind": kind, "cost": cost, "each": bool(item.get("each")),
                "alibi": bool(item.get("alibi")), "label": str(text.get("label") or kind_text("label")),
                "short": str(text.get("short") or kind_text("short")), "note": str(text.get("note", "")),
                "targets": [], "gives": None, **KINDS[kind]}
        if "gives" in item:
            proc["gives"] = _result(case, item["gives"], cost, code, path)
            if proc["gives"]["special"] == "material":
                proc["gives"]["note"] = ""
        else:
            targets = item["targets"]
            if not isinstance(targets, dict) or not targets:
                raise CaseError(f"{code}: targets must be key: result fields (B: E15-B, copec: E28, other: none)", path)
            labels = text.get("targets", {}) or {}
            notes = text.get("notes", {}) or {}
            for key in list(labels) + list(notes):
                if str(key) not in {str(k) for k in targets}:
                    raise CaseError(f"{code}: '{key}' is not one of its targets", tpath)
            for key, value in targets.items():
                key = str(key)
                result = _result(case, value, cost, code, path)
                label = labels.get(key)
                if label is None:
                    if key == "other":
                        label = case.t(f"procedures.other_target.{KINDS[kind]['target']}")
                    elif key in places_by_id:
                        label = places_by_id[key]["name"]
                    elif key in names:
                        label = names[key]
                    elif key in letters:
                        raise CaseError(f"{code}: there is no name for {key} under names: in "
                                        f"languages/{case.lang}/procedures.yaml", tpath)
                    else:
                        raise CaseError(f"{code}: the target '{key}' is neither a suspect, a place of "
                                        "locations.yaml nor other; give it a label under targets: in "
                                        f"languages/{case.lang}/procedures.yaml", tpath)
                result.update(key=key, label=str(label), note=str(notes.get(key, "")), suspect=key in letters)
                proc["targets"].append(result)
                if key in places_by_id:
                    place = places_by_id[key]
                    if code not in place["procedures"]:
                        place["procedures"].append(code)
                    place["results"].append({**result, "procedure": code, "source": proc["source"]})
        _derive(proc)
        case.procedures.append(proc)
    for code in own_texts:
        if str(code) not in codes:
            raise CaseError(f"{code} is not a procedure of procedures.yaml", tpath)


def _cost(value, code, path):
    if not isinstance(value, int) or isinstance(value, bool) or value < 1:
        raise CaseError(f"{code}: the cost must be a whole number of tokens (1 or more)", path)
    return value


def _result(case, value, cost, code, path):
    """{sheets, shown, special, cost} from E15-B, [E29-J, E08], none, material or {gives: ..., cost: 2}."""
    own_cost = cost
    if isinstance(value, dict):
        if set(value) - {"gives", "cost"} or "gives" not in value:
            raise CaseError(f"{code}: a result with its own cost is {{gives: E13d, cost: 2}}", path)
        own_cost = _cost(value.get("cost", cost), code, path)
        value = value["gives"]
    if value is None:
        raise CaseError(f"{code}: a result is empty (write none for 'sin hallazgos')", path)
    if isinstance(value, str) and value in SPECIAL:
        return {"sheets": [], "shown": [], "special": value, "cost": own_cost}
    sheets = [str(x) for x in as_list(value)]
    known = {normalize_code(s) for s in case.dossier} | {normalize_code(s.get("code", i)) for i, s in case.dossier.items()}
    for s in sheets:
        if normalize_code(s) not in known:
            raise CaseError(f"{code} hands out {s}, which is not a sheet of the dossier", path)
    return {"sheets": sheets, "shown": [display_code(case, s) for s in sheets], "special": None, "cost": own_cost}


def _split(shown):
    """E15·B -> (E15, B); E24 -> (E24, None)."""
    base, _, suffix = shown.partition("·")
    return base, (suffix or None)


def _derive(proc):
    """What the templates need besides the data: the costs a request can have, the rows of the control sheet
    (one per sheet number: E15·B to E15·M are one row) and whether the results read as E15·B / T / C."""
    results = [proc["gives"]] if proc["gives"] else proc["targets"]
    proc["costs"] = sorted({r["cost"] for r in results} | ({proc["cost"]} if proc["gives"] is None else set()))
    for r in results:
        r["extra_cost"] = r["cost"] != proc["cost"]
    with_sheets = [r for r in results if r["sheets"]]
    rows = []
    for r in with_sheets:
        base, suffix = _split(r["shown"][0])
        row = next((x for x in rows if x["base"] == base), None)
        if row is None:
            row = {"base": base, "suffixes": [], "targets": [], "cost": r["cost"]}
            rows.append(row)
        if suffix:
            row["suffixes"].append(suffix)
        row["targets"].append(r)
    for row in rows:
        one = len(row["targets"]) == 1 and not row["suffixes"] and proc["gives"] is None
        row["label"] = row["targets"][0]["label"] if one else None
    proc["control_rows"] = rows
    # E29·P / B / J + E08 / X: every target with a sheet shares the number and has a letter, and none is empty.
    proc["by_letter"] = (proc["gives"] is None and len(rows) == 1 and len(with_sheets) > 1
                         and len(rows[0]["suffixes"]) == len(with_sheets) and len(with_sheets) == len(results))
    for r in with_sheets:
        r["suffix"] = _split(r["shown"][0])[1]
        r["also"] = r["shown"][1:]


def person_matrix(case):
    """The quick sheet's table of procedures on a person: one row per person, one column per procedure that has
    at least two suspects as targets, in the order of the suspects. Each cell is the target's result or None.
    Returns None when the case has no such procedure."""
    cols = [p for p in case.procedures
            if p["target"] == "person" and sum(1 for t in p["targets"] if t.get("suspect")) >= 2]
    if not cols:
        return None
    order = [str(s.get("letter")) for s in case.suspects]
    for p in cols:
        for t in p["targets"]:
            if t["key"] not in order and t["key"] != "other":
                order.append(t["key"])
    rows = []
    for key in order:
        cells = [next((t for t in p["targets"] if t["key"] == key), None) for p in cols]
        if any(cells):
            name = next(t["label"] for t in cells if t)
            rows.append({"key": key, "name": name, "cells": cells})
    return {"cols": cols, "rows": rows}


def reachable(case):
    """Normalized codes of every dossier sheet a team can get: the envelopes, the procedures' results and the
    sheets the cards hand out (attach)."""
    out = set()
    for sec in case.sections:
        if sec.get("envelope") is not None:
            for pid in sec.get("items", []) or []:
                out.add(normalize_code(pid))
                if pid in case.dossier:
                    out.add(normalize_code(case.dossier[pid].get("code", pid)))
    for p in case.procedures:
        for r in ([p["gives"]] if p["gives"] else p["targets"]):
            out |= {normalize_code(s) for s in r["sheets"]}
    for c, g in iter_cards(case):
        out |= {normalize_code(a) for a in as_list(c.get("attach"))}
    return out


def card_rows(case):
    """The cards that hand out a sheet (attach), for the control sheet: [{codes, shown, what}], in the order
    of cards.yaml. `what` is the sheet's `short` (front matter) or its title. A procedure that hands the sheet
    out besides its own (DG12 J: E29·J + E08) joins the card's row: J2 o DG12 J → E08."""
    rows = []
    for c, g in iter_cards(case):
        attach = as_list(c.get("attach"))
        if not attach or card_kind(c, g) in ("notice", "press", "hint", "closing"):
            continue
        rows.append({"codes": [str(c["code"])], "sheets": {normalize_code(a) for a in attach},
                     "shown": [display_code(case, a) for a in attach], "what": _what(case, attach[0])})
    for who, sheet in _also(case):
        row = next((r for r in rows if normalize_code(sheet) in r["sheets"]), None)
        if row is not None:
            row["codes"].append(who)
    return rows


def also_rows(case):
    """The sheets a procedure hands out besides its own that no card hands out, as rows of the procedures'
    table: [{code, shown, what}] (DG12 J → E08 when no card gives E08)."""
    by_cards = {normalize_code(a) for c, g in iter_cards(case) for a in as_list(c.get("attach"))
                if card_kind(c, g) not in ("notice", "press", "hint", "closing")}
    return [{"code": who, "shown": display_code(case, sheet), "what": _what(case, sheet)}
            for who, sheet in _also(case) if normalize_code(sheet) not in by_cards]


def _also(case):
    """(DG12 J, E08) for each sheet a procedure's target hands out after its first one."""
    for p in case.procedures:
        for r in ([p["gives"]] if p["gives"] else p["targets"]):
            for sheet in r["sheets"][1:]:
                yield (f"{p['code']} {r['key']}" if r.get("suspect") else p["code"]), sheet


def _what(case, ref):
    s = _sheet(case, ref)
    return str((s.get("short") or s.get("title", "")) if s is not None else "")


def _sheet(case, ref):
    n = normalize_code(ref)
    for sheet_id, s in case.dossier.items():
        if n in (normalize_code(sheet_id), normalize_code(s.get("code", sheet_id))):
            return s
    return None


def check(case):
    """Warnings about procedures and places that the loader cannot call errors, and the reach of the follow-ups
    and witnesses (only when the case lists its procedures: without them the engine cannot know what a team can
    get)."""
    if not has_procedures(case):
        return
    for p in case.procedures:
        if p["alibi"] and not p["locates"]:
            case.warnings.append(f"{p['code']} has alibi: true, but a procedure of kind {p['kind']} does not show "
                                 "where someone was (alibi tokens only pay for that)")
        if p["alibi"] and not case.figures["alibi_tokens_per_team"]:
            case.warnings.append(f"{p['code']} has alibi: true, but the case has no alibi tokens "
                                 "(alibi_tokens_per_team)")
    for place in case.locations:
        for r in place["results"]:
            if r["source"] and r["sheets"] and not place["sources"]:
                case.warnings.append(f"{r['procedure']} hands out {', '.join(r['shown'])} for {place['id']}, but "
                                     "locations.yaml says the place has no camera or register")
            if r["source"] and r["special"] == "none" and place["sources"]:
                case.warnings.append(f"{r['procedure']} finds nothing at {place['id']}, but locations.yaml says the "
                                     f"place has a {' and a '.join(place['sources'])}")
    reach = reachable(case)
    for sec in case.sections:
        for pid in sec.get("items", []) or []:
            s = case.dossier.get(pid)
            if s is None or s.get("notice") or sec.get("envelope") is not None:
                continue
            if normalize_code(s.get("code", pid)) not in reach and normalize_code(pid) not in reach:
                case.warnings.append(f"no team can get {display_code(case, pid)}: no procedure hands it out and "
                                     "no card attaches it")
    cards = {normalize_code(c["code"]) for c, g in iter_cards(case) if c.get("code")}
    for c, g in iter_cards(case):
        for field, what in (("unlocked_by", "the follow-up"), ("appears_in", "the witness")):
            refs = as_list(c.get(field)) if field == "unlocked_by" else (
                list(c.get(field)) if isinstance(c.get(field), (list, tuple)) else as_list(c.get(field)))
            for ref in refs:
                n = normalize_code(ref)
                if n not in cards and n not in reach and _sheet(case, ref) is not None:
                    case.warnings.append(f"{what} {c['code']} needs {display_code(case, ref)} ({field}), which no "
                                         "team can get")


def text_fields(case):
    """The texts a language writes for the procedures, as "DG3 label", "DG11 notes.karaoke", "names.B": what
    compare_languages checks a translation has (a missing label would fall back to the kind's without notice)."""
    path = _file(case, "procedures.yaml", True)
    if not path.exists():
        return set()
    data = read_yaml_file(path)
    out = {f"names.{k}" for k in (data.get("names") or {})}
    for code, text in (data.get("procedures") or {}).items():
        for key, value in (text or {}).items():
            if isinstance(value, dict):
                out |= {f"{code} {key}.{k}" for k in value}
            else:
                out.add(f"{code} {key}")
    return out


def text_of(case):
    """Every text of the procedures and places, for the acronyms check."""
    parts = []
    for p in case.procedures:
        parts += [p["label"], p["short"], p["note"]]
        parts += [t["label"] + " " + t["note"] for t in p["targets"]]
    parts += [pl["name"] + " " + pl["note"] for pl in case.locations]
    return "\n".join(x for x in parts if x)
