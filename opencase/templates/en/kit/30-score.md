---
institution: Rules of the game
description: Counted at the end, with the accusation and discard sheets
title: Score
---
{% import "_macros.j2" as m %}
{% set alibi = f.alibi_tokens_per_team %}

```table compact
| Achievement | Points |
|---|---|
| Naming the right killer, with at least one piece of evidence linking them | {{ score.culprit|num }} ({{ score.culprit_no_evidence|num }} without evidence) |
| Explaining how they did it | {{ score.how|num }} |
| Explaining why they did it | {{ score.why|num }} |
| Giving the time window of the crime | {{ score.window|num }} |
{% if bonus %}
| {{ bonus.text }} | {{ bonus.points|num }} |
{% endif %}
| Pointing out a contradiction in the culprit's words | {{ score.contradiction|num }} |
| Each innocent suspect ruled out with two pieces of evidence of different origin that place them away from the scene at the time of the crime (with only one, {{ m.pts(score.discard_one) }}; two from the same person or source count as one) | {{ score.discard_two|num }} each |
| Each innocent suspect left unexplained on the discard sheet | {{ score.discard_blank|num }} each |
| Each red herring explained with its evidence | {{ score.red_herring|num }} each |
| Each token left over{{ " (alibi tokens do not count)" if alibi else "" }} | {{ score.spare_token|num }} each |
| Each hint asked of the director ({{ m.hint_costs(hint_groups) }}) | − |
| Accusing the wrong person: the team cannot win (if everyone is wrong, there is no winner) | {{ score.wrong_accusation|num }} |
| Handing in no accusation: 0 on the accusation and discard sheets (neither up nor down); only the tokens left over score, hints asked still subtract and there is no −1 per unexplained innocent | — |
```

The team with the most points wins. On a tie, the team that spent fewer tokens wins; if still tied, the one that presented the clearest theory.
{.small}
