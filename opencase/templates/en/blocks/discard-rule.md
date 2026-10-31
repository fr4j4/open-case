---
# ```discard-rule in the kit's discard sheet: how the discard scores.
---
{% import "_macros.j2" as m %}

Fill it in during the investigation, not at the end. For each innocent ruled out with two pieces of evidence of different origin (document, witness, phone tower, camera or digital record) that place them away from the scene at the time of the crime you score {{ m.pts(score.discard_two) }}; with only one, {{ score.discard_one|num }}. For each innocent left blank you lose {{ (-score.discard_blank)|num }}. The suspect's own statement is not evidence: witnesses, documents, phone towers and cameras are. Two pieces of evidence from the same person or source count as one.
{.small}
