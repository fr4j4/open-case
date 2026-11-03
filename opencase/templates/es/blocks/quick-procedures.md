---
# ```quick-procedures in the guide's quick sheet (inside a ````columns block): each procedure and what it
# hands out, short. Results by letter read E15·B / T / C. With `skip_persons: true` inside the block, the procedures
# that are already columns of the ```quick-persons table are left out.
---
{% import "_macros.j2" as m %}
{% if procedures %}
| Diligencia | Entrega |
|---|---|
{% for p in procedures %}
{% if data.get("skip_persons") and person_matrix and p in person_matrix.cols %}
{% elif p.gives %}
| {{ m.dg(p, f) }} | {{ p.short|cell }} → {{ m.result(p.gives, True) }}{{ (" (" ~ m.tokens(p.gives.cost) ~ ")") if p.gives.extra_cost else "" }} |
{% elif p.by_letter %}
| {{ m.dg(p, f) }} | {{ p.short|cell }} → {% for t in p.targets %}{{ t.shown[0] if loop.first else t.suffix }}{{ (" + " ~ t.also|join(" + ")) if t.also else "" }}{{ " / " if not loop.last else "" }}{% endfor %} |
{% else %}
| {{ m.dg(p, f) }} | {{ p.short|cell }} → {% for t in p.targets %}{{ t.label|cell }} {{ m.result(t, True) }}{{ (" (" ~ m.tokens(t.cost) ~ ")") if t.extra_cost else "" }}{{ " · " if not loop.last else "" }}{% endfor %} |
{% endif %}
{% endfor %}
{% endif %}
