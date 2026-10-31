"""Reads a case folder: YAML files, Markdown sheets with component blocks, and cross-checks."""
import difflib
import re
from dataclasses import dataclass, field
from pathlib import Path

import yaml

from .i18n import Strings

DEFAULTS_FILE = Path(__file__).resolve().parent / "defaults.yaml"


class CaseError(Exception):
    """A problem in the case files, with the file and line when known."""

    def __init__(self, message, file=None, line=None):
        self.file = file
        self.line = line
        where = ""
        if file:
            where = str(file) + (f":{line}" if line else "") + ": "
        super().__init__(where + message)


# --- YAML without surprises ---------------------------------------------------
# YAML 1.1 turns 07:12 into a number (sexagesimal) and "no" into False. A case is full of
# times and short answers, so this loader only recognises decimal integers, decimals with
# a dot, and true/false.

class _Loader(yaml.SafeLoader):
    pass


_Loader.yaml_implicit_resolvers = {
    k: [r for r in v if r[0] not in ("tag:yaml.org,2002:bool", "tag:yaml.org,2002:int",
                                      "tag:yaml.org,2002:float", "tag:yaml.org,2002:timestamp")]
    for k, v in yaml.SafeLoader.yaml_implicit_resolvers.items()
}
_Loader.add_implicit_resolver("tag:yaml.org,2002:bool", re.compile(r"^(?:true|false)$"), list("tf"))
_Loader.add_implicit_resolver("tag:yaml.org,2002:int", re.compile(r"^-?(?:0|[1-9][0-9]*)$"), list("-0123456789"))
_Loader.add_implicit_resolver("tag:yaml.org,2002:float", re.compile(r"^-?(?:0|[1-9][0-9]*)\.[0-9]+$"), list("-0123456789"))


def read_yaml(text, file=None, base_line=0):
    try:
        return yaml.load(text, Loader=_Loader)
    except yaml.YAMLError as e:
        line = None
        mark = getattr(e, "problem_mark", None)
        if mark is not None:
            line = base_line + mark.line + 1
        raise CaseError("invalid YAML: " + str(getattr(e, "problem", e)), file, line) from None


def read_yaml_file(path):
    path = Path(path)
    if not path.exists():
        raise CaseError("file not found", path)
    data = read_yaml(path.read_text(encoding="utf-8"), path)
    return data if data is not None else {}


# --- Markdown sheets ------------------------------------------------------------

@dataclass
class Block:
    type: str            # "md" for prose; otherwise the component name
    arg: str             # whatever follows the name on the ```name argument line
    content: str
    line: int


@dataclass
class Sheet:
    id: str              # file name without extension
    path: Path
    data: dict           # front matter
    blocks: list = field(default_factory=list)

    def get(self, key, default=None):
        return self.data.get(key, default)


_FENCE = re.compile(r"^(`{3,}|~{3,})\s*([A-Za-z][\w-]*)?[ \t]*(.*?)\s*$")


def split_blocks(text, base_line=1):
    """Splits a body into Markdown prose and ```component blocks."""
    blocks = []
    prose, prose_start = [], base_line
    lines = text.split("\n")
    i = 0
    while i < len(lines):
        m = _FENCE.match(lines[i])
        if m and m.group(2):
            fence, kind, arg = m.group(1), m.group(2), m.group(3)
            j = i + 1
            while j < len(lines) and not lines[j].strip().startswith(fence[0] * len(fence)):
                j += 1
            if j >= len(lines):
                raise CaseError(f"the ```{kind} block is never closed", None, base_line + i)
            if any(l.strip() for l in prose):
                blocks.append(Block("md", "", "\n".join(prose), prose_start))
            blocks.append(Block(kind.lower(), arg, "\n".join(lines[i + 1:j]), base_line + i))
            prose, prose_start = [], base_line + j + 1
            i = j + 1
            continue
        prose.append(lines[i])
        i += 1
    if any(l.strip() for l in prose):
        blocks.append(Block("md", "", "\n".join(prose), prose_start))
    return blocks


def read_sheet(path):
    path = Path(path)
    return parse_sheet(path.read_text(encoding="utf-8"), path, path.stem)


