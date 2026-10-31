---
# ```acronyms in a sheet of the case: the glossary as a table. `only: [PDI, SAG]` limits it to those.
---
{% for x in data.only|default([]) if x not in glossary|map(attribute="abbr")|list %}
{{ fail("```acronyms: the glossary has no acronym " ~ x ~ " (languages/en/case.yaml, glossary)") }}
{% endfor %}
{% set shown = data.only if data.only is defined else glossary|map(attribute="abbr")|list %}

```table compact
| Acronym | Stands for |
|---|---|
{% for a in glossary if a.abbr in shown %}
| **{{ a.abbr }}** | {{ a.long }} |
{% endfor %}
```
