# Case format

A case is a folder. Inside there are a few YAML files with the data, one Markdown file per sheet of the game, and the photos and drawings those sheets use. The exporter reads all of it and makes the PDFs.

The sample case, `cases/chupacabras-labranza/`, uses almost everything described here. When something is unclear, the quickest way is to open the matching file of that case and copy it.

Everything the exporter reads is in English: file names, YAML keys, block names and options. The text of the case (what players read) can be in any language.

```
cases/my-case/
├── case.yaml            neutral data: paper, teams, tokens, order of the dossier, languages
├── procedures.yaml      optional: the procedures of the team's menu and what each one hands out
├── locations.yaml       optional: the places a team may ask about and their sources (camera, register)
├── signatures.yaml      optional: the pen strokes of the people who sign the sheets
├── photos/              images shared by every language (.jpg / .png)
├── diagrams/            drawings shared by every language (.svg)
├── styles.css           optional: extra CSS only for this case
└── languages/
    └── es/              one folder per language, with the same file names in each
        ├── case.yaml    title, taglines, cover notes, dossier section titles, envelope labels
        ├── suspects.yaml
        ├── cards.yaml
        ├── procedures.yaml  the texts of the procedures (labels, names, notes for the director)
        ├── locations.yaml   the names of the places
        ├── kit/         sheets of the team kit, one .md file each
        ├── dossier/     one piece of evidence per file (E01.md, E02.md…)
        └── guide/       sheets of the director's guide
```

`photos/` and `diagrams/` are a habit, not a rule: image paths are always written from the case folder (`photos/e02_f1.jpg`), and you can arrange them as you like.

Before exporting, run `python export.py cases/my-case --check` (or `make check`). It cross-checks references without opening the browser and reports the file and line of every problem.

## Languages

`case.yaml` declares them:

```yaml
base_language: es
languages: [es, en]
```

Each language has its own folder under `languages/` with the same structure and the same file names. To translate a case, copy `languages/es/` to `languages/en/` and translate the files one by one. Keep these identical in every language:

- file names, and the `code` of every sheet and card (`B1`, `E01`, `DEC-B`), so cross references still work;
- the order of the dossier, which lives in the neutral `case.yaml`, not in the language files.

Images are looked up first in `languages/<lang>/` and then in the case folder. A photo or drawing with text in it can be translated by putting its own version in the language folder, with the same path (`languages/en/diagrams/night.svg`). Images without text are shared.

Export one language with `--lang en`, or all of them with `--lang all`. Each goes to its own folder: `output/<case>/<lang>/`. A translation is checked against the base language, and the export stops, listing them, if sheets, cards or suspects are missing. A printed sheet never mixes languages.

The words the exporter prints itself ("Sheet 1 of 2", "Team", "Attached"…) come from `opencase/strings/<lang>.yaml`. A language that has no file there falls back to English, and a case can change any of them in `languages/<lang>/case.yaml`:

```yaml
strings:
  request:
    title: Solicitud de diligencia
```

## Website data (`site:`)

By default every case in `cases/` is published on the website. A case that has not been validated (played with real teams) is kept in the repository but hidden with `published: false` in the neutral `case.yaml`: the site build leaves it out of `cases.json`, the zips and the page, and does not need a `site:` block for it. `python3 -m opencase.site --include-unpublished` builds it anyway, to preview it locally. Cases written with `skills/open-case-author` start with `published: false`. Exporting PDFs with `export.py` is not affected.

The website (`python3 -m opencase.site`, `make site`) draws one card per case. Its data lives in the neutral `case.yaml`:

```yaml
site:
  author: Open Case                # required
  license: CC BY-NC-SA 4.0         # required
  date: 2026-10-29                 # shown on the card
  cover: photos/e09_2250.jpg       # optional: image of the card (a spoiler-free one)
  min_teams: 2                     # the maximum is the length of `teams`
  duration_minutes: [60, 70]       # a number or [min, max]
  players_per_team: [5, 7]         # a number or [min, max]
  slug: my-case                    # optional: defaults to the folder name
```

and, in every `languages/<lang>/case.yaml`, `summary` (two or three spoiler-free sentences) and `cover_alt` (description of the cover; required when there is a cover).

The build exports the PDFs of every language and packs two reproducible zips per case and language (`<slug>-<lang>-teams.zip`, without the solution, and `<slug>-<lang>-director.zip`, with it), then writes `cases.json`, the list the page reads. Check the metadata alone with `python3 -m opencase.site --check`.

## case.yaml (neutral)

