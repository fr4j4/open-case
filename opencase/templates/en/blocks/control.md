---
# ```control in the guide's control sheet. Inside the block, the case's rows:
#   rows:
#     - [J2 → E08, Javiera's live stream, 1]      code, what it is, tokens
# The team columns come from `teams` and the last rows (notices, hints, tokens left) from the case's cards and the figures.
---
{% import "_macros.j2" as m %}
{% set n = teams|length %}

```table control
| Code | What it is | Tokens | {{ teams|map("team_label")|join(" | ") }} |
|---|---|---|{{ "---|" * n }}
{% for r in data.rows %}
| `{{ r[0] }}` | {{ r[1] }} | {{ r[2] }} |{{ "  |" * n }}
{% endfor %}
{% for a in notices %}
| `{{ a.code }}{{ (" · min %s" % a.minute) if a.minute else "" }}` | {{ a.title }} | 0 |{{ "  |" * n }}
{% endfor %}
| `Other questions` | Write down the codes | 1 each |{{ "  |" * n }}
{% if hints %}
| `Hints` | {{ m.hint_costs_short(hint_groups) }} |  |{{ "  |" * n }}
{% endif %}
| `Tokens left` | At the end |  |{{ "  |" * n }}
{% if f.alibi_tokens_per_team %}
| `Alibi tokens used` | Out of {{ f.alibi_tokens_per_team }} (they do not score) |  |{{ "  |" * n }}
{% endif %}
```
