"""Snapshots of what the exporter prints, to see what a change does to the PDFs.

    python3 tools/snapshot.py take [REF]                 snapshot of a git ref (default: the working tree)
    python3 tools/snapshot.py compare BASE [HEAD]        snapshot both and report the differences
    python3 tools/snapshot.py compare DIR_A DIR_B        compare two snapshots already taken

A snapshot holds, for every case and language at that ref, and for every document:
  - the total number of pages of the PDF;
  - the visible text of each sheet (by its code: E08, 01-mision...) and of each answer card, with
    the pages each sheet takes;
  - the cards that do not fit even with the smallest type, and the ones that needed smaller type;
  - the HTML, normalised (no absolute paths, one block per line).

The ref is exported with its own exporter (its opencase/ and its cases/), and measured with this
file's browser routine, so both sides of a comparison use the same ruler. Snapshots go to
.snapshots/<ref>-<commit>/ (or .snapshots/worktree/); the comparison report is printed in Markdown,
ready to paste into a pull request, and saved as .snapshots/compare.md (the two snapshots it
compares stay in .snapshots/compare-base/ and .snapshots/compare-head/).

Cases that fail to build at a ref are reported, not fatal. Needs the same packages as export.py.
"""
import argparse
import difflib
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SNAPSHOTS = REPO / ".snapshots"
FORMAT = 1

# Runs inside the exported tree (its cwd and sys.path), with that tree's opencase package.
# argv: output folder for the raw HTML, JSON list of case folders (empty: every case).
RUNNER = r"""
import json, sys, traceback
from pathlib import Path
from opencase.loader import case_languages, load_case
from opencase.markup import use_strings
from opencase.documents import build_documents

out = Path(sys.argv[1])
cases = json.loads(sys.argv[2]) or sorted(str(p.parent) for p in Path("cases").glob("*/case.yaml"))
manifest = []
for root in cases:
    name = Path(root).name
    try:
        base, langs = case_languages(root)
    except Exception as ex:
        manifest.append({"case": name, "lang": None, "error": str(ex)})
        continue
    for lang in langs:
        entry = {"case": name, "lang": lang, "documents": []}
        try:
            case = load_case(root, lang)
            use_strings(case.strings)
            entry["paper"] = case.paper
            entry["warnings"] = list(case.warnings)
            for d in build_documents(case):
                folder = out / name / lang
                folder.mkdir(parents=True, exist_ok=True)
                (folder / f"{d.file}.html").write_text(d.html, encoding="utf-8")
                entry["documents"].append({"file": d.file, "key": d.key, "folder": d.folder, "kind": d.kind})
        except Exception as ex:
            entry["error"] = f"{type(ex).__name__}: {ex}"
        manifest.append(entry)
(out / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=1), encoding="utf-8")
"""

# Every printed unit of a document: the sheets (article.oc-hoja), each answer card with a code, and
# the card sheets without coded cards (badges, tokens, backs). Sheets also report the pages they take.
JS_UNITS = """
(pageHeight) => {
  const units = [];
  let n = 0;
  for (const el of document.querySelectorAll('article.oc-hoja, section.oc-pliego')) {
    n += 1;
    if (el.matches('section.oc-pliego')) {
      const cards = el.querySelectorAll('.oc-tarjeta[data-code]');
      if (cards.length) {
        for (const c of cards) units.push({key: 'card ' + c.dataset.code, text: c.innerText, pages: null});
      } else {
        units.push({key: 'card sheet ' + n, text: el.innerText, pages: null});
      }
      continue;
    }
    const code = el.querySelector('.oc-membrete .oc-codigo');
    const key = (code && code.textContent.trim()) || el.id || (el.classList.contains('oc-tapa') ? 'cover' : 'sheet ' + n);
    const height = el.getBoundingClientRect().height;
    units.push({key: key, text: el.innerText, pages: Math.ceil((height - 2) / pageHeight)});
  }
  return units;
}
"""

_BLOCK = re.compile(r"(?=<(?:article|section|header|div|p|h[1-6]|table|thead|tbody|tr|ul|ol|li|figure|img|svg|main|style|link)\b)")


def normalize_html(html, root):
    """The HTML without the absolute path of the repository, one block element per line, so that
    it is the same on every machine and a diff shows what changed."""
    html = html.replace(Path(root).resolve().as_uri(), "{REPO}")
    return _BLOCK.sub("\n", html).strip() + "\n"


def normalize_text(text):
    lines = [re.sub(r"[ \t ]+", " ", l).strip() for l in text.replace("\r", "").split("\n")]
    return re.sub(r"\n{3,}", "\n\n", "\n".join(lines)).strip()


# --- Taking a snapshot -------------------------------------------------------------------