```yaml
brand: Open Case
paper: letter                  # letter or a4

base_language: es
languages: [es]

teams: [A, B]                  # up to four: A navy, B green, C violet, D copper
tokens_per_team: 16
alibi_tokens_per_team: 0       # optional: extra tokens with a dashed border, coded C1, C2… (A1… in English)
players_per_team: 7            # badges per team
score_bonus: 3                 # optional: the case's own line of the score (its text: score_texts.bonus)
# engine_sheets: false         # optional: see "The game and the case" below

brand_footer: [kit, guide, dossier]
ink_saver: true

dossier:
  sections:
    - id: start
      envelope: 1
      items: [E01, E02, E03]
    - id: procedures
      items: [E12, E13a]
```

**brand_footer** says which documents carry, at the bottom of every sheet, the monogram with the brand and the case name. The values are `kit`, `guide` and `dossier`. By default all three do, so no sheet loses its case if the pages get mixed up. To leave one out, list only the others (`brand_footer: [kit, guide]`), or use `brand_footer: []` for none.

**ink_saver** is on by default. It is explained at the end.

**tokens_per_team**, **alibi_tokens_per_team** and any other figure of the game (minutes, notices, hints, score) can be written here to change the engine's recommended value for this case. They are listed in [The game and the case](#the-game-and-the-case).

### Dossier sections

The sections give the order of the evidence and decide who gets what. Each `id` is free text, and the titles and notes of each section are written in the language file (see below). Every item is the name of a file in `dossier/` without `.md`. An item can be in one section only, and a sheet that is in none is reported and not exported.

Sections with `envelope: 1` are put together in a separate PDF, `teams/02_Envelope_1.pdf`, which is the only part of the dossier that goes in the teams' folder. Several sections can point to the same envelope. Every other sheet goes into `director/02_Evidence.pdf` (`02_Pruebas.pdf` in Spanish), **ordered by code** (E08, E09, E10, E13a, E13b, E15 · B… E30), whatever its section: the director prints one copy per team, uncollated, and hands each sheet only to the team that paid for it. The guide ends with the evidence index, which lists every sheet by section with where it is (an envelope or the Evidence file); sheets that print the same code (`E13b-2.md` with `code: E13b`, one piece of evidence on two sheets) share one row, "· 2 hojas".

The prosecutor's notices are **cards** (`type: notice` in `cards.yaml`), read aloud to every team; a case does not need notice sheets. If a case still has sheets with `notice: true` in a section, they go into the Evidence file like any other sheet.

### What to print (the print plan)

The engine decides how the material is grouped, how many copies are printed and when each document is handed out; the case only brings its data (teams, tokens, sheets, cards). The `print-plan` block in the guide's first sheet draws the table, and the `LEEME.txt`/`README.txt` next to the PDFs is written from the same plan (`opencase/printing.py`):

| Package | Document | Copies | Paper |
|---|---|---|---|
| Each team | Badges | one sheet per team, in its colour (one PDF with all) | card stock |
| Each team | Tokens | one sheet + back per team, in its colour: its tokens, its alibi tokens and spares | card stock, double-sided |
| Each team | Requests (optional: the director may take them by word of mouth) | one per team; `ceil(tokens + alibi tokens / 8)` sheets of 8 slips | paper |
| Each team | Suspects, kit (no cover), envelopes | one per team | card stock / paper |
| Director | Guide (with the evidence index at the end) | 1 | paper |
| Director | Evidence | one per team, uncollated (0 with `--chat`) | paper |
| Director | Answer cards, and the common back on the reverse of each sheet | one per team, uncollated | card stock |
| Director | Envelope labels | 1 (one label per envelope and team) | paper or adhesive |

The plan counts pages from the data, not from a browser: a sheet is one page unless it says otherwise with `pages: N` in its front matter. `tools/check_print.py` (`make print-check`, and the CI) exports every case and fails when a PDF has other pages than the plan says, or when a sheet of the kit, an envelope or the Evidence file fills more than 95 % of the pages it declares (about two lines of room, because the same text comes out a little taller on another computer). In the guide this is only a warning.

Two options of `export.py` change the plan: `--teams N` exports for the first N teams only (badges, tokens, labels, the columns of the control sheet and the copies), and `--chat` sends the Evidence file through each team's chat group (0 copies in the plan, and one image per sheet in `chat-images/`, as with `--images`).

## languages/\<lang\>/case.yaml

