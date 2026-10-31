# The game model

What a case has to contain, how a session runs, and the numbers that work. Read this once before designing anything; come back to §Numbers when you size a case and to §Codes when you write the bible from phase 2 on.

## A session

One director, two teams (A and B; the exporter allows up to four, A to D) of 3 to 7 players each, one table per team, far enough apart not to overhear. Both teams get the same material and the same chances; they compete on points.

| Phase | Standard case | Short case | What happens |
|---|---|---|---|
| Preparation | 5 min | 5 min | Teams, kit, tokens, one badge per player. The director reads "How to play" aloud. |
| Scene | 10 min | 8 min | The director reads the opening script, hands out envelope 1. Teams read. No questions yet. |
| Investigation | 30 min | 20–22 min | Teams send written requests with a token; the director answers with a card or a sheet, and marks the control sheet. Prosecutor's notices are read when the director sees fit, at about the suggested minutes. |
| Accusation | 15 min | 12–15 min | Teams fill the accusation and discard sheets. The director collects both before anyone speaks. Each team presents (2 min). The director scores, reads the confession if earned, and closes. |
| Total | 65–75 min | 45–50 min | |

The director's golden rule: **never lie as narrator and never invent a clue.** If something is not in the material: "there is no information about that".

## What a team can do with a token

Every action costs tokens from a fixed budget (16 in a standard case, 8 to 10 in a short one). Each one is a written request: code, who or which evidence, why.

