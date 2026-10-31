---
# ```locations in the guide: the places of locations.yaml, the sources each one has (camera, register),
# the procedures that reach it and what they hand out. It answers the free question "does it have a camera?".
---
{% import "_macros.j2" as m %}
{% if locations %}
### Lugares: qué fuente tiene cada uno

Si preguntan si un lugar tiene cámaras o un registro, contesta sí o no sin cobrar. Ver lo que muestra es la diligencia, y se cobra.
{.small}

```table compact
| Lugar | Cámara o registro | Se pide con | Entrega |
|---|---|---|---|
{% for l in locations %}
| {{ l.name|cell|capitalize_first }} | {{ l.sources|map("source_word")|join(" y ") or "no" }} | {% for c in l.procedures %}`{{ c }}`{{ " · " if not loop.last else "" }}{% else %}—{% endfor %} | {% for r in l.results %}{{ m.result(r) }}{{ (" (" ~ r.note|cell ~ ")") if r.note else "" }}{{ " · " if not loop.last else "" }}{% endfor %}{{ ((". " if l.results else "") ~ l.note|cell|capitalize_first) if l.note else ("" if l.results else "—") }} |
{% endfor %}
```
{% endif %}