def parse_sheet(text, path, sheet_id):
    """A sheet from its text: front matter and blocks. `path` is only used in error messages."""
    text = text.replace("\r\n", "\n")
    data, body, body_line = {}, text, 1
    if text.startswith("---\n"):
        end = text.find("\n---", 4)
        if end < 0:
            raise CaseError("the front matter (---) is never closed", path, 1)
        data = read_yaml(text[4:end], path, 1) or {}
        if not isinstance(data, dict):
            raise CaseError("the front matter must be a list of key: value fields", path, 2)
        rest = text[end + 4:]
        body_line = text[:end + 4].count("\n") + 1
        if rest.startswith("\n"):
            rest = rest[1:]
            body_line += 1
        body = rest
    try:
        blocks = split_blocks(body, body_line)
    except CaseError as e:
        raise CaseError(str(e).split(": ", 1)[-1], path, e.line) from None
    return Sheet(sheet_id, path, data, blocks)


def read_sheet_folder(folder):
    folder = Path(folder)
    if not folder.is_dir():
        return []
    return [read_sheet(p) for p in sorted(folder.glob("*.md"))]


# --- The whole case ---------------------------------------------------------------

@dataclass
class Case:
    root: Path               # the case folder
    lang: str                # language being exported
    lang_root: Path          # root/languages/<lang>
    data: dict               # case.yaml (neutral) merged with languages/<lang>/case.yaml
    suspects: list
    card_groups: list
    kit: list                # sheets
    dossier: dict            # id -> Sheet
    guide: list              # sheets
    strings: Strings
    warnings: list = field(default_factory=list)
    neutral: dict = field(default_factory=dict, repr=False)   # case.yaml (neutral) alone: the figures come from it
    _figures: dict = field(default=None, repr=False)

    @property
    def title(self):
        return self.data["title"]

    def get(self, key, default=None):
        return self.data.get(key, default)

    def t(self, key, **kw):
        return self.strings(key, **kw)

    def suspect(self, letter):
        for s in self.suspects:
            if s.get("letter") == letter:
                return s
        return None

    @property
    def sections(self):
        return (self.get("dossier", {}) or {}).get("sections", []) or []

    @property
    def paper(self):
        return str(self.get("paper", "letter")).lower()

    @property
    def figures(self):
        """The game's figures (opencase/defaults.yaml) with the ones the case changes in its neutral case.yaml."""
        if self._figures is None:
            self._figures = resolve_figures(self.neutral, self.root / "case.yaml")
        return self._figures

    def engine_sheets(self, doc):
        """`engine_sheets` in case.yaml for one document (kit, guide): False, or a dict with `after` and `skip`.
        By default the engine's sheets go into the kit and the guide."""
        value = self.get("engine_sheets", True)
        if isinstance(value, dict):
            value = value.get(doc, True)
        if value is True or value is None:
            return {}
        if not value:
            return False
        if not isinstance(value, dict):
            raise CaseError(f"engine_sheets.{doc} must be true, false or {{after: ..., skip: [...]}}",
                            self.root / "case.yaml")
        return value

    @property
    def uses_engine(self):
        """False when the case turns the engine's sheets off everywhere (it still carries its own rules)."""
        return bool(self.engine_sheets("kit") is not False or self.engine_sheets("guide") is not False)


def load_defaults():
    return read_yaml_file(DEFAULTS_FILE)


# Keys of the neutral case.yaml besides the figures of opencase/defaults.yaml (see docs/case-format.md).
NEUTRAL_KEYS = ("brand", "paper", "base_language", "languages", "published", "teams", "players_per_team",
                "brand_footer", "ink_saver", "dossier", "site", "engine_sheets", "score_bonus")


