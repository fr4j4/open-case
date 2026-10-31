"""Command line: python3 export.py cases/<case> [options]"""
import argparse
import shutil
import sys
import time
from pathlib import Path

from .loader import CaseError, case_languages, compare_languages, load_case
from .documents import build_documents, ink_saver
from .markup import use_strings
from . import printing
from .printing import SHEET_LIMIT


def main(argv=None):
    p = argparse.ArgumentParser(prog="export", description="Exports an Open Case case to print-ready PDFs.")
    p.add_argument("case", help="the case folder, for example cases/chupacabras-labranza")
    p.add_argument("--output", default="output", help="folder for the PDFs (default: output/)")
    p.add_argument("--lang", help="language to export (default: the case's base language); "
                                  "'all' exports every language of the case")
    p.add_argument("--only", help="export only some documents, separated by commas: kit, envelopes, evidence, guide, "
                                  "cards, card-backs, suspects, badges, tokens, requests, labels. "
                                  "Example: --only kit,envelopes")
    p.add_argument("--check", action="store_true",
                   help="only check the case files (and that translations match the base language), without making PDFs")
    ink = p.add_mutually_exclusive_group()
    ink.add_argument("--color", dest="ink_saver", action="store_false", default=None,
                     help="full-colour PDFs, with the backgrounds of sheets, cards and screens. By default the PDFs "
                          "come out in ink-saver mode: no backgrounds or large fills, with colour only in bands, "
                          "codes, stamps and text (can be set with ink_saver in case.yaml)")
    ink.add_argument("--ink-saver", dest="ink_saver", action="store_true",
                     help="force ink-saver mode even if case.yaml says ink_saver: false")
    p.add_argument("--images", action="store_true", help="also make one PNG per evidence sheet, to send through a chat")
    p.add_argument("--teams", type=int, metavar="N",
                   help="export for the first N teams of the case only (for example 2): fewer badges, tokens and "
                        "labels, and the print plan counts N copies. By default, every team in case.yaml")
    p.add_argument("--chat", action="store_true",
                   help="the Evidence file is sent as images through each team's chat group instead of printed: "
                        "the print plan counts 0 copies of it and the images are made (as with --images)")
    a = p.parse_args(argv)

    root = Path(a.case)
    try:
        base, languages = case_languages(root)
        wanted = languages if a.lang == "all" else [a.lang or base]
    except CaseError as ex:
        print(f"Error: {ex}", file=sys.stderr)
        sys.exit(2)

    status = 0
    for lang in wanted:
        status = max(status, run_language(a, root, lang, base))
    if status:
        sys.exit(status)


def run_language(a, root, lang, base):
    start = time.time()
    try:
        case = load_case(root, lang)
        if lang != base:
            problems = compare_languages(load_case(root, base), case)
            if problems:
                for pr in problems:
                    print(f"Error: {pr}", file=sys.stderr)
                return 2
        if a.ink_saver is not None:
            case.data["_ink_saver"] = a.ink_saver
        if getattr(a, "teams", None) is not None:
            use_teams(case, a.teams)
        if getattr(a, "chat", False):
            case.data["_chat"] = True
        use_strings(case.strings)
        docs = build_documents(case)
    except CaseError as ex:
        print(f"Error: {ex}", file=sys.stderr)
        return 2
    saver = ink_saver(case)
    print(f"Case: {case.title} [{lang}]  ({len(case.dossier)} dossier sheets, "
          f"{sum(len(g.get('cards') or []) for g in case.card_groups)} cards, {len(case.kit)} kit sheets, "
          f"{len(case.guide)} guide sheets)")
    print("  mode: ink saver (no backgrounds). Use --color for the full-colour version." if saver
          else "  mode: full colour, with backgrounds.")
    for w in case.warnings:
        print(f"  ! {w}")
    if a.check:
        print("Check finished." if not case.warnings else "Check finished, with warnings.")
        return 0

    if a.only:
        wanted = {x.strip() for x in a.only.split(",") if x.strip()}
        docs = [d for d in docs if d.key in wanted or d.key.split(":")[0] in wanted]
        if not docs:
            print("Error: --only does not match any document. Available: "
                  + ", ".join(sorted({d.key.split(":")[0] for d in build_documents(case)})), file=sys.stderr)
            return 2

    out = Path(a.output) / case.root.name / lang
    for sub in ("teams", "director"):
        if not a.only and (out / sub).exists():
            shutil.rmtree(out / sub)
    from .pdf import BrowserError, count_pages, export
    height = 297 if case.paper == "a4" else 279
    try:
        results = export(docs, out / "html", out, paper_height_mm=height, images=a.images or getattr(a, "chat", False))
    except BrowserError as ex:
        print(f"Error: {ex}", file=sys.stderr)
        return 3
    problems = 0
    for r in results:
        n = count_pages(r["pdf"])
        print(f"  {r['pdf'].relative_to(out)}  ({n} pages)" if n else f"  {r['pdf'].relative_to(out)}")
        for fit in r["fits"]:
            if fit["status"] == "overflow":
                problems += 1
                print(f"    ! card {fit['code']} does not fit even with the smallest type: split it into (1 of 2) and (2 of 2)")
        for h in r["sheets"]:
            if h["pages"] > h["declared"]:
                print(f"    ! {h['code']} takes {h['pages']} pages but declares {h['declared']}: shorten it, or write "
                      f"pages: {h['pages']} in its front matter")
            elif h["fill"] > SHEET_LIMIT:
                print(f"    · {h['code']} fills {h['fill']:.0%} of its {_pages(h['declared'])}: it may not fit on another "
                      "computer (tools/check_print.py)")
    (out / case.t("readme_name")).write_text(
        printing.readme(case, time.strftime("%Y-%m-%d"), case.t("readme_ink_saver" if saver else "readme_color")),
        encoding="utf-8")
    print(f"Done in {time.time() - start:.0f} s: {out}/")
    return 1 if problems else 0


def use_teams(case, n):
    """--teams N: the first N teams of the case. Everything that is per team (badges, tokens, labels, the
    columns of the control sheet, the copies in the print plan) follows."""
    teams = printing.teams(case)
    if not 1 <= n <= len(teams):
        raise CaseError(f"--teams {n}: the case has {len(teams)} teams ({', '.join(teams)}); use 1 to {len(teams)}")
    least = (case.get("site", {}) or {}).get("min_teams")
    if least and n < int(least):
        case.warnings.append(f"--teams {n}: the case is meant for at least {least} teams")
    case.data["teams"] = teams[:n]


def _pages(n):
    return "page" if n == 1 else f"{n} pages"
