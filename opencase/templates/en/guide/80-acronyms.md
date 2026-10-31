---
place: end
institution: Rules for running the game
description: To say them right out loud
title: Acronyms of the case
---
{% if glossary %}
The acronyms that appear in the documents, with what they stand for.
{.small}

```table compact
| Acronym | Stands for |
|---|---|
{% for a in glossary %}
| **{{ a.abbr }}** | {{ a.long }} |
{% endfor %}
```
{% endif %}
