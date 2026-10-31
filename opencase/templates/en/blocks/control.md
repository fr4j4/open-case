---
# ```control in the guide's control sheet: one column per team and one row per thing the director hands out.
# With the case's procedures.yaml the rows come by themselves: first the procedures (one row per sheet number,
# E15·B to E15·M in one), then the cards that hand out a sheet (attach), named by the sheet's `short` or title.
# A case without procedures.yaml writes its rows inside the block:
#   rows:
#     - [J2 → E08, Javiera's live stream, 1]      code, what it is, tokens
# The last rows (notices, other questions, hints, tokens left) come from the case's cards and the figures.
---
{% import "_macros.j2" as m %}
{% set n = teams|length %}
{% set head %}
| Code | What it is | Tokens | {{ teams|map("team_label")|join(" | ") }} |
|---|---|---|{{ "---|" * n }}
{% endset %}
{% if data.rows is defined %}

```table control
{{ head }}{% for r in data.rows %}
| `{{ r[0] }}` | {{ r[1] }} | {{ r[2] }} |{{ "  |" * n }}
{% endfor %}
{% else %}
{% if procedures %}
### Procedures

```table control
{{ head }}{% for p in procedures %}{% for r in p.control_rows %}
| `{{ p.code }} → {{ r.base }}` | {{ p.short|cell }}{{ (": " ~ r.label|cell) if r.label else "" }}{{ (" (·" ~ r.suffixes|join(" ·") ~ ")") if r.suffixes else "" }} | {{ r.cost }} |{{ "  |" * n }}
{% endfor %}{% endfor %}
```

### Evidence handed out with a card
{% endif %}

```table control
{{ head }}{% for c in procedure_cards %}
| `{{ c.code }} → {{ c.shown|join(" · ") }}` | {{ c.what|cell }} | 1 |{{ "  |" * n }}
{% endfor %}
{% endif %}
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
