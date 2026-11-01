---
# ```procedures in the team kit: the menu of procedures, from the case's procedures.yaml and the texts of
# languages/<lang>/procedures.yaml. The codes that can be paid with an alibi token (alibi: true) get a dashed
# border, explained under the table when the case has alibi tokens.
---
{% import "_macros.j2" as m %}
| Code | Procedure | Tokens |
|---|---|---|
{% for p in procedures %}
| {{ m.dg(p, f) }} | {{ p.label|cell }} | {{ m.dg_cost(p) }} |
{% endfor %}
{% if f.alibi_tokens_per_team and procedures|selectattr("alibi")|list %}

Codes with a dashed border can also be paid with an alibi token.
{.small}
{% endif %}

If a procedure does not fit, the director says "does not apply" and no token is spent.
{.small}
