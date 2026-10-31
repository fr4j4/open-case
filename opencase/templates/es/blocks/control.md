---
# ```control in the guide's control sheet. Inside the block, the case's rows:
#   rows:
#     - [J2 → E08, Live de Javiera, 1]      code, what it is, tokens
# The team columns come from `teams` and the last rows (notices, hints, tokens left) from the case's cards and the figures.
---
{% import "_macros.j2" as m %}
{% set n = teams|length %}

```table control
| Código | Qué es | Fichas | {{ teams|map("team_label")|join(" | ") }} |
|---|---|---|{{ "---|" * n }}
{% for r in data.rows %}
| `{{ r[0] }}` | {{ r[1] }} | {{ r[2] }} |{{ "  |" * n }}
{% endfor %}
{% for a in notices %}
| `{{ a.code }}{{ (" · min %s" % a.minute) if a.minute else "" }}` | {{ a.title }} | 0 |{{ "  |" * n }}
{% endfor %}
| `Otras preguntas` | Anota los códigos | 1 c/u |{{ "  |" * n }}
{% if hints %}
| `Pistas guiadas` | {{ m.hint_costs_short(hint_groups) }} |  |{{ "  |" * n }}
{% endif %}
| `Fichas restantes` | Al final |  |{{ "  |" * n }}
{% if f.alibi_tokens_per_team %}
| `Coartada usadas` | De {{ f.alibi_tokens_per_team }} (no suman al final) |  |{{ "  |" * n }}
{% endif %}
```
