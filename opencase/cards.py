"""Cut-out cards (63 × 88 mm), badges, requests, envelope labels, tokens and the sheets they print on."""
import re

from .loader import CaseError, as_list
from .markup import e, line, plain_text

TYPES = {
    # type: (modifier class of the design system, strings key of the header suffix)
    "answer": ("", ""),
    "follow-up": ("", "follow_up"),
    "confrontation": ("oc-tarjeta--confrontacion", "confrontation"),
    "failed": ("oc-tarjeta--fallida", "failed"),
    "witness": ("oc-tarjeta--testigo", ""),
    "wildcard": ("oc-tarjeta--comodin", ""),
    "notice": ("oc-tarjeta--aviso", ""),
    "press": ("oc-tarjeta--prensa", ""),
    "hint": ("oc-tarjeta--pista", ""),
    "closing": ("oc-tarjeta--cierre", ""),
}
# These go on their own sheets (card standard: notices, press and hints together).
SEPARATE_TYPES = {"notice", "press", "hint", "closing"}


def team_modifier(team):
    """Class that colours a team's badge: A is navy (the default), B green, C violet, D copper."""
    return f" oc-equipo--{str(team).lower()}" if str(team).upper() in ("B", "C", "D") else ""


def brand(case, right=None):
    return (f'<div class="oc-tarjeta__marca"><span>{e(case.get("brand", "Open Case"))}</span>'
            f'<span>{e(right or case.title)}</span></div>')


def engine_fields(case):
    """What the engine writes on the notice, press and hint cards of a case that uses it, by id() of the card:
    "1 de 2" after `who` on notices, which notice a press card comes with, and the points a hint costs
    as its footer. A field the case writes itself is kept (the "1 de 2" is always added to a notice).
    The suggested minutes are only in the guide: the cards go to the teams' tables."""
    if not case.uses_engine:
        return {}
    out, n_notice, n_hint = {}, 0, 0
    penalties = list(case.figures["hint_penalties"] or [])
    kinds = [str(c.get("type", g.get("type", "answer"))).lower()
             for g in case.card_groups for c in g.get("cards", []) or []]
    total = kinds.count("notice")
    for g in case.card_groups:
        for c in g.get("cards", []) or []:
            kind = str(c.get("type", g.get("type", "answer"))).lower()
            if kind == "notice":
                n_notice += 1
                who = c.get("who") or case.t("cards.notice_who")
                if total > 1:
                    who = f'{who} · {case.t("cards.notice_of", n=n_notice, total=total)}'
                out[id(c)] = {"who": who}
            elif kind == "press" and not c.get("who") and n_notice:
                out[id(c)] = {"who": case.t("cards.press_who", n=n_notice)}
            elif kind == "hint":
                n_hint += 1
                if c.get("footer"):
                    continue
                if n_hint > len(penalties):
                    raise CaseError(f"card {c.get('code')} is hint number {n_hint}, but hint_penalties has only "
                                    f"{len(penalties)} values: add one in case.yaml (or write its footer)",
                                    case.lang_root / "cards.yaml")
                p = penalties[n_hint - 1]
                out[id(c)] = {"footer": case.t("cards.hint_footer_one" if p == 1 else "cards.hint_footer", n=p)}
    return out


def card(c, group, case, extra=None):
    if extra:
        c = {**c, **extra}
    kind = str(c.get("type", group.get("type", "answer"))).lower()
    if kind not in TYPES:
        raise CaseError(f"card {c.get('code')} has type '{kind}'; the types are: " + ", ".join(TYPES),
                        case.lang_root / "cards.yaml")
    css, suffix = TYPES[kind]
    style = c.get("style")
    if style:
        css = TYPES.get(style, (f"oc-tarjeta--{style}", ""))[0]
    code = str(c["code"])
    letter = c.get("suspect", group.get("suspect"))
    if kind == "confrontation" and letter and "◆" not in code:
        code = f"{letter}◆ · {code}"
    who = c.get("who")
    if not who:
        if suffix:
            who = f'{group.get("short") or group.get("who") or group.get("title", "")} · {case.t("card_types." + suffix)}'
        else:
            who = group.get("who") or group.get("title", "")
    parts = ['<div class="oc-tarjeta__banda"></div>',
             f'<div class="oc-tarjeta__cab"><b>{e(code)}</b><span>{line(who)}</span></div>']
    if c.get("headline"):
        parts.append(f'<div class="oc-tarjeta__titular">{line(c["headline"])}</div>')
    if c.get("question"):
        parts.append(f'<div class="oc-tarjeta__pregunta">{line(c["question"])}</div>')
    parts.append(f'<div class="oc-tarjeta__respuesta">{line(c.get("answer", ""))}</div>')
    if c.get("note"):
        parts.append(f'<div class="oc-tarjeta__pregunta">{line(c["note"])}</div>')
    for att in as_list(c.get("attach")):
        parts.append(f'<div class="oc-tarjeta__pie">{e(case.t("cards.attached"))} {e(att)}</div>')
    for nxt in as_list(c.get("follow_up")):
        parts.append(f'<div class="oc-tarjeta__pie oc-tarjeta__pie--seg">{e(case.t("cards.follow_up_available"))}: {e(nxt)}</div>')
    if c.get("footer"):
        parts.append(f'<div class="oc-tarjeta__pie oc-tarjeta__pie--seg">{line(c["footer"])}</div>')
    parts.append(brand(case))
    return (f'<div class="oc-tarjeta {css}" data-code="{e(c["code"])}" '
            f'data-length="{len(plain_text(c.get("answer", "")))}">{"".join(parts)}</div>')