def git(*args, cwd=REPO):
    r = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True)
    if r.returncode:
        raise SystemExit(f"Error: git {' '.join(args)}: {r.stderr.strip()}")
    return r.stdout.strip()


def resolve_ref(ref):
    """The commit of a ref, trying origin/<ref> when there is no local branch with that name."""
    for candidate in (ref, f"origin/{ref}"):
        r = subprocess.run(["git", "rev-parse", "--verify", "--quiet", f"{candidate}^{{commit}}"],
                           cwd=REPO, capture_output=True, text=True)
        if r.returncode == 0:
            return r.stdout.strip()
    raise SystemExit(f"Error: '{ref}' is not a branch, tag or commit of this repository "
                     f"(try `git fetch origin {ref}`)")


def extract(commit, dest):
    proc = subprocess.Popen(["git", "archive", "--format=tar", commit], cwd=REPO, stdout=subprocess.PIPE)
    with tarfile.open(fileobj=proc.stdout, mode="r|") as tar:
        try:
            tar.extractall(dest, filter="data")
        except TypeError:  # Python < 3.12
            tar.extractall(dest)
    if proc.wait():
        raise SystemExit(f"Error: git archive {commit} failed")


def take(ref=None, out=None, cases=(), report=print):
    """Exports and measures every case at `ref` (None: the working tree). Returns the snapshot folder."""
    if ref:
        commit = resolve_ref(ref)
        label = re.sub(r"[^\w.-]+", "-", ref) + "-" + commit[:8]
    else:
        commit, label = git("rev-parse", "HEAD"), "worktree"
    out = Path(out) if out else SNAPSHOTS / label
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    with tempfile.TemporaryDirectory(prefix="oc-snapshot-") as tmp:
        tmp = Path(tmp)
        src = REPO
        if ref:
            src = tmp / "src"
            src.mkdir()
            extract(commit, src)
        raw = tmp / "html"
        raw.mkdir()
        report(f"Building {ref or 'the working tree'} ({commit[:8]})...")
        r = subprocess.run([sys.executable, "-c", RUNNER, str(raw), json.dumps(list(cases))],
                           cwd=src, capture_output=True, text=True,
                           env={**_env(), "PYTHONPATH": str(src)})
        if r.returncode:
            raise SystemExit(f"Error: the exporter at {ref or 'the working tree'} failed:\n{r.stderr}")
        manifest = json.loads((raw / "manifest.json").read_text(encoding="utf-8"))
        report("Measuring in the browser...")
        _measure(manifest, raw, src, out, tmp, report)
    meta = {"format": FORMAT, "ref": ref or "working tree", "commit": commit,
            "dirty": not ref and bool(git("status", "--porcelain", "--", "opencase", "cases", "design")),
            "entries": manifest}
    (out / "snapshot.json").write_text(json.dumps(meta, ensure_ascii=False, indent=1), encoding="utf-8")
    report(f"Snapshot: {out.relative_to(REPO) if out.is_relative_to(REPO) else out}")
    return out


def _env():
    return {k: v for k, v in os.environ.items() if k != "PYTHONPATH"}


def _measure(manifest, raw, src, out, tmp, report):
    sys.path.insert(0, str(REPO))
    from opencase.pdf import JS_FIT_CARDS, JS_WAIT, MM, open_browser
    from playwright.sync_api import sync_playwright
    from pypdf import PdfReader

    margin = 14
    with sync_playwright() as pw:
        browser, name = open_browser(pw)
        report(f"  browser: {name}")
        page = browser.new_context(viewport={"width": 900, "height": 1200}, device_scale_factor=1).new_page()
        for entry in manifest:
            if entry.get("error"):
                report(f"  ! {entry['case']} [{entry.get('lang')}]: {entry['error']}")
                continue
            page_height = ((297 if entry.get("paper") == "a4" else 279) - 2 * margin) * MM
            for d in entry["documents"]:
                html_path = raw / entry["case"] / entry["lang"] / f"{d['file']}.html"
                folder = out / entry["case"] / entry["lang"]
                folder.mkdir(parents=True, exist_ok=True)
                html = normalize_html(html_path.read_text(encoding="utf-8"), src)
                (folder / f"{d['file']}.html").write_text(html, encoding="utf-8")
                d["html_sha256"] = hashlib.sha256(html.encode("utf-8")).hexdigest()

                page.emulate_media(media="print")
                page.set_viewport_size({"width": round((216 - 2 * margin) * MM), "height": 1200})
                page.goto(html_path.as_uri(), wait_until="load")
                d["broken_images"] = [Path(b).name for b in page.evaluate(JS_WAIT)]
                fits = page.evaluate(JS_FIT_CARDS)
                d["overflow"] = [f["code"] for f in fits if f["status"] == "overflow"]
                d["smaller_type"] = {f["code"]: f["status"] for f in fits if f["status"] != "overflow"}
                units = page.evaluate(JS_UNITS, page_height)
                pdf = tmp / "page.pdf"
                page.pdf(path=str(pdf), prefer_css_page_size=True, print_background=True)
                d["pages"] = len(PdfReader(str(pdf)).pages)

                seen = {}
                d["units"] = []
                with open(folder / f"{d['file']}.txt", "w", encoding="utf-8") as f:
                    for u in units:
                        seen[u["key"]] = seen.get(u["key"], 0) + 1
                        key = u["key"] + (f" #{seen[u['key']]}" if seen[u["key"]] > 1 else "")
                        text = normalize_text(u["text"])
                        d["units"].append({"key": key, "pages": u["pages"],
                                           "sha256": hashlib.sha256(text.encode("utf-8")).hexdigest()})
                        f.write(f"===== {key}" + (f" ({u['pages']} pages)" if u["pages"] else "") + f" =====\n{text}\n\n")
        browser.close()


