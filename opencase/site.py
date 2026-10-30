"""Builds the website: python3 -m opencase.site [--out _site]

For every published case in cases/ (those without `published: false`) and every language it declares, the build
  1. exports the PDFs (the same ones as `export.py`),
  2. packs them into two zips: the teams' material (no solution) and the director's material,
  3. and writes cases.json, the list the web page reads to draw one card per case.

Then it assembles the site (the static files of site/, the fonts, the covers and the zips) in the
output folder, ready to publish. Every path in the page and in cases.json is relative, so the site works
the same from a local folder, from https://<user>.github.io/<repo>/ and from a preview.

The zips are reproducible: sorted entries and a fixed date, so the same PDFs give the same bytes.
"""
import argparse
import hashlib
import json
import shutil
import sys
import zipfile
from pathlib import Path
from types import SimpleNamespace

from .loader import CaseError, case_languages, read_yaml_file

ROOT = Path(__file__).resolve().parent.parent
ZIP_DATE = (1980, 1, 1, 0, 0, 0)
SITE_URL = "https://fr4j4.github.io/open-case/"

# What goes inside the readme of each zip, per language. A language without text uses English.
READMES = {
    "es": ("{title}\nOpen Case · {license}\nAutoría: {author}\n\n{what}\n\nMás casos y el código: {url}\n",
           {"teams": "Material de los equipos. No incluye la solución.",
            "director": "Material del director. CONTIENE LA SOLUCIÓN: no lo compartas con los equipos."}),
    "en": ("{title}\nOpen Case · {license}\nAuthor: {author}\n\n{what}\n\nMore cases and the code: {url}\n",
           {"teams": "Material for the teams. It does not include the solution.",
            "director": "Material for the director. IT CONTAINS THE SOLUTION: do not share it with the teams."}),
}


def main(argv=None):
    p = argparse.ArgumentParser(prog="python3 -m opencase.site",
                                description="Builds the Open Case website: PDFs, zips, cases.json and the page.")
    p.add_argument("--cases", default=str(ROOT / "cases"), help="folder with the cases (default: cases/)")
    p.add_argument("--out", default="_site", help="folder for the finished site (default: _site/)")
    p.add_argument("--only", help="build only these cases (folder names, comma separated)")
    p.add_argument("--pdf-dir", help="use PDFs already exported in this folder (output/<case>/<lang>/…) "
                                     "instead of exporting them again")
    p.add_argument("--color", action="store_true", help="full-colour PDFs instead of ink-saver mode")
    p.add_argument("--include-unpublished", action="store_true",
                   help="also build the cases that have `published: false` (to preview them locally)")
    p.add_argument("--check", action="store_true", help="only check the case metadata and the page, without PDFs")
    a = p.parse_args(argv)

    cases_dir = Path(a.cases)
    out = Path(a.out)
    wanted = {x.strip() for x in a.only.split(",")} if a.only else None
    folders = sorted(d for d in cases_dir.iterdir() if (d / "case.yaml").exists() and (not wanted or d.name in wanted))
    try:
        hidden = [d for d in folders if not is_published(d)]
    except CaseError as ex:
        print(f"Error: {ex}", file=sys.stderr)
        return 2
    if not a.include_unpublished:
        folders = [d for d in folders if d not in hidden]
        for d in hidden:
            print(f"skip  {d.name}  (published: false)")
    if not folders:
        print(f"Error: no published cases found in {cases_dir}", file=sys.stderr)
        return 2

    try:
        metas = [read_meta(d) for d in folders]
    except CaseError as ex:
        print(f"Error: {ex}", file=sys.stderr)
        return 2
    slugs = [m["slug"] for m in metas]
    if len(set(slugs)) != len(slugs):
        print("Error: two cases have the same site.slug", file=sys.stderr)
        return 2
    if a.check:
        for m in metas:
            print(f"ok  {m['slug']}  ({', '.join(m['languages'])})")
        return 0

    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    work = Path(a.pdf_dir) if a.pdf_dir else out.parent / ".site-work"
    entries = []
    for meta in metas:
        if not a.pdf_dir:
            status = export_case(meta, work, a.color)
            if status:
                return status
        entries.append(pack_case(meta, work, out))
    (out / "cases.json").write_text(json.dumps({"cases": entries}, ensure_ascii=False, indent=2, sort_keys=False) + "\n",
                                    encoding="utf-8")
    assemble_site(out)
    total = sum(f.stat().st_size for f in out.rglob("*") if f.is_file())
    print(f"Site ready: {out}/  ({len(entries)} cases, {total / 1e6:.1f} MB)")
    return 0


def is_published(folder):
    """A case is published unless its case.yaml says `published: false`."""
    value = read_yaml_file(folder / "case.yaml").get("published", True)
    if not isinstance(value, bool):
        raise CaseError("published must be true or false", folder / "case.yaml")
    return value


