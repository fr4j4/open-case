"""A ```component block in a sheet -> the HTML of a design-system component.

Each function takes the block and the context and returns HTML using the oc- classes of
design/open-case.css. The block names are the ones listed in docs/case-format.md."""
import re
from pathlib import Path

from . import templates
from .loader import CaseError, Sheet, read_yaml, resolve_media, split_blocks
from .markup import e, line, line_pre, md, plain_text

ARROWS = {"incoming": "↘", "outgoing": "↗", "missed": "✕"}

# Names used in case files -> classes of the design system (which are in Spanish).
HANDWRITTEN = {"notebook": "", "scribble": "oc-manuscrito--garabato", "pencil": "oc-manuscrito--lapiz",
               "letter": "oc-manuscrito--carta", "no-lines": "oc-manuscrito--sin-lineas"}
TABLE_VARIANTS = {"control": "control", "work": "trabajo", "score": "puntaje", "compact": "compacta",
                  "narrow": "angosta", "log": "registro"}
STAMP_VARIANTS = {"stamp": "", "ink": "oc-sello--tinta", "brass": "oc-sello--laton", "forest": "oc-sello--bosque",
                  "large": "oc-sello--grande", "corner": "oc-sello--esquina"}


class Context:
    """What a component needs to know about the case and where it is being drawn."""

    def __init__(self, case, repo_root):
        self.case = case
        self.repo_root = Path(repo_root)
        self.sheet = None

    def path(self, ref):
        p = resolve_media(self.case, ref)
        if p is None:
            raise CaseError(f"file '{ref}' does not exist", self.sheet.path if self.sheet else None)
        return p

    def url(self, ref):
        return self.path(ref).as_uri()

    def design(self, ref):
        return (self.repo_root / "design" / ref).as_uri()

    def svg(self, ref, cls="", label=None):
        return inline_svg(self.path(ref).read_text(encoding="utf-8"), cls, label)


def inline_svg(source, cls="", label=None):
    s = re.sub(r"<\?xml[^>]*\?>|<!DOCTYPE[^>]*>", "", source)
    s = re.sub(r"<metadata>.*?</metadata>", "", s, flags=re.S)
    s = s.strip()
    if cls:
        s = re.sub(r"<svg\b", f'<svg class="{cls}"', s, count=1)
    if label and "aria-label" not in s[:400]:
        s = re.sub(r"<svg\b", f'<svg role="img" aria-label="{e(label)}"', s, count=1)
    # Generic typefaces in the drawings become the design system's.
    s = re.sub(r'font-family="(?:monospace|IBM Plex Mono, monospace)"', 'font-family="IBM Plex Mono, monospace"', s)
    s = re.sub(r'font-family="sans-serif"', 'font-family="Public Sans, Arial, sans-serif"', s)
    return s


def _data(block, ctx, kind=(list, dict)):
    data = read_yaml(block.content, ctx.sheet.path if ctx.sheet else None, block.line)
    if data is None:
        data = [] if kind is list or (isinstance(kind, tuple) and list in kind) else {}
    if not isinstance(data, kind):
        names = {list: "a list (lines starting with '- ')", dict: "key: value fields"}
        expected = names.get(kind, " or ".join(names[t] for t in kind) if isinstance(kind, tuple) else str(kind))
        raise CaseError(f"the {block.type} block must be {expected}", ctx.sheet.path if ctx.sheet else None, block.line)
    return data


def _pairs(data):
    """Accepts a dict or a list of [key, value] / {key: value}."""
    if isinstance(data, dict):
        return list(data.items())
    pairs = []
    for it in data:
        if isinstance(it, dict):
            pairs.extend(it.items())
        elif isinstance(it, (list, tuple)) and len(it) == 2:
            pairs.append(tuple(it))
        else:
            pairs.append((str(it), ""))
    return pairs


def _columns(arg, default=None):
    m = re.search(r"(\d+)\s*columns?", arg or "")
    n = int(m.group(1)) if m else default
    return f' style="--oc-columnas:{n}"' if n else ""


# --- Documents ------------------------------------------------------------------

def c_meta(b, ctx):
    rows = "".join(f"<div><span>{e(k)}</span>{line(v)}</div>" for k, v in _pairs(_data(b, ctx)))
    return f'<div class="oc-meta">{rows}</div>'