```yaml
title: El Chupacabras de Labranza     # required
version: Versión 5 · octubre de 2026  # printed on the covers
tagline: Todos mienten. Las pruebas no.

badge:
  title: Detective
  unit: [Brigada de Homicidios, Temuco]

request:
  help: 1 ficha por pregunta · diligencias según menú   # optional, text on the request form

kit:
  description: …               # text on the screen header (the kit has no printed cover)

guide:
  description: …
  cover_note: …

dossier:
  title: Expediente El Arrayán
  kicker: PDI · Brigada de Homicidios Temuco
  description: …               # screen header text
  sections:
    start: {title: Sobre 1, note: Se entrega a ambos equipos al comenzar}
    procedures: {title: Diligencias, note: Se entregan al equipo que paga la ficha}

envelope_labels:               # labels to stick on the paper envelopes (one per team)
  - number: 1
    when: se entrega al comenzar
    description: Lo que sabemos hasta ahora.
    contents: [E01 Parte policial, E02 Set fotográfico]
    token_footer: true         # "16 fichas · 1 placa por jugador", from the case's figures
  - number: 2
    when: al investigar
    contents: [E06 Informe de autopsia]
    footer: Al comenzar la investigación   # a free line instead

score_texts:                   # required when the neutral case.yaml has score_bonus
  bonus: Explicar qué pasó con los ataques a los animales y por qué
  bonus_short: Bonus ataques   # optional: the shorter text of the director's score sheet

glossary:                      # optional: the acronyms the sheets use (see "Acronyms" below)
  PDI: Policía de Investigaciones de Chile
  SUV: {long: vehículo utilitario deportivo, expand: false}
glossary_ignore: [BIRO]        # optional: words in capitals that are not acronyms

strings: …                     # optional: replaces words the exporter prints
```

### Acronyms

An acronym is defined once, as data of the case, and the engine does the rest: the director's guide gets a table of the glossary (sheet "Siglas del caso", at the end), and `--check` (and `case_lint.py`) warns about two things.

- **An acronym used before its long form.** In the order a team reads: the kit, then the sheets of the envelopes in the order of the sections of `case.yaml` (inside a sheet, its front matter first). Write it out the first time (`Servicio Agrícola y Ganadero (SAG)`, or `SAG` right before `(Servicio Agrícola y Ganadero)`). A sheet that comes with an answer, and each card, are checked on their own against what the teams already read. What a person says does not count: chats, statements (`phones`, `posts`, `statement`, `quote`, `handwritten` blocks) and quoted answers on the cards.
- **A word that looks like an acronym but is in no glossary** (2 to 6 capitals, not part of a heading in capitals, not the prefix of a code such as `E` or `DEC`). Add it to `glossary`, or to `glossary_ignore` when it is not one (`BIRO`).

An entry written as `{long: …, expand: false}` is an acronym everybody knows (SUV, ADN): it is in the director's table, but the sheets do not have to write it out. The glossary changes with the language, so it is in `languages/<lang>/case.yaml`; a translation brings its own. To show the table to the teams, put a ` ```acronyms ` block in a sheet of the kit (`only: [PDI, SAG]` limits it to some).

## suspects.yaml

```yaml
suspects:
  - letter: B                    # the letter of their codes: B1, B◆, DEC · B
    name: Benjamín Ferrada
    short_name: Benja            # optional, for the card if the name is long
    role: hermano de la víctima
    portrait: photos/benjamin.jpg   # optional; without one the card shows a folder silhouette
    confront: Confrontar con una prueba   # optional, text of the menu's confront row
    facts:                       # up to five, one line each
      Edad: 41
      Oficio: Ingeniero comercial
```

This makes the suspect cards and the headings of the kit's question menu. A portrait must never show a recognisable face: from behind, from afar or in shadow.

## cards.yaml

Cards go in groups. Each group prints together and in the order of the file:

```yaml
groups:
  - title: Benjamín Ferrada
    suspect: B           # the cards of the group belong to B
    who: Benjamín Ferrada
    short: Benjamín      # for "Benjamín · confrontación"
    cards:
      - code: B1
        menu: true       # the question appears in the kit's menu
        question: ¿Dónde estuvo el viernes entre las 22:00 y la 01:00?
        answer: '"En mi departamento, en la Torre Alemania…"'
        attach: E30      # the director also hands out that evidence
        follow_up: B1+   # enables another question
      - code: B5
        type: confrontation
        question: '"Usted estuvo en Labranza esa noche."'
        answer: '"Ya, sí… fui."'
```

