---
# ```follow-ups in the guide's answer table: the follow-up cards of cards.yaml, with the full question
# (the team's card only shows code, cost and condition), the cards that enable them (follow_up), the
# evidence they also need (unlocked_by) and the case's note for the director (guide_note).
---
{% import "_macros.j2" as m %}
{% if follow_ups %}
### Follow-ups ({{ m.tok(f.costs.follow_up) }})

Hand them only to a team that already has the card they come from{{ " and, if the table names a piece of evidence, that evidence too" if follow_ups|selectattr("unlocked_by")|list else "" }}; if it does not, do not charge. The full question is only here: the team's card shows the code, the cost and the condition.
{.small}

| Code | Question | Comes with | Note for you |
|---|---|---|---|
{% for s in follow_ups %}
| `{{ s.code }}` | {{ s.question|cell }} | {{ s.mothers|join(" · ") or "—" }}{{ (", with " ~ s.unlocked_by|join(" or ")) if s.unlocked_by else "" }} | {{ ("[attached] " ~ s.attach|join(", ") ~ ". ") if s.attach else "" }}{{ s.note|cell }} |
{% endfor %}
{% endif %}