def c_signature(b, ctx):
    parts = []
    for it in _data(b, ctx, list):
        if isinstance(it, dict) and ("scrawl" in it or "label" in it):
            scrawl = f'<span class="oc-firma__trazo">{e(it.get("scrawl", ""))}</span>' if it.get("scrawl") else ""
            parts.append(f'<div>{scrawl}<span>{line(it.get("label", ""))}</span></div>')
        else:
            if isinstance(it, dict):
                it = ": ".join(f"{k}: {v}" for k, v in it.items())
            parts.append(f"<span>{line(it)}</span>")
    if len(parts) == 1:
        parts.append("<span></span>")
    return f'<div class="oc-firma">{"".join(parts)}</div>'


def c_statement(b, ctx):
    return f'<div class="oc-declaracion">{line_pre(b.content)}</div>'


def c_quote(b, ctx):
    return f'<div class="oc-cita">{line_pre(b.content)}</div>'


def c_handwritten(b, ctx):
    classes = ["oc-manuscrito"]
    for v in (b.arg or "").split():
        if v.lower() not in HANDWRITTEN:
            raise CaseError(f"handwritten: unknown variant '{v}' (use {', '.join(sorted(HANDWRITTEN))})",
                            ctx.sheet.path, b.line)
        if HANDWRITTEN[v.lower()]:
            classes.append(HANDWRITTEN[v.lower()])
    return f'<div class="{" ".join(classes)}">{e(b.content.strip())}</div>'


def c_postit(b, ctx):
    return f'<div class="oc-postit">{e(b.content.strip())}</div>'


def c_marker(b, ctx):
    return "".join(f'<div class="oc-plumon">{e(l)}</div>' for l in b.content.strip().split("\n") if l.strip())


def c_mono(b, ctx):
    return f'<div class="oc-mono oc-bloque-mono">{md(b.content)}</div>'


def c_small(b, ctx):
    return f'<div class="oc-pequeno">{md(b.content)}</div>'


def c_table(b, ctx):
    variants = [TABLE_VARIANTS.get(v, v) for v in (b.arg or "").split() if v]
    htm = md(b.content)
    classes = " ".join(f"oc-tabla--{v}" for v in variants)
    return htm.replace('<div class="oc-tabla">', f'<div class="oc-tabla {classes}">')


def c_stamp(b, ctx):
    classes = ["oc-sello"] + [STAMP_VARIANTS.get(v.lower(), "") for v in (b.arg or "").split()]
    return f'<span class="{" ".join(c for c in classes if c)}">{e(b.content.strip())}</span>'


def c_evidence_bag(b, ctx):
    d = _data(b, ctx, dict)
    head = f'{e(ctx.case.t("evidence"))} <small>{e(d.get("number", ""))}</small>'
    fields = "".join(f'<div class="oc-bolsa__campo"><span>{e(k)}</span><b>{e(v)}</b></div>'
                     for k, v in _pairs(d.get("fields", {})))
    return f'<div class="oc-bolsa"><div class="oc-bolsa__cab">{head}</div>{fields}</div>'


def c_press(b, ctx):
    d = _data(b, ctx, dict)
    return ('<article class="oc-prensa">'
            f'<div class="oc-prensa__kicker"><span>{e(d.get("outlet", ""))}</span><span>{e(d.get("date", ""))}</span></div>'
            f'<h3>{line(d.get("headline", ""))}</h3>'
            f'<div class="oc-prensa__cuerpo">{md(d.get("body", ""))}</div></article>')


def c_email(b, ctx):
    d = _data(b, ctx, dict)
    head = "".join(f"<span>{ctx.case.t('email.' + k)}</span><div>{e(d[k])}</div>"
                   for k in ("from", "to", "cc", "date", "subject") if d.get(k))
    att = "".join(f'<span class="oc-msg__adjunto">📎 {e(a)}</span>' for a in d.get("attachments", []) or [])
    return (f'<div class="oc-correo"><div class="oc-correo__cab">{head}</div>'
            f'<div class="oc-correo__cuerpo">{line(d.get("body", ""))}{att}</div></div>')