| Field | What it is for |
|---|---|
| `code` | Required. On confrontations the suspect's letter and a diamond are put in front: `B◆ · B5`. |
| `type` | `answer` (the default), `follow-up`, `confrontation`, `failed`, `witness`, `wildcard`, `notice`, `press`, `hint` or `closing`. It changes the band colour. It can be set on the group for all its cards. |
| `question` | What the team asked, in italics at the top. |
| `menu_question` | Another wording for the kit's menu, if needed. |
| `answer` | The main text. At most 420 characters: more does not fit in 63 × 88 mm. |
| `note` | A small line after the answer ("No se cobra ficha"). |
| `headline` | A big headline before the text (used by press cards). |
| `who` | What goes to the right of the code. If missing it is built from the group. |
| `attach` | One or several evidence codes handed out with the card. |
| `follow_up` | One or several follow-up codes the card enables (its follow-ups). On the team's card they show as a box with the code, the cost and, if the follow-up has `unlocked_by`, its condition: "Seguimiento H2+ · 1 ficha · si ya tienen E13b". The codes are printed the way their sheet prints them (`E15-M` shows as E15·M). The question itself is only in the guide. |
| `unlocked_by` | Only on follow-ups: one or several codes of the dossier or of cards that the team must also have (any one of them is enough). Use it when the follow-up names something its mother card does not say (see below). |
| `appears_in` | Only on witnesses: the dossier sheets or cards where the teams can read the person's name. The guide's witness table shows them. |
| `aliases` | Only on witnesses: other ways the material calls the person ("conserje", "Maca"). |
| `guide_note` | A note for the director, printed only in the guide's generated tables (follow-ups and witnesses), never on the card. It can use the pills `[true]`, `[false]`, `[key]`… |
| `footer` | A free line at the bottom. Hint cards without one get it from `hint_penalties` ("Resta 1 punto al equipo que la pidió"). |
| `menu` | `true` to show the question in the kit's menu. |
| `suspect` | If the card is about another suspect than its group's. |

Notice cards add which notice they are to `who` ("Fiscalía · 1 de 2"); without `who`, a notice says "Aviso" and a press card "Con el aviso N". They never print the suggested minute: the cards go to the teams' tables, and the minute is only in the guide. Cards of type `notice`, `press`, `hint` and `closing` print on a separate sheet at the end, because they are used at another moment of the game. The exporter checks that every `attach` exists in the dossier and warns when an answer is over 420 characters.

**Follow-ups and witnesses.** A follow-up is one of two kinds. Kind A: the mother card's answer already opens the topic ("pelear por plata", then "¿De qué plata?"); `follow_up` on the mother card is enough. Kind B: the question names something the mother card did not say and that comes from another piece of evidence (H2+ asks about "papeles", which are in E13b); then `unlocked_by` is required and names that evidence. A witness is the set of cards of type `witness` with the same `who` (the name is what comes before a comma); `appears_in`, `aliases` and `guide_note` can go on any of them and add up. The export stops when `follow_up`, `unlocked_by` or `appears_in` name something that does not exist, and warns about a follow-up no card enables, a witness without `appears_in` and a witness whose name and aliases are in none of the places of its `appears_in` (the teams could never ask for them). The guide's tables come from these fields with the blocks `follow-ups`, `witnesses`, `quick-follow-ups` and `quick-witnesses`.

If a card does not fit when printing, it shrinks the type down to 8.5 pt; if it still does not fit, it outlines the card in red and says so in the console.

## Procedures and places

The procedures (diligencias) of the team's menu are data of the case, in `procedures.yaml` (neutral) and `languages/<lang>/procedures.yaml` (texts). The engine knows the **kinds** of procedure and what each one is; the case gives each of its procedures its own **code**, so DG9 can be the phone towers in one case and the cameras in another. From these files the engine draws the kit's menu (`procedures` block), the guide's answer table (`procedure-answers`), the quick sheet's column (`quick-procedures`) and the rows of the control sheet (`control`). A case without `procedures.yaml` keeps writing those tables by hand.

```yaml
# procedures.yaml (neutral)
procedures:
  - code: DG1
    kind: report
    gives: E12                       # one result
  - code: DG3
    kind: bank_statement
    targets: {B: E15-B, T: E15-T, M: E15-M}     # one result per target
  - code: DG8
    kind: premises_search
    each: true                       # each target is a request of its own: "1 c/u"
    targets: {desk: E24, safe: E25}
  - code: DG11
    kind: cameras
    alibi: true                      # an alibi token can pay for it
    targets: {copec: E28, karaoke: none}
  - code: DG12
    kind: phone
    targets: {P: E29-P, J: [E29-J, E08], other: E29-X}   # J hands out two sheets
  - code: DG10
    kind: other
    targets:
      deleted_message: {gives: E13d, cost: 2}           # a target with a cost of its own
      other: material
```

| Field | What it is for |
|---|---|
| `code` | Required. The code on the menu. |
| `kind` | Required. `report`, `phone`, `bank_statement`, `social_media`, `vehicle`, `area_search`, `belongings`, `premises_search`, `phone_towers`, `cameras` or `other`. It gives the default label and short name (`procedures.kinds` in the strings) and says what the procedure can do: only `phone_towers` and `cameras` show where someone was, and only `cameras` reads a source a place has. |
| `cost` | Tokens; 1 if missing. A target may have its own: `{gives: E13d, cost: 2}`, and the menu then says "1 o 2". |
| `each` | `true` when every target is a separate request (the menu says "1 c/u"). |
| `alibi` | `true` when an alibi token can pay for it. It is never worked out from the results: the kit and the guide print the code with a dashed border, and the kit explains it under the menu (only when the case has alibi tokens). |
| `gives` / `targets` | One of the two. `gives` is the result; `targets` maps each target to its result. A target is a suspect's letter, a place of `locations.yaml`, `other` (anyone or anything else) or a key of the case's own. A result is a sheet (`E12`), several sheets (`[E29-J, E08]`), `none` ("sin hallazgos": it makes sense but there is nothing, and the token is spent) or `material` (only for open requests: hand out what the material has, if anything). |

