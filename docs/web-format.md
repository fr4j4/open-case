# The case compiled for the web

`python3 -m opencase.web` (or `make web`) turns a case into the files the web app (`site/play/`) reads. The app
never reads YAML or Markdown: this folder is the contract between the engine (Python) and the app (JavaScript).
Everything is drawn from the same data and the same functions as the PDFs, so a rule or a text changed once
changes both. A case adds nothing for the web: a new case compiles as it is.

```
make web                              every published case, into _site/play/
make web CASE=cases/cierre-de-caja    one case, also one with `published: false`
python3 -m opencase.web --out DIR     the same, into DIR/play/
python3 -m opencase.site              the site (PDFs, zips…) also builds play/
```

## Where things are

```
play/
  cases/index.json                         which version of each case and language is current
  cases/<slug>/<lang>/<version>/
    manifest.json                          version, schema_version, size of every file
    team.json                              what the teams' devices may know
    director.json                          what only the director's device may know
    sheets/<id>.html                       one page per sheet of the dossier (an evidence sheet or a statement)
    sheets/kit-<id>.html                   one page per sheet of the team kit (the engine's included)
    cards/<code>.html                      one page per card of cards.yaml
    suspects/<letter>.html                 one page per suspect card
    assets/design/…                        the stylesheets, fonts and logos those pages use
    assets/media/…                         the photos and drawings, with the same paths as in the case folder
  strings/<lang>.json                      the engine's words for the app (`web:` of opencase/strings/<lang>.yaml)
```

- `<slug>` is `site.slug` of `case.yaml` (the folder name when there is none).
- `<version>` is the first 12 characters of a hash of every file of the folder: the same case compiles to the same
  version, and any change (a word, a photo, the engine) makes a new one. The app compares it with `index.json` to
  know it is out of date. The site replaces the whole folder in every deployment, so old versions disappear.
- Every page is a whole HTML document that links its styles with relative paths (`../assets/…`), so it opens
  on its own, in an iframe, or from the service worker's cache. Every path in the pages is relative.
- File names: letters, digits and `-` stay; anything else becomes `_` and the code point in four hex digits
  (`B1+` is `B1_002b.html`, `B✕` is `B_2715.html`). The JSON always gives the `file`, so the app never builds a name.
- Sheets are named by their **id** (the file name in `dossier/`), not by their printed code: `E13b` and `E13b-2`
  are two sheets with the code `E13b`.
- The pages of a sheet are the `<article>` the PDFs print, byte for byte after normalising spaces and paths
  (`tests/test_web.py` checks it for every sheet). A card page is the card the PDF cuts out.

## `schema_version`

All the JSON carries `schema_version` (today **4**). The JSON Schemas in `docs/web-schema/` (`team`, `director`,
`manifest`) describe every field and are checked by `tests/test_web.py` against the real files. They have
`additionalProperties: false`: adding a field is a change of the contract. To change the schema:

1. edit `docs/web-schema/*.schema.json` and the code of `opencase/web.py`;
2. raise `SCHEMA_VERSION` in `opencase/web.py` and the `const` of `schema_version` in the three schemas;
3. run `python3 -m opencase.web --write-fingerprint` and commit `docs/web-schema/fingerprint.json`.

A test fails if the schema changes without a new `SCHEMA_VERSION`.

## `team.json` (public)