# --- Comparing two snapshots ----------------------------------------------------------------

def load(folder):
    folder = Path(folder)
    meta = json.loads((folder / "snapshot.json").read_text(encoding="utf-8"))
    docs, errors = {}, {}
    for entry in meta["entries"]:
        where = f"{entry['case']}/{entry.get('lang')}"
        if entry.get("error"):
            errors[where] = entry["error"]
            continue
        for d in entry["documents"]:
            docs[(entry["case"], entry["lang"], d["file"])] = d
    return meta, docs, errors


def read_units(folder, case, lang, file):
    """{key: text} of a document of a snapshot."""
    text = (Path(folder) / case / lang / f"{file}.txt").read_text(encoding="utf-8")
    units = {}
    for m in re.finditer(r"^===== (.+?)(?: \(\d+ pages\))? =====\n(.*?)(?=^===== |\Z)", text, re.M | re.S):
        units[m.group(1)] = m.group(2).rstrip("\n")
    return units


def compare(a_dir, b_dir, html=False):
    """Markdown report of what changes from snapshot a to snapshot b, and whether anything changed."""
    a_meta, a_docs, a_err = load(a_dir)
    b_meta, b_docs, b_err = load(b_dir)

    def name(meta):
        dirty = " + uncommitted changes" if meta.get("dirty") else ""
        return f"`{meta['ref']}` ({meta['commit'][:8]}{dirty})"

    out = [f"## What changes in the PDFs: {name(a_meta)} → {name(b_meta)}", ""]
    changed = False
    for where in sorted(set(a_err) | set(b_err)):
        if a_err.get(where) != b_err.get(where):
            changed = True
        if where in b_err:
            out.append(f"- ⚠️ **{where}** does not build at {name(b_meta)}: {b_err[where]}")
        elif where in a_err:
            out.append(f"- **{where}** did not build at {name(a_meta)}: {a_err[where]}")

    rows, details = [], []
    for key in sorted(set(a_docs) | set(b_docs)):
        case, lang, file = key
        label = f"{case}/{lang} · {file}"
        a, b = a_docs.get(key), b_docs.get(key)
        if not a or not b:
            changed = True
            rows.append(f"| {label} | {'new' if b else 'removed'} | {b['pages'] if b else a['pages']} | | |")
            continue
        pages = f"{a['pages']}" if a["pages"] == b["pages"] else f"**{a['pages']} → {b['pages']}**"
        a_units = {u["key"]: u for u in a["units"]}
        b_units = {u["key"]: u for u in b["units"]}
        text_changed = [k for k in b_units if k in a_units and a_units[k]["sha256"] != b_units[k]["sha256"]]
        added = [k for k in b_units if k not in a_units]
        removed = [k for k in a_units if k not in b_units]
        moved = not (added or removed) and list(a_units) != list(b_units)
        longer = [f"{k} ({a_units[k]['pages']} → {b_units[k]['pages']})" for k in b_units
                  if k in a_units and a_units[k]["pages"] != b_units[k]["pages"]]
        new_overflow = sorted(set(b["overflow"]) - set(a["overflow"]))
        fixed_overflow = sorted(set(a["overflow"]) - set(b["overflow"]))
        type_changes = [f"{c} ({a['smaller_type'].get(c, 'normal')} → {b['smaller_type'].get(c, 'normal')})"
                        for c in sorted(set(a["smaller_type"]) | set(b["smaller_type"]))
                        if a["smaller_type"].get(c) != b["smaller_type"].get(c) and c not in b["overflow"]]
        html_changed = a["html_sha256"] != b["html_sha256"]
        if not (html_changed or a["pages"] != b["pages"] or text_changed or added or removed or moved
                or longer or new_overflow or fixed_overflow or type_changes):
            continue
        changed = True
        sheets = ", ".join(f"`{k}`" for k in text_changed[:12]) + (" …" if len(text_changed) > 12 else "")
        rows.append(f"| {label} | {pages} | {sheets or '—'} | {len(added)} / {len(removed)} | "
                    f"{'yes' if html_changed else 'no'} |")

        notes = []
        if moved:
            notes.append("- the order of the sheets changed")
        if added:
            notes.append("- new: " + ", ".join(f"`{k}`" for k in added))
        if removed:
            notes.append("- removed: " + ", ".join(f"`{k}`" for k in removed))
        if longer:
            notes.append("- pages per sheet: " + ", ".join(longer))
        if new_overflow:
            notes.append("- ⚠️ cards that no longer fit: " + ", ".join(new_overflow))
        if fixed_overflow:
            notes.append("- cards that fit now: " + ", ".join(fixed_overflow))
        if type_changes:
            notes.append("- card type size: " + ", ".join(type_changes))
        if html_changed and not (text_changed or added or removed):
            notes.append("- only the HTML changed (classes or structure), not the visible text")
        diff = []
        if text_changed or added or removed:
            at, bt = read_units(a_dir, *key), read_units(b_dir, *key)
            for k in [k for k in b_units if k in text_changed or k in added] + removed:
                diff += [f"@@@@ {k}"] + list(difflib.unified_diff(
                    at.get(k, "").split("\n"), bt.get(k, "").split("\n"), lineterm="", n=1))[2:]
        if html and html_changed:
            ah = (Path(a_dir) / case / lang / f"{file}.html").read_text(encoding="utf-8").split("\n")
            bh = (Path(b_dir) / case / lang / f"{file}.html").read_text(encoding="utf-8").split("\n")
            diff += ["@@@@ HTML"] + list(difflib.unified_diff(ah, bh, lineterm="", n=1))[2:]
        body = ["\n".join(notes)] if notes else []
        if diff:
            body.append("```diff\n" + "\n".join(diff) + "\n```")
        details.append(f"<details><summary><b>{label}</b></summary>\n\n" + "\n\n".join(body) + "\n\n</details>")

    if rows:
        out += ["| Document | Pages | Sheets whose text changes | New / removed | HTML |",
                "|---|---|---|---|---|", *rows, "", *details]
    elif not changed:
        out.append("No differences: same text, same pages and same HTML in every document.")

    overflow = sorted(f"{case}/{lang} · {c}" for (case, lang, _), d in b_docs.items() for c in d["overflow"])
    out += ["", "**Cards that do not fit at " + name(b_meta) + ":** " + (", ".join(overflow) if overflow else "none")]
    return "\n".join(out) + "\n", changed


