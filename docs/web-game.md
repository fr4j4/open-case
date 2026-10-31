# The whole game: phases, notices, hints and score (F5)

From the scene to the closing the game runs in the app. The director runs the clock of the phases; the teams can only ask during
the investigation; the director hands out the notices and the hints; the teams hand in their sheets; and the director ticks the
score, which adds up by itself. Everything is a figure or a block the engine already publishes: **a case adds nothing**.

## The clock (`js/clock.js`)

A pure module (no DOM, no network, no clock of its own: every function takes `now`). The phases are `figures.phases` in the order of
`opencase/defaults.yaml` (`setup`, `scene`, `investigation`, `accusation`) and then `closing` (the first of `closing_minutes`); a case
changes any of them in its `case.yaml` and the app follows, without touching JS (`tests/web/test_game.py` does it).

- The director chooses the phase (a button per phase, with its minutes) or goes to the next one, pauses, starts and moves the time by
  ±1 minute ("advance"). **Nothing changes phase by itself**: when the time runs out the clock shows how much it ran over.
- A team may ask **only in the investigation** (rule 1 of the kit). The phone does not let it send (`requests.why.phase`) and the
  director's panel refuses to answer a request outside it (`requests.panel.error.phase`). `book.clock` is the director's clock; a
  `newBook()` without one (the rules tests) has no phases.
- Minute 0 of the investigation is when the director moves to it (the kit says: "minute 0 is when envelope 2 is opened").
- It travels as `{k:'clock', phase, running, elapsedMs}`, to the phones that connect and every time it changes. A phone counts from
  its own clock starting at the moment the message arrived, so nothing depends on seconds sent over the network (and a clock that
  arrives before the phone has its folder is kept and applied right after).

## Notices and press (Game tab)

The notices and the press card are the cards of the case (`director.notices`). The panel marks as **due** a notice whose minute
(`figures.notice_minutes`) has passed, and shows a toast, but only the director decides: *Hand out to all* gives the card to every
team (the same delivery as the *Give* tab) and the notice stays marked as read. The team never sees the suggested minute (the
kit and the phones say only "notice 1 of 2"); notice 2 is up to the director.

## Hints

`director.hints` (cards `hint`) are handed out **in order** to a team (*Give hint*), each with its penalty
(`figures.hint_penalties`, shown in the button). The hints given are kept per team and are subtracted in the score.

## The sheets handed in (*Hand in* tab of the phones)

The kit sheets in `team.json` → `forms` (the accusation and the discard sheet: their labels, boxes and rows) are drawn as forms.
What a team writes is kept on the phone as it types. *Hand in to the director* sends it (`{k:'form', id, values}`); the phone
shows it as handed in when the director answers `{k:'formok', id}`, and until then it stays queued and goes again each time the
director connects. **When the director moves to the closing, what a team wrote and did not hand in is sent by itself.** The
director checks every key (`f<part>.<item>` or `t<part>.<row>.<column>`, texts of at most 2000 characters) and keeps the last
version of each sheet per team. It reads them in the *Score* tab, laid out as the sheet.

## Score (`js/score.js`)

A pure module over `figures.score` and `director.score.bonus` (the case's own line). The director ticks, per team, what the printed
sheet asks: the accusation (none, culprit with evidence, culprit without, wrong person), how, why, window, the case's line,
contradiction, and the counts of innocents ruled out with two pieces of evidence or one, innocents left unexplained and red herrings
explained (never more innocents than the case has). The app adds the numbered tokens left over (`score.spare_token` each; alibi
tokens do not count, as in `rules.js`) and subtracts the hints.

- **Wrong accusation:** `score.wrong_accusation` and the team cannot win. If every team fails there is no winner.
- **No accusation:** only the tokens left over count (the kit says "solo suman las fichas que les sobren"); the hints still cost.
- **Ranking:** teams that can win first; more points, then fewer numbered tokens spent. A tie in both is shown as such, because
  "the clearest theory" is judged by the director.
- **Final report:** *Download the final report* writes a Markdown file with the ranking, the score of each team line by line, every
  request with its answer and cost, what was handed out and the sheets each team handed in.

## Where it is

| File | What it does |
|---|---|
| `js/clock.js`, `js/score.js` | the pure accounts (`tests/web/game.test.mjs`) |
| `director/partida.js` | *Game* and *Score* tabs and the report |
| `equipo/partida.js` | the phase strip and the *Hand in* tab |
| `director/app.js`, `equipo/app.js`, `js/room.js` | the wiring: clock messages, sheets, notices, hints |
| `opencase/web.py` | `team.json` → `forms` (schema_version 3) |

Words: `web.game` in `opencase/strings/es.yaml` and `en.yaml` (F6c translates the values; the keys are already in both).

## Tests and closing

- `tests/web/test_game.py` (node): the phases, the clock, the notices' minutes, the score of a scripted game of four teams and the
  ranking, all against numbers worked out apart from the JS from `defaults.yaml`; and a case that changes `phases.investigation`,
  `notice_minutes` and `score` and gets the new times and points with the same JS.
- `tests/web/test_game_ui.py`: a whole game of a director and two phones over the real `relay` transport: nobody asks before the
  investigation, the notice comes due and reaches both teams, a hint reaches one and costs, a sheet is handed in and another goes at
  the closing, and the totals shown are those of the figures.
- `tests/web/test_requests_ui.py` now moves the clock to the investigation first.

**Technical closing:** the above, in the CI. **Field closing (for fr4j4, it blocks only phase I):** a whole game without paper in the
preview, with a table, from the scene to the score, and the minutes of the phases and the notices as a director feels them.