| Field | What it is |
|---|---|
| `case` | `slug`, `language`, `title`, `summary`, `paper`, `brand` |
| `figures` | `opencase/defaults.yaml` already combined with the figures the case changes (tokens, minutes, score…) |
| `rules` | see below |
| `teams[]` | `id`; `tokens` (1…`tokens_per_team`); `alibi_tokens` (`C1`, `C2`…) |
| `suspects[]` | what the suspect card says: `letter`, `name`, `short_name`, `role`, `facts[]`, `portrait`, `card`, `questions` (menu codes), `confront` (`B◆` and its text) |
| `menu[]` | the question menu of the kit: `code`, `suspect`, `question` |
| `follow_ups[]` | `code`, `cost`, `unlocked_by` (codes the team must already have). The question is only in the guide |
| `procedures[]` | the menu of procedures: `code`, `kind`, `label`, `target` (person, place or thing), `cost`, `costs`, `each`, `alibi`, `source`, and `targets` (suspects, places and "other" only: a target of the case's own, like the deleted message, is left out because its name would say something) |
| `envelopes[]` | envelope `number` and its `sections` with the `code`, `id` and `file` of each sheet |
| `forms[]` | the sheets the team fills in and hands to the director (F5): `id`, `title`, `file` and `parts`, taken from the kit's own blocks: `{kind: fields, items: [{label, type: line\|box}]}` and `{kind: table, columns, rows}`. The kit sheet with the schedule (the timeline) is left out |
| `kit[]` | the pages of the team kit, in order |
| `texts` | `title`, `tagline` |

It has **no** result of a procedure, no text of a card, nothing of the guide. `tests/test_web.py` looks for the
answers of the cards, the `guide_note`s, the notes of procedures and places and every paragraph of the guide
(texts of more than 30 characters, if the kit or the envelopes do not also say them) in `team.json` and fails if
it finds one. The sheets and cards are public files too (anyone who knows the URL can open them): the app keeps
what is not yet handed out out of the way, in good faith, as agreed in the plan.

## `director.json` (only the director's device)

| Field | What it is |
|---|---|
| `case`, `figures`, `rules` | as in `team.json` |
| `sheets[]` | every sheet of the dossier, in the order of `case.yaml`: `id`, `code`, `title`, `file`, `section`, `envelope` (`null` when it is handed out by a procedure or a card) |
| `cards[]` | every card of `cards.yaml`: `code`, `type`, `file`, `suspect`, `who`, `headline`, `question`, `answer`, `note`, `footer` (what the engine writes: the points of a hint, "1 de 2" of a notice), `menu`, `attach` (sheets it hands out), `follow_up`, `unlocked_by`, `guide_note`, `opens_with` (the rules of the evidence that open a confrontation card: `all`, `any`, `none`, `held`, `priority`; empty on the other cards) |
| `procedures[]` | those of `team.json` plus `short`, `note` and **what each hands out**: `gives` (one result) or, per target, `sheets` (printed codes), `special` (`none`: "sin hallazgos"; `material`: hand out what the material has), `cost` and `note` |
| `locations[]` | the places and the `sources` (`camera`, `register`) each has |
| `witnesses[]` | `name`, `cards`, `appears_in` (where the teams can read the name), `aliases`, `attach` |
| `follow_ups[]` | the full question, its `mothers` (the cards that enable it) and its condition |
| `notices[]` | the notices and press cards in order, with the suggested `minute` (`figures.notice_minutes`) |
| `hints[]` | each hint and its `penalty` |
| `score` | the points, the case's own line (`bonus`) and the hint penalties |

## `rules` (in both)

What is needed to charge and give tokens back:

- `tokens_per_team`, `alibi_tokens_per_team`;
- `costs`: `question`, `witness`, `confrontation` and `follow_up`, from `figures.costs` of `opencase/defaults.yaml`
  (a case may change them; the kit, the guide and the follow-up box print the same number);
- `requests`: for each kind of request (`question`, `witness`, `follow_up`, `confrontation`, `procedure`, `source`) its
  `cost` (null for a procedure, which has its own, and for `source`, which is free) and `answers`: every answer the
  director can give and whether it **charges** (`give`, `obvious`, `unavailable`, `nothing_to_add`, `locked`,
  `failed`, `no_basis`, `nothing_found`, `already_have`, `yes`, `no`; the meaning of each is in
  `opencase/procedures.py`, `REQUESTS`). A follow-up has `unlock: "any"`: one of its `unlocked_by` is enough;
- `wildcards`: the code of the card that answers in the engine's name (`role:` of a wildcard card in `cards.yaml`:
  `no_findings`, `unavailable`, `nothing_to_add`, `confrontation_failed`), or null when the case has none;
- `procedure_kinds`: for each kind of procedure, what its target is (`target`), whether it shows where someone was
  (`locates`, so an alibi token can pay it) and whether it reads a source a place has (`source`, so asking if the
  place has one is free);
