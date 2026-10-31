"""Builds the HTML of every document of a case: kit, envelopes, dossier, guide and card sheets."""
import re
from dataclasses import dataclass
from pathlib import Path

from . import cards as C
from . import templates
from .components import Context, render_blocks
from .markup import e, line

REPO_ROOT = Path(__file__).resolve().parent.parent
PAPERS = {"letter": ("letter", "216mm", "279mm"), "a4": ("A4", "210mm", "297mm")}


@dataclass
class Document:
    key: str          # short name for --only (kit, guide, cards...)
    folder: str       # teams | director
    file: str         # PDF name without extension
    title: str
    html: str
    kind: str         # sheets | card-sheets
    check_sheets: bool = False   # warn when a sheet takes more than one page


def ink_saver(case):
    return case.get("_ink_saver", case.get("ink_saver", True))


def _page(case, title, body, mesa_class="oc-mesa"):
    size, width, height = PAPERS.get(case.paper, PAPERS["letter"])
    styles = [(REPO_ROOT / "design" / "open-case.css").as_uri(),
              (REPO_ROOT / "opencase" / "styles" / "export.css").as_uri()]
    if ink_saver(case):
        styles.append((REPO_ROOT / "opencase" / "styles" / "ink-saver.css").as_uri())
    extra = case.root / "styles.css"
    if extra.exists():
        styles.append(extra.as_uri())
    links = "".join(f'<link rel="stylesheet" href="{h}">' for h in styles)
    return (f'<!doctype html><html lang="{e(case.get("language", "es"))}"><head><meta charset="utf-8">'
            f'<meta name="viewport" content="width=device-width,initial-scale=1"><title>{e(title)}</title>{links}'
            f'<style>@page{{size:{size}}}:root{{--hoja-ancho:{width};--hoja-alto:{height};--pagina-ancho:{width};--pagina-alto:{height}}}</style>'
            f'</head><body><main class="{mesa_class}">{body}</main></body></html>')


def _screen_header(kicker, title, text=""):
    p = f"<p>{line(text)}</p>" if text else ""
    return (f'<header class="oc-portada"><span class="oc-sobrelinea">{e(kicker)}</span>'
            f"<h1>{e(title)}</h1>{p}</header>")


def sheet(h, ctx, defaults=None):
    d = dict(defaults or {})
    d.update(h.data)
    if d.get("notice") and not d.get("description") and ctx.case.uses_engine:
        d["description"] = _notice_description(ctx.case, h.id)
    classes = ["oc-hoja"]
    if d.get("reserved"):
        classes.append("oc-hoja--reservada")
    if d.get("aged") or d.get("paper") == "aged":
        classes.append("oc-hoja--vieja")
    head_cls = "oc-membrete oc-membrete--reservado" if d.get("reserved") else "oc-membrete"
    logo = ""
    if d.get("logo"):
        logo = (f'<img class="oc-membrete__logo" src="{ctx.design("logos/oc-wordmark-tinta.svg")}" alt="Open Case">'
                f'<span class="oc-membrete__caso">{e(ctx.case.title)}</span>')
    if d.get("code"):
        right = f'<span class="oc-codigo">{e(d["code"])}</span>'
    elif d.get("team_line"):
        right = f'<span class="oc-equipo-linea">{e(ctx.case.t("team_line"))}</span>'
    elif d.get("tag"):
        mod = " oc-tag--marino" if d.get("tag_navy") else ""
        right = f'<span class="oc-tag{mod}">{e(d["tag"])}</span>'
    else:
        right = ""
    letterhead = ""
    if d.get("institution") or d.get("description") or right:
        letterhead = (f'<div class="{head_cls}"><div class="oc-membrete__inst">{logo}<b>{line(d.get("institution", ""))}</b>'
                      f'{line(d.get("description", ""))}</div>{right}</div>')
    title = f'<h2>{line(d["title"])}</h2>' if d.get("title") else ""
    stamp = ""
    if d.get("stamp"):
        s = d["stamp"] if isinstance(d["stamp"], dict) else {"text": d["stamp"]}
        color = {"ink": " oc-sello--tinta", "brass": " oc-sello--laton", "forest": " oc-sello--bosque"}.get(s.get("color", ""), "")
        stamp = f'<span class="oc-sello oc-sello--esquina{color}">{e(s["text"])}</span>'
    if d.get("notice"):
        classes.append("oc-hoja--aviso")
    body = render_blocks(h, ctx)
    footer = ""
    if d.get("brand_footer"):
        mono = ctx.design("logos/oc-monograma-tinta.svg")
        footer = (f'<div class="oc-hoja__marca"><img src="{mono}" alt="{e(ctx.case.get("brand", "Open Case"))}">'
                  f'<span>{e(ctx.case.get("brand", "Open Case"))}</span><span>{e(ctx.case.title)}</span></div>')
    return f'<article class="{" ".join(classes)}" id="{e(h.id)}">{letterhead}{title}{body}{stamp}{footer}</article>'


