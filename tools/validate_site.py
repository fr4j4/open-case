"""Checks a built site (the folder made by `python3 -m opencase.site`).

    python3 tools/validate_site.py _site

It verifies that every local link and image of the pages exists, that every zip in cases.json is
there with the size and hash it declares, that the teams' zips carry only the files of the teams'
folder (the director's PDFs hold the solution), and that every path is relative, so the site works
under /open-case/ as well as at the root.
"""
import hashlib
import json
import re
import sys
import zipfile
from pathlib import Path
from urllib.parse import unquote, urlparse


def main(argv):
    site = Path(argv[1] if len(argv) > 1 else "_site")
    problems = []

    def bad(msg):
        problems.append(msg)

    pages = sorted(site.rglob("*.html"))
    if not pages:
        bad("no pages found")
    for page in pages:
        text = page.read_text(encoding="utf-8")
        for attr, ref in re.findall(r'\b(href|src)="([^"]*)"', text):
            check_ref(site, page, attr, ref, bad)
    for css in sorted(site.rglob("*.css")):
        for ref in re.findall(r"url\(([^)]+)\)", css.read_text(encoding="utf-8")):
            ref = ref.strip("'\" ")
            if not ref.startswith(("data:", "#")):
                check_ref(site, css, "url", ref, bad)

    data_file = site / "cases.json"
    if not data_file.exists():
        bad("cases.json is missing")
    else:
        data = json.loads(data_file.read_text(encoding="utf-8"))
        if not data.get("cases"):
            bad("cases.json has no cases")
        for case in data.get("cases", []):
            validate_case(site, case, bad)

    if problems:
        print(f"{len(problems)} problem(s) in {site}:")
        for p in problems:
            print("  -", p)
        return 1
    print(f"{site}: ok ({len(pages)} pages, {len(data['cases'])} cases)")
    return 0


def check_ref(site, source, attr, ref, bad):
    if not ref or ref.startswith(("#", "mailto:", "data:", "http://", "https://")):
        return
    if ref.startswith("/"):
        bad(f"{source.relative_to(site)}: {attr}=\"{ref}\" is absolute; use a relative path")
        return
    path = unquote(urlparse(ref).path)
    if path and not (source.parent / path).exists():
        bad(f"{source.relative_to(site)}: {attr}=\"{ref}\" points to a file that does not exist")


def validate_case(site, case, bad):
    slug = case.get("slug", "?")
    for key in ("slug", "author", "license", "min_teams", "max_teams", "duration_minutes", "players_per_team", "languages"):
        if case.get(key) in (None, "", []):
            bad(f"{slug}: '{key}' is missing in cases.json")
    if case.get("cover") and not (site / case["cover"]).exists():
        bad(f"{slug}: the cover {case['cover']} does not exist")
    for lang, item in (case.get("languages") or {}).items():
        for key in ("title", "summary"):
            if not item.get(key):
                bad(f"{slug}/{lang}: '{key}' is missing")
        for kind in ("teams", "director"):
            info = item.get(f"{kind}_zip")
            if not info:
                bad(f"{slug}/{lang}: the {kind} zip is missing")
                continue
            zpath = site / info["file"]
            if not zpath.exists():
                bad(f"{slug}/{lang}: {info['file']} does not exist")
                continue
            blob = zpath.read_bytes()
            if len(blob) != info["bytes"] or hashlib.sha256(blob).hexdigest() != info["sha256"]:
                bad(f"{slug}/{lang}: {info['file']} does not match the size or hash in cases.json")
            try:
                names = zipfile.ZipFile(zpath).namelist()
            except zipfile.BadZipFile:
                bad(f"{slug}/{lang}: {info['file']} is not a valid zip")
                continue
            pdfs = sorted(Path(n).name for n in names if n.endswith(".pdf"))
            if pdfs != sorted(info["files"]):
                bad(f"{slug}/{lang}: the PDFs in {info['file']} are not the ones listed in cases.json")
        teams = set(item.get("teams_zip", {}).get("files", []))
        director = set(item.get("director_zip", {}).get("files", []))
        if teams & director:
            bad(f"{slug}/{lang}: a PDF is in both the teams' and the director's zip: {sorted(teams & director)}")


if __name__ == "__main__":
    sys.exit(main(sys.argv))
