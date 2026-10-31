"""Checks that what the exporter prints matches the print plan, in a real browser.

    python3 tools/check_print.py                      every case
    python3 tools/check_print.py cases/<case> ...     only these cases
    python3 tools/check_print.py --teams 2            as exported with --teams 2

For every case and language it exports the PDFs to a temporary folder and checks:
  1. every PDF has the pages the print plan says (opencase/printing.py), which is what the guide's
     table and the README tell the director to print;
  2. no sheet of the kit, the envelopes or the Evidence file fills more than 95 % of the pages it
     declares (`pages: N` in its front matter, 1 by default): about two lines of room, because the
     same text comes out a little taller on another computer. In the guide this is only a warning.

The reference is the browser of the CI (Playwright's Chromium), not each one's Chrome: set
OPENCASE_CHROMIUM to compare locally. Cases with `published: false` only warn. Exit status 1 when a
published case fails.
"""
import argparse
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from opencase import printing  # noqa: E402
from opencase.cli import use_teams  # noqa: E402
from opencase.documents import build_documents  # noqa: E402
from opencase.loader import CaseError, case_languages, load_case, read_yaml_file  # noqa: E402
from opencase.markup import use_strings  # noqa: E402


def check(root, lang, out, teams=None, limit=printing.SHEET_LIMIT, report=print):
    """(errors, warnings) of one case and language."""
    from opencase.pdf import count_pages, export
    case = load_case(root, lang)
    if teams is not None:
        use_teams(case, teams)
    use_strings(case.strings)
    docs = build_documents(case)
    plan = {i.file: i for i in printing.plan(case)}
    results = export(docs, out / "html", out, paper_height_mm=297 if case.paper == "a4" else 279,
                     report=lambda *_: None)
    errors, warnings = [], []
    for r in results:
        doc = r["doc"]
        pages = count_pages(r["pdf"])
        item = plan.get(doc.file)
        if item is None:
            errors.append(f"{doc.file}: the print plan does not list it")
        elif pages != item.pages:
            (errors if doc.strict_fit else warnings).append(
                f"{doc.file}: the PDF has {pages} pages but the print plan says {item.pages}")
        for h in r["sheets"]:
            where = f"{doc.file} · {h['code'] or h['id']}"
            declared = "its page" if h["declared"] == 1 else f"its {h['declared']} pages"
            if h["pages"] > h["declared"]:
                msg = (f"{where} takes {h['pages']} pages but declares {h['declared']}: shorten it, or write "
                       f"pages: {h['pages']} in its front matter")
            elif h["fill"] > limit:
                msg = f"{where} fills {h['fill']:.0%} of {declared} (the limit is {limit:.0%}): shorten it"
            else:
                continue
            (errors if doc.strict_fit else warnings).append(msg)
    missing = set(plan) - {r["doc"].file for r in results}
    errors += [f"{f}: the print plan lists it, but it was not exported" for f in sorted(missing)]
    return errors, warnings


def main(argv=None):
    p = argparse.ArgumentParser(prog="check_print", description=__doc__.split("\n\n")[0])
    p.add_argument("cases", nargs="*", help="case folders (default: every case in cases/)")
    p.add_argument("--teams", type=int, help="check the export for the first N teams")
    p.add_argument("--limit", type=float, default=printing.SHEET_LIMIT, help="the most a sheet may fill (0.95)")
    a = p.parse_args(argv)
    roots = [Path(c) for c in a.cases] or sorted(q.parent for q in (REPO / "cases").glob("*/case.yaml"))
    status = 0
    with tempfile.TemporaryDirectory(prefix="oc-print-") as tmp:
        for root in roots:
            published = (read_yaml_file(root / "case.yaml") or {}).get("published", True) is not False
            for lang in case_languages(root)[1]:
                label = f"{root.name} [{lang}]"
                try:
                    errors, warnings = check(root, lang, Path(tmp) / root.name / lang, a.teams, a.limit)
                except CaseError as ex:
                    errors, warnings = [str(ex)], []
                if not errors and not warnings:
                    print(f"== {label}: every PDF matches the print plan and every sheet has room")
                    continue
                print(f"== {label}")
                for w in warnings:
                    print(f"  · {w}")
                for e in errors:
                    print(f"  ! {e}")
                if errors and published:
                    status = 1
                elif errors:
                    print(f"  (not published yet: these errors do not fail the check)")
    return status


if __name__ == "__main__":
    sys.exit(main())
