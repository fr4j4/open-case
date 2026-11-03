---
# ```quick-persons in the guide's quick sheet: the procedures on a person as a table, one row per person and one
# column per procedure (DG3, DG5, DG7, DG9, DG12…), with the sheet each one hands out. It is built from the targets
# of procedures.yaml, so it never needs to be written by hand.
---
{% import "_macros.j2" as m %}
{% if person_matrix %}
| Persona |{% for p in person_matrix.cols %} {{ p.code }} {{ p.short|cell }} |{% endfor %}{{ "" }}
|---|{% for p in person_matrix.cols %}---|{% endfor %}{{ "" }}
{% for r in person_matrix.rows %}
| {{ r.name|cell }} |{% for t in r.cells %} {{ m.result(t, True) if t else "—" }} |{% endfor %}{{ "" }}
{% endfor %}
{% endif %}
