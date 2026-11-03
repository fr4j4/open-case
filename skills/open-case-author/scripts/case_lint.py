#!/usr/bin/env python3
"""Cross references that the exporter's --check does not verify, plus a spoiler scan of the kit.

    python case_lint.py cases/<case> [--lang es]

Errors (exit 1):
  - a suspect letter is duplicated, or a card's suspect letter has no suspect
(follow_up, unlocked_by and appears_in pointing nowhere, follow-ups no card enables and invisible witnesses
are checked by the exporter itself: run export.py --check too.)
Warnings (exit 0):
  - a suspect has fewer than 2 menu questions or no confrontation card
  - a suspect has no statement file (DEC-<letter>.md)
  - a card code or a dossier code that is never mentioned in the guide (no row to answer it; a sheet counts as
    mentioned when the code it prints is, so E13b-2.md with `code: E13b` is covered by E13b)
  - a code written in backticks in the kit or the guide that is neither a card, a dossier sheet nor a DG code of the kit
    (or of procedures.yaml)
  - a kit sheet that mentions a dossier code that is not in an envelope section (possible spoiler)
  - the kit never mentions the number of tokens of case.yaml (cases with engine_sheets: false), or a kit,
    guide or notice sheet writes by hand a figure the engine prints (tokens, minutes, hint costs), or
    session_minutes is shorter than the phases and the closing add up to
  - an acronym used before its long form is written, or a word in capitals that is in no glossary (the
    exporter's own check, see "Acronyms" in docs/case-format.md)
  - the culprit (from a `# culprit: X` comment in suspects.yaml, optional) is listed first in suspects.yaml

Needs pyyaml (the exporter needs it too).
"""
import argparse
import re
import sys
from pathlib import Path

try:
    import yaml
except ImportError:  # pragma: no cover
    print("Error: pyyaml is needed (pip install pyyaml)", file=sys.stderr)
    sys.exit(2)

CODE_IN_TICKS = re.compile(r"`([^`\n]+)`")
DG = re.compile(r"^DG\d+[A-Z]?$")


def norm(code):
    """`E17·B`, `E17 · B`, `DEC · B`, `E17-B` → `E17-B`."""
    return re.sub(r"\s*[·•]\s*", "-", str(code).strip()).replace(" ", "")


def tokens_in_ticks(text):
    out = []
    for m in CODE_IN_TICKS.finditer(text):
        for t in re.split(r"\s*(?:→|/|,|;|\s·\s|\s)\s*", m.group(1)):
            t = t.strip("() ")
            if t and t not in ("→", "·", "/", "+", "c/u") and not t.isdigit():
                out.append(norm(t))
    return out


def load_yaml(path):
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def printed_code(path):
    """The code a dossier sheet prints (`code:` in its front matter; the file name by default). E13b-2.md
    prints E13b: the second sheet of the same piece of evidence."""
    m = re.match(r"---\s*\n(.*?)\n---\s*(?:\n|$)", path.read_text(encoding="utf-8"), re.S)
    data = (yaml.safe_load(m.group(1)) or {}) if m else {}
    return norm(data.get("code") or path.stem) if isinstance(data, dict) else norm(path.stem)


