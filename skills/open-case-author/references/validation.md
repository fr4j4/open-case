# Validation

A case is validated twice: the bible before generation (phase 4, `problem-detection.md`) and the generated case before it is called ready. This file is the second one. It has three desk audits, a simulation with two teams, and the acceptance criteria. The prompts are in `templates/audit-prompts.md`.

The audits are done on the text the exporter produces, not on the bible: export the case, extract or read the PDFs (or the HTML in `output/<case>/<lang>/html/`), and give each auditor the whole material. Each auditor reads with one question in mind and must not change any file. Findings go to bible §15 with severity, fix and status.

## Audit 1 · Consistency and contradictions

Reader: a meticulous clerk. Reads everything (kit, teams' envelopes, the Evidence file, cards, guide, images). Looks for: times and places that do not fit; distances against travel times; numbers that do not add up; who provided a sheet against who hands it out; captions against images; statements against suspect cards; sketch against text; weekday against date; anything the guide says that the dossier does not support.

Output: a list by severity (breaks / unfair / cosmetic), each with the quotes that clash and a minimal fix. Ends with "verified without problem" for the main chain of the solution, hour by hour.

## Audit 2 · Difficulty and paths

Reader: a strong player who knows the solution and tries to break the economy. Computes: the shortest route to a correct accusation and to the confession, counting tokens from zero and including free material; the independent paths and whether each is visible from the menu; whether the free material alone names the culprit; whether the elimination route is cheaper than the deduction route; how many tokens it costs to discard every innocent; whether the main red herring can be avoided entirely; what the hints give away; the director's load (requests per minute, codes without a row).

Output: the numbers, a path table (path → sheets → ◆ card → tokens → visible?), and a verdict: too easy / right / too hard, with the minimal change. Check against `design-rules.md` §19–21.

## Audit 3 · Spoilers, rules and playability

Reader: a player who only has the kit, then a novice director who only has the guide. Looks for: anything in the teams' material that reveals the solution, a red herring, a location or a key datum before it is earned; rules the kit does not state or states differently from the guide; terms used but not defined; what happens in the final phase; fairness (order of presentation, queue, free questions); whether a novice could run it with the guide alone; photos against the brand rules (faces, blood, logos, file names).

Output: findings by severity with the quote and the fix; a list of "what is not a problem" so the author does not re-check it.

## Simulation with two teams

When agents or the person can run it. It measures what desk audits cannot: whether the paths are found, how long the red herring holds, how many tokens are spent, whether both teams converge, and whether the response table works under load.

Setup:
- Two team agents, each with: the kit, envelope 1, envelope 2 and the images, as text files. Each represents five players deliberating. They do not see each other.
- One director (you, or an agent) with the Evidence file, the cards and the guide.
- Rounds: 6 (standard) or 4 (short), up to 3 requests per round per team, alternating teams. Notices after rounds 2 and 4 (standard) or 1 and 3 (short).
- Fixed request format and accusation format (in `templates/audit-prompts.md`), so the log can be scored.
- Keep a log: round, team, request, delivery, tokens. Score both accusations with the guide's rubric.

Read the log for:
- Did either team spend fewer than 60 % of its tokens and still accuse correctly with confession? Too easy.
- Did a team accuse an innocent with a coherent theory the material supports? A hole: find which sheet should have stopped them.
- How many rounds did the main red herring hold? Fewer than two: it is weak. Until the end: the explaining sheets are not visible enough.
- Which paths were used? If both teams used the same one, the others are not visible from the menu.
- Did the director have to improvise an answer? Add the row.
- Did "one ◆ = one card" and "you already have it" work?

The simulation uses language models as players: it finds structural problems, not what humans will enjoy. One real table before publishing is still the rule of the README.

## Acceptance criteria

The case is ready when all of these hold:

1. `python export.py cases/<case> --check` ends with "Check finished." and every remaining warning is explained in bible §15.
2. `scripts/case_lint.py cases/<case>` reports no errors; its warnings are explained.
3. The export reports no card overflow; two-page sheets are only the mission and the response table, or justified.
4. Audit 1 has no "breaks" findings open; "unfair" findings fixed or accepted by the person.
5. Audit 2: minimum route ≥ 40 % of the budget; free material does not name the culprit; three paths of different type each visible from the menu; discards cost 50–65 % of the budget; main red herring avoidable but pushed.
6. Audit 3: nothing in `teams/` reveals the solution; every rule of `design-rules.md` §31 is in the kit; kit and guide agree on every number.
7. Simulation, if run: both teams reach a correct accusation in the last third of rounds, neither for free; at least two different paths used across the two teams; no improvised answers.
8. The person has seen the audit summary and the list of changes made after their validation of the bible.

## What to tell the person

One message: the three numbers (minimum route, discard cost, expected spend), the verdict of each audit in one line, the list of changes you made to their validated design and why, what was not changed and why, and where the PDFs are. Then the one thing that matters most: play it once with real people before printing twenty copies.