def resolve_figures(data, path=None):
    """Defaults first, then the case: a key of defaults.yaml that the case also has takes the case's value
    (dicts are merged key by key). `data` is the neutral case.yaml; a key in it that is neither a figure
    nor one of NEUTRAL_KEYS is taken for a misspelt figure and stops the export."""
    defaults = load_defaults()
    for key in data:
        if key not in defaults and key not in NEUTRAL_KEYS:
            near = difflib.get_close_matches(key, list(defaults) + list(NEUTRAL_KEYS), n=1)
            hint = f" (did you mean '{near[0]}'?)" if near else ""
            raise CaseError(f"'{key}' is not a key of case.yaml{hint}; the figures of the game are in "
                            "opencase/defaults.yaml", path)
    out = {}
    for key, value in defaults.items():
        mine = data.get(key)
        if isinstance(value, dict):
            merged = dict(value)
            if isinstance(mine, dict):
                for k, v in mine.items():
                    if k not in value:
                        raise CaseError(f"'{key}.{k}' is not a figure of the game (see opencase/defaults.yaml)", path)
                    merged[k] = v
            elif mine is not None:
                raise CaseError(f"'{key}' must be a list of key: value fields, like in opencase/defaults.yaml", path)
            out[key] = merged
        else:
            out[key] = value if mine is None else mine
    return out


def normalize_code(code):
    """E17·B, E17 · B and E17-B are the same code."""
    return re.sub(r"\s*[·\-]\s*", "·", str(code).strip()).upper()


def case_languages(root):
    """(base language, all languages) as declared in the neutral case.yaml."""
    neutral = read_yaml_file(Path(root).resolve() / "case.yaml")
    langs = neutral.get("languages") or [neutral.get("base_language", "es")]
    return neutral.get("base_language", langs[0]), list(langs)


def load_case(root, lang=None):
    root = Path(root).resolve()
    if not (root / "case.yaml").exists():
        raise CaseError("there is no case.yaml in this folder", root)
    neutral = read_yaml_file(root / "case.yaml")
    base, languages = case_languages(root)
    lang = lang or base
    if lang not in languages:
        raise CaseError(f"the case has no '{lang}' language (it declares: {', '.join(languages)})", root / "case.yaml")
    lang_root = root / "languages" / lang
    if not (lang_root / "case.yaml").exists():
        raise CaseError(f"missing languages/{lang}/case.yaml", root)
    texts = read_yaml_file(lang_root / "case.yaml")
    if not texts.get("title"):
        raise CaseError("the field 'title' is missing", lang_root / "case.yaml")

    for key in list(load_defaults()) + ["score_bonus", "engine_sheets"]:
        if key in texts:
            raise CaseError(f"'{key}' is the same in every language: write it in the neutral case.yaml, "
                            f"not in languages/{lang}/case.yaml", lang_root / "case.yaml")
    data = {**neutral, **{k: v for k, v in texts.items() if k not in ("dossier", "strings")}}
    data["language"] = lang
    # Dossier: the order and contents of the sections are neutral; titles and notes are translated.
    text_dossier = texts.get("dossier", {}) or {}
    text_sections = text_dossier.get("sections", {}) or {}
    sections = []
    for sec in (neutral.get("dossier", {}) or {}).get("sections", []) or []:
        sections.append({**sec, **(text_sections.get(sec.get("id"), {}) or {})})
    data["dossier"] = {**text_dossier, "sections": sections}

    suspects = []
    if (lang_root / "suspects.yaml").exists():
        suspects = read_yaml_file(lang_root / "suspects.yaml").get("suspects", []) or []
    card_groups = []
    if (lang_root / "cards.yaml").exists():
        card_groups = read_yaml_file(lang_root / "cards.yaml").get("groups", []) or []
    case = Case(root, lang, lang_root, data, suspects, card_groups,
                read_sheet_folder(lang_root / "kit"),
                {s.id: s for s in read_sheet_folder(lang_root / "dossier")},
                read_sheet_folder(lang_root / "guide"),
                Strings.load(lang, texts.get("strings")), neutral=neutral)
    validate(case)
    return case


