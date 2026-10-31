---
# ```witnesses in the guide's answer table: the witness cards of cards.yaml grouped by person (`who`),
# where their name appears (appears_in) and what to hand out, with the case's guide_note. Inside the
# block the case may add the row of the other names of the material:
#   others: {names: "Jorge P8 u otro nombre del material", appears_in: [E04], card: NADA QUE APORTAR}
---
{% set o = data.get("others") %}
{% set o_in = o.get("appears_in", []) if o else [] %}
### Testigos (1 ficha por pregunta)

Se pueden entrevistar cuando su nombre ya apareció en el material del equipo: la columna "Aparece en" dice dónde. Si todavía no apareció, entrega la tarjeta de testigo no disponible y no cobres. Los testigos dicen la verdad.
{.small}

| Testigo | Aparece en | Entrega |
|---|---|---|
{% for w in witnesses %}
| {{ w.who|cell }} | {{ w.appears_in_shown|join(", ") or "—" }} | {{ ("Tarjeta " ~ w.cards[0]) if w.cards|length == 1 else ("Tarjetas " ~ w.cards[:-1]|join(", ") ~ " y " ~ w.cards[-1] ~ " (1 ficha cada una)") }}{{ (" + " ~ w.attach|join(" + ")) if w.attach else "" }}{{ (". " ~ w.note|cell) if w.note else "" }} |
{% endfor %}
{% if o %}
| {{ o.names|cell }} | {{ o_in if o_in is string else o_in|join(", ") }} | Tarjeta "{{ o.card|capitalize }}". No se cobra. |
{% endif %}