# --- Command line ----------------------------------------------------------------------------

def _snapshot_of(arg, cases, side):
    """A snapshot folder given as is, or a git ref ('' or None: the working tree) to snapshot now
    in .snapshots/compare-<side>/."""
    if arg and (Path(arg) / "snapshot.json").exists():
        return Path(arg)
    return take(arg or None, SNAPSHOTS / f"compare-{side}", cases)


def main(argv=None):
    p = argparse.ArgumentParser(prog="snapshot", description=__doc__.split("\n\n")[0])
    sub = p.add_subparsers(dest="command", required=True)
    t = sub.add_parser("take", help="snapshot a git ref (default: the working tree)")
    t.add_argument("ref", nargs="?", help="branch, tag or commit; omit it for the working tree")
    t.add_argument("--out", help="folder for the snapshot (default: .snapshots/<ref>-<commit>)")
    c = sub.add_parser("compare", help="report what changes between two refs or two snapshot folders")
    c.add_argument("base", help="git ref or snapshot folder, for example development")
    c.add_argument("head", nargs="?", default="", help="git ref or snapshot folder (default: the working tree)")
    c.add_argument("--html", action="store_true", help="also show the diff of the normalised HTML")
    c.add_argument("--strict", action="store_true", help="exit with status 1 when anything changes")
    c.add_argument("--report", default=str(SNAPSHOTS / "compare.md"), help="where to save the report")
    for s in (t, c):
        s.add_argument("--case", action="append", default=[],
                       help="only this case folder (repeatable), for example cases/chupacabras-labranza")
    a = p.parse_args(argv)
    if a.command == "take":
        take(a.ref, a.out, a.case)
        return 0
    base = _snapshot_of(a.base, a.case, "base")
    head = _snapshot_of(a.head, a.case, "head")
    text, changed = compare(base, head, html=a.html)
    Path(a.report).parent.mkdir(parents=True, exist_ok=True)
    Path(a.report).write_text(text, encoding="utf-8")
    print()
    print(text)
    print(f"(saved in {a.report})")
    return 1 if (changed and a.strict) else 0


if __name__ == "__main__":
    sys.exit(main())