def c_receipt(b, ctx):
    rows = []
    for it in _data(b, ctx, list):
        if it in ("---", "-", "line"):
            rows.append("<hr>")
        elif isinstance(it, dict) and "center" in it:
            rows.append(f'<div class="oc-boleta__centro">{line(it["center"])}</div>')
        elif isinstance(it, dict) and "total" in it:
            a, z = it["total"]
            rows.append(f'<div class="oc-boleta__fila"><b>{e(a)}</b><b>{e(z)}</b></div>')
        elif isinstance(it, (list, tuple)) and len(it) == 2:
            rows.append(f'<div class="oc-boleta__fila"><span>{e(it[0])}</span><span>{e(it[1])}</span></div>')
        else:
            rows.append(f'<div class="oc-boleta__centro">{e(it)}</div>')
    return f'<div class="oc-boleta">{"".join(rows)}</div>'


# --- Photos, cameras and drawings -------------------------------------------------

def _img(ctx, ref, alt, cls=""):
    attr = f' class="{cls}"' if cls else ""
    return f'<img{attr} src="{ctx.url(ref)}" alt="{e(alt)}" loading="eager">'


def c_photos(b, ctx):
    figures = []
    for f in _data(b, ctx, list):
        title = f.get("title", "")
        text = f.get("text", "")
        alt = f.get("alt") or plain_text(f"{title} {text}")
        label = f'<span class="oc-foto__rotulo">{e(f["label"])}</span>' if f.get("label") else ""
        caption = (f"<b>{line(title)}</b> " if title else "") + line(text)
        figures.append(f'<figure class="oc-foto"><div class="oc-foto__cuadro">{_img(ctx, f["image"], alt)}{label}</div>'
                       f"<figcaption>{caption}</figcaption></figure>")
    return f'<div class="oc-fotos"{_columns(b.arg)}>{"".join(figures)}</div>'


def c_cctv(b, ctx):
    figures = []
    for f in _data(b, ctx, list):
        text = f.get("text", "")
        title = f.get("title", "")
        alt = f.get("alt") or plain_text(f"{title} {text}")
        osd = "".join(f'<span class="oc-cctv__osd{" oc-cctv__osd--d" if side == "right" else ""}">{e(f[k])}</span>'
                      for k, side in (("osd", "left"), ("osd_right", "right")) if f.get(k))
        caption = (f"<b>{line(title)}</b> " if title else "") + line(text)
        figures.append(f'<figure class="oc-cctv">{_img(ctx, f["image"], alt)}{osd}<figcaption>{caption}</figcaption></figure>')
    return f'<div class="oc-cctvs"{_columns(b.arg)}>{"".join(figures)}</div>'


def c_image(b, ctx):
    d = _data(b, ctx, dict)
    width = f' style="width:{e(d["width"])}"' if d.get("width") else ""
    caption = f"<figcaption>{line(d['caption'])}</figcaption>" if d.get("caption") else ""
    return f'<figure class="oc-imagen"{width}>{_img(ctx, d["image"], d.get("alt") or plain_text(d.get("caption", "")))}{caption}</figure>'


def c_svg(b, ctx):
    """A drawing from the case (sketch map, diagrams). The argument is the file path."""
    ref = (b.arg or b.content).strip()
    if not ref:
        raise CaseError("svg: the file path is missing (```svg diagrams/map.svg```)", ctx.sheet.path, b.line)
    return f'<div class="oc-dibujo">{ctx.svg(ref)}</div>'


def c_legend(b, ctx):
    items = []
    for color, text in _pairs(_data(b, ctx)):
        items.append(f'<span><i style="background:{e(color)}"></i>{line(text)}</span>')
    return f'<div class="oc-leyenda">{"".join(items)}</div>'


# --- Screens ----------------------------------------------------------------------

def _chat(messages, ctx, b):
    colors, next_color = {}, iter("abcde" * 4)
    out = []
    for m in messages or []:
        if isinstance(m, str):
            out.append(f'<span class="oc-dia">{e(m)}</span>')
            continue
        if "day" in m:
            out.append(f'<span class="oc-dia">{e(m["day"])}</span>')
            continue
        classes = ["oc-msg"]
        if m.get("outgoing") or m.get("me"):
            classes.append("oc-msg--saliente")
        text = m.get("text", "")
        if m.get("deleted"):
            classes.append("oc-msg--borrado")
            text = text or ctx.case.t("deleted_message")
        who = ""
        if m.get("from"):
            letter = m.get("color") or colors.setdefault(m["from"], next(next_color))
            mod = "" if letter == "a" else f" oc-msg__quien--{letter}"
            who = f'<span class="oc-msg__quien{mod}">{e(m["from"])}</span>'
        att = f'<span class="oc-msg__adjunto">📎 {e(m["attachment"])}</span>' if m.get("attachment") else ""
        if m.get("time") is None:
            raise CaseError("a chat message has no time (the design guide asks for a time on every message)",
                            ctx.sheet.path, b.line)
        when = f'<time>{e(m["time"])}</time>'
        out.append(f'<div class="{" ".join(classes)}">{who}{line(text)}{att}{when}</div>')
    return f'<div class="oc-chat">{"".join(out)}</div>'


