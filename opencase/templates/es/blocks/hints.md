---
# ```hints in the guide's script: the hint cards of cards.yaml in order, with what each one costs.
---
{% import "_macros.j2" as m %}

### Si un equipo se estanca (pistas en orden, de más suave a más fuerte)

{% for h in hints %}
{{ h.n }}. {{ h.answer }}
{% endfor %}

{{ m.hint_costs(hint_groups)|capitalize }}, al equipo que la pidió.
{.small}
