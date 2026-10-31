---
# ```follow-ups in the guide's answer table: the follow-up cards of cards.yaml, with the full question
# (the team's card only shows code, cost and condition), the cards that enable them (follow_up), the
# evidence they also need (unlocked_by) and the case's note for the director (guide_note).
---
{% if follow_ups %}
### Seguimientos (1 ficha)

Entrégalos solo al equipo que ya tiene la tarjeta de la que salen{{ " y, si la tabla nombra una prueba, también esa prueba" if follow_ups|selectattr("unlocked_by")|list else "" }}; si no la tiene, no cobres. La pregunta completa está solo aquí: la tarjeta del equipo muestra el código, el costo y la condición.
{.small}

| Código | Pregunta | Viene en | Nota para ti |
|---|---|---|---|
{% for s in follow_ups %}
| `{{ s.code }}` | {{ s.question|cell }} | {{ s.mothers|join(" · ") or "—" }}{{ (", con " ~ s.unlocked_by|join(" o ")) if s.unlocked_by else "" }} | {{ ("[attached] " ~ s.attach|join(", ") ~ ". ") if s.attach else "" }}{{ s.note|cell }} |
{% endfor %}
{% endif %}
