"""The print plan: which documents the director prints, how many copies, on what paper and when each
one is handed out. It is a rule of the game, the same in every case; the case only brings its data
(teams, tokens, sheets, cards).

The plan is counted from the data (sheets, the pages each one declares, cards), not measured in a
browser, so it is the same on every machine. tools/check_print.py exports the case and checks that
every PDF has the pages the plan says and that no sheet is too full for its pages.

Two packages:
  team       printed for every team and handed over whole before playing (badges, tokens, requests,
             suspects, kit, envelopes)
  director   handed out little by little (guide, the Evidence file, cards, card backs, envelope labels)

Options of the export that change the plan (cli.py): --teams N (the first N teams of the case) and
--chat (the Evidence file is sent as images through a chat group instead of printed).
"""
import math
import re
from dataclasses import dataclass

from .loader import CaseError

SHEET_LIMIT = 0.95   # a sheet may fill at most this share of the pages it declares (see tools/check_print.py)
TOKENS_PER_SHEET = 35
CARDS_PER_SHEET = 8
INDEX_ROWS_PER_SHEET = 23


@dataclass
class Item:
    key: str            # the document's key (as in --only): badges, tokens, kit, envelopes:1, guide, evidence...
    package: str        # team | director
    folder: str         # teams | director (the output folder)
    file: str           # PDF name without extension
    name: str           # the document's title
    pages: int          # pages of the PDF
    paper: str          # bond | cardstock | labels
    copies: int         # how many times the whole PDF is printed (0: not printed, sent through the chat)
    per_team: bool = False    # the PDF already holds each team's own pages (print it once)
    duplex: bool = False      # every other page is the back of the one before
    optional: bool = False
    backs_for: str = ""       # key of the document whose sheets this one goes on the back of
    what: str = ""
    when: str = ""

    @property
    def sheets(self):
        """Physical sheets of one copy: duplex documents print two pages on one sheet."""
        return self.pages // 2 if self.duplex else self.pages


def teams(case):
    return [str(t) for t in case.get("teams", ["A", "B"])]


def chat_mode(case):
    return bool(case.get("_chat"))


def sheet_pages(sheet):
    """The pages a sheet declares with `pages: N` in its front matter (1 by default)."""
    value = sheet.data.get("pages", 1)
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise CaseError(f"pages must be a whole number of 1 or more (it is '{value}')", sheet.path)
    return value


def natural_key(text):
    """E08 < E09 < E10 < E13a < E13b < E15 · B: the numbers inside a code compare as numbers."""
    return [int(p) if p.isdigit() else p.casefold() for p in re.split(r"(\d+)", str(text)) if p]


def envelope_sections(case):
    """{envelope number: [sections]} in the order of case.yaml."""
    out = {}
    for sec in case.sections:
        if sec.get("envelope") is not None:
            out.setdefault(sec["envelope"], []).append(sec)
    return out


def evidence_ids(case):
    """The sheets of the Evidence file: every sheet that is in no envelope, ordered by its code."""
    ids = [pid for sec in case.sections if sec.get("envelope") is None for pid in sec.get("items", []) or []]
    return sorted(ids, key=lambda pid: (natural_key(case.dossier[pid].get("code", pid)), natural_key(pid)))


def where(case):
    """{sheet id: where the director finds it}: "Envelope 1", "Envelope 2" or "Evidence"."""
    out = {}
    for sec in case.sections:
        for pid in sec.get("items", []) or []:
            out[pid] = (case.t("envelope", n=sec["envelope"]) if sec.get("envelope") is not None
                        else case.t("print.evidence.title"))
    return out


def index_rows(case):
    """Rows of the evidence index, the annex of the guide: a heading per section, then its sheets (the
    sections of the Evidence file by code, as they are printed). Sheets in a row that print the same code
    (E13b and E13b-2, one piece of evidence on two sheets) share one row: ("sheet", [sheets], place)."""
    from .loader import normalize_code
    places = where(case)
    rows = []
    for sec in case.sections:
        items = list(sec.get("items", []) or [])
        if sec.get("envelope") is None:
            items.sort(key=lambda pid: (natural_key(case.dossier[pid].get("code", pid)), natural_key(pid)))
        rows.append(("section", sec, None))
        for pid in items:
            s = case.dossier[pid]
            last = rows[-1]
            if (last[0] == "sheet" and last[2] == places[pid]
                    and normalize_code(last[1][0].get("code", last[1][0].id)) == normalize_code(s.get("code", pid))):
                last[1].append(s)
            else:
                rows.append(("sheet", [s], places[pid]))
    return rows


