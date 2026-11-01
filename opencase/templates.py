"""The engine's own texts: the rules, phases, glossary and score that are the same in every case.

They live in opencase/templates/<lang>/ as Markdown sheets (the same format as a case's sheets) written
with Jinja2, so they can print the case's figures ({{ f.tokens_per_team }}) and change with them
({% if f.alibi_tokens_per_team %}). A variable that no YAML defines stops the export: the templates
use StrictUndefined. A case cannot replace these files; it can only leave sheets out (engine_sheets).

  kit/*.md, guide/*.md    sheets the exporter inserts by itself into the team kit and the guide
  blocks/<name>.md        pieces a case places in its own sheets with a ```<name> block
  _macros.j2              helpers shared by the templates of one language

Front matter keys that only the engine reads (they are removed before drawing the sheet):
  place: anchor          after the case's anchor sheet (engine_sheets.<doc>.after, default its first sheet)
  place: end             after the case's last sheet
  place: after-block X   after the case's sheet that holds a ```X block (or at the end if none does)
  optional: true         left out when it draws nothing in this case (an empty glossary)
  join: true             its blocks go at the bottom of the sheet right before it instead of on a new page
"""
import sys
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, StrictUndefined, TemplateNotFound, TemplateSyntaxError
from jinja2.exceptions import UndefinedError

from . import confrontations, followups, procedures, witnesses
from .acronyms import table_rows
from .loader import CaseError, Sheet, as_list, card_kind, parse_sheet, read_yaml

TEMPLATES_DIR = Path(__file__).resolve().parent / "templates"
ENGINE_KEYS = ("place", "join", "optional")


def language_dir(lang):
    return TEMPLATES_DIR / lang


def environment(lang):
    folder = language_dir(lang)
    if not folder.is_dir():
        raise CaseError(f"the engine has no templates in '{lang}' (opencase/templates/{lang}/): write them, or turn "
                        "the engine's sheets off with engine_sheets: false in case.yaml")
    env = Environment(loader=FileSystemLoader(str(folder)), undefined=StrictUndefined, autoescape=False,
                      trim_blocks=True, lstrip_blocks=True, keep_trailing_newline=True)
    return env


def _number(strings):
    decimal = strings("format.decimal")

    def fmt(value, signed=False):
        if isinstance(value, float) and value.is_integer():
            value = int(value)
        text = str(abs(value)).replace(".", decimal)
        if value < 0:
            return "−" + text
        return ("+" + text) if signed and value > 0 else text
    return fmt


def _fail(message):
    """{{ fail("...") }} in a template: stops the export with that message (for data the case got wrong)."""
    raise CaseError(message)


def _team_label(team):
    """The coloured team mark of the design system (A navy, B green, C violet, D copper)."""
    from .cards import team_modifier
    from .markup import e
    return f'<span class="oc-equipo{team_modifier(team)}">{e(team)}</span>'


def _cell(text):
    """Text that goes inside a cell of a Markdown table: one line, with its | escaped."""
    return " ".join(str(text).split()).replace("|", "\\|")


def _hint_groups(penalties):
    """[1, 1, 1, 2, 2] -> [{first: 1, last: 3, penalty: 1}, {first: 4, last: 5, penalty: 2}]."""
    groups = []
    for n, p in enumerate(penalties, 1):
        if groups and groups[-1]["penalty"] == p:
            groups[-1]["last"] = n
        else:
            groups.append({"first": n, "last": n, "penalty": p})
    return groups


def notice_minute(case, n):
    """Suggested minute for the n-th notice (1-based), or None when the figures have fewer."""
    minutes = case.figures["notice_minutes"] or []
    return minutes[n - 1] if 0 < n <= len(minutes) else None


