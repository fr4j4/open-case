"""Markdown for sheets and short texts, with Open Case's additions.

On top of plain Markdown (bold, italics, lists, tables):
  ==text==             yellow highlighter over printed text
  [true] [false]       pills for the director's guide (also [key], [attached],
  [red-herring]        [procedure], [pending]); their words come from the language strings
  `E01`                a code, in the codes typeface
  {.small}             on its own line right after a paragraph: smaller type
"""
import html
import re

import markdown as _markdown

# pill token -> (CSS modifier of the design system, strings key)
PILLS = {
    "true": ("oc-pastilla--v", "pills.is_true"),
    "false": ("oc-pastilla--m", "pills.is_false"),
    "key": ("oc-pastilla--k", "pills.key"),
    "red-herring": ("oc-pastilla--k", "pills.red_herring"),
    "attached": ("oc-pastilla--d", "pills.attached"),
    "procedure": ("oc-pastilla--d", "pills.procedure"),
    "pending": ("", "pills.pending"),
}
_PILL_RE = re.compile(r"\[(" + "|".join(re.escape(k) for k in PILLS) + r")\](?!\()", re.I)
_HIGHLIGHT_RE = re.compile(r"==(?=\S)(.+?)(?<=\S)==")

_strings = None


def use_strings(strings):
    """Sets the language strings used for the words inside pills."""
    global _strings
    _strings = strings


def e(text):
    """Escapes plain text for HTML."""
    return html.escape("" if text is None else str(text), quote=True)


def _pill(m):
    css, key = PILLS[m.group(1).lower()]
    word = _strings(key) if _strings else m.group(1).lower()
    return f'<span class="oc-pastilla {css}">{word}</span>'


def _after(htm):
    htm = _HIGHLIGHT_RE.sub(r'<mark class="oc-resaltado">\1</mark>', htm)
    htm = _PILL_RE.sub(_pill, htm)
    # Markdown tables are wrapped like the design system's tables.
    htm = re.sub(r"<table>", '<div class="oc-tabla"><table>', htm)
    htm = re.sub(r"</table>", "</table></div>", htm)
    return htm


def _md():
    return _markdown.Markdown(extensions=["tables", "sane_lists", "attr_list"], output_format="html")


def md(text):
    """Block Markdown: paragraphs, lists, tables, headings."""
    if not text:
        return ""
    text = re.sub(r"(?m)^\{\.(\w[\w-]*)\}[ \t]*$", lambda m: "{: .oc-" + SMALL_CLASSES.get(m.group(1), m.group(1)) + "}", text)
    return _after(_md().convert(str(text)))


# Names usable in {.name} -> class of the design system.
SMALL_CLASSES = {"small": "pequeno"}


def line(text):
    """Inline Markdown for short fields (an answer, a caption). Keeps line breaks."""
    if text is None:
        return ""
    text = str(text).strip()
    if not text:
        return ""
    parts = [p for p in re.split(r"\n\s*\n", text)]
    out = []
    for p in parts:
        htm = _md().convert(p.replace("\n", "  \n"))
        htm = re.sub(r"^<p>(.*)</p>$", r"\1", htm.strip(), flags=re.S)
        out.append(htm)
    return _after("<br><br>".join(out) if len(out) > 1 else out[0])


def line_pre(text):
    """For blocks that keep their line breaks as written (statements, scripts, quotes):
    inline Markdown on each line, without adding <br>."""
    if text is None:
        return ""
    rows = []
    for r in str(text).strip("\n").split("\n"):
        htm = _md().convert(r) if r.strip() else ""
        rows.append(re.sub(r"^<p>(.*)</p>$", r"\1", htm.strip(), flags=re.S))
    return _after("\n".join(rows))


def plain_text(text):
    """Strips Markdown marks (to count characters or fill an alt attribute)."""
    t = re.sub(r"[*_`]|==", "", str(text or ""))
    return re.sub(r"\s+", " ", t).strip()