def _notice_description(case, sheet_id):
    """"For every team · 1 of 2": the line under a notice sheet. The teams get a copy, so it never says the
    suggested minute (that is only in the guide)."""
    ids = [pid for sec in case.sections for pid in sec.get("items", []) or [] if case.dossier[pid].get("notice")]
    if sheet_id not in ids:
        return ""
    if len(ids) == 1:
        return case.t("notice_description_plain")
    return case.t("notice_description", n=ids.index(sheet_id) + 1, total=len(ids))


def cover(case, ctx, doc, note="", reserved=False, team_line=False):
    classes = "oc-hoja oc-tapa" + (" oc-hoja--reservada oc-tapa--reservada" if reserved else "")
    team = f'<span class="oc-equipo-linea">{e(case.t("team_line"))}</span>' if team_line else ""
    tag = f'<span class="oc-tag">{e(case.t("director_only"))}</span>' if reserved else ""
    version = f'<div class="oc-tapa__version">{e(case.get("version"))}</div>' if case.get("version") else ""
    return (f'<article class="{classes}"><img class="oc-tapa__sello" src="{ctx.design("logos/oc-sello-sello.svg")}" alt="Open Case. {e(case.get("tagline", ""))}">'
            f'<div class="oc-tapa__caso">{e(case.title)}</div><div class="oc-tapa__doc">{e(doc)}</div>{tag}'
            f'{"<p class=oc-tapa__nota>" + line(note) + "</p>" if note else ""}{team}'
            f'<div class="oc-tapa__lema">{e(case.get("tagline", case.t("tagline")))}</div>{version}</article>')


def build_documents(case):
    ctx = Context(case, REPO_ROOT)
    t = case.t
    docs = []
    title = case.title
    brand = case.get("brand", "Open Case")

    def doc(key, folder, number, name_key, html, kind, check=False):
        docs.append(Document(key, folder, f"{number}_{t(f'docs.{name_key}.name')}", t(f"docs.{name_key}.title"),
                             html, kind, check))

    def page(name_key, body, mesa="oc-mesa oc-mesa--pliegos"):
        return _page(case, f"{t(f'docs.{name_key}.page')} · {title}", body, mesa)

    # --- Team kit -------------------------------------------------------------------
    kit_cfg = case.get("kit", {}) or {}
    if case.kit:
        body = _screen_header(f"{brand} · {title}", t("docs.kit.title"), kit_cfg.get("description", ""))
        body += cover(case, ctx, t("docs.kit.title"), kit_cfg.get("cover_note", ""), team_line=True)
        defaults = {"logo": True, "team_line": True, "brand_footer": _brand_footer(case, "kit")}
        body += "".join(sheet(h, ctx, defaults) for h in templates.sheets_for(case, "kit", case.kit))
        doc("kit", "teams", "01", "kit", page("kit", body, "oc-mesa"), "sheets", True)

    # --- Dossier: by envelope for the teams, and complete for the director ----------------
    dossier = case.get("dossier", {}) or {}
    sections = case.sections
    by_envelope = {}
    for sec in sections:
        if sec.get("envelope") is not None:
            by_envelope.setdefault(sec["envelope"], []).append(sec)
    for n, (num, secs) in enumerate(by_envelope.items(), start=2):
        name = t("envelope", n=num)
        body = _screen_header(dossier.get("kicker", ""), name, secs[0].get("note", ""))
        for sec in secs:
            body += _section_title(sec)
            body += "".join(sheet(case.dossier[p], ctx, {"brand_footer": _brand_footer(case, "dossier")}) for p in sec.get("items", []))
        docs.append(Document(f"envelopes:{num}", "teams", f"{n:02d}_{t('docs.envelope_file', n=num)}", name,
                             _page(case, f"{name} · {title}", body), "sheets", True))

    if sections:
        dossier_title = dossier.get("title", t("docs.dossier.title"))
        body = _screen_header(dossier.get("kicker", ""), dossier_title, dossier.get("description", ""))
        body += _dossier_index(case, dossier, sections)
        for sec in sections:
            body += _section_title(sec)
            body += "".join(sheet(case.dossier[p], ctx, {"brand_footer": _brand_footer(case, "dossier")}) for p in sec.get("items", []))
        docs.append(Document("dossier", "director", f"02_{t('docs.dossier.name')}", dossier_title,
                             _page(case, f"{dossier_title} · {title}", body), "sheets", True))

    # --- Director's guide -------------------------------------------------------------
    guide_cfg = case.get("guide", {}) or {}
    if case.guide:
        body = _screen_header(t("guide_kicker"), t("docs.guide.title"), guide_cfg.get("description", ""))
        body += cover(case, ctx, t("docs.guide.title"), guide_cfg.get("cover_note", ""), reserved=True)
        defaults = {"logo": True, "reserved": True, "tag": t("director_only"), "brand_footer": _brand_footer(case, "guide")}
        body += "".join(sheet(h, ctx, defaults) for h in templates.sheets_for(case, "guide", case.guide))
        doc("guide", "director", "01", "guide", page("guide", body, "oc-mesa"), "sheets")

    # --- Answer cards and notices -----------------------------------------------------------
    answers, separate = C.split_cards(case)
    if answers or separate:
        extra = C.engine_fields(case)
        card_html = [C.card(c, g, case, extra.get(id(c))) for c, g in answers]
        codes = [C.short_code(c) for c, g in answers]
        sheets = C.card_sheets(card_html, case, t("labels.cards"), codes)
        if separate:
            sheets += C.card_sheets([C.card(c, g, case, extra.get(id(c))) for c, g in separate], case, t("labels.notices"))
        sheets = _renumber(case, sheets)
        body = _screen_header(f"{brand} · {title}", t("docs.cards.title"), t("docs.cards.note"))
        doc("cards", "director", "03", "cards", page("cards", body + "".join(sheets)), "card-sheets")

    # --- Common card back ---------------------------------------------------------------------
    backs = C.card_sheets([C.card_back(case, ctx)] * 8, case, t("labels.card_backs"))
    doc("card-backs", "director", "04", "card_backs",
        page("card_backs", _screen_header(brand, t("docs.card_backs.title")) + "".join(backs)), "card-sheets")

    # --- Material for the teams ---------------------------------------------------------------------
    teams = case.get("teams", ["A", "B"])
    if case.suspects:
        cards = [C.suspect_card(s, case, ctx) for s in case.suspects]
        sheets = C.card_sheets(cards, case, t("labels.suspects"), [s["letter"] for s in case.suspects], vertical=True)
        doc("suspects", "teams", "10", "suspects",
            page("suspects", _screen_header(title, t("docs.suspects.title"), t("docs.suspects.note")) + "".join(sheets)),
            "card-sheets")
    n_badges = int(case.get("players_per_team", 7))
    sheets = []
    for team in teams:
        sheets += C.card_sheets([C.badge(case, ctx, team)] * n_badges, case, t("labels.badges", name=team), vertical=True)
    doc("badges", "teams", "11", "badges",
        page("badges", _screen_header(title, t("docs.badges.title")) + "".join(_renumber(case, sheets))), "card-sheets")
    doc("tokens", "teams", "12", "tokens",
        page("tokens", _screen_header(title, t("docs.tokens.title")) + "".join(C.token_sheets(case, ctx))), "card-sheets")
    sheets = C.card_sheets([C.request_card(case)] * 8, case, t("labels.requests"))
    doc("requests", "teams", "13", "requests",
        page("requests", _screen_header(title, t("docs.requests.title")) + "".join(sheets)), "card-sheets")
    labels = case.get("envelope_labels", []) or []
    if labels:
        cards = [C.envelope_label(env, case, team) for env in labels for team in teams]
        sheets = C.card_sheets(cards, case, t("labels.envelope_labels"))
        doc("labels", "teams", "14", "envelope_labels",
            page("envelope_labels", _screen_header(title, t("docs.envelope_labels.title")) + "".join(sheets)), "card-sheets")
    return docs