```yaml
# languages/es/procedures.yaml
names: {B: Benjamín, T: Toto, M: Matías o la empresa}    # how the guide names the people of the targets
procedures:
  DG1: {label: Informe del Servicio Agrícola y Ganadero (SAG) sobre las muertes de animales, short: SAG}
  DG8:
    label: "Allanar la caseta de El Arrayán (indiquen: el escritorio o la caja fuerte)"
    short: Caseta
    targets: {desk: escritorio, safe: caja fuerte}   # labels of the case's own targets (and of other)
  DG11:
    notes: {karaoke: el local no tiene cámaras}     # a note for the director next to one target
  DG4:
    note: (solo publicaciones públicas)            # a note next to the whole procedure
```

`label` is what the kit's menu says and `short` the name in the guide's tables ("Cartola: Benjamín · Toto"); without them the kind's own are used. The places go in `locations.yaml`, with their sources, and their names in `languages/<lang>/locations.yaml`:

```yaml
# locations.yaml (neutral)
locations:
  - id: copec
    sources: [camera]
  - id: karaoke
    sources: []          # it has none: asking is free, and the answer is no
```

```yaml
# languages/es/locations.yaml
locations:
  copec: {name: Copec}
  karaoke: {name: karaoke, note: optional note for the director}
```

The `locations` block draws the guide's table of places: which source each one has, which procedure reaches it and what it hands out. It is what the director needs for the free question "does it have a camera?" (asking whether a source exists is free; seeing it is the procedure).

The export stops when a procedure has an unknown kind or field, both or neither of `gives` and `targets`, a result that is not a sheet of the dossier, a target with no name, or a text for a code or target that does not exist. It warns when `alibi: true` is on a kind that does not show where someone was or the case has no alibi tokens, when a camera procedure hands out a sheet for a place without sources (or finds nothing at a place that has one), when a sheet outside the envelopes can be got neither by a procedure nor with a card, and when a follow-up's `unlocked_by` or a witness's `appears_in` is a sheet no team can get. `--check` also compares the texts of procedures.yaml between languages.

## Signatures

A signature at the bottom of a sheet can be drawn as the strokes of a ballpoint pen, so each person of the case signs in a hand of their own and two signatures can be compared. The engine knows how to draw one; the case brings the strokes of its signers in `signatures.yaml` (neutral: a signature does not change with the language):

```yaml
# signatures.yaml (neutral)
signatures:
  B:                          # the id a signature block names with `signer: B`
    name: Benjamín Ferrada Soto
    width: 1.7                # pen width, in units of the viewbox (optional, 1.5)
    viewbox: 0 0 53 40        # the box the strokes are drawn in (optional, 0 0 120 40)
    strokes:                  # SVG path data, one stroke of the pen each
      - "M3 27.9C5 23.7 12.9 3.1 14.9 3C17 2.9 13.7 25.3 15.5 27.4"
      - "M3.3 37L38 35.3"
      - "M49.2 34.9h0.6"      # a dot
```

And in the sheet:

````markdown
```signature
- {signer: B, scrawl: Benjamín Ferrada Soto, label: Firma del declarante}
- Detective a cargo
```
````

The strokes are printed in the pen's ink colour at the height of the signature line, whatever the viewbox. A signer with no strokes in `signatures.yaml` is printed as before, with its `scrawl` in the handwriting font, so a case can draw some signatures and not others. The ids are free: a suspect's letter is the usual one, and anyone else who signs (`painemal`) gets a word.

You do not need to draw them by hand. `python3 tools/signatures.py cases/my-case` (or `make signatures`) reads the signature blocks, draws the signers that have no strokes yet from their `scrawl` and writes them in `signatures.yaml`. Each one comes from a hand movement (a flowing name, a scribble, zig-zags, a wave...) that no other person of the case shares while there are movements left; the details come from the name and a seed. `--redo B` draws B again with the next seed, `--family` picks the movement, and `--preview page.html` shows them all side by side. What it writes is plain data: retouch the paths, or paste the paths of a signature drawn in a vector editor. The exporter only reads the file, so a signature never changes by itself.

The export stops when a stroke is not SVG path data, a viewbox is not four numbers, or a signer has neither strokes nor `scrawl`; it warns when a signature of `signatures.yaml` signs no sheet.

## Sheets: kit, dossier and guide

Each `.md` file is one sheet. At the top there is a YAML header between `---` and below it the content:

