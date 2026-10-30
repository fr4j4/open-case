# Example: a short case from a conversation

This folder shows one complete run of the skill, from a two-line idea to an exported case.

1. `conversation.md`: the (condensed, simulated) conversation between an author writing in Spanish and an assistant following `SKILL.md`. Watch for the moves: proposing before asking, reflecting decisions back, counting the three numbers, running the problem-detection pass before asking for validation, and reporting changes made after validation.
2. `bible.md`: the case bible at the moment of validation, plus the log of what changed while generating. It passes `scripts/bible_check.py`.
3. `cases/cierre-de-caja/` in the repository root: the generated case. It passes `python export.py cases/cierre-de-caja --check` and `scripts/case_lint.py`, and exports to PDF in a few seconds. Numbers: 4 suspects, 10 tokens, 33 dossier sheets, 43 cards, 6 kit sheets, 7 guide sheets, 45–50 minutes.

To reproduce the export:

```
python export.py cases/cierre-de-caja
```

What was not done for the example, and should be before a real table: the simulation with two LLM teams (`references/validation.md`) and a play test with people.
