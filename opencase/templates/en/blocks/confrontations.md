---
# ```confrontations in the guide's answer table: the `opens_with` rules of the cards of cards.yaml.
# One row per rule: the evidence they show (`shows`, or built from the codes), the card to hand out (with
# what it attaches) and the case's note (`note`). The last row is the confrontation that proves nothing.
# A case without `opens_with` does not use this block: it writes its table by hand.
---
{% import "_macros.j2" as m %}
{% if confrontations %}
### Confrontations ◆ ({{ m.tok(f.costs.confrontation) }}): which evidence counts

| Code | If they show… | Hand out |
|---|---|---|
{% for r in confrontations %}
| `{{ r.mark }}` | {{ r.shows|cell }} | Card {{ r.card|cell }}{{ (" + " ~ r.attach|join(" + ")) if r.attach else "" }}{{ (r.sep ~ r.note|cell) if r.note else "" }} |
{% endfor %}
| `Any ◆` | Any other evidence | {% if confrontation_failed %}Card "{{ confrontation_failed.code|cell }}" ({{ confrontation_failed.text|cell }}). {% endif %}The token is charged. |
{% endif %}
