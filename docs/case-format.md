# Case format

A case is a folder. Inside there are a few YAML files with the data, one Markdown file per sheet of the game, and the photos and drawings those sheets use. The exporter reads all of it and makes the PDFs.

The sample case, `cases/chupacabras-labranza/`, uses almost everything described here. When something is unclear, the quickest way is to open the matching file of that case and copy it.

Everything the exporter reads is in English: file names, YAML keys, block names and options. The text of the case (what players read) can be in any language.

```
cases/my-case/
├── case.yaml            neutral data: paper, teams, tokens, order of the dossier, languages
├── photos/              images shared by every language (.jpg / .png)
├── diagrams/            drawings shared by every language (.svg)
├── styles.css           optional: extra CSS only for this case
└── languages/
    └── es/              one folder per language, with the same file names in each
        ├── case.yaml    title, taglines, cover notes, dossier section titles, envelope labels
        ├── suspects.yaml
        ├── cards.yaml
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

### Dossier sections

The sections give the order of the evidence and decide who gets what. Each `id` is free text, and the titles and notes of each section are written in the language file (see below). Every item is the name of a file in `dossier/` without `.md`. An item can be in one section only, and a sheet that is in none is reported and not exported.

Sections with `envelope: 1` are put together in a separate PDF, `teams/02_Envelope_1.pdf`, which is the only part of the dossier that goes in the teams' folder. Several sections can point to the same envelope. Everything else stays only in `director/02_Complete_dossier.pdf`, which has every section with an index at the beginning.

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
  description: …               # text on the screen header
  cover_note: …                # note on the printed cover

guide:
  description: …
  cover_note: …

dossier:
  title: Expediente El Arrayán
  kicker: PDI · Brigada de Homicidios Temuco
  description: …               # screen header text
  printed_description: …       # text on the printed index
  sections:
    start: {title: Sobre 1, note: Se entrega a ambos equipos al comenzar}
    procedures: {title: Diligencias, note: Se entregan al equipo que paga la ficha}

envelope_labels:               # labels to stick on the paper envelopes (one per team)
  - number: 1
    when: se entrega al comenzar
    description: Lo que sabemos hasta ahora.
    contents: [E01 Parte policial, E02 Set fotográfico]
    footer: 16 fichas · 1 placa por jugador

strings: …                     # optional: replaces words the exporter prints
```

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
| `follow_up` | One or several question codes the card enables. |
| `footer` | A free line at the bottom. |
| `menu` | `true` to show the question in the kit's menu. |
| `suspect` | If the card is about another suspect than its group's. |

Cards of type `notice`, `press`, `hint` and `closing` print on a separate sheet at the end, because they are used at another moment of the game. The exporter checks that every `attach` exists in the dossier and warns when an answer is over 420 characters. If a card does not fit when printing, it shrinks the type down to 8.5 pt; if it still does not fit, it outlines the card in red and says so in the console.

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
| `notice` | `true` for the amber strip of the prosecutor's notices. |
| `aged` | `true` for aged paper (letters, old documents). `paper: aged` also works. |

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
| `signature` | Signatures at the bottom | List of `{scrawl: I. Painemal, label: Comisario a cargo}`, or plain texts |
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
| `columns` | Side-by-side columns, for quick-reference sheets. Argument: minimum width of a column in px (default 230) | Markdown pieces separated by a line with `===` |
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

If you write a block that does not exist, the exporter stops and tells you which ones there are.

## Ink saver

By default the PDFs come out without backgrounds: white sheets, without the grey of table headings or the fill of notes, phones or tokens. Colour stays where it means something: card bands, codes, stamps, token rings, rules and text. Printing backgrounds uses a lot of ink and does not help play.

For the full-colour version, for a print shop or to look at it on screen:

```
python export.py cases/my-case --color
```

If a case is always printed in colour, put `ink_saver: false` in its `case.yaml`; `--ink-saver` then forces the saver mode again. Photos print the same in both modes, and the chat images (`--images`) are always full colour, because they are not printed.

## Styles of a case

If a case needs something the design system does not have, create `styles.css` in its folder. It is loaded after everything else. Use it sparingly: whatever is useful for more than one case should go to `design/open-case.css`.
