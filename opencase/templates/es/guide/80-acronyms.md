---
place: end
institution: Reglas para dirigir
description: Para decirlas bien en voz alta
title: Siglas del caso
---
{% if glossary %}
Las siglas que aparecen en los documentos, con lo que significan.
{.small}

```table compact
| Sigla | Significa |
|---|---|
{% for a in glossary %}
| **{{ a.abbr }}** | {{ a.long }} |
{% endfor %}
```
{% endif %}
