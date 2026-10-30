#!/usr/bin/env python3
"""Checks a case bible before the author validates it.

    python bible_check.py cases/<case>/bible.md

Reports: sections missing or still empty (⬜), placeholders left ({…}, TODO, ???, TBD),
sections without a status marker, duplicated suspect letters, and the three numbers of
section 6 if they are written. Exit code 1 when something must be fixed, 0 otherwise.
Standard library only.
"""
import re
import sys
from pathlib import Path

SECTIONS = [
    "0 · Frame", "1 · The truth", "2 · Setting and time", "3 · The victim", "4 · Suspects",
    "5 · Timeline of the night", "6 · Deduction paths", "7 · Red herrings", "8 · Evidence",
    "9 · Questions and cards", "10 · Procedures and witnesses", "11 · Notices, press, hints",
    "12 · Economy and scoring", "13 · Director's script", "14 · Graphics",
    "15 · Decisions, problems and changes",
]
PLACEHOLDER = re.compile(r"\{[^}\n]{1,80}\}|\bTODO\b|\bTBD\b|\?\?\?")
STATUS = {"⬜": "empty", "🟨": "draft", "✅": "validated"}


def main(path):
    text = Path(path).read_text(encoding="utf-8")
    lines = text.splitlines()
    problems, notes = [], []

    # Split into sections by "## " headings.
    heads = [(i, l) for i, l in enumerate(lines) if l.startswith("## ")]
    bodies = {}
    for n, (i, head) in enumerate(heads):
        end = heads[n + 1][0] if n + 1 < len(heads) else len(lines)
        bodies[head[3:].strip()] = (i + 1, lines[i + 1:end])

    for name in SECTIONS:
        number = name.split(" · ")[0]
        found = next((h for h in bodies if h.startswith(number + " ")), None)
        if not found:
            problems.append(f"section missing: '{name}'")
            continue
        marker = next((m for m in STATUS if m in found), None)
        if not marker:
            problems.append(f"section '{found}' has no status marker (⬜ 🟨 ✅)")
        elif marker == "⬜":
            problems.append(f"section '{found}' is marked empty")
        elif marker == "🟨":
            notes.append(f"section '{found}' is still a draft")
        start, body = bodies[found]
        content = " ".join(l.strip() for l in body if l.strip() and not l.strip().startswith("|---"))
        if len(content) < 80:
            problems.append(f"section '{found}' has almost no content")
        for k, l in enumerate(body):
            if l.lstrip().startswith(">"):
                continue
            for m in PLACEHOLDER.finditer(l):
                problems.append(f"line {start + k + 1}: placeholder left: {m.group(0)}")

    # Suspect letters in section 4: first column of table rows, one or two characters.
    sec4 = next((bodies[h] for h in bodies if h.startswith("4 ")), None)
    if sec4:
        letters = []
        for l in sec4[1]:
            m = re.match(r"\|\s*([A-ZÑ]{1,2})\s*\|", l)
            if m:
                letters.append(m.group(1))
        dup = {x for x in letters if letters.count(x) > 1}
        if dup:
            problems.append(f"duplicated suspect letters in section 4: {', '.join(sorted(dup))}")
        if letters:
            notes.append(f"suspects: {len(letters)} ({', '.join(letters)})")
        culprit = re.search(r"Culprit:\s*\*?([A-ZÑ]{1,2})", "\n".join(sec4[1]))
        if culprit and letters and culprit.group(1) == letters[0]:
            notes.append("the culprit is listed first in section 4; the kit will show them first (design-rules §27)")

    # The three numbers of section 6.
    sec6 = next((bodies[h] for h in bodies if h.startswith("6 ")), None)
    if sec6:
        joined = "\n".join(sec6[1])
        for label in ("Minimum route", "Cost to discard", "Cost to sweep"):
            m = re.search(label + r"[^\n]*?(\d+)\s*tokens", joined)
            if m:
                notes.append(f"{label}: {m.group(1)} tokens")
            else:
                problems.append(f"section 6: '{label}' is not counted")

    for p in problems:
        print("! " + p)
    for n in notes:
        print("· " + n)
    print("Bible check finished." + (" Fix the lines marked with !." if problems else " Ready to ask for validation."))
    return 1 if problems else 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(2)
    sys.exit(main(sys.argv[1]))