def read_meta(folder):
    """Everything the site needs to know about a case, from its case.yaml files."""
    neutral = read_yaml_file(folder / "case.yaml")
    site = neutral.get("site") or {}
    base, languages = case_languages(folder)
    where = folder / "case.yaml"
    for key in ("author", "license"):
        if not site.get(key):
            raise CaseError(f"site.{key} is missing", where)
    teams = neutral.get("teams") or []
    meta = {
        "folder": folder,
        "slug": site.get("slug") or folder.name,
        "author": site["author"],
        "license": site["license"],
        "cover": site.get("cover"),
        "version": site.get("version"),
        "date": str(site.get("date") or "") or None,
        "base": base,
        "languages": languages,
        "min_teams": int(site.get("min_teams", min(2, len(teams)) or 2)),
        "max_teams": len(teams) or None,
        "duration_minutes": pair(site.get("duration_minutes"), "duration_minutes", where),
        "players_per_team": pair(site.get("players_per_team", neutral.get("players_per_team")), "players_per_team", where),
        "texts": {},
    }
    if meta["cover"] and not (folder / meta["cover"]).exists():
        raise CaseError(f"site.cover points to a file that does not exist: {meta['cover']}", where)
    for lang in languages:
        lang_file = folder / "languages" / lang / "case.yaml"
        texts = read_yaml_file(lang_file)
        for key in ("title", "summary"):
            if not texts.get(key):
                raise CaseError(f"the field '{key}' is missing", lang_file)
        meta["texts"][lang] = {"title": texts["title"], "summary": " ".join(str(texts["summary"]).split()),
                               "cover_alt": texts.get("cover_alt") or ""}
        if meta["cover"] and not meta["texts"][lang]["cover_alt"]:
            raise CaseError("cover_alt is missing (the description of the cover image)", lang_file)
    return meta


def pair(value, name, where):
    """A number or a [min, max] pair, always returned as [min, max]."""
    if value is None:
        raise CaseError(f"site.{name} is missing", where)
    if isinstance(value, (int, float)):
        return [int(value), int(value)]
    if isinstance(value, (list, tuple)) and len(value) == 2 and value[0] <= value[1]:
        return [int(value[0]), int(value[1])]
    raise CaseError(f"site.{name} must be a number or [min, max]", where)


def export_case(meta, work, color):
    from .cli import run_language
    root = meta["folder"]
    for lang in meta["languages"]:
        args = SimpleNamespace(output=str(work), ink_saver=False if color else None, check=False, only=None, images=False)
        status = run_language(args, root, lang, meta["base"])
        if status:
            print(f"Error: exporting {root.name} [{lang}] failed", file=sys.stderr)
            return status
    return 0


def pack_case(meta, work, out):
    slug = meta["slug"]
    entry = {
        "slug": slug,
        "author": meta["author"],
        "license": meta["license"],
        "date": meta["date"],
        "min_teams": meta["min_teams"],
        "max_teams": meta["max_teams"],
        "duration_minutes": meta["duration_minutes"],
        "players_per_team": meta["players_per_team"],
        "base_language": meta["base"],
        "cover": None,
        "languages": {},
    }
    if meta["version"]:
        entry["version"] = meta["version"]
    if meta["cover"]:
        cover_dir = out / "covers"
        cover_dir.mkdir(exist_ok=True)
        src = meta["folder"] / meta["cover"]
        shutil.copyfile(src, cover_dir / f"{slug}{src.suffix.lower()}")
        entry["cover"] = f"covers/{slug}{src.suffix.lower()}"
    for lang in meta["languages"]:
        pdfs = work / meta["folder"].name / lang
        text = meta["texts"][lang]
        item = {"title": text["title"], "summary": text["summary"], "cover_alt": text["cover_alt"]}
        for kind, folder in (("teams", "teams"), ("director", "director")):
            files = sorted((pdfs / folder).glob("*.pdf"))
            if not files:
                raise SystemExit(f"Error: no PDFs in {pdfs / folder}. Export the case first (or drop --pdf-dir).")
            target = out / "downloads" / slug / lang / f"{slug}-{lang}-{kind}.zip"
            info = write_zip(target, f"{slug}-{lang}-{kind}", files, readme_for(meta, lang, kind), lang)
            item[f"{kind}_zip"] = {**info, "file": target.relative_to(out).as_posix(),
                                   "files": [f.name for f in files]}
        entry["languages"][lang] = item
    return entry


def readme_for(meta, lang, kind):
    template, what = READMES.get(lang, READMES["en"])
    return template.format(title=meta["texts"][lang]["title"], license=meta["license"], author=meta["author"],
                           what=what[kind], url=SITE_URL)


def write_zip(target, top, files, readme, lang):
    target.parent.mkdir(parents=True, exist_ok=True)
    readme_name = "LEEME.txt" if lang == "es" else "README.txt"
    members = [(readme_name, readme.encode("utf-8"))] + [(f.name, f.read_bytes()) for f in files]
    with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for name, data in sorted(members):
            zi = zipfile.ZipInfo(f"{top}/{name}", ZIP_DATE)
            zi.compress_type = zipfile.ZIP_DEFLATED
            zi.external_attr = 0o644 << 16
            z.writestr(zi, data, compresslevel=9)
    data = target.read_bytes()
    return {"bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}


def assemble_site(out):
    """Copies the static page, the fonts it uses and a marker so GitHub Pages serves everything as it is."""
    site = ROOT / "site"
    if not (site / "index.html").exists():
        raise SystemExit("Error: site/index.html is missing")
    for item in sorted(site.iterdir()):
        if item.name == "fonts":
            continue
        if item.is_dir():
            shutil.copytree(item, out / item.name, dirs_exist_ok=True)
        else:
            shutil.copyfile(item, out / item.name)
    fonts = out / "fonts"
    shutil.copytree(ROOT / "design" / "fonts", fonts, ignore=shutil.ignore_patterns("licenses"))
    shutil.copytree(site / "fonts", fonts, dirs_exist_ok=True)
    (out / ".nojekyll").write_text("", encoding="utf-8")


if __name__ == "__main__":
    sys.exit(main())
