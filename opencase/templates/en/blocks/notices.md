---
# ```notices in the guide's script: the notice and press cards of cards.yaml, to read aloud,
# with the minute suggested for each one (notice_minutes). The director decides when to read them.
---
{% for r in readings %}
{% if r.kind == "notice" %}
### Notice {{ r.n }}{{ (" (suggested at minute %s)" % r.minute) if r.minute else "" }}
{% else %}
### Press card (with notice {{ r.n }})
{% endif %}

```script
{{ (r.headline|upper ~ " · ") if r.headline else "" }}{{ r.answer }}
```

{% endfor %}
{% if readings|selectattr("kind", "equalto", "notice")|selectattr("minute", "none")|list %}
Notices without a suggested minute are optional: read them when the pace calls for it. None of them hands out evidence or changes the score.
{.small}

{% endif %}
