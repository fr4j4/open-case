# Case bible · {Title}

> The single source of truth while the case is designed. Never exported, never shown to players.
> Status per section: ⬜ empty · 🟨 draft (or proposed by the assistant, marked 🟨 proposed) · ✅ validated by the author.
> Codes follow `references/game-model.md` §Codes from section 5 on. Replace every `{…}` and remove this note before validation.

## 0 · Frame ⬜

| Field | Value |
|---|---|
| Title | {working title; the case name only} |
| Slug (folder) | {lowercase-ascii-hyphens} |
| Case language | {es / en / …} |
| Locality | {town, country; real or fictional; whose institutions and formats} |
| Players | {how many, ages, genre familiarity} |
| Duration | {standard 65–75 min / short 45–50 min} |
| Teams · tokens · players per team | {2 · 16 · 7} |
| Tone | Police procedural, no horror. {anything specific} |
| Images | {none / sketches as SVG / photos the author will provide} |
| Paper | {letter / a4} |
| Version · date | {v0.1 · YYYY-MM-DD} |
| Validated by the author on | {—} |

## 1 · The truth ⬜

{One paragraph. Who killed whom, how, why, when (the window), and the telling detail: the thing the culprit could not avoid and nobody else would have done. Then the hidden plot behind the cover story, if any.}

**Cover story (what it looks like on the morning after):** {robbery / accident / animal / …}

**Telling detail:** {what it is, which sheets reveal it, which card explains it}

## 2 · Setting and time ⬜

{Place, season, date, weekday. The environment events that mark the night from outside: rain start, power cut, a loud event, a live stream. Distances between the places that matter, with travel times by foot, car, bus.}

## 3 · The victim ⬜

| Field | Value |
|---|---|
| Name · age · occupation | |
| Why several people wanted them gone | |
| What they did in their last 24 hours | |
| What they carried / what was found with them | |

## 4 · Suspects ⬜

Order here is the order of the kit and the suspect cards: not the culprit first.

| Letter | Name · age | Role / relation | Apparent motive (visible in free material) | Secret (unrelated to the crime, or the crime itself) | The lie (specific, checkable) | True alibi (for innocents: where they were in the window) | Discard evidence (two sources, different origin) |
|---|---|---|---|---|---|---|---|
| {B} | | | | | | | |
| {H} | | | | | | | |
| {J} | | | | | | | |
| {P} | | | | | | | |

Culprit: {letter}. Main red herring: {letter}.

Five facts per suspect for the card (age, occupation, relation, lives in, description): {table or list}.

## 5 · Timeline of the night ⬜

Crime window: {HH:MM–HH:MM}. Key minute: {HH:MM}.

| Time | Victim | {B} | {H} | {J} | {P} | Environment (weather, light, events) | Recorded by |
|---|---|---|---|---|---|---|---|
| | | | | | | | |

Check: travel times possible; every record (tower, camera, log, witness) matches this table; weather matches clothes and photos.

## 6 · Deduction paths ⬜

At least three of different type plus the motive; each with at least one paid sheet.

| Path | Type (movement / alibi / knowledge / physical / motive) | Sheets (how obtained) | ◆ card obtained | Tokens from zero | Visible from the menu? |
|---|---|---|---|---|---|
| A | | | | | |
| B | | | | | |
| C | | | | | |
| M (motive) | | | | | |

Minimum route to the confession: {list of requests} = {n} tokens of {budget} ({%}).
Cost to discard every innocent: {n} tokens ({%}).
Cost to sweep one procedure across all suspects: {n}.

## 7 · Red herrings ⬜

| Red herring | Who or what pushes it (notice, free sheet, suspect) | Points at | Sheets that explain it | Points for explaining |
|---|---|---|---|---|
| {main} | {notice 1 and 2} | | | 1 |
| | | | | 1 |

## 8 · Evidence ⬜

| Code | Title | Kind (report, statement, log, chat, bank, tower, camera, search, receipt…) | How obtained (free envelope 1 / envelope 2 / with card X / procedure DGn target / witness) | Provided by (in the fiction) | What it shows | Truth or chosen-to-show | Serves paths / discards / red herrings | Spoiler risk |
|---|---|---|---|---|---|---|---|---|
| E01 | | | free, envelope 1 | | | | | |
| DEC · {B} | | statement | free, envelope 1 | | | lie: … | | |

