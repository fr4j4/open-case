---
# ```procedures in the team kit: the menu of procedures, from the case's procedures.yaml and the texts of
# languages/<lang>/procedures.yaml. The codes that can be paid with an alibi token (alibi: true) get a dashed
# border, explained under the table when the case has alibi tokens.
---
{% import "_macros.j2" as m %}
| Código | Diligencia | Fichas |
|---|---|---|
{% for p in procedures %}
| {{ m.dg(p, f) }} | {{ p.label|cell }} | {{ m.dg_cost(p) }} |
{% endfor %}
{% if f.alibi_tokens_per_team and procedures|selectattr("alibi")|list %}

Los códigos con borde punteado también se pueden pagar con una ficha de coartada.
{.small}
{% endif %}
