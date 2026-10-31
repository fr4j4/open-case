"""The case compiled for the web (opencase/web.py): every sheet and card has its page, the pages are the ones the
PDFs print, team.json tells nothing the teams must not know, and the JSON follows docs/web-schema/.
The expected values of the Chupacabras are in tests/web_expected/."""
import json
import re
from pathlib import Path

import jsonschema
import pytest

from opencase import cards as C
from opencase import documents, followups, web, witnesses
from opencase.loader import as_list, card_kind, display_code, iter_cards, load_case, normalize_code
from opencase.markup import use_strings

REPO = Path(__file__).resolve().parent.parent
CASES = REPO / "cases"
EXPECTED = Path(__file__).resolve().parent / "web_expected"
CASE = "chupacabras-labranza"


def _case(name, lang="es"):
    case = load_case(CASES / name, lang)
    use_strings(case.strings)
    return case


@pytest.fixture(scope="module")
def site(tmp_path_factory):
    """The Chupacabras compiled once into a temporary site: (folder of the version, loaded case, out)."""
    out = tmp_path_factory.mktemp("web")
    entries = web.build_cases([CASES / CASE], out)
    entry = next(e for e in entries if e["language"] == "es")
    return out / "play" / entry["path"], _case(CASE), out


def _json(folder, name):
    return json.loads((folder / name).read_text(encoding="utf-8"))


def _article(html, sheet_id):
    m = re.search(rf'<article class="[^"]*" id="{re.escape(sheet_id)}"[^>]*>.*?</article>', html, re.S)
    assert m, f"no article {sheet_id}"
    return m.group(0)


def _normal(html, case):
    """The HTML of a sheet with its paths as the web pages write them, and the spaces between tags gone."""
    html = html.replace((documents.REPO_ROOT / "design").as_uri() + "/", "../assets/design/")
    html = html.replace(case.root.as_uri() + "/", "../assets/media/")
    return re.sub(r"\s+", " ", re.sub(r">\s+<", "><", html)).strip()


# --- Coverage ----------------------------------------------------------------------------------

def test_every_sheet_card_and_suspect_has_its_page_and_none_is_left_over(site):
    folder, case, _ = site
    kit = documents.kit_sheets(case)
    want_sheets = {f"kit-{web.file_slug(h.id)}.html" for h in kit}
    want_sheets |= {f"{web.file_slug(pid)}.html" for sec in case.sections for pid in sec.get("items", []) or []}
    assert {p.name for p in (folder / "sheets").iterdir()} == want_sheets
    want_cards = {f"{web.file_slug(c['code'])}.html" for c, g in iter_cards(case)}
    assert {p.name for p in (folder / "cards").iterdir()} == want_cards
    assert len(want_cards) == len(iter_cards(case)), "two cards would share a file"
    assert {p.name for p in (folder / "suspects").iterdir()} == {f"{web.file_slug(s['letter'])}.html" for s in case.suspects}


def test_the_files_the_json_names_exist(site):
    folder, case, _ = site
    team, director = _json(folder, "team.json"), _json(folder, "director.json")
    files = [i["file"] for e in team["envelopes"] for s in e["sections"] for i in s["items"]]
    files += [k["file"] for k in team["kit"]] + [s["card"] for s in team["suspects"]]
    files += [s["file"] for s in director["sheets"]] + [c["file"] for c in director["cards"]]
    assert files and all((folder / f).is_file() for f in files)
    # the envelopes name every sheet the PDFs put in them, by code
    in_envelopes = {i["id"] for e in team["envelopes"] for s in e["sections"] for i in s["items"]}
    assert in_envelopes == {pid for sec in case.sections if sec.get("envelope") is not None for pid in sec["items"]}


def test_the_manifest_lists_every_file_with_its_size(site):
    folder, _, _ = site
    manifest = _json(folder, "manifest.json")
    on_disk = {p.relative_to(folder).as_posix(): p.stat().st_size for p in folder.rglob("*") if p.is_file()}
    on_disk.pop("manifest.json")
    assert manifest["files"] == on_disk
    assert manifest["version"] in str(folder)
    assert manifest["total_size"] == sum(on_disk.values())


