---
# ```confrontations en la tabla de respuestas de la guía: las reglas `opens_with` de las tarjetas de cards.yaml.
# Una fila por regla: la prueba que se muestra (`shows`, o armada con los códigos), la tarjeta que se entrega
# (con lo que adjunta) y la nota del caso (`note`). La última fila es la confrontación que no prueba nada.
# Un caso sin `opens_with` no usa este bloque: escribe su tabla a mano.
---
{% import "_macros.j2" as m %}
{% if confrontations %}
### Confrontaciones ◆ ({{ m.tok(f.costs.confrontation) }}): qué prueba vale

| Código | Si muestran… | Entrega |
|---|---|---|
{% for r in confrontations %}
| `{{ r.mark }}` | {{ r.shows|cell }} | Tarjeta {{ r.card|cell }}{{ (" + " ~ r.attach|join(" + ")) if r.attach else "" }}{{ (r.sep ~ r.note|cell) if r.note else "" }} |
{% endfor %}
| `Cualquier ◆` | Cualquier otra prueba | {% if confrontation_failed %}Tarjeta "{{ confrontation_failed.code|cell }}" ({{ confrontation_failed.text|cell }}). {% endif %}La ficha se cobra. |
{% endif %}
