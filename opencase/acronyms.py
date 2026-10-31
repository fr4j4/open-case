"""Acronyms (SAG, PDI, SML…): the case's glossary and the check that each one is written out when it first appears.

The glossary is data of the case (languages/<lang>/case.yaml, `glossary:`), because the acronyms change with
the language; the mechanism is the engine's:

  * the director's guide gets a table of the glossary (engine sheet guide/80-acronyms.md);
  * a case can put the same table in one of its sheets with a ```acronyms block (blocks/acronyms.md);
  * `--check` warns when an acronym of the glossary is used before its long form is written (reading order),
    and when a word that looks like an acronym is in no glossary.

Reading order, which is what a team sees:
  1. the kit, then the sheets of the envelopes in the order of the sections of case.yaml (sheet by sheet; inside a
     sheet, its front matter first);
  2. every other piece (a sheet that comes with an answer, a card) separately, with what the teams already read.
The director's guide is read after all that, and its glossary table counts as the long form of everything.
What a person says (a chat, a statement, a quoted answer) is not checked: people speak the way they speak.
"""
import re

from .loader import CaseError, normalize_code

# Blocks that hold what someone says or writes in their own voice: not checked.
VOICE_BLOCKS = {"phones", "posts", "statement", "quote", "handwritten"}
# Front matter that is not text for the reader.
SKIP_KEYS = {"code", "place", "join", "tag", "image", "logo", "notice", "brand_footer", "id"}
# Blocks whose content is not prose (drawings, photos with their captions in YAML): only these are read as text.
PROSE_BLOCKS = {"md", "table", "note", "note-ok", "note-warning", "meta", "fields", "mono", "legend", "columns",
                "script", "steps", "work-table", "menu", "signature"}

_WORD = r"(?<![\w·\-/@#])%s(?![\w·\-/])"
_CANDIDATE = re.compile(r"(?<![\w·\-/@#])[A-ZÁÉÍÓÚÑ]{2,6}(?![\w·\-/])")
_QUOTED = re.compile(r'"[^"\n]*"|“[^”\n]*”|«[^»\n]*»')


def glossary(case):
    """{abbreviation: {"long": text, "expand": bool}} from `glossary:` of languages/<lang>/case.yaml.
    An entry is `SAG: Servicio Agrícola y Ganadero`, or `SUV: {long: ..., expand: false}` when every reader knows
    it: it goes in the director's table but nothing asks the sheets to write it out."""
    raw = case.get("glossary")
    path = case.lang_root / "case.yaml"
    if raw is None:
        return {}
    if not isinstance(raw, dict):
        raise CaseError("'glossary' must be a list of ACRONYM: long form fields", path)
    out = {}
    for abbr, value in raw.items():
        abbr = str(abbr)
        if not re.fullmatch(r"[A-ZÁÉÍÓÚÑ]{2,8}", abbr):
            raise CaseError(f"glossary: '{abbr}' is not an acronym (2 to 8 capital letters)", path)
        if isinstance(value, dict):
            unknown = set(value) - {"long", "expand"}
            if unknown:
                raise CaseError(f"glossary.{abbr}: unknown field(s) {', '.join(sorted(map(str, unknown)))} "
                                "(use long and expand)", path)
            long, expand = value.get("long"), value.get("expand", True)
        else:
            long, expand = value, True
        if not isinstance(long, str) or not long.strip():
            raise CaseError(f"glossary.{abbr} needs its long form (the words the letters stand for)", path)
        if not isinstance(expand, bool):
            raise CaseError(f"glossary.{abbr}.expand must be true or false", path)
        out[abbr] = {"long": long.strip(), "expand": expand}
    ignored = case.get("glossary_ignore")
    if ignored is not None and not isinstance(ignored, list):
        raise CaseError("'glossary_ignore' must be a list of words", path)
    return out


def ignored_words(case):
    return {str(w) for w in (case.get("glossary_ignore") or [])}


def table_rows(case):
    """For the templates: [{abbr, long, expand}] in the order of the glossary."""
    return [{"abbr": a, **v} for a, v in glossary(case).items()]


def _text(sheet):
    """What a reader reads in a sheet, in order: front matter, then the prose of its blocks (no voices)."""
    parts = [str(v) for k, v in sheet.data.items() if k not in SKIP_KEYS and isinstance(v, str)]
    for b in sheet.blocks:
        if b.type in PROSE_BLOCKS:
            parts.append(b.content)
    return "\n".join(parts)


def _name(sheet):
    return str(sheet.get("code", sheet.id)).strip() or sheet.id


def _first(pattern, text, flags=0):
    m = re.search(pattern, text, flags)
    return m.start() if m else None