def test_the_index_and_the_strings_are_published(site):
    _, _, out = site
    index = _json(out / "play" / "cases", "index.json")
    assert [(e["slug"], e["language"]) for e in index["cases"]] == [(CASE, "es")]
    assert (out / "play" / index["cases"][0]["path"] / "team.json").is_file()
    words = _json(out / "play" / "strings", "es.json")["web"]      # each phase adds its own subsection (web.team, web.director…)
    assert {"team", "director"} <= set(words)


# --- Fidelity ----------------------------------------------------------------------------------

def test_each_sheet_page_is_the_sheet_the_pdf_prints(site):
    folder, case, _ = site
    docs = documents.build_documents(case)
    printed = "".join(d.html for d in docs if d.key in ("kit", "evidence") or d.key.startswith("envelopes"))
    kit = documents.kit_sheets(case)
    checked = 0
    for file, doc, h in web._sheet_files(case, kit):
        mine = _article((folder / file).read_text(encoding="utf-8"), h.id)
        theirs = _article(printed, h.id)
        assert _normal(theirs, case) == _normal(mine, case), file
        checked += 1
    assert checked == len(list((folder / "sheets").iterdir()))


def test_each_card_page_is_the_card_the_pdf_prints(site):
    folder, case, _ = site
    extra = C.engine_fields(case)
    for c, g in iter_cards(case):
        html = (folder / "cards" / f"{web.file_slug(c['code'])}.html").read_text(encoding="utf-8")
        card = C.card(c, g, case, extra.get(id(c)))
        assert _normal(card, case) in _normal(html, case), c["code"]


def test_the_pages_point_only_to_relative_files_that_exist(site):
    folder, _, _ = site
    pages = [p for p in folder.rglob("*.html")]
    assert pages
    for page in pages:
        text = page.read_text(encoding="utf-8")
        for attr, ref in re.findall(r'\b(href|src)="([^"]*)"', text):
            if ref.startswith("#"):
                continue
            assert not ref.startswith(("/", "http", "file:")), f"{page.name}: {attr}={ref}"
            assert (page.parent / ref).exists(), f"{page.name}: {ref} does not exist"
    for css in folder.rglob("*.css"):
        for ref in re.findall(r"url\(([^)]+)\)", css.read_text(encoding="utf-8")):
            ref = ref.strip("'\" ")
            assert (css.parent / ref).exists(), f"{css.name}: {ref} does not exist"


# --- No spoilers -------------------------------------------------------------------------------

def _strings_of(value):
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for v in value.values():
            yield from _strings_of(v)
    elif isinstance(value, list):
        for v in value:
            yield from _strings_of(v)


def _secret_texts(case):
    """What only the director may read: the answers of the cards, the director's notes, what the procedures say about
    their results and the paragraphs of the guide."""
    from opencase.markup import plain_text
    out = []
    for c, g in iter_cards(case):
        out += [c.get("answer", ""), c.get("guide_note", "")]
        if c.get("type", g.get("type")) in ("confrontation", "failed"):   # what the director says to confront
            out.append(c.get("question", ""))
    for p in case.procedures:
        out.append(p["note"])
        out += [t["note"] for t in p["targets"]]
    for pl in case.locations:
        out.append(pl["note"])
    for h in documents.templates.sheets_for(case, "guide", case.guide):
        for b in h.blocks:
            if b.type == "md":
                out += re.split(r"\n\s*\n", b.content)
    return [plain_text(str(t)).strip() for t in out if len(plain_text(str(t)).strip()) > 30]


def test_team_json_tells_nothing_the_director_alone_knows(site):
    folder, case, _ = site
    team = " ".join(_strings_of(_json(folder, "team.json")))
    # The kit and the envelopes are public, so a paragraph the guide shares with them is not a leak.
    public = " ".join(plain_text_of(h) for h in documents.kit_sheets(case)) + " " + " ".join(
        plain_text_of(case.dossier[pid]) for sec in case.sections if sec.get("envelope") is not None for pid in sec["items"])
    leaks = [t for t in _secret_texts(case) if t in team and t not in public]
    assert not leaks, leaks[:3]


def plain_text_of(sheet):
    from opencase.markup import plain_text
    return plain_text(" ".join(b.content for b in sheet.blocks))