def context(case, data=None):
    """Everything a template can read. Figures are under `f`; the rest comes from the case's data."""
    f = case.figures
    cards = [(c, g) for g in case.card_groups for c in g.get("cards", []) or []]
    notice_sheets = []
    for sec in case.sections:
        for pid in sec.get("items", []) or []:
            h = case.dossier.get(pid)
            if h is not None and h.get("notice"):
                notice_sheets.append(h)
    notices = [{"n": n, "code": h.get("code", h.id), "title": h.get("title", ""), "minute": notice_minute(case, n)}
               for n, h in enumerate(notice_sheets, 1)]
    if not notice_sheets:   # the notices are only cards (the usual case): the control sheet lists the cards
        notice_cards = [c for c, g in cards if card_kind(c, g) == "notice"]
        notices = [{"n": n, "code": str(c.get("code", "")), "title": c.get("title") or c.get("headline", ""),
                    "minute": notice_minute(case, n)} for n, c in enumerate(notice_cards, 1)]
    readings, n_notice = [], 0
    for c, g in cards:
        kind = card_kind(c, g)
        if kind == "notice":
            n_notice += 1
            readings.append({"kind": kind, "n": n_notice, "code": str(c.get("code", "")),
                             "answer": c.get("answer", ""), "headline": c.get("headline", ""),
                             "minute": notice_minute(case, n_notice)})
        elif kind == "press":
            readings.append({"kind": kind, "n": n_notice, "code": str(c.get("code", "")),
                             "answer": c.get("answer", ""), "headline": c.get("headline", ""),
                             "minute": notice_minute(case, n_notice)})
    # How many notices, press cards and hints there are is the case's (its cards and sheets); the figures
    # only give each one its minute or its cost, so a case with fewer uses the first ones.
    n_notices = max(sum(1 for r in readings if r["kind"] == "notice"), len(notice_sheets))
    minutes = list(f["notice_minutes"] or [])
    if n_notices > len(minutes):
        raise CaseError(f"the case has {n_notices} notices but notice_minutes gives {len(minutes)} minutes: "
                        "add the missing ones in case.yaml", case.root / "case.yaml")
    minutes = minutes[:n_notices]
    has_press = any(r["kind"] == "press" for r in readings)
    penalties = list(f["hint_penalties"] or [])
    hints = [{"n": n, "code": str(c.get("code", "")), "answer": c.get("answer", ""),
              "penalty": penalties[n - 1] if n <= len(penalties) else None}
             for n, (c, g) in enumerate([(c, g) for c, g in cards if card_kind(c, g) == "hint"], 1)]
    if len(hints) > len(penalties):
        raise CaseError(f"the case has {len(hints)} hint cards but hint_penalties gives {len(penalties)} costs: "
                        "add the missing ones in case.yaml", case.root / "case.yaml")
    penalties = penalties[:len(hints)]
    score_points = (f["score"] or {})
    bonus = None
    texts = case.get("score_texts", {}) or {}
    points = case.get("score_bonus")
    if points is not None:
        if not texts.get("bonus"):
            raise CaseError("score_bonus has points but languages/<lang>/case.yaml has no score_texts.bonus "
                            "(the line of the score table)", case.lang_root / "case.yaml")
        bonus = {"points": points, "text": texts["bonus"], "short": texts.get("bonus_short", texts["bonus"])}
    envelopes = []
    for sec in case.sections:
        if sec.get("envelope") is not None and sec["envelope"] not in envelopes:
            envelopes.append(sec["envelope"])
    kit = case.engine_sheets("kit")
    how_to_play_in_kit = kit is not False and "10-how-to-play" not in as_list(kit.get("skip"))
    return {
        "f": f,
        "score": score_points,
        "bonus": bonus,
        "teams": [str(t) for t in case.get("teams", ["A", "B"])],
        "n_suspects": len(case.suspects),
        "envelopes": envelopes,
        "notices": notices,
        "readings": readings,
        "notice_minutes": minutes,
        "has_press": has_press,
        "hints": hints,
        "hint_groups": _hint_groups(penalties),
        "how_to_play_in_kit": how_to_play_in_kit,
        "follow_ups": followups.follow_ups(case),
        "witnesses": witnesses.witnesses(case),
        "confrontations": confrontations.rows(case),
        "confrontation_failed": confrontations.failed_card(case),
        "procedures": case.procedures,
        "locations": case.locations,
        "procedure_cards": procedures.card_rows(case),
        "procedure_also": procedures.also_rows(case),
        "case_title": case.title,
        "glossary": table_rows(case),
        "data": data if data is not None else {},
    }


def _template_line(path):
    """The line of the template where a rendering error happened (Jinja keeps it in the traceback)."""
    tb = sys.exc_info()[2]
    line = None
    while tb is not None:
        if tb.tb_frame.f_code.co_filename == str(path):
            line = tb.tb_lineno
        tb = tb.tb_next
    return line