```markdown
---
code: E01
institution: Policía de Investigaciones de Chile
description: Brigada de Homicidios Temuco · Parte policial
title: Parte N° 4471 · Hallazgo de cadáver
---

**Matías Ferrada Soto**, 38 años, corredor de propiedades…
```

The sheets of the kit and the guide are ordered by file name (`01-mision.md`, `02-menu.md`…). Those of the dossier, by the sections of `case.yaml`.

| Field | What it is for |
|---|---|
| `code` | The evidence code, in the red box at the top right. |
| `institution` | First line of the letterhead, in capitals. |
| `description` | Second line of the letterhead. |
| `title` | The big title of the sheet. |
| `tag` | A label in the place of the code (the guide uses "Solo director"). |
| `team_line` | `true` to print "Team: ______" (the kit does). |
| `logo` | `true` for the Open Case wordmark in the letterhead (the kit and the guide do). |
| `reserved` | `true` for the red "reserved material" strip (the guide does). |
| `stamp` | A stamp in the corner: `stamp: Confidencial`, or `stamp: {text: Anulado, color: ink}` (colours: `ink`, `brass`, `forest`). |
| `notice` | `true` for the amber strip of a notice sheet (the notices are usually only cards). Without `description`, the engine writes "Aviso para todos los equipos · 1 de 2" (never the suggested minute, because the teams get a copy). |
| `aged` | `true` for aged paper (letters, old documents). `paper: aged` also works. |
| `short` | A short name of the evidence for the director's tables (the control sheet names the sheets that cards hand out with it: "Live de Javiera"). Without it, the title. |
| `pages` | How many pages the sheet takes, when it takes more than one (`pages: 2`). The print plan counts it, and the check fails when the sheet does not fit in them. |

### Content

The body is plain Markdown: paragraphs, **bold**, *italics*, lists, `### subheadings` and tables. Besides:

- `==text==` highlights.
- `` `E01` `` writes a code in the codes typeface.
- `[true]`, `[false]`, `[key]`, `[red-herring]`, `[attached]`, `[procedure]` and `[pending]` are coloured pills for the director's guide. The word printed comes from the language strings.
- `{.small}` on the line right after a paragraph, with no blank line in between, makes that paragraph small.
- `![caption](diagrams/map.svg)` inserts an image; an SVG stays inside the sheet and uses the design system's fonts.

### Blocks

For what is not running text there are blocks between three backticks with the name of the block. Those that carry data are written in YAML:

````markdown
```meta
Date and time of the report: Saturday 31-10-2026, 07:42
Place: Parcela El Arrayán, Camino Los Copihues km 3.2
```
````

One YAML detail worth knowing: if a text has `: ` or `#` in it, or starts with a quote, put it in single quotes or use `>-` to write it over several lines. The exporter's reader does not convert times such as `22:30` or dates: they stay as you wrote them.

**Documents**

| Block | What it draws | Content |
|---|---|---|
| `meta` | The data grid at the top of a report | `Label: value`, one per line |
| `signature` | Signatures at the bottom | List of `{signer: painemal, scrawl: I. Painemal, label: Comisario a cargo}`, or plain texts. `signer` draws the strokes of `signatures.yaml`; without strokes, `scrawl` is printed with the handwriting font (see "Signatures") |
| `statement` | A statement, in typewriter type | Free text, keeps its line breaks |
| `quote` | A highlighted quote | Free text |
| `handwritten` | Handwriting. Optional argument: `notebook`, `scribble`, `pencil`, `letter`, `no-lines` | Free text |
| `postit` | A sticky note | Free text |
| `marker` | Marker lettering, one line per row | Free text |
| `mono` | A block in typewriter type (logs, lists) | Markdown |
| `small` | A block in small type | Markdown |
| `table` | A Markdown table, with variants: `control`, `work`, `score`, `compact`, `narrow`, `log` | Markdown table |
| `stamp` | A rubber stamp. Argument: `ink`, `brass`, `forest`, `large` | The text of the stamp |
| `evidence-bag` | An evidence bag label | `number:` and `fields:` |
| `press` | A newspaper clipping | `outlet:`, `date:`, `headline:`, `body:` |
| `email` | A printed email | `from:`, `to:`, `cc:`, `date:`, `subject:`, `body:`, `attachments:` |
| `receipt` | A receipt or ticket | List of `[item, amount]`, `{center: text}`, `{total: [Total, $12.990]}` or `---` |

**Photos, cameras and drawings**

