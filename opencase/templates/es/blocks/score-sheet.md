---
# ```score-sheet in the guide: how to break a tie and the score sheet (one per team), with the
# case's bonus line (score_bonus in case.yaml, its text in score_texts).
---
{% import "_macros.j2" as m %}
{% set innocents = n_suspects - 1 %}

### Desempate

Gana el equipo con más puntos. Si empatan, gana el que gastó menos fichas; si siguen empatados, el que expuso la teoría más clara (lo decides tú).

### Hoja de puntaje (imprime una por equipo)

```table score
| Punto | Pts | Equipo ______ |
|---|---|---|
| Asesino (con una prueba) · sin ninguna prueba | {{ score.culprit|num }} · {{ score.culprit_no_evidence|num }} |  |
| Cómo | {{ score.how|num }} |  |
| Por qué | {{ score.why|num }} |  |
| Ventana | {{ score.window|num }} |  |
{% if bonus %}
| {{ bonus.short }} | {{ bonus.points|num }} |  |
{% endif %}
| Contradicción | {{ score.contradiction|num }} |  |
| Inocentes descartados ({{ score.discard_two|num }} c/u, {{ score.discard_one|num }} con una prueba) × {{ innocents }} | hasta {{ (innocents * score.discard_two)|num }} |  |
| Inocentes sin explicar | {{ score.discard_blank|num }} c/u |  |
| Pistas falsas explicadas | {{ score.red_herring|num }} c/u |  |
| Fichas que sobran × {{ score.spare_token|num }} | {{ score.spare_token|num }} c/u |  |
{% if hints %}
| Pistas pedidas ({{ m.hint_costs_short(hint_groups) }}) | − |  |
{% endif %}
| **Total** |  |  |
```

Mientras un equipo expone, ve puntuando la hoja de otro. Si todos acusan a la persona equivocada, no hay ganador: lee igual el cierre.
{.small}
