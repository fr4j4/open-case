"""Command line: python3 export.py cases/<case> [options]"""
import argparse
import shutil
import sys
import time
from pathlib import Path

from .loader import CaseError, case_languages, compare_languages, load_case
from .documents import build_documents, ink_saver
from .markup import use_strings


def main(argv=None):
    p = argparse.ArgumentParser(prog="export", description="Exports an Open Case case to print-ready PDFs.")
    p.add_argument("case", help="the case folder, for example cases/chupacabras-labranza")
    p.add_argument("--output", default="output", help="folder for the PDFs (default: output/)")
    p.add_argument("--lang", help="language to export (default: the case's base language); "
                                  "'all' exports every language of the case")
    p.add_argument("--only", help="export only some documents, separated by commas: kit, envelopes, dossier, guide, "
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
        results = export(docs, out / "html", out, paper_height_mm=height, images=a.images)
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
        for h in r["long_sheets"]:
            print(f"    · {h['code'].strip()} takes {h['pages']} pages")
    (out / case.t("readme_name")).write_text(
        case.t("readme", title=case.title, date=time.strftime("%Y-%m-%d"),
               mode=case.t("readme_ink_saver" if saver else "readme_color")), encoding="utf-8")
    print(f"Done in {time.time() - start:.0f} s: {out}/")
    return 1 if problems else 0