def main():
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    p.add_argument("case")
    p.add_argument("--lang")
    a = p.parse_args()
    root = Path(a.case)
    neutral = load_yaml(root / "case.yaml")
    lang = a.lang or neutral.get("base_language") or "es"
    L = root / "languages" / lang
    errors, warnings, info = [], [], []

    # Suspects
    suspects = load_yaml(L / "suspects.yaml").get("suspects") or []
    letters = [str(s.get("letter")) for s in suspects]
    for x in {l for l in letters if letters.count(l) > 1}:
        errors.append(f"suspects.yaml: letter {x} is used by more than one suspect")
    culprit = None
    for line in (L / "suspects.yaml").read_text(encoding="utf-8").splitlines():
        m = re.match(r"\s*#\s*culprit:\s*([A-ZÑ]{1,2})", line)
        if m:
            culprit = m.group(1)
    if culprit and letters and letters[0] == culprit:
        warnings.append("suspects.yaml: the culprit is listed first; the kit and the suspect cards will show them first")

    # Cards
    groups = load_yaml(L / "cards.yaml").get("groups") or []
    cards = []
    for g in groups:
        for c in g.get("cards") or []:
            c = dict(c)
            c["_suspect"] = c.get("suspect") or g.get("suspect")
            c["_type"] = c.get("type") or g.get("type") or "answer"
            cards.append(c)
    codes = {norm(c.get("code")) for c in cards if c.get("code")}
    for c in cards:
        if c["_suspect"] and str(c["_suspect"]) not in letters:
            errors.append(f"cards.yaml: card {c.get('code')} belongs to suspect {c['_suspect']}, who is not in suspects.yaml")
    for l in letters:
        mine = [c for c in cards if str(c["_suspect"]) == l]
        menu = [c for c in mine if c.get("menu")]
        conf = [c for c in mine if c["_type"] == "confrontation"]
        if len(menu) < 2:
            warnings.append(f"suspect {l} has {len(menu)} menu question(s); 3 or 4 is the norm")
        if not conf:
            warnings.append(f"suspect {l} has no confrontation card")
        if not (L / "dossier" / f"DEC-{l}.md").exists():
            warnings.append(f"suspect {l} has no statement (dossier/DEC-{l}.md)")

    # Dossier codes and sections
    dossier_files = {f.stem for f in (L / "dossier").glob("*.md")}
    free = set()
    for sec in (neutral.get("dossier") or {}).get("sections") or []:
        if sec.get("envelope"):
            free.update(norm(x) for x in sec.get("items") or [])
    paid = {norm(x) for x in dossier_files} - free

    # Guide: every card and dossier code should have a row somewhere
    # Cards used at fixed moments (notices, press, hints, closing, wildcards) and the free sheets
    # (envelopes, notices) do not need a row in the response table.
    guide_text = "\n".join(f.read_text(encoding="utf-8") for f in sorted((L / "guide").glob("*.md")))
    # With procedures.yaml the engine draws the procedures' tables (```procedures, ```procedure-answers,
    # ```quick-procedures, ```control): its codes and the sheets they hand out are covered.
    procedures = load_yaml(root / "procedures.yaml").get("procedures") or [] if (root / "procedures.yaml").exists() else []
    proc_codes = {norm(p.get("code")) for p in procedures if p.get("code")}
    proc_sheets = set()
    for proc in procedures:
        results = [proc.get("gives")] if "gives" in proc else list((proc.get("targets") or {}).values())
        for r in results:
            r = r.get("gives") if isinstance(r, dict) else r
            proc_sheets.update(norm(x) for x in (r if isinstance(r, list) else [r]) if x not in (None, "none", "material"))
    if re.search(r"^`{3,}\s*(?:procedure-answers|quick-procedures|quick-persons|control)\b", guide_text, re.M):
        guide_text += "\n" + " ".join(sorted(proc_codes | proc_sheets))
    guide_norm = norm(guide_text).casefold()
    fixed = {"notice", "press", "hint", "closing", "wildcard"}
    # The engine draws the tables of follow-ups and witnesses from cards.yaml (```follow-ups, ```witnesses and
    # their quick- versions): a guide that uses them covers those cards.
    for kind, block in (("follow-up", "follow-ups"), ("witness", "witnesses")):
        if re.search(rf"^`{{3,}}\s*(?:quick-)?{block}\b", guide_text, re.M):
            fixed.add(kind)
    for c in cards:
        code = norm(c.get("code"))
        if c["_type"] in fixed or (c["_type"] == "failed" and not c["_suspect"]):
            continue
        if code.casefold() not in guide_norm:
            warnings.append(f"card {code} is never mentioned in the guide (how does the director know when to hand it?)")
    for code in sorted(norm(x) for x in dossier_files):
        if code in free or code.upper().startswith(("AVISO", "NOTICE")):
            continue
        printed = printed_code(L / "dossier" / f"{code}.md") if (L / "dossier" / f"{code}.md").exists() else code
        if code.casefold() not in guide_norm and printed.casefold() not in guide_norm:
            warnings.append(f"dossier sheet {code} is never mentioned in the guide")

    # Kit: DG codes, spoiler scan, tokens
    kit_files = sorted((L / "kit").glob("*.md"))
    kit_text = "\n".join(f.read_text(encoding="utf-8") for f in kit_files)
    dg_codes = {t for t in tokens_in_ticks(kit_text) if DG.match(t)} | proc_codes
    for dg in sorted(dg_codes):
        if dg.casefold() not in guide_norm:
            warnings.append(f"procedure {dg} is in the kit but never mentioned in the guide")
    families = {x.split("-")[0] for x in (norm(y) for y in dossier_files) if "-" in x}
    known = codes | {norm(x) for x in dossier_files} | families | dg_codes | {"TESTIGO", "PISTA", "PER1", "DG10"}
    for f in kit_files:
        for t in tokens_in_ticks(f.read_text(encoding="utf-8")):
            if t in paid:
                warnings.append(f"kit/{f.name} mentions {t}, which teams only get by paying (spoiler?)")
            elif t not in known and re.match(r"^[A-ZÑ]{1,4}\d*[+✕◆]?$", t):
                info.append(f"kit/{f.name}: code `{t}` is not a card, a sheet or a procedure")
    tokens = neutral.get("tokens_per_team")
    guide_files = sorted((L / "guide").glob("*.md"))
    engine = neutral.get("engine_sheets", True)
    if isinstance(engine, dict):
        engine = engine.get("kit", True) is not False or engine.get("guide", True) is not False
    if engine is False:
        # The case still carries its own copy of the rules: they must at least say its number of tokens.
        if tokens and not re.search(rf"\b{tokens}\s+fichas?\b|\b{tokens}\s+tokens?\b", kit_text):
            warnings.append(f"the kit never says '{tokens} fichas' (tokens_per_team is {tokens})")
    else:
        # The engine writes the rules and their figures (opencase/templates/); a figure written by hand in
        # the case's sheets will go stale the day the case or the defaults change it.
        defaults_file = Path(__file__).resolve().parents[3] / "opencase" / "defaults.yaml"
        defaults = load_yaml(defaults_file) if defaults_file.exists() else {}
        fig = {k: neutral.get(k, defaults.get(k)) for k in ("tokens_per_team", "alibi_tokens_per_team", "notice_minutes")}
        # The whole session the kit and the guide announce must fit the phases and the closing.
        phases = {**(defaults.get("phases") or {}), **(neutral.get("phases") or {})}
        closing = neutral.get("closing_minutes", defaults.get("closing_minutes")) or []
        session = neutral.get("session_minutes", defaults.get("session_minutes")) or []
        if len(closing) == 2 and len(session) == 2:
            low, high = sum(phases.values()) + closing[0], sum(phases.values()) + closing[1]
            if session[0] < low or session[1] < high:
                warnings.append(f"session_minutes is {session[0]}–{session[1]}, but the phases and closing_minutes "
                                f"add up to {low}–{high} minutes")
        alt = lambda values: "|".join(str(v) for v in values if v)  # noqa: E731
        hand = []
        if fig["alibi_tokens_per_team"]:
            hand.append((rf"\b(?:{fig['alibi_tokens_per_team']})\s+(?:fichas?\s+de\s+coartada|alibi\s+tokens?)\b", "alibi tokens"))
        if fig["tokens_per_team"]:
            hand.append((rf"\b(?:{fig['tokens_per_team']})\s+(?:fichas|tokens)\b", "tokens per team"))
        if fig["notice_minutes"]:
            hand.append((rf"\b(?:minutos?|min|minute)\s+(?:{alt(fig['notice_minutes'])})\b", "minute of a notice"))
        hand.append((r"\bresta\s+\d+\s+puntos?\b|\bcosts?\s+\d+\s+points?\b", "cost of a hint"))
        for f in kit_files + guide_files + sorted((L / "dossier").glob("AVISO*.md")):
            text = re.sub(r"<!--.*?-->", "", f.read_text(encoding="utf-8"), flags=re.S)
            for pattern, what in hand:
                for m in re.finditer(pattern, text, re.I):
                    warnings.append(f"{f.parent.name}/{f.name}: '{m.group(0)}' looks like a figure written by hand "
                                    f"({what}); the engine prints it from opencase/defaults.yaml and case.yaml")
                    break

    # Guide: codes in backticks that point nowhere
    for f in sorted((L / "guide").glob("*.md")):
        for t in tokens_in_ticks(f.read_text(encoding="utf-8")):
            base = t.split("-")[0] if t.startswith(("E", "DEC")) else t
            if t in known or base in known:
                continue
            if re.match(r"^[A-ZÑ]{1,4}\d+[+✕]?$|^E\d+", t):
                info.append(f"guide/{f.name}: code `{t}` is not a card, a sheet or a procedure (typo?)")

    # Acronyms: the exporter's own check (needs the exporter next to the skill; skipped if it is not there)
    sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
    try:
        from opencase.acronyms import check as check_acronyms
        from opencase.loader import CaseError, load_case
        from opencase.templates import sheets_for
        try:
            c = load_case(root, lang)
            warnings += check_acronyms(c, sheets_for(c, "kit", c.kit) if c.kit else [],
                                       sheets_for(c, "guide", c.guide) if c.guide else [])
        except CaseError as ex:
            errors.append(str(ex))
    except ImportError as ex:
        info.append(f"acronyms were not checked (the exporter could not be imported: {ex})")

    for e in errors:
        print("!! " + e)
    for w in warnings:
        print("!  " + w)
    for i in sorted(set(info)):
        print("·  " + i)
    print(f"Lint finished: {len(errors)} errors, {len(warnings)} warnings, {len(set(info))} notes "
          f"({len(suspects)} suspects, {len(cards)} cards, {len(dossier_files)} dossier sheets).")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
