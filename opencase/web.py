"""Compiles a case for the web: python3 -m opencase.web [cases/<case> ...] [--out _site]

The web app (site/play/) never reads YAML or Markdown. This module is the contract between the engine and
it: for every case and language it writes, in <out>/play/cases/<slug>/<lang>/<version>/,

  team.json       what the teams' devices may know: teams and tokens, suspects, the question menu, the menu of
                  procedures (without what they hand out), follow-ups with their condition, the envelopes
  director.json   what only the director's device may know: every card, what each procedure hands out, places,
                  witnesses, notices, hints and the score
  sheets/*.html   one page per sheet of the dossier and of the team kit (the <article> the PDFs print)
  cards/*.html    one page per card of cards.yaml; suspects/*.html one per suspect card
  assets/         the stylesheets, fonts, logos and photos those pages use
  manifest.json   the version (a hash of every other file), schema_version and the size of each file

and play/cases/index.json (which version is current) and play/strings/<lang>.json (the engine's words for
the app). Everything is drawn from the same data and functions as the PDFs; nothing is copied. The format
is described field by field in docs/web-format.md and validated by docs/web-schema/*.json.

Only the engine knows the game. The case adds no field for the web: a new case compiles as it is.
"""
import argparse
import hashlib
import json
import re
import shutil
import sys
from pathlib import Path

from . import cards as C
from . import confrontations, documents, followups, printing, procedures, templates, witnesses
from .components import Context
from .loader import CaseError, as_list, card_kind, case_languages, display_code, iter_cards, load_case, read_yaml_file
from .loader import read_yaml
from .markup import plain_text, use_strings
from .i18n import Strings

ROOT = Path(__file__).resolve().parent.parent
SCHEMA_VERSION = 4
SCHEMA_DIR = ROOT / "docs" / "web-schema"

# --- Names of files and of assets ---------------------------------------------------------------

def file_slug(code):
    """A file name made of a code: letters, digits, - and _ stay; anything else (B1+, B✕, E15·B) becomes
    _ and its code point in hex (4 digits; 6 after a second _ for the rare ones above U+FFFF), so two different
    codes never share a file and the name needs no escaping in a URL."""
    return re.sub(r"[^A-Za-z0-9\-]",
                  lambda m: "_%04x" % ord(m.group(0)) if ord(m.group(0)) <= 0xFFFF else "__%06x" % ord(m.group(0)), str(code))


class WebContext(Context):
    """Draws photos and logos from the version's own assets/ folder (the pages are one folder deep:
    sheets/X.html reads ../assets/...) and remembers which files that takes."""

    def __init__(self, case, repo_root):
        super().__init__(case, repo_root)
        self.assets = {}   # path inside the version folder -> source file

    def url(self, ref):
        src = self.path(ref)
        try:
            rel = src.relative_to(self.case.root)
        except ValueError:   # a file outside the case folder
            rel = Path("external") / src.name
        dest = f"assets/media/{rel.as_posix()}"
        self.assets[dest] = src
        return "../" + dest

    def design(self, ref):
        dest = f"assets/design/{ref}"
        self.assets[dest] = self.repo_root / "design" / ref
        return "../" + dest


def page(case, title, body, css):
    """A whole page for one sheet or card, to open on its own or inside an iframe."""
    links = "".join(f'<link rel="stylesheet" href="../{href}">' for href in css)
    from .markup import e
    return (f'<!doctype html><html lang="{e(case.get("language", "es"))}"><head><meta charset="utf-8">'
            f'<meta name="viewport" content="width=device-width,initial-scale=1"><title>{e(title)}</title>{links}'
            f'</head><body><main class="oc-mesa">{body}</main></body></html>')


# --- The case, as data -----------------------------------------------------------------------

def _text(value):
    return plain_text(str(value)) if value not in (None, "") else ""


def _sheet_entry(case, sheet, **extra):
    return {"id": sheet.id, "code": display_code(case, sheet.get("code", sheet.id)),
            "title": _text(sheet.get("title", "")), **extra}


def _case_info(case, slug):
    texts = read_yaml_file(case.lang_root / "case.yaml")
    return {"slug": slug, "language": case.lang, "title": case.title, "summary": " ".join(str(texts.get("summary", "")).split()),
            "paper": case.paper, "brand": str(case.get("brand", "Open Case"))}


