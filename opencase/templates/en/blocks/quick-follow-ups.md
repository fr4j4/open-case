---
# ```quick-follow-ups in the guide's quick sheet (inside a ````columns block): each follow-up and what the
# team must already have to get it.
---
{% if follow_ups %}
| Follow-up | Hand out |
|---|---|
{% for s in follow_ups %}
| `{{ s.code }}` | card{{ (" + " ~ s.attach|join(" + ")) if s.attach else "" }}, if they have {{ ([s.mothers|join(" or ") or "—"] + ([s.unlocked_by|join(" or ")] if s.unlocked_by else []))|join(" and ") }} |
{% endfor %}
{% endif %}