def suspect_card(s, case, ctx):
    if s.get("portrait"):
        portrait = f'<img class="oc-tarjeta__retrato" src="{ctx.url(s["portrait"])}" alt="{e(s["name"])}">'
    else:
        portrait = f'<div class="oc-tarjeta__retrato-vacio"><img src="{ctx.design("icons/carpeta.svg")}" alt=""></div>'
    facts = "".join(f"<span>{e(k)}</span><div>{line(v)}</div>" for k, v in list((s.get("facts") or {}).items())[:5])
    codes = [c["code"] for g in case.card_groups for c in g.get("cards", []) or []
             if c.get("menu") and c.get("suspect", g.get("suspect")) == s["letter"]]
    questions = ""
    if codes:
        span = codes[0] if len(codes) == 1 else f"{codes[0]}–{codes[-1]}"
        questions = (f'<div class="oc-tarjeta__pie oc-tarjeta__pie--seg">{e(case.t("cards.questions"))}: '
                     f'{e(span)} · {e(s["letter"])}◆</div>')
    role = " · ".join(x for x in (s.get("role", ""), case.t("cards.suspect_label", letter=s["letter"])) if x)
    return ('<div class="oc-tarjeta oc-tarjeta--vertical oc-tarjeta--sospechoso"><div class="oc-tarjeta__banda"></div>'
            f'{portrait}<div class="oc-tarjeta__nombre">{e(s.get("short_name") or s["name"])}</div>'
            f'<div class="oc-tarjeta__rol">{e(role)}</div><div class="oc-tarjeta__datos">{facts}</div>'
            f'{questions}{brand(case)}</div>')


STAR = ('<svg class="oc-placa__estrella" viewBox="0 0 60 60" aria-hidden="true"><path d="M30 3l7 17 18 1-14 11 '
        '5 18-16-10-16 10 5-18L5 21l18-1z" fill="#b48a2c" stroke="#7a5d1c"/></svg>')


def badge(case, ctx, team):
    b = case.get("badge", {}) or {}
    unit = b.get("unit", "")
    unit = "<br>".join(e(x) for x in unit if x) if isinstance(unit, list) else e(unit).replace("\n", "<br>")
    mod = team_modifier(team)
    return ('<div class="oc-tarjeta oc-tarjeta--vertical oc-placa">'
            f'{STAR}<div class="oc-placa__titulo">{e(b.get("title", case.t("badge.title")))}</div>'
            f'<div class="oc-placa__unidad">{unit}</div><span class="oc-equipo{mod}">{e(case.t("team", name=team))}</span>'
            f'<div class="oc-placa__nombre"></div><div class="oc-placa__nombre-rotulo">{e(case.t("badge.name"))}</div>'
            f'<img class="oc-placa__mono" src="{ctx.design("logos/oc-monograma-tinta.svg")}" alt="Open Case"></div>')


def request_card(case):
    r = case.get("request", {}) or {}
    help_text = r.get("help", case.t("request.help"))
    return ('<div class="oc-tarjeta oc-solicitud">'
            f'<div class="oc-solicitud__titulo">{e(case.t("request.title"))} <small>{e(help_text)}</small></div>'
            f'<div class="oc-campo"><span>{e(case.t("request.team"))}</span><i></i><span>{e(case.t("request.code"))}</span><i></i></div>'
            f'<div class="oc-campo"><span>{e(case.t("request.evidence"))}</span><i></i></div>'
            f'<div class="oc-campo oc-campo--corto"><span>{e(case.t("request.why"))}</span><i></i></div>'
            '<div class="oc-campo oc-campo--corto"><span></span><i></i></div>'
            f'<div class="oc-solicitud__ficha">{e(case.t("request.token_here"))}</div>'
            f'{brand(case, case.t("request.number"))}</div>')


def envelope_label(env, case, team):
    items = "".join(f"<li>{line(x)}</li>" for x in env.get("contents", []) or [])
    mod = team_modifier(team)
    who = f'<span class="oc-equipo{mod}">{e(case.t("team", name=team))}</span>' if team else "<span></span>"
    text = env.get("footer")
    if env.get("token_footer"):
        f = case.figures
        key = "labels.token_footer_alibi" if f["alibi_tokens_per_team"] else "labels.token_footer"
        text = case.t(key, tokens=f["tokens_per_team"], alibi=f["alibi_tokens_per_team"])
    footer = f'<span class="oc-tarjeta__pie oc-tarjeta__pie--seg">{line(text)}</span>' if text else ""
    desc = f'<div class="oc-tarjeta__pregunta">{line(env["description"])}</div>' if env.get("description") else ""
    return ('<div class="oc-tarjeta oc-sobre">'
            f'<div class="oc-sobre__numero">{e(case.t("envelope", n=env.get("number", "")))} <small>{e(env.get("when", ""))}</small></div>'
            f'{desc}<ul class="oc-sobre__lista">{items}</ul>'
            f'<div style="display:flex;justify-content:space-between;align-items:center;margin-top:auto;gap:8px">{who}{footer}</div>'
            f'{brand(case)}</div>')