def wildcards(case):
    """The code of the card that answers in the engine's name for each role (`role:` of a wildcard card in
    cards.yaml: no_findings, unavailable, nothing_to_add, confrontation_failed); null when the case has none."""
    out = {role: None for role in procedures.WILDCARD_ROLES}
    for c, g in iter_cards(case):
        role = c.get("role")
        if role is None:
            continue
        if role not in out:
            raise CaseError(f"card {c.get('code')}: the role '{role}' does not exist (use {', '.join(out)})",
                            case.lang_root / "cards.yaml")
        if out[role] is not None:
            raise CaseError(f"two cards have the role '{role}': {out[role]} and {c.get('code')}",
                            case.lang_root / "cards.yaml")
        out[role] = str(c["code"])
    return out


def rules(case):
    """What is needed to charge and give back tokens: the figures, the cost of each kind of request, the answers
    a director can give to each and whether they charge, and which procedures accept an alibi token or can be
    asked about for free. site/play/js/rules.js applies exactly this; tests/web/test_rules.py checks it."""
    f = case.figures
    costs = {k: f["costs"][k] for k in ("question", "witness", "confrontation", "follow_up")}
    requests = {}
    for kind, r in procedures.REQUESTS.items():
        requests[kind] = {"cost": costs[r["cost"]] if r["cost"] else None,
                          "answers": {name: {"charge": charge} for name, charge in r["answers"].items()}}
        if "unlock" in r:
            requests[kind]["unlock"] = r["unlock"]
    return {
        "tokens_per_team": f["tokens_per_team"],
        "alibi_tokens_per_team": f["alibi_tokens_per_team"],
        "costs": costs,
        "requests": requests,
        "wildcards": wildcards(case),
        "procedure_kinds": {k: dict(v) for k, v in procedures.KINDS.items()},
        "alibi_procedures": [p["code"] for p in case.procedures if p["alibi"]],
        "free_source_procedures": [p["code"] for p in case.procedures if p["source"]],
    }


def _teams(case):
    f = case.figures
    out = []
    for team in printing.teams(case):
        out.append({"id": str(team), "tokens": list(range(1, int(f["tokens_per_team"]) + 1)),
                    "alibi_tokens": [case.t("tokens.alibi_code", i=i) for i in range(1, int(f["alibi_tokens_per_team"]) + 1)]})
    return out


def _suspects(case, ctx):
    menu_codes = {}
    for c, g in iter_cards(case):
        if c.get("menu"):
            menu_codes.setdefault(str(c.get("suspect", g.get("suspect"))), []).append(str(c["code"]))
    out = []
    for s in case.suspects:
        letter = str(s["letter"])
        out.append({
            "letter": letter, "name": str(s["name"]), "short_name": str(s.get("short_name") or s["name"]),
            "role": _text(s.get("role", "")),
            "facts": [{"label": str(k), "value": _text(v)} for k, v in (s.get("facts") or {}).items()],
            "portrait": ctx.url(s["portrait"])[3:] if s.get("portrait") else None,
            "card": f"suspects/{file_slug(letter)}.html",
            "questions": menu_codes.get(letter, []),
            "confront": {"code": f"{letter}◆", "text": _text(s.get("confront", case.t("menu.confront_default")))},
        })
    return out


def _menu(case):
    out = []
    for c, g in iter_cards(case):
        if c.get("menu"):
            out.append({"code": str(c["code"]), "suspect": str(c.get("suspect", g.get("suspect"))),
                        "question": _text(c.get("menu_question") or c.get("question", ""))})
    return out


def _procedure_team(case, p):
    targets = []
    for t in p["targets"]:
        if t["key"] == "other" or t["suspect"] or any(pl["id"] == t["key"] for pl in case.locations):
            kind = "other" if t["key"] == "other" else ("suspect" if t["suspect"] else "place")
            targets.append({"key": t["key"], "label": t["label"], "kind": kind})
    return {"code": p["code"], "kind": p["kind"], "label": p["label"], "target": p["target"], "cost": p["cost"],
            "costs": p["costs"], "each": p["each"], "alibi": p["alibi"], "source": p["source"], "targets": targets}


def _result(r):
    return {"sheets": list(r["shown"]), "special": r["special"], "cost": r["cost"]}


def _procedure_director(case, p):
    out = {**_procedure_team(case, p), "short": p["short"], "note": p["note"],
           "gives": _result(p["gives"]) if p["gives"] else None}
    out["targets"] = [{"key": t["key"], "label": t["label"], "note": t["note"], "suspect": t["suspect"], **_result(t)}
                      for t in p["targets"]]
    return out


