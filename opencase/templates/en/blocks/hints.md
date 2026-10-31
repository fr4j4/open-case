---
# ```hints in the guide's script: the hint cards of cards.yaml in order, with what each one costs.
---
{% import "_macros.j2" as m %}

### If a team gets stuck (hints in order, from mildest to strongest)

{% for h in hints %}
{{ h.n }}. {{ h.answer }}
{% endfor %}

{{ m.hint_costs(hint_groups)|capitalize }}, to the team that asked for it.
{.small}