def index_sheet_count(case):
    return math.ceil(len(index_rows(case)) / INDEX_ROWS_PER_SHEET) if case.sections else 0


def _card_counts(case):
    from .cards import split_cards
    answers, separate = split_cards(case)
    return len(answers) + len(separate), math.ceil(len(answers) / CARDS_PER_SHEET) + math.ceil(len(separate) / CARDS_PER_SHEET)


def tokens_per_team(case):
    f = case.figures
    return int(f["tokens_per_team"]), int(f["alibi_tokens_per_team"])


def plan(case):
    """The print plan of the case, in the order the material is put together."""
    from . import templates
    t = case.t
    team_list = teams(case)
    n = len(team_list)
    items = []

    def doc_file(number, name_key):
        return f"{number}_{t(f'docs.{name_key}.name')}"

    tokens, alibis = tokens_per_team(case)
    all_tokens = tokens + alibis

    # --- The team package -----------------------------------------------------------------
    players = int(case.get("players_per_team", 7))
    items.append(Item("badges", "team", "teams", doc_file("11", "badges"), t("docs.badges.title"),
                      math.ceil(players / CARDS_PER_SHEET) * n, "cardstock", 1, per_team=True,
                      what=t("print.what.badges", n=players), when=t("print.when.start")))
    token_sheets = math.ceil(all_tokens / TOKENS_PER_SHEET)
    items.append(Item("tokens", "team", "teams", doc_file("12", "tokens"), t("docs.tokens.title"),
                      token_sheets * 2 * n, "cardstock", 1, per_team=True, duplex=True,
                      what=t("print.what.tokens_alibi" if alibis else "print.what.tokens", tokens=tokens, alibi=alibis),
                      when=t("print.when.start")))
    items.append(Item("requests", "team", "teams", doc_file("13", "requests"), t("docs.requests.title"),
                      math.ceil(all_tokens / CARDS_PER_SHEET), "bond", n, optional=True,
                      what=t("print.what.requests", n=math.ceil(all_tokens / CARDS_PER_SHEET) * CARDS_PER_SHEET,
                             tokens=all_tokens),
                      when=t("print.when.requests")))
    if case.suspects:
        items.append(Item("suspects", "team", "teams", doc_file("10", "suspects"), t("docs.suspects.title"),
                          math.ceil(len(case.suspects) / CARDS_PER_SHEET), "cardstock", n,
                          what=t("print.what.suspects", n=len(case.suspects)), when=t("print.when.start")))
    if case.kit:
        kit = templates.sheets_for(case, "kit", case.kit)
        items.append(Item("kit", "team", "teams", doc_file("01", "kit"), t("docs.kit.title"),
                          sum(sheet_pages(s) for s in kit), "bond", n,
                          what=t("print.what.kit"), when=t("print.when.start")))
    labels = {int(env.get("number", 0) or 0): env for env in case.get("envelope_labels", []) or []
              if str(env.get("number", "")).isdigit()}
    for k, (num, secs) in enumerate(envelope_sections(case).items(), start=2):
        ids = [pid for sec in secs for pid in sec.get("items", []) or []]
        codes = [str(case.dossier[pid].get("code", pid)) for pid in ids]
        when = (labels.get(int(num)) or {}).get("when") if str(num).isdigit() else None
        items.append(Item(f"envelopes:{num}", "team", "teams", f"{k:02d}_{t('docs.envelope_file', n=num)}",
                          t("envelope", n=num), sum(sheet_pages(case.dossier[p]) for p in ids), "bond", n,
                          what=", ".join(dict.fromkeys(codes)),
                          when=_capital(when) if when else t("print.when.envelope", n=num)))

    # --- The director's package -------------------------------------------------------------
    if case.guide:   # its cover, its sheets and the evidence index
        guide = templates.sheets_for(case, "guide", case.guide)
        items.append(Item("guide", "director", "director", doc_file("01", "guide"), t("docs.guide.title"),
                          1 + sum(sheet_pages(s) for s in guide) + index_sheet_count(case), "bond", 1,
                          what=t("print.what.guide"), when=t("print.when.guide")))
    evidence = evidence_ids(case)
    if evidence:
        chat = chat_mode(case)
        items.append(Item("evidence", "director", "director", f"02_{t('print.evidence.name')}",
                          t("print.evidence.title"), sum(sheet_pages(case.dossier[p]) for p in evidence), "bond",
                          0 if chat else n, what=t("print.what.evidence", n=len(evidence)),
                          when=t("print.when.evidence_chat" if chat else "print.when.evidence")))
    n_cards, card_sheets = _card_counts(case)
    if n_cards:
        items.append(Item("cards", "director", "director", doc_file("03", "cards"), t("docs.cards.title"),
                          card_sheets, "cardstock", n, what=t("print.what.cards", n=n_cards),
                          when=t("print.when.cards")))
        items.append(Item("card-backs", "director", "director", doc_file("04", "card_backs"),
                          t("docs.card_backs.title"), 1, "cardstock", card_sheets * n, backs_for="cards",
                          what=t("print.what.card_backs"), when=t("print.when.card_backs")))
    envelope_labels = case.get("envelope_labels", []) or []
    if envelope_labels:
        items.append(Item("labels", "director", "director", doc_file("05", "envelope_labels"),
                          t("docs.envelope_labels.title"), math.ceil(len(envelope_labels) * n / CARDS_PER_SHEET),
                          "labels", 1, what=t("print.what.labels", n=len(envelope_labels) * n),
                          when=t("print.when.labels")))
    return items