def _follow_ups_team(case):
    out = []
    for c, g in iter_cards(case):
        if card_kind(c, g) == followups.KIND:
            out.append({"code": str(c["code"]), "cost": case.figures["costs"]["follow_up"],
                        "unlocked_by": [display_code(case, x) for x in as_list(c.get("unlocked_by"))]})
    return out


def _sheet_files(case, kit):
    """Every sheet that gets a page: [(file, doc, sheet)], the kit's and the dossier's."""
    out = []
    for h in kit:
        out.append((f"sheets/kit-{file_slug(h.id)}.html", "kit", h))
    for sec in case.sections:
        for pid in sec.get("items", []) or []:
            out.append((f"sheets/{file_slug(pid)}.html", "dossier", case.dossier[pid]))
    return out


def _envelopes(case):
    out = []
    for num, secs in printing.envelope_sections(case).items():
        out.append({"number": num, "sections": [
            {"id": str(s.get("id", "")), "title": _text(s.get("title", "")), "note": _text(s.get("note", "")),
             "items": [{"id": pid, "code": display_code(case, case.dossier[pid].get("code", pid)),
                        "file": f"sheets/{file_slug(pid)}.html"} for pid in s.get("items", []) or []]}
            for s in secs]})
    return out


def _forms(case, kit):
    """The sheets of the team kit the team fills in and hands to the director (the accusation and the discard sheet):
    every kit sheet with a `fields` block or a work table, except the one with the schedule (the timeline is the team's
    own working sheet, not something it hands in). The app draws them as forms, in the order and with the labels of the
    sheet, and the director receives the answers."""
    out = []
    for h in kit:
        parts = []
        if any(b.type == "work-table" and (read_yaml(b.content, h.path, b.line) or {}).get("schedule") for b in h.blocks):
            continue
        for b in h.blocks:
            if b.type == "fields":
                data = read_yaml(b.content, h.path, b.line) or []
                items = []
                for c in data:
                    c = {"label": c} if isinstance(c, str) else c
                    items.append({"label": _text(c.get("label", "")), "type": "box" if c.get("type") == "box" else "line"})
                parts.append({"kind": "fields", "items": items})
            elif b.type == "work-table":
                data = read_yaml(b.content, h.path, b.line) or {}
                parts.append({"kind": "table", "columns": [_text(c) for c in data.get("columns", [])],
                              "rows": [_text(r) for r in data.get("rows", [])]})
        if parts:
            out.append({"id": h.id, "title": _text(h.get("title") or h.get("institution", "")),
                        "file": f"sheets/kit-{file_slug(h.id)}.html", "parts": parts})
    return out


def team_json(case, slug, ctx, kit):
    return {
        "schema_version": SCHEMA_VERSION, "kind": "team", "case": _case_info(case, slug),
        "figures": case.figures, "rules": rules(case), "teams": _teams(case),
        "suspects": _suspects(case, ctx), "menu": _menu(case), "follow_ups": _follow_ups_team(case),
        "procedures": [_procedure_team(case, p) for p in case.procedures],
        "envelopes": _envelopes(case),
        "forms": _forms(case, kit),
        "kit": [{"id": h.id, "title": _text(h.get("title") or h.get("institution", "")), "file": f}
                for f, doc, h in _sheet_files(case, kit) if doc == "kit"],
        "texts": {"title": case.title, "tagline": str(case.get("tagline", case.t("tagline")))},
    }


def _card_entry(case, c, g, extra, file):
    kind = card_kind(c, g)
    c2 = {**c, **extra} if extra else c
    return {
        "code": str(c["code"]), "type": kind, "file": file,
        "suspect": str(c.get("suspect", g.get("suspect"))) if c.get("suspect", g.get("suspect")) else None,
        "who": _text(c2.get("who") or g.get("who") or g.get("title", "")),
        "headline": _text(c2.get("headline", "")), "question": _text(c2.get("question", "")),
        "answer": _text(c2.get("answer", "")), "note": _text(c2.get("note", "")),
        "footer": _text(c2.get("footer", "")), "menu": bool(c.get("menu")),
        "attach": [display_code(case, a) for a in as_list(c.get("attach"))],
        "follow_up": [str(x) for x in as_list(c.get("follow_up"))],
        "unlocked_by": [display_code(case, x) for x in as_list(c.get("unlocked_by"))],
        "guide_note": _text(c.get("guide_note", "")),
        "opens_with": [{"all": r["all"], "any": r["any"], "none": r["none"], "held": r["held"],
                        "priority": r["priority"]} for r in confrontations.rules_of(case, c)],
    }