| Action | Code form | Cost | What they get |
|---|---|---|---|
| Question to a suspect from the menu | `B1`, `B2`… | 1 | An answer card; sometimes it attaches a sheet. |
| Question off the menu | free text | 1 if it has an answer; free if obvious in the fiction | A spoken answer from the material. |
| Follow-up | `B3+` | 1 | Only after the card that enables it. |
| Confrontation ◆ | `B◆` + the evidence codes shown | 1, charged even if it fails | One card: a new lie, an admission, or a failed card. The most specific combination wins. |
| Procedure (diligencia) | `DG1`… `DG12`, with the target (the codes are the case's; the engine only knows the kinds, see `procedures.yaml`) | 1 (2 for the rare expensive one) | An evidence sheet. Every target has a sheet; nothing comes back blank. |
| Witness | `R1`, `TESTIGO <name>` | 1 | A witness card, sometimes with a sheet. Only once the name has appeared in their material. Witnesses never lie. |
| Expert consultation | `PER1` | 1 | A card that interprets a technical datum they already have. |
| Hint | `PISTA` | 0 tokens, −1 or −2 points | One of the ordered hints in the guide. |

What is free: envelope 1 (the opening material), the statements, envelope 2 (usually the autopsy, handed at the start of the investigation), the prosecutor's notices, the press card, and what is obvious inside the fiction (does X own a car?).

## The material and who gets it

**Teams (no spoilers, one copy per team):**

| Piece | Content |
|---|---|
| Kit | The mission (the case's story), then the engine's sheets (how to play, phases, glossary, rules, during the game, score), question menu built from the suspects and the `menu: true` cards, procedures menu with the token tracker, timeline worksheet, accusation sheet, discard sheet. |
| Envelope 1 | The opening evidence: police report, scene photos or sketch, social media, a chat group, weather, the statements of every suspect. Enough to start, never enough to convict. |
| Envelope 2 | What arrives when the investigation begins (the autopsy). |
| Suspect cards | One vertical 63 × 88 card per suspect: name, role, five facts, optional portrait (never a recognisable face). |
| Badges, tokens, request forms, envelope labels | Produced by the exporter from the YAML. |

**Director only:**

| Piece | Content |
|---|---|
| Guide | Preparation (what to print, how to arm the envelopes, the table, what is particular to the case), the engine's sheets (running the game, fair play, request log), the solution in one page, diagrams (night, deduction), the script with timings (opening, notices, press, hints), the response table for every code, the control sheet, the evaluation (scoring rubric, discard table, red-herring table, confession conditions, score sheet), the confession and the closing. |
| Complete dossier | Every evidence sheet with an index by section. Handed out one sheet at a time, only to the team that earned it. |
| Answer cards | Every card, two copies (one per team), printed 8 per sheet, 63 × 88 mm, with a common back. |

The dossier sections in the neutral `case.yaml` decide who gets what: sections with `envelope: N` go to the teams' folder; everything else goes into the director's Evidence file, ordered by code, one copy per team.

## The shape of a case

**The truth.** One culprit, one method, one motive, one window of time, and one *telling detail* the culprit could not avoid leaving (a message deleted from the victim's phone after death, a door code used at the wrong time, mud on the one finger used to unlock a phone). The truth is written first and never shown to players.

**The cast.** The victim and 3 to 6 suspects. Every suspect, including the culprit, has: an apparent motive visible from the free material, a secret they protect by lying, a lie that evidence can expose, and a true alibi (for innocents) verifiable by two sources of different origin inside the crime window. The culprit's "alibi" is true but does not cover the window (a receipt from 21:40 when the crime is at 23:15).

**The paths.** At least three independent chains of evidence lead to the culprit, each of a different type (movement or vehicle; alibi broken; what they knew; physical traces), plus a chain for the motive. Each path ends in a confrontation card. No single sheet convicts; the free material alone does not convict.

**The red herrings.** One main false lead pushed by the notices, and several smaller ones. Every red herring is something a character *chose to show* or a real coincidence, never a forged official document, and every one has evidence that explains it away (that is how teams score for it).

**The economy.** Tokens, costs, what is free, how many questions per suspect, how many procedures, which ones have per-suspect sheets, what the notices say and when, which hints exist and what they cost, the scoring table and the confession conditions. The economy is tuned so that a team that plays well spends most of its tokens and a team that guesses early still has to prove it.

## Numbers that work

| | Standard (65–75 min) | Short (45–50 min) |
|---|---|---|
| Suspects | 5–6 | 3–4 |
| Tokens per team | 16 | 8–10 |
| Evidence sheets (dossier) | 50–70 (6–8 free) | 25–35 (5–7 free) |
| Menu questions per suspect | 4 | 3 |
| Confrontation cards for the culprit | 8–12 | 4–6 |
| Confrontation cards per innocent | 2 | 1–2 |
| Follow-ups | 6–8 | 2–4 |
| Witnesses | 8–10 | 3–4 |
| Procedures in the menu | 12–14, with a per-suspect sheet for cell tower, vehicle, belongings, bank | 8–9 |
| Notices | 2 (suggested minutes 10 and 20) + press card | 2 (`notice_minutes: [7, 14]`) |
| Hints | 5, ordered | 3, ordered |
| Minimum tokens to confession (knowing what to ask) | 7–9 | 5–7 |
| Expected spend of a good team | 10–16 | 7–10 |
| Pages in the director's guide | 9–12 | 6–8 |

Rules of thumb: the minimum route to the confession costs at least 40 % of the budget; sweeping one procedure across every suspect should be possible but should cost a third of the budget; two teams of five people send about one request per minute of investigation, so plan for 25–30 requests in a standard case and 15–20 in a short one.

## Codes

Codes are the plumbing of the game: they appear on cards, sheets, menus and the director's tables, and the exporter cross-checks some of them. Use them from phase 2 of the bible on.

| What | Form | Examples |
|---|---|---|
| Evidence | `E` + two digits; a lowercase letter if split; `·` + suspect letter if per suspect | `E01`, `E13b`, `E17·B` (file name `E17-B.md`) |
| Statement | `DEC · ` + letter (file `DEC-B.md`) | `DEC · B` |
| Suspect | one unique letter, the initial when possible | B, H, J, P, T, C |
| Menu question | letter + number | `B1`…`B4` |
| Confrontation request | letter + `◆`; the card obtained has a number | `B◆` → `B5`, `B6` |
| Follow-up | base code + `+` | `B3+` |
| Failed confrontation | letter + `✕` | `B✕` |
| Procedure | `DG` + number, optional letter | `DG2`, `DG2W` |
| Witness | `R1`, `TESTIGO`, or initials + 1 | `R1`, `K1`, `CO1` |
| Expert | `PER1` | |
| Notices, press, hints, closing | word + number | `AVISO 1`, `PRENSA`, `PISTA 1` |
| Envelope | `Sobre` + number in opening order (translated per language) | `Sobre 1` |
| Teams | `Equipo A`, `Equipo B`; never colours as names | |

In Markdown, codes are written in backticks (`` `E01` ``) so they print in the codes typeface. In cards and YAML, `attach` and `follow_up` use the bare code. Keep codes identical in every language of the case.

## Card types

`answer` (default), `follow-up`, `confrontation`, `failed`, `witness`, `wildcard` ("that proves nothing", "witness not available", "nothing to add"), `notice`, `press`, `hint`, `closing`. The last four print on their own sheet because they are used at other moments. Every answer has at most 420 characters; a longer one is split into "(1 de 2)" and "(2 de 2)". Cards that the director hands over never carry director's notes; the notes live in the guide's response table.

## Sources

The sample case `cases/chupacabras-labranza/` and the brand guide in `design/guide/` (especially `08-redaccion.md`, nomenclature and tone, and `09-checklist.md`, what every artefact must pass). The exporter's format is `docs/case-format.md`.