class _Reader:
    """Remembers which acronyms have been written out so far in one reading."""

    def __init__(self, entries, introduced=()):
        self.entries = entries
        self.introduced = set(introduced)
        self.late = []        # (abbr, where)

    def read(self, text, where):
        for abbr, e in self.entries.items():
            if abbr in self.introduced:
                continue
            at = _first(_WORD % re.escape(abbr), text)
            long_at = _first(re.escape(e["long"]), text, re.I)
            if at is None:
                if long_at is not None:
                    self.introduced.add(abbr)
                continue
            self.introduced.add(abbr)
            if not e["expand"]:
                continue
            written_out = long_at is not None and long_at < at
            beside = re.match(r"\s*\(\s*" + re.escape(e["long"]), text[at + len(abbr):], re.I)
            if not (written_out or beside):
                self.late.append((abbr, where))


def check(case, kit, guide):
    """Warnings (added to case.warnings): acronyms used before their long form, and words that look like
    acronyms but are in no glossary. `kit` and `guide` are the final sheets of those documents."""
    entries = glossary(case)
    ignore = ignored_words(case)
    prefixes = {re.match(r"[A-Za-zÁÉÍÓÚÑ]*", normalize_code(s.get("code", s.id))).group()
                for s in case.dossier.values()}
    prefixes |= {re.match(r"[A-Za-zÁÉÍÓÚÑ]*", str(c.get("code", ""))).group()
                 for g in case.card_groups for c in g.get("cards", []) or []}
    known = set(entries) | ignore | {p.upper() for p in prefixes if p}

    # Teams' reading: kit, then the envelopes in order.
    in_envelope, loose = [], []
    for sec in case.sections:
        for pid in sec.get("items", []) or []:
            if pid in case.dossier:
                (in_envelope if sec.get("envelope") is not None else loose).append(case.dossier[pid])
    teams = _Reader(entries)
    sequence = [("kit", s) for s in kit] + [("envelope", s) for s in in_envelope]
    seen_texts = []
    for kind, s in sequence:
        text = _text(s)
        teams.read(text, f"{kind} {_name(s)}")
        seen_texts.append((f"{kind} {_name(s)}", text))
    late = list(teams.late)

    # Every other piece separately, with what the teams already read.
    for s in loose:
        text = _text(s)
        r = _Reader(entries, teams.introduced)
        r.read(text, f"dossier {_name(s)}")
        late += r.late
        seen_texts.append((f"dossier {_name(s)}", text))
    for g in case.card_groups:
        for c in g.get("cards", []) or []:
            text = _QUOTED.sub(" ", "\n".join(str(c.get(k, "")) for k in ("question", "answer", "headline", "who")))
            where = f"card {c.get('code', '?')}"
            r = _Reader(entries, teams.introduced)
            r.read(text, where)
            late += r.late
            seen_texts.append((where, text))

    # The guide: its own glossary table counts as the long form.
    director = _Reader(entries, entries.keys())
    for s in guide:
        if s.id == "oc-80-acronyms":   # the table itself says nothing about where the acronyms are used
            continue
        text = _text(s)
        director.read(text, f"guide {_name(s)}")
        seen_texts.append((f"guide {_name(s)}", text))

    warnings = []
    for abbr, where in late:
        warnings.append(f"{abbr} is used in {where} before its long form ('{entries[abbr]['long']}') is written; "
                        "write it out the first time (or set expand: false in glossary)")
    unknown = {}
    for where, text in seen_texts:
        spoken_out = _QUOTED.sub(" ", text)
        for m in _CANDIDATE.finditer(spoken_out):
            word = m.group()
            if word in known or _in_capitals_run(spoken_out, m):
                continue
            unknown.setdefault(word, where)
    for word, where in sorted(unknown.items()):
        warnings.append(f"{word} in {where} looks like an acronym but is in no glossary: add it to glossary in "
                        f"languages/{case.lang}/case.yaml, or to glossary_ignore if it is not one")
    everything = "\n".join([t for _, t in seen_texts] + [_voice_text(s) for s in
                                                          list(case.dossier.values()) + case.kit + case.guide])
    unused = [a for a in entries if not re.search(_WORD % re.escape(a), everything)]
    for a in unused:
        warnings.append(f"glossary: {a} is never used in the case")
    for w in warnings:
        if w not in case.warnings:
            case.warnings.append(w)
    return warnings


def _voice_text(sheet):
    return "\n".join(b.content for b in sheet.blocks if b.type in VOICE_BLOCKS)


def _in_capitals_run(text, m):
    """A heading or an overlay written in capitals (TESTIGO NO DISPONIBLE) is not an acronym."""
    before = text[max(0, m.start() - 12):m.start()]
    after = text[m.end():m.end() + 12]
    return bool(re.search(r"[A-ZÁÉÍÓÚÑ]{2,}[ \t\u00a0]$", before) or re.match(r"[ \t\u00a0][A-ZÁÉÍÓÚÑ]{2,}", after))
