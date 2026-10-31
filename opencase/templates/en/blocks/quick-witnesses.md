---
# ```quick-witnesses in the guide's quick sheet (inside a ````columns block): each witness and what to
# hand out. With `others: {card: NOTHING TO ADD}` it ends with the row of the other names.
---
{% set o = data.get("others") %}
| Witness | Hand out |
|---|---|
{% for w in witnesses %}
| `{{ w.name|cell }}` | {{ w.cards|join(" · ") }}{{ (" + " ~ w.attach|join(" + ")) if w.attach else "" }} |
{% endfor %}
{% if o %}
| `Other names` | "{{ o.card|capitalize }}" (not charged) |
{% endif %}