- `alibi_procedures`: the codes of the case that accept an alibi token (`alibi: true`);
- `free_source_procedures`: the codes whose existence of a source may be asked for free.

The cost of a procedure is in `procedures[].cost` (and `costs`, when a target costs more).

### How the app applies them (`site/play/js/rules.js`)

The module is pure (no DOM, no network) and reads only these fields and the cards, sheets, procedures and witnesses of
`director.json`; it has no number or code of its own. For each request it offers the director's buttons
(`answers`) and applies one (`resolve`), which returns the new state or an error and never leaves a negative balance.

| Rule of the kit | Where it is data | What `rules.js` does |
|---|---|---|
| 1 Questions cost `costs.question`, also off the menu; the obvious is free | `requests.question.answers` (`give` charges, `obvious` does not) | charges `give`; `obvious` keeps the tokens |
| 1 Only in the investigation | the app (F5) opens the phase | — |
| 2 A witness only once named | `witnesses[].appears_in` | `give` is refused (`unavailable`) until a sheet or card of `appears_in` is held; one card per question, in order; then `nothing_to_add` |
| 3 A confrontation hands out one card; a wrong one is charged | `requests.confrontation`, `cards[]` (`confrontation`, `failed`) | `give` with a card of that suspect, or `failed` (their `failed` card, else `wildcards.confrontation_failed`); the same card twice is `already_have` |
| 3b Which card a confrontation opens | `cards[].opens_with` | `matchConfrontation(game, state, suspect, evidence)` gives `{card, candidates}`: the cards of the suspect with a rule that fits (`all` every one shown, `any` at least one, `none` none, `held` cards the team already holds); the highest `priority` wins and `card` is null when the best ones tie (the panel lists them and the director asks) or none fits (`failed`). Same as `opencase/confrontations.py` `match` |
| 4 Procedures: no basis is free, "sin hallazgos" is charged, what they already have is free | `requests.procedure`, `procedures[].targets` (`special`) | `nothing_found` only where the result is `none` or `material`; `give` of a held sheet is `already_have`; `no_basis` is free |
| 5 Asking if a place has a source is free | `free_source_procedures`, `locations[].sources` | `source` answers `yes` or `no` (the one the place suggests) without charging |
| 6 Alibi tokens | `alibi_procedures`, `procedure_kinds[].locates` | an alibi token pays only a charged answer of a procedure in `alibi_procedures`; spare numbered tokens score `figures.score.spare_token`, alibi ones do not |
| 7 What places a person | — | judged by the director (it stays text) |

`tests/web/test_rules.py` runs `tests/web/rules.test.mjs` with node: the 100 % of the menu questions, follow-ups,
witnesses, confrontations and procedure–target pairs of the Chupacabras give in JS the cards, sheets and cost that
pytest works out from the loaded case (`requests` in `tests/web_expected/<case>.json`), and `tests/web_expected/<case>-confrontations.json` (the old guide table written by hand: evidence → card) gives the same card in Python and in JS; every kind of request
with every button is run against the balance (never below 0, spent + left = initial).

## `manifest.json`

`schema_version`, `version`, `case`, `language`, `files` (path inside the folder → bytes) and `total_size`.
`manifest.json` is not in its own list and not in the hash.

## `strings/<lang>.json`

`{"schema_version", "language", "web": {…}}`: the `web:` section of `opencase/strings/<lang>.yaml` of the
engine. It is empty in F1; each later phase adds its own subsection (`web.team`, `web.director`, `web.requests`…)
in `es.yaml` and `en.yaml` (`tests/test_strings.py` asks for the same keys in both).

## For authors of the engine

- `opencase.documents.render_sheet(case, code, ctx=None, doc=None, kit=None)` and
  `opencase.cards.render_card(case, code, extra=None)` give the HTML of one sheet or card, the one the PDFs use.
  `ctx` (a `Context`) decides where photos and logos are read from; the web build gives it a `WebContext`
  that points them to `assets/` and remembers which files that takes.
- To add a field: add it to `web.py` and to the schemas, raise `SCHEMA_VERSION`, run `--write-fingerprint`, and
  list the new field here.
