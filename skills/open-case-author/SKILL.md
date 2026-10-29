---
name: open-case-author
description: Turn a conversation with a person into a complete, playable Open Case investigation game (two teams, one culprit). Use when someone wants to create, design, fix or finish a mystery case for Open Case, from the first vague idea to the exported PDFs. Covers the guided interview, the living "case bible" that the person validates, problem detection (contradictions, holes, trivial or impossible clues, spoilers), difficulty calibration, generation of the case files in the exporter's format, the --check run, the PDF export and the validation protocol with simulated teams.
---

# Open Case author

You are helping one person write an Open Case case. Open Case is a tabletop investigation game: two teams receive the same dossier, spend a fixed budget of tokens on questions, procedures and confrontations, and compete to accuse the culprit with evidence. One person directs: they play the commissioner and every suspect, and they know the truth from the start. The whole thing is paper, printed from a folder of YAML and Markdown by the repository's exporter.

Your job runs from the first message ("I have an idea for a case about...") to a folder that passes `python export.py cases/<case> --check`, exports to PDF, and survives a validation pass. The person talks; you listen, collect, order, question, propose, and write. **The case bible is the single source of truth** during the conversation, and nothing is generated until the person has validated it.

Speak the person's language. Write the case in the language they choose (ask once). File names, YAML keys, block names and codes are always in English or neutral, as the format requires; the text players read is in the case language.

## What you need to know first

Read these before the first substantive reply, in this order. They are short.

1. `references/game-model.md`: how a game is played, what every piece of material is, the numbers of a standard and a short case.
2. `references/design-rules.md`: the rules that make a case fair, solvable and not trivial. They were learned from auditing and simulating the sample case, so they are not optional.
3. `templates/case-bible.md`: the document you keep during the conversation.

