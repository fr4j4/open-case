# Generation: from the bible to the case folder

Only after the person validated the bible. The format is `docs/case-format.md` in the repository; this file tells you which bible section feeds which file, in which order, and the mistakes that cost the most time. When a block or field is unclear, open the same file in `cases/chupacabras-labranza/` and copy its shape.

## 0 · Scaffold

```
python skills/open-case-author/scripts/scaffold_case.py cases/<slug> --lang <lang> --title "<Title>" --suspects B,H,J,P
```

Creates `case.yaml`, `languages/<lang>/{case.yaml,suspects.yaml,cards.yaml}`, the kit and guide sheets with placeholder front matter, `dossier/E01.md`, `dossier/DEC-<letter>.md` for each suspect, `diagrams/` and `photos/`. Every placeholder is `TODO`, so a grep finds what is left. The slug is lowercase ASCII with hyphens.

Put the bible next to it as `cases/<slug>/bible.md`. The exporter ignores it; `.gitignore` it if the person does not want it in the repository.

## 1 · Neutral `case.yaml` ← bible §0, §8, §12

`paper`, `base_language`, `languages`, `published: false` (the scaffold writes it: a new case stays off the website until it has been validated by playing it with real people; never set it to true yourself, and tell the person that this is the step that publishes it), `teams`, `tokens_per_team`, `players_per_team`, optionally `alibi_tokens_per_team`, `brand_footer` (leave the default), `ink_saver` (leave the default on), and `dossier.sections`.

Sections come from the evidence table (§8): one section per "how obtained" group, in this order: opening (`envelope: 1`), statements (`envelope: 1`), investigation start (`envelope: 2`, the autopsy), handed with an answer, procedures, notices. Every dossier file appears in exactly one section; the exporter refuses duplicates and warns about orphans.

## 2 · `languages/<lang>/case.yaml` ← bible §0, §13

