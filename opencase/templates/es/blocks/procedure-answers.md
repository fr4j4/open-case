---
# ```procedure-answers in the guide's answer table: what to hand out for each procedure of procedures.yaml,
# target by target (the names and the hand-outs go in the same order), with the case's notes.
---
{% import "_macros.j2" as m %}
{% if procedures %}
### Diligencias del menú del equipo

| Código | Si piden… | Entrega |
|---|---|---|
{% for p in procedures %}
{% if p.gives %}
| {{ m.dg(p, f) }} | {{ p.short|cell }}{{ (" (" ~ m.tokens(p.gives.cost) ~ ")") if p.gives.extra_cost else "" }} | {{ m.result(p.gives) }}{{ (" " ~ p.note|cell) if p.note else "" }} |
{% else %}
| {{ m.dg(p, f) }} | {{ p.short|cell }}: {% for t in p.targets %}{{ t.label|cell }}{{ (" (" ~ m.tokens(t.cost) ~ ")") if t.extra_cost else "" }}{{ " · " if not loop.last else "" }}{% endfor %}{{ (" (" ~ m.tokens(p.cost) ~ " cada uno)") if p.each else "" }} | {% for t in p.targets %}{{ m.result(t) }}{{ (" (" ~ t.note|cell ~ ")") if t.note else "" }}{{ " · " if not loop.last else "" }}{% endfor %}{{ (" " ~ p.note|cell) if p.note else "" }} |
{% endif %}
{% endfor %}
{% endif %}
