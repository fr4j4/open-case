---
# ```score-sheet in the guide: how to break a tie and the score sheet (one per team), with the
# case's bonus line (score_bonus in case.yaml, its text in score_texts).
---
{% import "_macros.j2" as m %}
{% set innocents = n_suspects - 1 %}

### Tie-break

The team with the most points wins. On a tie, the team that spent fewer tokens wins; if still tied, the one that presented the clearest theory (you decide).

### Score sheet (print one per team)

```table score
| Item | Pts | Team ______ |
|---|---|---|
| Killer (with evidence) · without any evidence | {{ score.culprit|num }} · {{ score.culprit_no_evidence|num }} |  |
| How | {{ score.how|num }} |  |
| Why | {{ score.why|num }} |  |
| Window | {{ score.window|num }} |  |
{% if bonus %}
| {{ bonus.short }} | {{ bonus.points|num }} |  |
{% endif %}
| Contradiction | {{ score.contradiction|num }} |  |
| Innocents ruled out ({{ score.discard_two|num }} each, {{ score.discard_one|num }} with one piece of evidence) × {{ innocents }} | up to {{ (innocents * score.discard_two)|num }} |  |
| Innocents unexplained | {{ score.discard_blank|num }} each |  |
| Red herrings explained | {{ score.red_herring|num }} each |  |
| Tokens left over × {{ score.spare_token|num }} | {{ score.spare_token|num }} each |  |
{% if hints %}
| Hints asked ({{ m.hint_costs_short(hint_groups) }}) | − |  |
{% endif %}
| **Total** |  |  |
```

While one team presents, keep scoring another's sheet. If everyone accuses the wrong person, there is no winner: read the closing anyway.
{.small}