Dossier sections (→ neutral `case.yaml`): opening (envelope 1): {codes}; statements (envelope 1): {codes}; investigation start (envelope 2): {codes}; handed with an answer: {codes}; procedures: {codes}; notices: {codes}.

## 9 · Questions and cards ⬜

Per suspect: menu questions (the first is "where were you"), follow-ups, confrontations with triggers, failed card.

### {B} · {name}

| Code | Type | Question (or evidence that triggers it) | Answer (≤ 420 chars) | Attach | Enables | Truth |
|---|---|---|---|---|---|---|
| {B}1 | menu | ¿Dónde estuvo…? | | | {B}1+ | false |
| {B}2 | menu | | | | | |
| {B}3 | menu | | | | | |
| {B}◆ → {B}4 | confrontation | shown: {E.. + E..} | | | | |
| {B}✕ | failed | shown: {E.. alone} | | | | |
| {B}1+ | follow-up | | | | | |

{repeat per suspect}

### Wildcards

"Eso no prueba nada" · "Testigo no disponible" (free) · "Nada que aportar" (free).

## 10 · Procedures and witnesses ⬜

Procedures menu (→ kit 03 and guide 06):

| Code | Procedure (neutral wording) | Cost | Targets → sheet |
|---|---|---|---|
| DG1 | | 1 | |
| DG2 | | 1 | |

Sheet matrix for per-suspect procedures:

| Procedure | {B} | {H} | {J} | {P} | Other |
|---|---|---|---|---|---|
| Tower | E..·B | | | | — |
| Vehicle | | | | | E..·X no findings |

Witnesses:

| Code | Witness | Appears in (what unlocks them) | Delivers | Truth it adds |
|---|---|---|---|---|
| R1 | | free (named in E01) | card R1 | |
| | | | card + E.. | |

People named in any sheet who are not suspects or witnesses (they get "Nada que aportar"): {list}.

Expert card: {PER1: what it interprets, after which sheet}.

## 11 · Notices, press, hints ⬜

| When | What is read (no codes, no unearned sheet content) | Pushes |
|---|---|---|
| Notice 1 · minute {10} | | {main red herring} |
| Notice 2 · minute {20} | | |
| Press card · with notice 2 | | |

Hints in order (soft → strong), with cost: 1. {…} (−1) 2. {…} (−1) 3. {…} (−1) 4. {…} (−2) 5. {…} (−2).

## 12 · Economy and scoring ⬜

Tokens {16}; timing {10 / 30 / 15}; what is free (closed list): {…}.

| Achievement | Points |
|---|---|
| Correct culprit with a linking sheet | 5 (2 without) |
| How | 2 |
| Why | 2 |
| Window (any range containing {key minute}) | 1 |
| Case-specific bonus: {…} | {3} |
| Contradiction of the culprit | 1 |
| Each innocent discarded (two sources, different origin) | 2 (1 with one) |
| Each innocent left blank | −1 |
| Each red herring explained with its sheet | 1 |
| Each token left | 0.25 |
| Each hint | −1 (4th and 5th −2) |
| Wrong accusation | −5, cannot win; both wrong: no winner |
| No accusation | only leftover tokens |

Tie-break: fewer tokens spent, then the clearer presentation.

Confession conditions: two of the paths {A/B/C/D} with their ◆ card, plus motive ({sheets or cards}), plus the name on the sheet. Confession scores nothing.

## 13 · Director's script ⬜

Opening (60–120 words): {…}
Notice 1: {…} · Notice 2: {…} · Press: {…}
Confession (120–200 words, first person): {…}
Closing (60–100 words, one line per suspect's fate): {…}
After: show the deduction diagram and walk through the paths.

## 14 · Graphics ⬜

| Image or drawing | For sheet | Constraints | Status |
|---|---|---|---|
| Sketch of the scene (SVG) | E02 | not to scale, legend | |

## 15 · Decisions, problems and changes ⬜

| Date | Kind (decision / problem / change / audit / simulation) | What | Severity | Fix | Status |
|---|---|---|---|---|---|
| | | | | | |