def _calls(rows, ctx):
    out = []
    for f in rows or []:
        if isinstance(f, dict) and "text" not in f:
            kind = str(f.get("type", "")).lower()
            parts = [f"{ARROWS.get(kind, '')} {f.get('who', '')}".strip()]
            if kind:
                try:
                    parts.append(ctx.case.t(f"calls.{kind}"))
                except KeyError:
                    parts.append(kind)
            if f.get("duration"):
                parts.append(str(f["duration"]))
            left, right = " · ".join(parts), f.get("time", "")
        elif isinstance(f, dict):
            left, right = f.get("text", ""), f.get("time", "")
        else:
            left, right = f
        out.append(f"<div><span>{line(left)}</span><span>{e(right)}</span></div>")
    return f'<div class="oc-llamadas">{"".join(out)}</div>'


def _app(rows):
    out = "".join(f'<div class="oc-app__fila"><span>{line(a)}</span><span>{line(z)}</span></div>'
                  for a, z in _pairs(rows or []))
    return f'<div class="oc-app">{out}</div>'


def _phone(c, ctx, b):
    bar = f'<div class="oc-celular__barra">{e(c.get("bar", ""))}<small>{e(c.get("sub", ""))}</small></div>'
    if "chat" in c:
        body = _chat(c["chat"], ctx, b)
    elif "calls" in c:
        body = _calls(c["calls"], ctx)
    elif "app" in c:
        body = _app(c["app"])
    else:
        raise CaseError("each phone needs chat:, calls: or app:", ctx.sheet.path, b.line)
    return f'<div class="oc-celular">{bar}{body}</div>'


def c_phones(b, ctx):
    data = _data(b, ctx)
    if isinstance(data, dict):
        data = [data]
    return f'<div class="oc-celulares"{_columns(b.arg)}>{"".join(_phone(c, ctx, b) for c in data)}</div>'


def c_videos(b, ctx):
    frames = []
    for v in _data(b, ctx, list):
        alt = v.get("alt") or plain_text(v.get("text", ""))
        img = _img(ctx, v["image"], alt) if v.get("image") else ""
        live = v.get("live")
        badge = f'<span class="oc-video__live">{e(live if isinstance(live, str) else ctx.case.t("live"))}</span>' if live else ""
        clock = f'<span class="oc-video__reloj">{e(v["clock"])}</span>' if v.get("clock") else ""
        comments = "".join(f"<span><b>{e(u)}</b> {e(t)}</span>" for u, t in _pairs(v.get("comments", []) or []))
        comments = f'<div class="oc-video__coments">{comments}</div>' if comments else ""
        caption = f'<small class="oc-video__meta">{e(v["caption"])}</small>' if v.get("caption") else ""
        text = f'<b>{line(v["text"])}</b>' if v.get("text") else ""
        frames.append(f'<div class="oc-video"><div class="oc-video__cuadro">{img}{badge}{clock}</div>'
                      f'<div class="oc-video__pie">{text}{caption}{comments}</div></div>')
    return f'<div class="oc-videos"{_columns(b.arg)}>{"".join(frames)}</div>'


def c_posts(b, ctx):
    posts = []
    for p in _data(b, ctx, list):
        if p.get("image"):
            visual = _img(ctx, p["image"], p.get("alt") or plain_text(p.get("text", "")))
        elif p.get("story"):
            visual = f'<div class="oc-historia" role="img" aria-label="{e(plain_text(p["story"]))}">{line(p["story"])}</div>'
        else:
            visual = ""
        meta = f"<small>{e(p['meta'])}</small>" if p.get("meta") else ""
        posts.append(f'<div class="oc-post"><div class="oc-post__cab"><i></i>{e(p.get("user", ""))}</div>{visual}'
                     f'<div class="oc-post__pie">{line(p.get("text", ""))}{meta}</div></div>')
    return f'<div class="oc-publicaciones"{_columns(b.arg)}>{"".join(posts)}</div>'


# --- Director's guide -------------------------------------------------------------