def validate(case):
    """Checks cross references. Errors stop the export; warnings do not."""
    case_file = case.root / "case.yaml"
    case.figures  # a misspelt key or a figure that is not one stops here, also with --check
    from .acronyms import glossary
    glossary(case)  # a glossary that is not ACRONYM: long form stops here
    seen = {}
    for sec in case.sections:
        for pid in sec.get("items", []) or []:
            if pid not in case.dossier:
                raise CaseError(f"section '{sec.get('id')}' lists '{pid}', but languages/{case.lang}/dossier/{pid}.md "
                                "does not exist", case_file)
            if pid in seen:
                raise CaseError(f"'{pid}' is in two sections ('{seen[pid]}' and '{sec.get('id')}')", case_file)
            seen[pid] = sec.get("id")
    for pid in case.dossier:
        if pid not in seen:
            case.warnings.append(f"dossier/{pid}.md is in no section of case.yaml, so it is not exported")
    codes = {normalize_code(s.get("code", s.id)) for s in case.dossier.values()}
    seen_cards = set()
    cards_file = case.lang_root / "cards.yaml"
    for g in case.card_groups:
        for c in g.get("cards", []) or []:
            code = c.get("code")
            if not code:
                raise CaseError(f"a card in the group '{g.get('title')}' has no code", cards_file)
            if code in seen_cards:
                case.warnings.append(f"card {code} appears twice in cards.yaml")
            seen_cards.add(code)
            for att in as_list(c.get("attach")):
                if normalize_code(att) not in codes:
                    case.warnings.append(f"card {code} attaches {att}, which is not in the dossier")
            length = len(re.sub(r"[*_`]", "", str(c.get("answer", ""))))
            if length > 420:
                case.warnings.append(f"card {code} has {length} characters (the limit is 420)")
    for sheet in list(case.dossier.values()) + case.kit + case.guide:
        for b in sheet.blocks:
            refs = re.findall(r"(?:image|portrait|file):\s*[\"']?([^\s\"'\n]+\.(?:jpe?g|png|webp|svg|gif))", b.content)
            refs += re.findall(r"!\[[^\]]*\]\(([^)\s]+)\)", b.content)
            refs += [b.arg.strip()] if b.type == "svg" and b.arg.strip() else []
            for ref in refs:
                if resolve_media(case, ref) is None:
                    raise CaseError(f"the image '{ref}' does not exist in the case folder", sheet.path, b.line)
    for s in case.suspects:
        if s.get("portrait") and resolve_media(case, s["portrait"]) is None:
            raise CaseError(f"the portrait '{s['portrait']}' does not exist in the case folder",
                            case.lang_root / "suspects.yaml")


def resolve_media(case, ref):
    """A photo or drawing: languages/<lang>/<ref> first (translated versions), then the case root."""
    for base in (case.lang_root, case.root):
        p = (base / str(ref)).resolve()
        if p.exists():
            return p
    return None


def compare_languages(base, other):
    """What a translation is missing compared with the base language. Returns a list of problems."""
    problems = []
    for folder, mine, theirs in (("kit", [s.id for s in base.kit], [s.id for s in other.kit]),
                                 ("dossier", list(base.dossier), list(other.dossier)),
                                 ("guide", [s.id for s in base.guide], [s.id for s in other.guide])):
        for missing in sorted(set(mine) - set(theirs)):
            problems.append(f"languages/{other.lang}/{folder}/{missing}.md is missing")
        for extra in sorted(set(theirs) - set(mine)):
            problems.append(f"languages/{other.lang}/{folder}/{extra}.md has no counterpart in '{base.lang}'")

    def card_codes(case):
        return [str(c.get("code")) for g in case.card_groups for c in g.get("cards", []) or []]
    a, b = card_codes(base), card_codes(other)
    for missing in [c for c in a if c not in b]:
        problems.append(f"cards.yaml ({other.lang}): card {missing} is missing")
    for extra in [c for c in b if c not in a]:
        problems.append(f"cards.yaml ({other.lang}): card {extra} does not exist in '{base.lang}'")
    sa, sb = [s.get("letter") for s in base.suspects], [s.get("letter") for s in other.suspects]
    if sa != sb:
        problems.append(f"suspects.yaml ({other.lang}): the suspects ({', '.join(map(str, sb))}) differ from "
                        f"'{base.lang}' ({', '.join(map(str, sa))})")
    return problems


def as_list(v):
    if v is None:
        return []
    if isinstance(v, (list, tuple)):
        return list(v)
    return [x.strip() for x in str(v).split(",") if x.strip()]