def test_the_check_would_catch_a_leak(site):
    """The test above is not vacuous: the director's text it looks for is really in director.json."""
    folder, case, _ = site
    director = " ".join(_strings_of(_json(folder, "director.json")))
    team = " ".join(_strings_of(_json(folder, "team.json")))
    answers = [c["answer"] for c, g in iter_cards(case) if len(c.get("answer", "")) > 60 and not c.get("menu")]
    from opencase.markup import plain_text
    assert answers and all(plain_text(a) in director for a in answers[:20])
    assert not any(plain_text(a) in team for a in answers)


def test_team_json_has_no_results_of_procedures(site):
    folder, _, _ = site
    for p in _json(folder, "team.json")["procedures"]:
        assert not {"gives", "note", "short"} & set(p)
        assert all(set(t) == {"key", "label", "kind"} for t in p["targets"])


# --- The contract ------------------------------------------------------------------------------

@pytest.mark.parametrize("name", ["team", "director", "manifest"])
def test_the_json_follows_its_schema(site, name):
    folder, _, _ = site
    schema = json.loads((web.SCHEMA_DIR / f"{name}.schema.json").read_text(encoding="utf-8"))
    jsonschema.Draft202012Validator.check_schema(schema)
    jsonschema.validate(_json(folder, f"{name}.json"), schema, cls=jsonschema.Draft202012Validator)


def test_the_schema_cannot_change_without_a_new_schema_version():
    saved = json.loads((web.SCHEMA_DIR / "fingerprint.json").read_text(encoding="utf-8"))
    if saved["schema_version"] == web.SCHEMA_VERSION:
        assert saved["sha256"] == web.schema_fingerprint(), (
            "docs/web-schema/*.schema.json changed but SCHEMA_VERSION in opencase/web.py did not: raise it, then run "
            "python3 -m opencase.web --write-fingerprint")
    else:
        pytest.fail("SCHEMA_VERSION was raised: run python3 -m opencase.web --write-fingerprint to save the new fingerprint")


def test_the_schemas_have_the_version_of_the_module():
    for name in ("team", "director", "manifest"):
        schema = json.loads((web.SCHEMA_DIR / f"{name}.schema.json").read_text(encoding="utf-8"))
        assert schema["properties"]["schema_version"]["const"] == web.SCHEMA_VERSION


def requests_expected(case):
    """What every request of the Chupacabras earns and costs, worked out from the loaded case (cards.yaml,
    procedures.yaml), not from the JSON: site/play/js/rules.js must give the same (tests/web/test_rules.py)."""
    costs = case.figures["costs"]
    shown = lambda c: [display_code(case, a) for a in as_list(c.get("attach"))]  # noqa: E731
    mothers = {f["code"]: f["mothers"] for f in followups.follow_ups(case)}
    appears = {w["who"]: w["appears_in_shown"] for w in witnesses.witnesses(case)}
    out = []
    for c, g in iter_cards(case):
        kind = card_kind(c, g)
        code = str(c["code"])
        if kind == "answer" and c.get("menu"):
            out.append({"kind": "question", "code": code, "cost": costs["question"], "cards": [code], "sheets": shown(c)})
        elif kind == "follow-up":
            out.append({"kind": "follow_up", "code": code, "cost": costs["follow_up"], "cards": [code], "sheets": shown(c),
                        "mothers": mothers[code], "unlocked_by": [display_code(case, x) for x in as_list(c.get("unlocked_by"))]})
        elif kind == "confrontation":
            out.append({"kind": "confrontation", "suspect": str(c.get("suspect", g.get("suspect"))), "card": code,
                        "cost": costs["confrontation"], "cards": [code], "sheets": shown(c)})
    by_who = {}
    for c, g in iter_cards(case):
        if card_kind(c, g) == "witness":
            by_who.setdefault(str(c.get("who") or g.get("who")), []).append(c)
    for who, cs in by_who.items():
        # one card per question, in the order of cards.yaml; the card's own sheets come with it
        out.append({"kind": "witness", "who": who, "cost": costs["witness"], "appears_in": appears[who],
                    "sequence": [{"cards": [str(c["code"])], "sheets": shown(c)} for c in cs]})
    for p in case.procedures:
        for r in ([dict(p["gives"], key=None)] if p["gives"] else p["targets"]):
            out.append({"kind": "procedure", "code": p["code"], "target": r["key"], "cost": r["cost"],
                        "sheets": list(r["shown"]), "special": r["special"]})
    return out