def _note(b, ctx, cls, default_label):
    label = (b.arg or default_label).strip()
    r = f'<span class="oc-nota__rotulo">{e(label)}</span>' if label else ""
    return f'<div class="oc-nota {cls}">{r}<div class="oc-nota__cuerpo">{md(b.content)}</div></div>'


def c_note(b, ctx):
    return _note(b, ctx, "", "")


def c_note_ok(b, ctx):
    return _note(b, ctx, "oc-nota--ok", "")


def c_note_warning(b, ctx):
    return _note(b, ctx, "oc-nota--aviso", "")


def c_script(b, ctx):
    label = f' data-label="{e(b.arg)}"' if b.arg else ""
    return f'<div class="oc-guion"{label}>{line_pre(b.content)}</div>'


def c_steps(b, ctx):
    steps = "".join(f'<div class="oc-paso"><b>{e(p.get("title", ""))}</b><span>{line(p.get("text", ""))}</span></div>'
                    for p in _data(b, ctx, list))
    return f'<div class="oc-pasos">{steps}</div>'


# --- Kit worksheets -----------------------------------------------------------------

def c_fields(b, ctx):
    out = []
    for c in _data(b, ctx, list):
        if isinstance(c, str):
            c = {"label": c}
        kind = c.get("type", "line")
        height = f' style="min-height:{e(c["height"])}"' if c.get("height") else ""
        box = '<div class="oc-caja"%s></div>' % height if kind == "box" else '<div class="oc-linea"></div>'
        out.append(f'<div class="oc-campo-hoja"><label>{line(c.get("label", ""))}</label>{box}</div>')
    return "".join(out)


def c_work_table(b, ctx):
    d = _data(b, ctx, dict)
    cols = d.get("columns", [])
    height = d.get("height")
    style = f' style="height:{e(height)}"' if height else ""
    head = "".join(f"<th>{e(c)}</th>" for c in cols)
    rows = "".join("<tr><td%s>%s</td>%s</tr>" % (style, line(f), f"<td{style}></td>" * (len(cols) - 1))
                   for f in d.get("rows", []))
    cls = "oc-tabla oc-linea-tiempo" if d.get("schedule") else "oc-tabla oc-tabla--trabajo"
    return f'<div class="{cls}"><table><thead><tr>{head}</tr></thead><tbody>{rows}</tbody></table></div>'


def c_checkboxes(b, ctx):
    """Boxes to tick off tokens. Argument: a number, or `alibi` for the alibi tokens (C1, C2…)."""
    arg = (b.arg or "").strip()
    if arg == "alibi":
        n = int(ctx.case.figures["alibi_tokens_per_team"])
        labels = [ctx.case.t("tokens.alibi_code", i=i) for i in range(1, n + 1)]
    else:
        n = int(arg) if arg.isdigit() else int(ctx.case.figures["tokens_per_team"])
        labels = [str(i) for i in range(1, n + 1)]
    return '<div class="oc-casillas">' + "".join(f"<span>{e(l)}</span>" for l in labels) + "</div>"


def c_columns(b, ctx):
    """Side-by-side Markdown pieces (tables, lists) separated by a line with `===`.
    Argument: the minimum width of a column in px (default 230). With four backticks (````columns) a piece
    can also hold ```blocks, like the body of a sheet."""
    width = (b.arg or "230").strip()
    if not width.isdigit():
        raise CaseError("columns: the argument is the minimum column width in px (for example ```columns 230)",
                        ctx.sheet.path, b.line)
    parts = re.split(r"(?m)^===\s*$", b.content)
    cells = "".join(f"<div>{_column(p, b, ctx)}</div>" for p in parts if p.strip())
    return (f'<div class="oc-columnas-libres" style="display:grid;grid-template-columns:repeat(auto-fit,minmax({width}px,1fr));'
            f'gap:10px;font-size:11px;line-height:1.3">{cells}</div>')


def _column(text, b, ctx):
    try:
        blocks = split_blocks(text, b.line + 1)
    except CaseError as ex:
        raise CaseError(str(ex).split(": ", 1)[-1], ctx.sheet.path, ex.line) from None
    if all(x.type == "md" for x in blocks):
        return md(text)
    sheet = ctx.sheet
    html = render_blocks(Sheet(sheet.id, sheet.path, sheet.data, blocks), ctx)
    ctx.sheet = sheet
    return html


