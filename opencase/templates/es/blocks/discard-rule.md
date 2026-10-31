---
# ```discard-rule in the kit's discard sheet: how the discard scores.
---
{% import "_macros.j2" as m %}

Llénenla durante la investigación, no al final. Por cada inocente descartado con dos pruebas de distinto origen (documento, testigo, antena, cámara o registro digital) que lo ubiquen lejos de la escena en el momento del crimen ganan {{ m.pts(score.discard_two) }}; con una sola prueba, {{ score.discard_one|num }}. Por cada inocente que quede en blanco pierden {{ (-score.discard_blank)|num }}. La declaración del propio sospechoso no cuenta como prueba: sí cuentan testigos, documentos, antenas y cámaras. Dos pruebas de la misma persona o fuente cuentan como una.
{.small}
