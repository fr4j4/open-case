---
# ```locations in the guide: the places of locations.yaml, the sources each one has (camera, register),
# the procedures that reach it and what they hand out. It answers the free question "does it have a camera?".
---
{% import "_macros.j2" as m %}
{% if locations %}
### Places: what source each one has

If they ask whether a place has cameras or a register, answer yes or no for free. Seeing what it shows is the procedure, and it costs.
{.small}

```table compact
| Place | Camera or register | Asked with | Hand out |
|---|---|---|---|
{% for l in locations %}
| {{ l.name|cell|capitalize_first }} | {{ l.sources|map("source_word")|join(" and ") or "no" }} | {% for c in l.procedures %}`{{ c }}`{{ " · " if not loop.last else "" }}{% else %}—{% endfor %} | {% for r in l.results %}{{ m.result(r) }}{{ (" (" ~ r.note|cell ~ ")") if r.note else "" }}{{ " · " if not loop.last else "" }}{% endfor %}{{ ((". " if l.results else "") ~ l.note|cell|capitalize_first) if l.note else ("" if l.results else "—") }} |
{% endfor %}
```
{% endif %}