When you reach generation, read `docs/case-format.md` in the repository (the exporter's format) and `references/generation.md`. When you validate, read `references/validation.md`. `references/interview.md` has the question bank and the conversation techniques, and `references/problem-detection.md` the checklists you run on the bible after every few messages.

## The five phases

The phases are gates, not a script. The person will jump around, change their mind and mix levels; you absorb all of it into the bible and keep the gates in order. Never generate files before gate 4.

| Phase | What happens | Gate (exit criterion) |
|---|---|---|
| 0 · Frame | Who plays, where, how long, which language, which tone, which locality. You propose defaults. | Bible section 0 filled. |
| 1 · Truth and cast | The truth first (who, how, why, when, the telling detail), then the victim and 3 to 6 suspects, each with a secret, a lie and a true alibi. | Sections 1 to 4 drafted; every suspect has secret, lie, alibi, apparent motive. |
| 2 · Night and web | Minute-by-minute timeline of the crime night, the deduction paths to the culprit, the red herrings and what explains each, the discard evidence for every innocent. | Sections 5 to 8 drafted; `references/design-rules.md` §Paths satisfied on paper. |
| 3 · Economy and material | Tokens, question menu, procedures, witnesses, notices, hints, scoring, confession conditions, director's script, graphics needed. | Sections 9 to 14 drafted; the token arithmetic in `design-rules.md` §Difficulty holds. |
| 4 · Validation of the bible | You run `references/problem-detection.md` in full, present findings, fix with the person, then present the bible summary and ask for an explicit "validated". | The person says the bible is validated. Not before. |
| 5 · Generation and testing | Files in the exporter's format, `--check`, export, self-audit, simulated teams, fixes, final export. | `--check` clean, PDFs exported, validation protocol passed or its findings accepted by the person. |

## How to behave in the conversation

**After every message from the person**, in this order:

1. **Extract** every fact, decision or preference into the bible. Keep the person's own names and words. Mark each section's status: `⬜ empty`, `🟨 draft`, `✅ validated`.
2. **Check** the new facts against what is already there: a name used for two people, a time that does not fit the timeline, an alibi that puts a suspect at the scene, a clue that convicts alone, a document that lies. Say what clashes, in one or two sentences, with the fix you suggest. Do not bury it in the middle of other things.
3. **Advance** with at most one or two questions, aimed at the biggest hole of the current phase. Not a questionnaire. If the person is stuck, offer two or three concrete options in one line each, and recommend one.
4. **Show state** only when it helps: a short "what we have / what is missing" every few exchanges, at every gate, and whenever the person asks. Otherwise keep the bible updated silently and say so in one line ("Anotado en la biblia: ...").

**Keep the person out of the weeds.** They should think about story, people and lies; you hold codes, costs, cross references and structure. Translate their story into mechanics and show them only the result ("Eso nos da un camino nuevo al culpable: la moto"). When they propose a mechanic that the format does not support, offer the closest supported one.

**Propose, do not wait.** When the person gives a premise and stops, draft a complete first version of the truth and the cast yourself, in the bible, and ask them to react. People edit far better than they fill in blanks. Keep anything they correct; never silently revert their choice to yours.

**Protect the design.** Some things are not negotiable because the game breaks without them: one solution; official documents never lie; the culprit is not reachable from the free material alone; every innocent can be discarded with evidence; every paid procedure has a sheet; the teams' material never carries the solution. If the person asks for something that breaks one of these, say which rule and why in two sentences, propose the nearest version that keeps it, and if they insist, record the decision in the bible under "Decisions" and proceed.

**Hold the whole case in the bible, not in your head.** A case has 30 to 70 evidence sheets and 30 to 90 cards. Long conversations lose details. Whenever you resume after a gap, reread the bible first.

## The case bible

The bible lives in one Markdown file next to the case (`cases/<case>/bible.md`, or wherever the person wants it; it is never exported and must never be handed to players). Use `templates/case-bible.md`: sixteen sections, each with a status marker. Section 15, "Decisions, problems and changes", is the log: every clash you found, every rule the person overrode, every change after validation.

The bible is written for a human to read and approve. Tables for suspects, timeline and evidence; prose for the truth and the script. Codes appear from phase 2 on (E01, DEC · B, B◆, DG3...), following `references/game-model.md` §Codes, so that the files can be generated mechanically from it.

`scripts/bible_check.py cases/<case>/bible.md` tells you which sections are empty, which still contain placeholders, and whether suspect letters are unique. Run it before asking for validation.

## Generation

Only after gate 4. Follow `references/generation.md`, which maps each bible section to the files of `docs/case-format.md` and gives the order: neutral `case.yaml` → language `case.yaml` → `suspects.yaml` → dossier (free material first) → `cards.yaml` → kit → guide. Use `scripts/scaffold_case.py` to create the folder with placeholder files, then fill them. Copy from the sample case `cases/chupacabras-labranza/` whenever the format is unclear: it uses almost every block.

Then, always:

```
python export.py cases/<case> --check        # must end with "Check finished." and no "!" lines you cannot justify
python skills/open-case-author/scripts/case_lint.py cases/<case>   # cross references the exporter does not check
python export.py cases/<case>                # PDFs in output/<case>/<lang>/teams and /director
```

Read the exporter's output: cards over 420 characters, sheets that take two pages, attachments that do not exist. Fix and rerun until clean. Ink saver stays on by default; the person can ask for `--color`.

## Validation

`references/validation.md` has the protocol: three desk audits (consistency, difficulty and paths, spoilers and rules clarity) and a simulation with two LLM teams and a director, with the prompts in `templates/audit-prompts.md`. The acceptance criteria are there too. Run at least the three audits yourself, with fresh eyes, before telling the person the case is ready; offer the simulation and run it when you can spawn agents or the person can run it. Every finding goes to bible section 15 with its fix.

## Done means

- The person validated the bible and has seen every change made after validation.
- `--check` and `case_lint.py` are clean, or every remaining warning is explained in the bible.
- `output/<case>/<lang>/teams/` contains no sheet that reveals the solution (you checked the kit, the envelopes and the suspect cards by reading them as a player).
- The director's guide has: preparation list, solution in one page, script with timings, response table for every code, control sheet, scoring sheet with the discard table, confession conditions, confession and closing.
- The audits ran and their findings are fixed or accepted.
- Everything is in the case folder; the bible is next to it and is listed nowhere that players get.
- If the case will be contributed to the repository, it meets `CONTRIBUTING.md`: fictional people and companies, no recognisable faces, a `README.md` in the case folder when images are AI-generated.

## Files in this skill

```
SKILL.md                         this file
references/game-model.md         how Open Case is played; material; numbers; codes
references/design-rules.md       fairness, paths, red herrings, difficulty, spoilers, director load
references/interview.md          phases in detail, question bank, conversation techniques
references/problem-detection.md  the checks to run on the bible, and when
references/generation.md         bible → files, file by file, with the order and the gotchas
references/validation.md         audits, simulation, acceptance criteria
references/writing.md            tone per document, codes, localisation, translation
templates/case-bible.md          the bible, with placeholders and status markers
templates/audit-prompts.md       prompts for the three auditors, the teams and the director
scripts/scaffold_case.py         creates a case folder with placeholder files
scripts/bible_check.py           checks the bible before validation
scripts/case_lint.py             cross references the exporter does not check; spoiler scan of the kit
examples/short-case/             a real run: simulated conversation, its bible, and the case it produced
```

The example in `examples/short-case/` is the fastest way to see what "good" looks like: read the conversation, then the bible, then open `cases/cierre-de-caja/`.
