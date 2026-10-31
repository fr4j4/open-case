# Problem detection

Checks to run on the bible. The quick checks run after every message that adds facts; the full pass runs at every gate and before validation. Report each finding with: what clashes, where (section and item), the fix you propose, severity.

Severity: **breaks** (an innocent can be convicted, the culprit is reachable for free, a path has no evidence, the format cannot express it), **unfair** (one team or the director is disadvantaged, rules are ambiguous, a spoiler), **cosmetic** (wording, duplicated names, numbers that do not add up without effect on the solution).

## Quick checks (every message)

- **Names:** two people with the same or similar name or initial; a person mentioned who is in no table; a suspect whose letter clashes.
- **Times:** a new time that contradicts the timeline; a person in two places; travel time impossible for the distance; an event before its cause (someone speaks of the blow before the autopsy reveals it).
- **Truth drift:** does the new fact change the truth paragraph? If yes, flag which sections depend on it.
- **Document honesty:** did the person just make an official document lie? Convert into "someone chose to show" or "a coincidence".
- **Free material leak:** does the new fact put something convicting into envelope 1, a statement or the autopsy?
- **Format fit:** is the person asking for a mechanic the exporter cannot print (an app, a sound, a real-time event)? Offer the closest supported piece.

## Full pass (gates and validation)

### A · Consistency

1. Timeline: every suspect accounted for at every row that matters; the culprit's movements fit every record that will exist; weather and light consistent with photos and clothes; dates match weekdays.
2. Distances and speeds: list every movement with distance and time; anything under 20 km/h on foot or over 60 km/h in town is suspect.
3. Numbers: counts, money, instalments, ages, years of relationships, phone minutes. Sum them.
4. Provenance: for every sheet, who "provided" it in the fiction matches who hands it out in the game (the witness who "has the stories" is the one whose card attaches them).
5. Coverage: a cell tower record states its coverage; it is used as a discard only if the scene is outside it.
6. Photos and sketches: what the caption says is visible is visible; the sketch's distances match the text or the sketch says "not to scale" and carries no measurement.
7. Statements: five identity fields match the suspect card and every other sheet (age, address, occupation, description).

### B · Solvability and difficulty

8. Paths: at least three of different type, each written as sheets → ◆ card, each with at least one paid sheet. Paths share at most one sheet.
9. Minimum route: count tokens from zero to the confession with perfect knowledge, including routes from free material. ≥ 40 % of the budget.
10. Free material: read envelope 1, statements and envelope 2 as a sharp player. Can you name the culprit with certainty? If yes, move a datum to a paid sheet or soften it.
11. Discards: each innocent has two sources of different origin inside the window; no tower covering the scene; no sighting outside the window; the sum to discard everyone is 50–65 % of the budget.
12. Red herrings: each one has at least one explaining sheet; the main one is pushed by a notice and dissolves with an alibi plus an innocent explanation of the damning fact.
13. Dead ends: every procedure target has a sheet or a documented "no findings"; every follow-up has a base card; every witness has an "appears in"; every expert card has the sheet it interprets.
14. Hidden routes: anything reachable only by a procedure that is not in the menu has a visible alternative.
15. Confrontation table: every sheet the guide calls a contradiction has a row; combinations are unambiguous; the failed card exists and hints at what is missing without director's notes.

### C · Spoilers and rules

16. Kit: no list of red herrings; no places not yet introduced; no key datum in the expert question; no hint of staging in the accusation sheet; suspect order not a tell; the phrase about "different types of evidence" is generic.
17. Notices and press: no codes; no sheet contents the teams have not earned.
18. Cards: no director's notes; no two confrontation answers on one card; nothing about another suspect that the team has not earned.
19. Envelope labels and suspect cards: no solution content.
20. Rules in the kit (the engine's sheets carry them; check that the case's sheets do not contradict or repeat them): costs of everything; what is free and who decides; different origin defined; crime window defined for scoring; final phase procedure; tie-break; both-wrong rule; confession scores nothing; hints exist, count and cost.
21. Kit vs guide: tokens, timings, notice minutes, scoring weights, hint penalties identical. The engine prints them from the same figures, so look for a number the case wrote by hand (the lint warns about tokens and notice minutes).

### D · Director load

22. Response table has a row for every code in the kit and every card in cards.yaml.
23. Policy rows: no sheet, already have it, redundant, off-menu obvious, off-menu answerable, witness not yet available.
24. Control sheet lists every deliverable with cost; score sheet exists; discard table and red-herring table exist.
25. Preparation list: copies, envelopes, cutting, wall, timers.
26. Queue policy and "collect sheets before presenting" are written.

### E · Format and material

27. Every sheet fits one page (a register of 12 rows, a statement of 6 paragraphs, a chat of 20 messages). Long ones are split (E13a, E13b).
28. Every card ≤ 420 characters; longer ones split into (1 de 2) and (2 de 2).
29. Every image promised exists or is replaced by text or an SVG.
30. Suspect letters unique; codes follow `game-model.md` §Codes; file names match codes (`E17-B.md` for `E17·B`).

## After generation

Run `--check` and `scripts/case_lint.py`; then reread, as a player, every file that the exporter puts in `teams/`. Then run the audits of `validation.md`.