`title`, `version` ("Versión 1 · <month year>"), `tagline` (the brand's), `badge` (title and two-line unit), `kit.description` and `kit.cover_note`, `guide.description` and `guide.cover_note`, `dossier.title`, `kicker`, `description`, `printed_description`, `dossier.sections.<id>` with `title` and `note` for every section id of the neutral file, `envelope_labels` (one per envelope: number, when, description, contents, footer), `glossary` (every acronym of the case with its long form; see `writing.md`, "Acronyms").

## 3 · `suspects.yaml` ← bible §4

One entry per suspect, in the order the kit will show them (not the culprit first). `letter`, `name`, `short_name` if long, `role`, up to five `facts` (age, occupation, relation, lives in, description), `portrait` only if the image exists.

## 4 · Dossier ← bible §8, §5, §4

Write the free material first (it is what you will reread as a player), then the sheets handed with answers, then the procedures, then the notices.

- **Police report `E01`:** `meta` (date and time, place, complainant, prosecutor), victim, account, observations in a `mono` block (6–10 lines, including the honest facts that make the cover story plausible and the first quiet oddity), `signature`.
- **Scene `E02`:** `photos` with captions, or an `svg` sketch plus a `legend`. Sketch SVGs are hand-written: 600 × 400 viewBox, the design system's fonts are applied by the exporter, text in the case language, "not to scale" if it carries no measurement.
- **Social media, chat group, weather:** `posts`, `phones` with `chat`, `table log`. Every chat message has a time; a deleted message is `deleted: true`.
- **Statements `DEC-<letter>.md`:** front matter `code: "DEC · B"` (quoted: it has a space and a dot), `meta` with the five identity fields, `statement` block, `signature`. One lie, three or four checkable truths.
- **Autopsy, lab, logs, bank statements, towers, cameras:** `meta` + prose or `table log` / `mono`. Registers: 6–12 rows, datum never first or last, coverage stated for towers.
- **Per-suspect sheets:** `E17-B.md`, `E17-T.md`… with `code: E17·B`. A generic `E17-X.md` for "other person: no findings" when needed.
- **Notices:** `notice: true`, short, no codes.
- **Letters and old documents:** `aged: true`, `handwritten letter` block.

Images: paths from the case folder (`photos/e02_f1.jpg`), lower-case, content-neutral names. The exporter stops if a referenced image does not exist.

## 5 · `cards.yaml` ← bible §9, §10, §11

One group per suspect (title, `suspect`, `who`, `short`), then groups for witnesses, wildcards, notices/press, hints and closing. Inside a suspect's group, order: menu questions (`menu: true`, the first is "where were you"), confrontations (`type: confrontation`, the question is the accusation in quotes), the failed card (`type: failed`, code `B✕`), follow-ups (`type: follow-up`, code `B3+`). `attach` for sheets handed with the card; `follow_up` for the code it enables.

Quote any answer that starts with a quote mark or contains `: ` or ` #`. Count characters: 420 is the limit, and the exporter warns. Split long ones into two cards with the same code and "(1 de 2)" / "(2 de 2)" in `footer`.

Wildcards every case needs: "Eso no prueba nada" (failed confrontation with irrelevant evidence), "Testigo no disponible" (name not yet in their material; free), "Nada que aportar" (a name that leads nowhere; free), "Sin hallazgos" is a sheet or a spoken answer, not a card.

## 6 · Kit ← bible §12, §9, §10, §4

Six sheets, numbered files so they order: `01-mission.md` (the story in two paragraphs, nothing else: the engine puts "How to play", the phases and the glossary under it), `02-menu.md` (one paragraph, the `menu` block, the witnesses table; the rules for witnesses and follow-ups are the engine's), `03-procedures.md` (procedures table with costs; `checkboxes` block for the tokens), `04-timeline.md` (`work-table` with `schedule: true`, one row per suspect, victim, "others / vehicles", "weather"), `05-accusation.md` (`fields`: who, how, why, window, three strongest codes, contradictions, the case-specific bonus question, red herrings explained), `06-discard.md` (the `discard-rule` block, then a `work-table` with the suspects).

The engine inserts its own sheets after the first one: the rules, "During the game" and the score, with the case's figures. Do not write rules, costs, minutes or score weights in the case's sheets; if the case needs a different figure, write it in the neutral `case.yaml` (see `docs/case-format.md`, "The game and the case").

Read the finished kit as a player: nothing in it may name a red herring, a place not yet introduced, or the key datum.

## 7 · Guide ← bible §1–§13

Numbered files: `01-preparation.md` (print table and how to set up the room; the phases, before they arrive, the golden rule and fair play are engine sheets placed right after it), `01b-case-notes.md` ("what is particular to this case": the exceptions to the engine's fair-play rules, so it comes after them), `02-solution.md` (one page: `note` with what happened; why; the telling detail; the hidden plot; table of what each suspect hides and their real alibi), `03-diagram-night.md` and `04-diagram-deduction.md` if you draw them (optional in a short case), `05-script.md` (the `script` for the opening; the `notices` block, which prints each notice and press card with its suggested minute; the `hints` block, which prints the hints with their cost), `06-responses.md` (tables: questions, follow-ups, confrontations with triggers, witnesses with "appears in", procedures with targets → sheets, off-menu policy; pills `[true]` `[false]` `[key]` `[attached]`), `07-control.md` (the `control` block with a row per deliverable, `[code, what it is, tokens]`; the engine adds a column per team, the notices, hints and tokens left, and the request log after the sheet), `08-evaluation.md` (rubric table, discard table, red-herring table, confession conditions in `note-ok` and `note-warning`, the `score-sheet` block, which carries the tie-break), `09-confession.md` (`script` confession, `script` closing, what to do after).

Everything the director must answer in under a minute is in a table with the code in the first column.

## 8 · Check, lint, export

```
python export.py cases/<slug> --check
python skills/open-case-author/scripts/case_lint.py cases/<slug>
python export.py cases/<slug>
```

Fix until `--check` ends with "Check finished." without warnings you cannot justify, the lint is clean, and the export reports no card overflow. Sheets that "take 2 pages" are acceptable for the mission and the response table; a 2-page evidence sheet usually means a register too long or a chat too long: split it.

Then read, in `output/<slug>/<lang>/teams/`, every PDF as a player. Then run `validation.md`.

## Gotchas that cost time

- `code: "DEC · B"` must be quoted in front matter; `E17·B` need not, but the file is `E17-B.md`.
- Times like `22:30` are kept as text by the loader, but a value with `: ` inside a sentence must be quoted.
- A chat message on one line, `{from: X, time: "21:04", text: "..."}`, needs quotes around text with commas or question marks.
- `menu`, `checkboxes`, `notices`, `hints`, `discard-rule` and `score-sheet` blocks are empty; they are filled from the YAML and the engine's figures.
- Cards: notices and press cards need no minute in `who`, and hints need no `footer`: the engine writes them from `notice_minutes` and `hint_penalties`. Envelope 1's label uses `token_footer: true`. The case's bonus line is `score_bonus` (neutral) with `score_texts.bonus` (language).
- `attach` must name a dossier file that is in some section; `follow_up` must name an existing card code (the lint checks it).
- The dossier order is in the neutral `case.yaml`, not in the language file; the titles and notes of sections are in the language file.
- Suspect order in `suspects.yaml` is the order of the kit's menu and the suspect cards: do not put the culprit first.
- Ink saver is on by default; never turn it off in `case.yaml` unless the person asks.
- `brand_footer` default is `[kit, guide, dossier]` (every sheet carries the monogram and the case name, so mixed pages find their case); list fewer documents only if the person asks.
- `teams` can list up to four (A, B, C, D); `alibi_tokens_per_team` adds extra tokens with a dashed border, for cases that use them. A short case stays with two teams and no alibi tokens.
- The repository's `CONTRIBUTING.md` applies to any case that will be submitted: fictional people, no recognisable faces, a `README.md` in the case folder if images are AI-generated, licences.