def director_json(case, slug, kit):
    extra = C.engine_fields(case)
    tctx = templates.context(case)
    cards = [_card_entry(case, c, g, extra.get(id(c)), f"cards/{file_slug(c['code'])}.html") for c, g in iter_cards(case)]
    sheets = []
    for sec in case.sections:
        for pid in sec.get("items", []) or []:
            sheets.append(_sheet_entry(case, case.dossier[pid], file=f"sheets/{file_slug(pid)}.html",
                                       section=str(sec.get("id", "")), envelope=sec.get("envelope")))
    return {
        "schema_version": SCHEMA_VERSION, "kind": "director", "case": _case_info(case, slug),
        "figures": case.figures, "rules": rules(case), "sheets": sheets, "cards": cards,
        "procedures": [_procedure_director(case, p) for p in case.procedures],
        "locations": [{"id": pl["id"], "name": pl["name"], "note": pl["note"], "sources": pl["sources"],
                       "procedures": pl["procedures"]} for pl in case.locations],
        "witnesses": [{"who": w["who"], "name": w["name"], "cards": w["cards"], "attach": w["attach"],
                       "appears_in": w["appears_in_shown"], "aliases": w["aliases"], "note": _text(w["note"])}
                      for w in tctx["witnesses"]],
        "follow_ups": [{"code": f["code"], "question": _text(f["question"]), "mothers": f["mothers"],
                        "unlocked_by": f["unlocked_by"], "attach": f["attach"], "note": _text(f["note"])}
                       for f in tctx["follow_ups"]],
        "notices": [{"n": r["n"], "code": r["code"], "kind": r["kind"], "headline": _text(r["headline"]),
                     "text": _text(r["answer"]), "minute": r["minute"]} for r in tctx["readings"]],
        "hints": [{"n": h["n"], "code": h["code"], "text": _text(h["answer"]), "penalty": h["penalty"]}
                  for h in tctx["hints"]],
        "score": {"points": dict(tctx["score"]),
                  "bonus": {"points": tctx["bonus"]["points"], "text": _text(tctx["bonus"]["text"])} if tctx["bonus"] else None,
                  "hint_penalties": list(case.figures["hint_penalties"] or [])},
    }


# --- Writing -----------------------------------------------------------------------------------

def _dump(data):
    return (json.dumps(data, ensure_ascii=False, separators=(",", ":")) + "\n").encode("utf-8")


def compile_case(case, slug):
    """Everything of one case in one language as {path inside the version folder: bytes}, without the manifest."""
    ctx = WebContext(case, documents.REPO_ROOT)
    kit = documents.kit_sheets(case)
    css = ["assets/design/open-case.css", "assets/design/export.css"]
    ctx.assets["assets/design/open-case.css"] = documents.REPO_ROOT / "design" / "open-case.css"
    ctx.assets["assets/design/export.css"] = documents.REPO_ROOT / "opencase" / "styles" / "export.css"
    extra_css = case.root / "styles.css"
    if extra_css.exists():
        ctx.assets["assets/design/case.css"] = extra_css
        css.append("assets/design/case.css")
    files = {}
    for file, doc, h in _sheet_files(case, kit):
        html = documents.render_sheet(case, h.id, ctx=ctx, doc=doc, kit=kit)
        files[file] = page(case, f"{_text(h.get('title') or h.id)} · {case.title}", html, css).encode("utf-8")
    extra = C.engine_fields(case)
    for c, g in iter_cards(case):
        html = C.render_card(case, c["code"], extra)
        files[f"cards/{file_slug(c['code'])}.html"] = page(case, f"{c['code']} · {case.title}", html, css).encode("utf-8")
    for s in case.suspects:
        html = C.suspect_card(s, case, ctx)
        files[f"suspects/{file_slug(s['letter'])}.html"] = page(case, f"{s['name']} · {case.title}", html, css).encode("utf-8")
    files["team.json"] = _dump(team_json(case, slug, ctx, kit))
    files["director.json"] = _dump(director_json(case, slug, kit))
    # The stylesheet's fonts, then everything the pages asked for.
    fonts = documents.REPO_ROOT / "design" / "fonts"
    for f in sorted(fonts.glob("*")):
        if f.is_file():
            ctx.assets[f"assets/design/fonts/{f.name}"] = f
    for dest, src in sorted(ctx.assets.items()):
        files[dest] = src.read_bytes()
    return files


def version_of(files):
    h = hashlib.sha256()
    for path in sorted(files):
        h.update(path.encode("utf-8") + b"\0" + hashlib.sha256(files[path]).digest())
    return h.hexdigest()[:12]