def render(case, name, data=None):
    """Renders opencase/templates/<lang>/<name> and returns its text."""
    env = environment(case.lang)
    env.filters["num"] = _number(case.strings)
    env.filters["team_label"] = _team_label
    env.globals["fail"] = _fail
    env.filters["cell"] = _cell
    env.filters["source_word"] = lambda source: case.t(f"procedures.sources.{source}")
    env.filters["capitalize_first"] = lambda text: str(text)[:1].upper() + str(text)[1:]
    path = language_dir(case.lang) / name
    try:
        template = env.get_template(name)
        return template.render(**context(case, data), t=case.t)
    except TemplateNotFound:
        raise CaseError(f"the engine has no template {name} in '{case.lang}'", path) from None
    except TemplateSyntaxError as ex:
        raise CaseError(f"template error: {ex.message}", path, ex.lineno) from None
    except UndefinedError as ex:
        raise CaseError(f"the template uses a value that no YAML defines ({ex.message}): add it to "
                        "opencase/defaults.yaml or to the case", path, _template_line(path)) from None
    except CaseError:
        raise
    except Exception as ex:   # a filter or a comparison with the wrong kind of value
        raise CaseError(f"the template cannot be drawn ({type(ex).__name__}: {ex})", path,
                        _template_line(path)) from None


def render_sheet(case, name, sheet_id=None, data=None):
    path = language_dir(case.lang) / name
    return parse_sheet(render(case, name, data), path, sheet_id or "oc-" + Path(name).stem)


def has_block(lang, name):
    return (language_dir(lang) / "blocks" / f"{name}.md").exists()


def block_names(lang):
    folder = language_dir(lang) / "blocks"
    return sorted(p.stem for p in folder.glob("*.md")) if folder.is_dir() else []


def block(case, name, content, path=None, line=None):
    """The blocks of the engine piece blocks/<name>.md, drawn with the YAML written inside the case's block."""
    data = read_yaml(content, path, line) if content.strip() else {}
    sheet = render_sheet(case, f"blocks/{name}.md", data=data)
    return sheet.blocks


def sheets_for(case, doc, own):
    """The case's sheets of one document (kit, guide) with the engine's sheets inserted in their place."""
    cfg = case.engine_sheets(doc)
    if cfg is False:
        return list(own)
    folder = language_dir(case.lang) / doc
    environment(case.lang)   # fails clearly when the language has no templates
    skip = set(as_list(cfg.get("skip")))
    names = sorted(p.name for p in folder.glob("*.md")) if folder.is_dir() else []
    unknown = skip - {Path(n).stem for n in names}
    if unknown:
        raise CaseError(f"engine_sheets.{doc}.skip names sheets the engine does not have: {', '.join(sorted(unknown))} "
                        f"(it has: {', '.join(Path(n).stem for n in names)})", case.root / "case.yaml")
    anchor = cfg.get("after")
    ids = [s.id for s in own]
    if anchor is not None and anchor not in ids:
        raise CaseError(f"engine_sheets.{doc}.after is '{anchor}', but there is no {doc}/{anchor}.md",
                        case.root / "case.yaml")
    groups = {}
    for name in names:
        if Path(name).stem in skip:
            continue
        sheet = render_sheet(case, f"{doc}/{name}")
        if sheet.data.get("optional") and not sheet.blocks:   # nothing to say in this case (an empty glossary)
            continue
        place = str(sheet.data.get("place", "anchor")).strip()
        groups.setdefault(place, []).append(sheet)
    out = list(own)

    def insert(after_index, sheets):
        """Inserts after out[after_index] (-1: at the start); `join` sheets go into the sheet before them."""
        pos = after_index + 1
        for s in sheets:
            if s.data.get("join") and pos > 0:
                prev = out[pos - 1]
                out[pos - 1] = Sheet(prev.id, prev.path, prev.data, prev.blocks + s.blocks)
                continue
            out.insert(pos, _clean(s))
            pos += 1

    for place in sorted(groups, key=lambda p: {"anchor": 0, "end": 2}.get(p, 1), reverse=True):
        sheets = groups[place]
        if place == "anchor":
            index = ids.index(anchor) if anchor is not None else (0 if own else -1)
            index = _index_of(out, own[index].id) if index >= 0 else -1
        elif place == "end":
            index = len(out) - 1
        elif place.startswith("after-block"):
            kind = place.split(None, 1)[1] if " " in place else ""
            holders = [i for i, s in enumerate(out) if any(b.type == kind for b in s.blocks)]
            index = holders[-1] if holders else len(out) - 1
        else:
            raise CaseError(f"unknown place '{place}' (use anchor, end or after-block <name>)", sheets[0].path)
        insert(index, sheets)
    return out


def _index_of(sheets, sheet_id):
    for i, s in enumerate(sheets):
        if s.id == sheet_id:
            return i
    return -1


def _clean(sheet):
    data = {k: v for k, v in sheet.data.items() if k not in ENGINE_KEYS}
    return Sheet(sheet.id, sheet.path, data, sheet.blocks)