| Block | What it draws | Content |
|---|---|---|
| `photos` | Photos with captions. Optional argument: `2 columns`, `3 columns` | List of `image:`, `title:`, `text:`, `alt:`, `label:` |
| `cctv` | Camera frames with the on-screen display | List of `image:`, `osd:`, `osd_right:`, `title:`, `text:` |
| `image` | A single image | `image:`, `caption:`, `width:` (for example `60%`), `alt:` |
| `svg` | A drawing of the case | The path in the argument: ` ```svg diagrams/map.svg ``` ` |
| `legend` | Colour legend of a sketch map | `color: text` |

**Screens**

| Block | What it draws | Content |
|---|---|---|
| `phones` | One or several phones | List of phones with `bar:`, `sub:` and one of `chat:`, `calls:` or `app:` |
| `videos` | Video frames or livestreams. Optional argument: `4 columns` | List of `image:`, `text:`, `caption:`, `clock:`, `live:`, `comments:` |
| `posts` | Social media posts. Optional argument: `4 columns` | List of `user:`, `image:` or `story:`, `text:`, `meta:` |

A chat is a list of messages. Every message needs a time, and a bare text in the list is a day separator:

```yaml
- bar: Vecinos Camino Los Copihues
  sub: 34 participantes
  chat:
    - day: 28 de octubre
    - from: Hernán Carrasco
      time: "21:02"
      text: Me robaron otra oveja.
    - from: Matías
      time: "23:18"
      deleted: true          # shown as "this message was deleted"
    - me: true               # your own message, on the right
      time: "23:20"
      text: ¿Alguien vio algo?
```

A message can also be written on one line, `{from: Rosa, time: "21:04", text: "Sí, yo"}`, but then the text goes in quotes: inside braces, commas and question marks confuse YAML. Calls are `{type: missed, who: Pía, time: "18:05"}` with `type` being `incoming`, `outgoing` or `missed`, and an optional `duration:`.

**Director's guide**