def expected(team, director, case=None):
    """The facts of a compiled case the JS tests check against: small, readable, and changed only by the case or the
    engine (not by the layout of a sheet)."""
    return {
        "schema_version": team["schema_version"],
        "teams": {t["id"]: {"tokens": len(t["tokens"]), "alibi": t["alibi_tokens"]} for t in team["teams"]},
        "suspects": [s["letter"] for s in team["suspects"]],
        "menu": [m["code"] for m in team["menu"]],
        "follow_ups": {f["code"]: f["unlocked_by"] for f in team["follow_ups"]},
        "procedures": {p["code"]: {"kind": p["kind"], "costs": p["costs"], "each": p["each"], "alibi": p["alibi"],
                                   "source": p["source"]} for p in team["procedures"]},
        "envelopes": {str(e["number"]): [i["code"] for s in e["sections"] for i in s["items"]] for e in team["envelopes"]},
        "kit": [k["id"] for k in team["kit"]],
        "costs": team["rules"]["costs"],
        "cards": {t: [c["code"] for c in director["cards"] if c["type"] == t] for t in sorted({c["type"] for c in director["cards"]})},
        "gives": {p["code"]: (p["gives"] or {}).get("sheets") or {t["key"]: [t["special"] or t["sheets"]] for t in p["targets"]}
                  for p in director["procedures"]},
        "notice_minutes": {n["code"]: n["minute"] for n in director["notices"]},
        "hint_penalties": {h["code"]: h["penalty"] for h in director["hints"]},
        "witnesses": sorted(w["name"] for w in director["witnesses"]),
        "score": director["score"],
        **({"requests": requests_expected(case)} if case is not None else {}),
    }


def test_expected_values_of_the_chupacabras(site, request):
    """The facts the JS tests rely on (tests/web_expected/<case>.json); rewrite with --update-snapshots."""
    folder, case, _ = site
    team, director = _json(folder, "team.json"), _json(folder, "director.json")
    got = expected(team, director, case)
    path = EXPECTED / f"{CASE}.json"
    if request.config.getoption("--update-snapshots") or not path.exists():
        path.parent.mkdir(exist_ok=True)
        path.write_text(json.dumps(got, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    assert got == json.loads(path.read_text(encoding="utf-8"))


# --- Size, repeatability and other cases --------------------------------------------------------

def test_the_files_are_small(site):
    folder, _, _ = site
    assert (folder / "team.json").stat().st_size < 50_000
    assert max(p.stat().st_size for p in (folder / "sheets").iterdir()) < 40_000


def test_compiling_twice_gives_the_same_version(site, tmp_path):
    folder, _, _ = site
    entries = web.build_cases([CASES / CASE], tmp_path)
    assert entries[0]["version"] == _json(folder, "manifest.json")["version"]


def test_a_case_not_published_compiles_too(tmp_path):
    entries = web.build_cases([CASES / "cierre-de-caja"], tmp_path)
    assert entries and (tmp_path / "play" / entries[0]["path"] / "team.json").is_file()


def test_render_sheet_and_render_card_by_code():
    case = _case(CASE)
    assert 'id="E01"' in documents.render_sheet(case, "E01")
    assert 'id="E15-B"' in documents.render_sheet(case, "E15·B")   # by its printed code
    assert 'data-code="B1"' in C.render_card(case, "B1")
    with pytest.raises(Exception):
        documents.render_sheet(case, "nope")
    with pytest.raises(Exception):
        C.render_card(case, "nope")


def test_file_slug_never_makes_two_codes_one():
    codes = ["B1", "B1+", "B1_2b", "B✕", "B 1", "Aviso 1", "Aviso_1", "E15·B", "E15-B", "B_002b"]
    assert len({web.file_slug(c) for c in codes}) == len(codes)
    assert all(re.fullmatch(r"[A-Za-z0-9_\-]+", web.file_slug(c)) for c in codes)
