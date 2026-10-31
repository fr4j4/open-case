---
# ```quick-witnesses in the guide's quick sheet (inside a ````columns block): each witness and what to
# hand out. With `others: {card: NADA QUE APORTAR}` it ends with the row of the other names.
---
{% set o = data.get("others") %}
| Testigo | Entrega |
|---|---|
{% for w in witnesses %}
| `{{ w.name|cell }}` | {{ w.cards|join(" · ") }}{{ (" + " ~ w.attach|join(" + ")) if w.attach else "" }} |
{% endfor %}
{% if o %}
| `Otros nombres` | "{{ o.card|capitalize }}" (no se cobra) |
{% endif %}