| Block | What it draws | Content |
|---|---|---|
| `columns` | Side-by-side columns, for quick-reference sheets. Argument: minimum width of a column in px (default 230) | Markdown pieces separated by a line with `===`. Open it with four backticks (```` ````columns ````) and a piece can also hold ```blocks, such as `quick-witnesses` |
| `note`, `note-ok`, `note-warning` | Plain, green or amber notes. Argument: the label | Markdown |
| `script` | What the director reads aloud. Optional argument: the label | Free text |
| `steps` | Numbered steps | List of `title:` and `text:` |

**Kit worksheets**

| Block | What it draws | Content |
|---|---|---|
| `fields` | Lines or boxes to write on | List of `label:`, `type: box` and `height:` (or just the label) |
| `work-table` | An empty table to fill in | `columns:`, `rows:`, `height:`, `schedule: true` for the timeline |
| `checkboxes` | Boxes to tick off tokens. Optional argument: how many, or `alibi` for the alibi tokens (labelled with `tokens.alibi_code`, C1, C2…) | Nothing; defaults to `tokens_per_team` |
| `menu` | The question menu, built from `suspects.yaml` and the cards with `menu: true` | Nothing |
| `html` | HTML as it is, for odd cases | HTML |
| `print-plan` | The table of what to print: each team's package and the director's, with copies, paper, size and when each one is handed out, and the totals. It follows `--teams` and `--chat` | Nothing |

**The engine's blocks.** These draw a fixed part of the game with the case's figures. They live in `opencase/templates/<lang>/blocks/`, so they come in the language of the case:

| Block | What it draws | Content |
|---|---|---|
| `control` | The director's control table: one column per team; with `procedures.yaml`, a table of the procedures (one row per sheet number: E15·B to E15·M in one) and one of the cards that hand out a sheet (`attach`, named by the sheet's `short`); then the notices, other questions, hints, tokens left and alibi tokens used | Nothing; a case without `procedures.yaml` writes `rows:`, a list of `[code, what it is, tokens]` |
| `procedures` | The kit's menu of procedures, from `procedures.yaml`: code (dashed when `alibi: true`), label and cost | Nothing |
| `procedure-answers` | The guide's table of procedures: each target and what to hand out, with the notes | Nothing |
| `quick-procedures` | The same, short, for the quick sheet (inside a `columns` block) | Nothing |
| `locations` | The guide's table of places: sources, procedures that reach them and what they hand out | Nothing |
| `notices` | What the director reads for each notice and press card, with its suggested minute, from the cards of type `notice` and `press` | Nothing |
| `hints` | The hints in order, with what each one costs, from the cards of type `hint` | Nothing |
| `acronyms` | The glossary of the case as a table of acronym and long form | Optional `only: [PDI, SAG]` |
| `discard-rule` | The kit's paragraph on ruling innocents out and what each discard is worth | Nothing |
| `score-sheet` | The director's score sheet, one column per team, with the tie-break | Nothing |
| `follow-ups` | The guide's follow-up table: each card of type `follow-up` with its full question, the cards that enable it (`follow_up`), the evidence it also needs (`unlocked_by`) and its `guide_note` | Nothing |
| `witnesses` | The guide's witness table: each witness (the cards of type `witness` with the same `who`), where their name appears (`appears_in`) and what to hand out, with its `guide_note` | Optional: `others:` with `names`, `appears_in` and `card` for the row of the other names of the material |
| `quick-follow-ups`, `quick-witnesses` | The same, short, for the quick sheet (inside a `columns` block) | Optional in `quick-witnesses`: `others: {card: ...}` |

If you write a block that does not exist, the exporter stops and tells you which ones there are.

## The game and the case

What is the same in every game of Open Case (the rules, the phases, the glossary, the score, the costs) belongs to the engine; a case brings only its data. So a case's `kit/` and `guide/` hold only what is its own: the story, its menu, its answers and its notes. The engine adds the rest.

**The figures** are in `opencase/defaults.yaml`. They are the recommended ones, and a case changes any of them in its neutral `case.yaml`, with the same key. Nested keys are merged one by one, so `phases: {investigation: 22}` changes only that phase. A key the neutral `case.yaml` does not know (a figure or one of the keys above) stops the export, so a misspelt `tokens_per_teams` does not go unnoticed; so does a figure written in `languages/<lang>/case.yaml`, because every language plays with the same rules.

How many notices, press cards and hints the rules mention comes from the case (its cards of type `notice`, `press` and `hint`, and its sheets with `notice: true`); the figures only give each one its suggested minute or its cost. A case with more notices than `notice_minutes` or more hints than `hint_penalties` stops the export, and a case with none leaves those paragraphs out. The lint warns when `session_minutes` is shorter than the phases and `closing_minutes` add up to.

| Key | Default | What it is |
|---|---|---|
| `tokens_per_team` | 16 | Numbered tokens for questions and procedures |
| `alibi_tokens_per_team` | 0 | Dashed tokens that only check where a suspect was |
| `team_size_min` | 2 | Smallest team |
| `phases` | `{setup: 5, scene: 10, investigation: 30, accusation: 15}` | Minutes of each phase. Minute 0 of the investigation is when envelope 2 is opened |
| `closing_minutes` | `[5, 10]` | Score, confession and the end of the story |
| `accusation_writing` | 5 | Minutes to fill in the accusation and the discards |
| `pitch_minutes` | 2 | Minutes each team has to present its theory |
| `session_minutes` | `[65, 75]` | The whole session, as the kit and the guide announce it |
| `notice_minutes` | `[10, 20]` | Suggested minute of the investigation for each notice; the director decides |
| `hint_penalties` | `[1, 1, 1, 2, 2]` | Points each hint costs, in order; one per hint card |
| `request_log_rows` | 16 | Rows of the request log in the guide |
| `score` | culprit 5, culprit without evidence 2, how 2, why 2, window 1, contradiction 1, discard with two pieces of evidence 2 / with one 1 / blank −1, red herring 1, spare token 0.25, wrong accusation −5 | Points of the score (keys in `defaults.yaml`) |

The case's own line of the score is `score_bonus` (its points) with `score_texts` in each language file (its text). A case without it has no bonus line.

**The engine's sheets** are in `opencase/templates/<lang>/kit/` and `guide/`. The exporter inserts them by itself: in the kit, "How to play" at the bottom of the first sheet and then the rules, "During the game" and the score; in the guide, "Running the game" and "Fair play" after the first sheet, and the request log right after the sheet with the `control` block. They are written in Markdown with Jinja2 and print the case's figures; a value that no YAML defines stops the export and says in which file and line. A case cannot replace these files, but it can leave them out:

```yaml
engine_sheets: false                 # no engine sheets, no generated card lines (the case writes everything)
engine_sheets:
  kit:
    after: 02-menu                   # put them after this sheet instead of the first one
    skip: [30-score]                 # leave this one out
  guide: false                       # none in the guide
```

The names in `after` and `skip` are file names without `.md`; a name that does not exist stops the export. With `engine_sheets: false` the case also writes its own card lines (who, hint footers) and notice descriptions, as before.

## Ink saver

By default the PDFs come out without backgrounds: white sheets, without the grey of table headings or the fill of notes, phones or tokens. Colour stays where it means something: card bands, codes, stamps, token rings, rules and text. Printing backgrounds uses a lot of ink and does not help play.

For the full-colour version, for a print shop or to look at it on screen:

```
python export.py cases/my-case --color
```

If a case is always printed in colour, put `ink_saver: false` in its `case.yaml`; `--ink-saver` then forces the saver mode again. Photos print the same in both modes, and the chat images (`--images`) are always full colour, because they are not printed.

## Styles of a case

If a case needs something the design system does not have, create `styles.css` in its folder. It is loaded after everything else. Use it sparingly: whatever is useful for more than one case should go to `design/open-case.css`.