def write_case(case, slug, play):
    """Writes the version folder of one case and language under `play`; returns its entry for index.json."""
    files = compile_case(case, slug)
    version = version_of(files)
    manifest = {"schema_version": SCHEMA_VERSION, "version": version, "case": slug, "language": case.lang,
                "files": {p: len(b) for p, b in sorted(files.items())}}
    manifest["total_size"] = sum(manifest["files"].values())
    files["manifest.json"] = _dump(manifest)
    folder = play / "cases" / slug / case.lang / version
    if folder.exists():
        shutil.rmtree(folder)
    for path, data in files.items():
        dest = folder / path
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(data)
    return {"slug": slug, "language": case.lang, "version": version, "path": f"cases/{slug}/{case.lang}/{version}/",
            "size": manifest["total_size"]}


def write_strings(play, languages):
    """play/strings/<lang>.json: the engine's words for the app (the `web:` section of opencase/strings)."""
    folder = play / "strings"
    folder.mkdir(parents=True, exist_ok=True)
    for lang in sorted(languages):
        data = {"schema_version": SCHEMA_VERSION, "language": lang, "web": Strings.load(lang).data.get("web") or {}}
        (folder / f"{lang}.json").write_bytes(_dump(data))


def build_cases(folders, out, slugs=None):
    """Compiles the given case folders into <out>/play/. `slugs` maps a folder name to its site slug."""
    play = Path(out) / "play"
    for generated in ("cases", "strings"):          # only what this module writes: site/play/ also holds the app's own files
        if (play / generated).exists():
            shutil.rmtree(play / generated)
    entries, languages = [], set()
    for folder in folders:
        folder = Path(folder)
        base, langs = case_languages(folder)
        slug = (slugs or {}).get(folder.name) or (read_yaml_file(folder / "case.yaml").get("site") or {}).get("slug") or folder.name
        for lang in langs:
            case = load_case(folder, lang)
            use_strings(case.strings)
            for w in case.warnings:
                print(f"  ! {folder.name} [{lang}]: {w}", file=sys.stderr)
            entry = write_case(case, slug, play)
            entries.append(entry)
            languages.add(lang)
            print(f"web  {slug} [{lang}]  {entry['version']}  ({entry['size'] / 1e6:.1f} MB)")
    (play / "cases").mkdir(parents=True, exist_ok=True)
    (play / "cases" / "index.json").write_bytes(_dump({"schema_version": SCHEMA_VERSION, "cases": entries}))
    write_strings(play, languages)
    return entries


# --- The contract's fingerprint ----------------------------------------------------------------

def schema_fingerprint():
    """A hash of the JSON Schemas. tests/test_web.py fails when it differs from the one saved in
    docs/web-schema/fingerprint.json without a new SCHEMA_VERSION."""
    h = hashlib.sha256()
    for path in sorted(SCHEMA_DIR.glob("*.schema.json")):
        h.update(path.name.encode() + b"\0" + json.dumps(json.loads(path.read_text(encoding="utf-8")), sort_keys=True).encode())
    return h.hexdigest()


def main(argv=None):
    p = argparse.ArgumentParser(prog="python3 -m opencase.web",
                                description="Compiles cases for the web app: team.json, director.json, one page per sheet and card.")
    p.add_argument("cases", nargs="*", help="case folders (default: every published case in cases/)")
    p.add_argument("--out", default="_site", help="the site folder; the result goes in <out>/play/ (default: _site)")
    p.add_argument("--write-fingerprint", action="store_true",
                   help="save the hash of docs/web-schema/*.schema.json together with SCHEMA_VERSION (after bumping it)")
    a = p.parse_args(argv)
    if a.write_fingerprint:
        (SCHEMA_DIR / "fingerprint.json").write_text(
            json.dumps({"schema_version": SCHEMA_VERSION, "sha256": schema_fingerprint()}, indent=2) + "\n", encoding="utf-8")
        print(f"fingerprint saved for schema_version {SCHEMA_VERSION}")
        return 0
    try:
        if a.cases:
            folders = [Path(c) for c in a.cases]
        else:
            from .site import is_published
            folders = sorted(d for d in (ROOT / "cases").iterdir() if (d / "case.yaml").exists() and is_published(d))
        if not folders:
            print("Error: no cases to compile", file=sys.stderr)
            return 2
        entries = build_cases(folders, a.out)
    except CaseError as ex:
        print(f"Error: {ex}", file=sys.stderr)
        return 2
    print(f"Web ready: {Path(a.out) / 'play'}/  ({len(entries)} case versions)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
