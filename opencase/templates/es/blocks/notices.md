---
# ```notices in the guide's script: the notice and press cards of cards.yaml, to read aloud,
# with the minute suggested for each one (notice_minutes). The director decides when to read them.
---
{% for r in readings %}
{% if r.kind == "notice" %}
### Aviso {{ r.n }}{{ (" (minuto sugerido %s)" % r.minute) if r.minute else "" }}
{% else %}
### Tarjeta de prensa (con el aviso {{ r.n }})
{% endif %}

```script
{{ (r.headline|upper ~ " · ") if r.headline else "" }}{{ r.answer }}
```

{% endfor %}
