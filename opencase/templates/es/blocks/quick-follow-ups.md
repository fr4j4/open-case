---
# ```quick-follow-ups in the guide's quick sheet (inside a ````columns block): each follow-up and what the
# team must already have to get it.
---
{% if follow_ups %}
| Seguimiento | Entrega |
|---|---|
{% for s in follow_ups %}
| `{{ s.code }}` | tarjeta{{ (" + " ~ s.attach|join(" + ")) if s.attach else "" }}, si tienen {{ ([s.mothers|join(" o ") or "—"] + ([s.unlocked_by|join(" o ")] if s.unlocked_by else []))|join(" y ") }} |
{% endfor %}
{% endif %}