def _brand_footer(case, doc):
    """brand_footer in case.yaml: the documents (kit, guide, dossier) whose sheets carry the brand footer.
    By default all three do: every sheet shows the logo and the case name at the bottom."""
    value = case.get("brand_footer", ["kit", "guide", "dossier"])
    if value is True:
        return True
    if not value:
        return False
    return doc in value


def _renumber(case, sheets_html):
    """Sheet footers say "Sheet N of M"; renumber them so M counts every sheet of the document."""
    marker = case.t("sheet_of", n="\0", total="\0")
    pattern = re.escape(marker).replace("\0", r"\d+")
    total = len(sheets_html)
    return [re.sub(pattern, lambda m, n=n: case.t("sheet_of", n=n, total=total), p, count=1)
            for n, p in enumerate(sheets_html, 1)]


def _section_title(sec):
    return f'<div class="oc-seccion"><b>{e(sec.get("title", ""))}</b><span>{e(sec.get("note", ""))}</span></div>'


def _dossier_index(case, dossier, sections):
    rows = []
    for sec in sections:
        rows.append(f'<tr><th colspan="2">{e(sec.get("title", ""))}{" · " + e(sec["note"]) if sec.get("note") else ""}</th></tr>')
        for pid in sec.get("items", []):
            h = case.dossier[pid]
            rows.append(f'<tr><td class="c">{e(h.get("code", pid))}</td><td>{line(h.get("title", ""))}'
                        f'<span class="oc-pequeno"> · {line(h.get("institution", ""))}</span></td></tr>')
    kicker = f'<div class="oc-caratula__sobre">{e(dossier.get("kicker", ""))}</div>' if dossier.get("kicker") else ""
    desc = f"<p>{line(dossier.get('printed_description', ''))}</p>" if dossier.get("printed_description") else ""
    return (f'<article class="oc-hoja oc-caratula" id="indice">{kicker}<h1>{e(dossier.get("title", case.t("docs.dossier.title")))}</h1>{desc}'
            f'<div class="oc-tabla oc-indice-tabla oc-tabla--compacta"><table><tbody>{"".join(rows)}</tbody></table></div>'
            f'<span class="oc-sello oc-sello--esquina">{e(case.t("reserved"))}</span></article>')
