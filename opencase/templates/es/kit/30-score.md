---
institution: Reglas del juego
description: Se cuenta al final, con las hojas de acusación y de descarte
title: Puntaje
---
{% import "_macros.j2" as m %}
{% set alibi = f.alibi_tokens_per_team %}

```table compact
| Logro | Puntos |
|---|---|
| Nombrar al asesino correcto, con al menos una prueba que lo vincule | {{ score.culprit|num }} ({{ score.culprit_no_evidence|num }} sin prueba) |
| Explicar cómo lo hizo | {{ score.how|num }} |
| Explicar por qué lo hizo | {{ score.why|num }} |
| Indicar la ventana horaria del crimen | {{ score.window|num }} |
{% if bonus %}
| {{ bonus.text }} | {{ bonus.points|num }} |
{% endif %}
| Señalar una contradicción en las palabras del culpable | {{ score.contradiction|num }} |
| Cada sospechoso inocente descartado con dos pruebas de distinto origen que lo ubiquen lejos de la escena en el momento del crimen (con una sola prueba, {{ m.pts(score.discard_one) }}; dos pruebas de la misma persona o fuente cuentan como una) | {{ score.discard_two|num }} c/u |
| Cada sospechoso inocente que quede sin explicar en la hoja de descarte | {{ score.discard_blank|num }} c/u |
| Cada pista falsa que expliquen con su prueba | {{ score.red_herring|num }} c/u |
| Cada ficha que les sobre{{ " (las de coartada no cuentan)" if alibi else "" }} | {{ score.spare_token|num }} c/u |
| Cada pista pedida al director ({{ m.hint_costs(hint_groups) }}) | − |
| Acusar a la persona equivocada: el equipo no puede ganar (si todos se equivocan, no hay ganador) | {{ score.wrong_accusation|num }} |
| No acusar a nadie: solo suman las fichas que les sobren | — |
```

Gana el equipo con más puntos. Si empatan, gana el que gastó menos fichas; si siguen empatados, el que expuso la teoría más clara.
{.small}