def card_back(case, ctx):
    return ('<div class="oc-tarjeta oc-reverso">'
            f'<img class="oc-reverso__sello" src="{ctx.design("logos/oc-sello-sello.svg")}" alt="Open Case">'
            f'<div class="oc-reverso__caso">{e(case.title)}</div></div>')


def rotate(htm):
    """A vertical card turned 90° so it fits the landscape 2 × 4 grid."""
    return f'<div class="oc-tarjeta oc-tarjeta--rotada">{htm}</div>'


def card_sheets(cards, case, label, codes=None, vertical=False):
    """Splits cards into sheets of 8 and returns the HTML of each sheet.

    `codes` is a parallel list with each card's code, for the footer."""
    batches = []
    for i in range(0, len(cards), 8):
        batch = cards[i:i + 8]
        batch_codes = codes[i:i + 8] if codes else None
        cells = [rotate(c) if vertical else c for c in batch]
        cells += ['<div class="oc-tarjeta oc-tarjeta--vacia"></div>'] * (8 - len(batch))
        batches.append((cells, batch_codes))
    total = len(batches)
    html = []
    for n, (cells, batch_codes) in enumerate(batches, 1):
        span = ""
        if batch_codes:
            span = f" · {label} {batch_codes[0]}–{batch_codes[-1]}" if len(batch_codes) > 1 else f" · {label} {batch_codes[0]}"
        elif label:
            span = f" · {label}"
        footer = f'{e(case.title)} · {e(case.t("sheet_of", n=n, total=total))}{e(span)} · {e(case.t("print_100"))}'
        html.append(f'<section class="oc-pliego">{"".join(cells)}<div class="oc-pliego__pie">{footer}</div></section>')
    return html


def token_sheets(case, ctx):
    """Sheets of 35 tokens (5 × 7): each team's numbered (and alibi) tokens, with spares to fill the sheet; plus a back for each."""
    n = int(case.figures["tokens_per_team"])
    alibis = int(case.figures["alibi_tokens_per_team"])
    teams = case.get("teams", ["A", "B"])
    tokens = []
    for team in teams:
        mod = f" oc-ficha--{str(team).lower()}" if str(team).upper() in ("A", "B", "C", "D") else ""
        team_label = e(case.t("team", name=team))
        tokens += [f'<span class="oc-ficha{mod}"><b>{i}</b>{e(case.t("tokens.token"))}<small>{team_label}</small></span>'
                   for i in range(1, n + 1)]
        # Alibi tokens: dashed border, coded C1, C2... (see `alibi_tokens_per_team` in docs/case-format.md)
        tokens += [f'<span class="oc-ficha{mod} oc-ficha--coartada"><b>{e(case.t("tokens.alibi_code", i=i))}</b>'
                   f'{e(case.t("tokens.alibi"))}<small>{team_label}</small></span>' for i in range(1, alibis + 1)]
    fronts = []
    for i in range(0, len(tokens), 35):
        batch = tokens[i:i + 35]
        spare = 35 - len(batch)
        batch += [f'<span class="oc-ficha"><b>&nbsp;</b>{e(case.t("tokens.token"))}<small>{e(case.t("tokens.spare"))}</small></span>'] * spare
        fronts.append(batch)
    total = len(fronts)
    out = []
    # Two monograms: the light one on brass (color), the ink one on white (ink saver).
    mono = (f'<img class="oc-ficha__mono-color" src="{ctx.design("logos/oc-monograma-papel.svg")}" alt="">'
            f'<img class="oc-ficha__mono-ahorro" src="{ctx.design("logos/oc-monograma-tinta.svg")}" alt="">')
    for k, batch in enumerate(fronts, 1):
        footer = e(case.t("tokens.front_footer", title=case.title, k=k, total=total))
        out.append(f'<section class="oc-pliego oc-pliego--fichas">{"".join(batch)}<div class="oc-pliego__pie">{footer}</div></section>')
        back = "".join(f'<span class="oc-ficha oc-ficha--reverso">{mono}</span>' for _ in batch)
        footer = e(case.t("tokens.back_footer", title=case.title, k=k, total=total))
        out.append(f'<section class="oc-pliego oc-pliego--fichas">{back}<div class="oc-pliego__pie">{footer}</div></section>')
    return out


def split_cards(case):
    """Separates the cards into (answers, separate) keeping the file order."""
    answers, separate = [], []
    for g in case.card_groups:
        for c in g.get("cards", []) or []:
            kind = str(c.get("type", g.get("type", "answer"))).lower()
            (separate if kind in SEPARATE_TYPES else answers).append((c, g))
    return answers, separate


def short_code(c):
    return re.sub(r"\s+", " ", str(c["code"]))
