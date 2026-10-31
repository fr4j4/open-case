---
# ```witnesses in the guide's answer table: the witness cards of cards.yaml grouped by person (`who`),
# where their name appears (appears_in) and what to hand out, with the case's guide_note. Inside the
# block the case may add the row of the other names of the material:
#   others: {names: "Jorge P8 or any other name in the material", appears_in: [E04], card: NOTHING TO ADD}
---
{% set o = data.get("others") %}
{% set o_in = o.get("appears_in", []) if o else [] %}
### Witnesses (1 token per question)

They can be interviewed once their name has appeared in the team's material: the "Appears in" column says where. If it has not appeared yet, hand out the witness-not-available card and do not charge. Witnesses tell the truth.
{.small}

| Witness | Appears in | Hand out |
|---|---|---|
{% for w in witnesses %}
| {{ w.who|cell }} | {{ w.appears_in_shown|join(", ") or "—" }} | {{ ("Card " ~ w.cards[0]) if w.cards|length == 1 else ("Cards " ~ w.cards[:-1]|join(", ") ~ " and " ~ w.cards[-1] ~ " (1 token each)") }}{{ (" + " ~ w.attach|join(" + ")) if w.attach else "" }}{{ (". " ~ w.note|cell) if w.note else "" }} |
{% endfor %}
{% if o %}
| {{ o.names|cell }} | {{ o_in if o_in is string else o_in|join(", ") }} | Card "{{ o.card|capitalize }}". Not charged. |
{% endif %}