def totals(items):
    """Pages of bond, sheets of card stock (backs go on the reverse, so they add none) and sheets of labels."""
    bond = sum(i.pages * i.copies for i in items if i.paper == "bond")
    card = sum(i.sheets * i.copies for i in items if i.paper == "cardstock" and not i.backs_for)
    labels = sum(i.sheets * i.copies for i in items if i.paper == "labels")
    return {"bond": bond, "cardstock": card, "labels": labels}


def copies_text(case, item):
    t = case.t
    if item.copies == 0:
        text = t("print.copies.chat")
    elif item.per_team:
        text = t("print.copies.per_team")
    elif item.backs_for:
        text = t("print.copies.backs", n=item.copies)
    elif item.package == "team" or item.copies > 1:
        text = t("print.copies.uncollated" if item.package == "director" else "print.copies.n", n=item.copies)
    else:
        text = str(item.copies)
    return text + (t("print.copies.optional") if item.optional else "")


def size_text(case, item):
    t = case.t
    n = len(teams(case))
    if item.paper == "bond":
        return t("print.size.page" if item.pages == 1 else "print.size.pages", n=item.pages)
    if item.per_team:
        per = item.sheets // n if n else item.sheets
        key = "print.size.duplex_per_team" if item.duplex else "print.size.sheet_per_team"
        return t(key + ("" if per == 1 else "_many"), n=per)
    return t("print.size.sheet" if item.sheets == 1 else "print.size.sheets", n=item.sheets)


def paper_text(case, item):
    return case.t(f"print.paper.{item.paper}" + ("_duplex" if item.duplex or item.backs_for else ""))


def summary(case, items=None):
    """"With 4 teams: 333 pages of bond, 53 sheets of card stock and 1 of labels." """
    items = plan(case) if items is None else items
    tot = totals(items)
    return case.t("print.totals", teams=len(teams(case)), bond=tot["bond"], cardstock=tot["cardstock"],
                  labels=tot["labels"])


def readme(case, date, mode):
    """The LEEME/README next to the PDFs, written from the same plan as the table in the guide."""
    t = case.t
    items = plan(case)
    out = [case.title, t("print.readme.made", date=date),
           t("print.readme.teams", n=len(teams(case)), names=", ".join(teams(case))), ""]
    for package in ("team", "director"):
        out.append(t(f"print.readme.{package}"))
        for i in items:
            if i.package != package:
                continue
            out.append(f"  {i.folder}/{i.file}.pdf")
            out.append(f"      {i.what} · {copies_text(case, i)} · {paper_text(case, i)} · {size_text(case, i)}")
            out.append(f"      {i.when}")
        out.append("")
    out += [summary(case, items), "", t("print.readme.actual_size"), "", mode, ""]
    return "\n".join(out)


def _capital(text):
    text = str(text).strip()
    return text[:1].upper() + text[1:]