def c_menu(b, ctx):
    """The question menu, generated from suspects.yaml and the cards marked `menu: true`."""
    case = ctx.case
    out = []
    for s in case.suspects:
        letter = s["letter"]
        rows = []
        for g in case.card_groups:
            for c in g.get("cards", []) or []:
                if c.get("menu") and (c.get("suspect", g.get("suspect")) == letter):
                    rows.append((c["code"], c.get("menu_question") or c.get("question", "")))
        if not rows:
            continue
        rows.append((f"{letter}◆", s.get("confront", case.t("menu.confront_default"))))
        who = f'{s["name"]} · {s.get("role", "")}'.strip(" ·")
        body = "".join(f'<tr><td class="c">{e(c)}</td><td>{line(q)}</td></tr>' for c, q in rows)
        out.append(f'<div class="oc-quien">{e(who)}</div><div class="oc-tabla oc-tabla--menu"><table><tbody>{body}</tbody></table></div>')
    return "".join(out)


def c_html(b, ctx):
    return b.content


COMPONENTS = {
    "meta": c_meta, "signature": c_signature, "statement": c_statement, "quote": c_quote,
    "handwritten": c_handwritten, "postit": c_postit, "marker": c_marker, "mono": c_mono,
    "small": c_small, "table": c_table, "stamp": c_stamp, "evidence-bag": c_evidence_bag,
    "press": c_press, "email": c_email, "receipt": c_receipt,
    "photos": c_photos, "cctv": c_cctv, "image": c_image, "svg": c_svg, "legend": c_legend,
    "phones": c_phones, "videos": c_videos, "posts": c_posts,
    "note": c_note, "note-ok": c_note_ok, "note-warning": c_note_warning, "script": c_script, "steps": c_steps,
    "fields": c_fields, "work-table": c_work_table, "checkboxes": c_checkboxes, "columns": c_columns,
    "menu": c_menu, "html": c_html,
}


def render_blocks(sheet, ctx):
    ctx.sheet = sheet
    out = []
    for b in sheet.blocks:
        if b.type == "md":
            out.append(_md_with_images(b.content, ctx))
            continue
        fn = COMPONENTS.get(b.type)
        if fn is None and templates.has_block(ctx.case.lang, b.type):
            out.append(_engine_block(b, ctx))
            continue
        if fn is None:
            raise CaseError(f"unknown block ```{b.type}. The available ones are: "
                            + ", ".join(sorted(set(COMPONENTS) | set(templates.block_names(ctx.case.lang)))),
                            sheet.path, b.line)
        try:
            out.append(fn(b, ctx))
        except CaseError:
            raise
        except (KeyError, TypeError, ValueError, AttributeError) as ex:
            raise CaseError(f"the ```{b.type} block has data I cannot read ({type(ex).__name__}: {ex})",
                            sheet.path, b.line) from None
    return "\n".join(out)


def _engine_block(b, ctx):
    """A ```name block that is a piece of the engine (opencase/templates/<lang>/blocks/name.md)."""
    sheet = ctx.sheet
    blocks = templates.block(ctx.case, b.type, b.content, sheet.path, b.line)
    html = render_blocks(Sheet(sheet.id, sheet.path, sheet.data, blocks), ctx)
    ctx.sheet = sheet
    return html


def _md_with_images(text, ctx):
    htm = md(text)

    def replace(m):
        alt, src = m.group(2), m.group(1)
        if src.startswith(("http:", "https:", "file:", "data:")):
            return m.group(0)
        if src.lower().endswith(".svg"):
            return f'<span class="oc-dibujo">{ctx.svg(src, label=alt)}</span>'
        return f'<img src="{ctx.url(src)}" alt="{alt}">'

    htm = re.sub(r'<img alt="([^"]*)" src="([^"]+)"\s*/?>', lambda m: replace(_Swapped(m)), htm)
    htm = re.sub(r'<img src="([^"]+)" alt="([^"]*)"\s*/?>', replace, htm)
    # An image alone in its paragraph does not get the <p>.
    htm = re.sub(r"<p>(<span class=\"oc-dibujo\">.*?</span>)</p>", r"\1", htm, flags=re.S)
    return htm


class _Swapped:
    """Markdown writes alt before src; `replace` expects src first."""

    def __init__(self, m):
        self.m = m

    def group(self, i):
        return {0: self.m.group(0), 1: self.m.group(2), 2: self.m.group(1)}[i]
