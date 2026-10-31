---
place: anchor
institution: Rules for the director
description: How to answer without improvising
title: Keeping it fair
---
{% import "_macros.j2" as m %}
{% set alibi = f.alibi_tokens_per_team %}

```note-warning Golden rule
As the narrator you never lie and never make up a new clue. If they ask something that is not in the material, answer "there is no information about that" or "that person does not know".
```

- **Serve in order of arrival, taking turns between teams.** Answer each request before taking the next; if a team piles up several, answer one and move on to the next team.
- **Questions only in the investigation,** never in the scene. Suspects can be interviewed from its start, at 1 token per question; the statement in envelope 1 is not an interview.
- **Witnesses:** they can be asked for once their name has appeared in the team's material, even in a list or a register. The first time a new name appears in something you hand out, say it aloud: "you can interview that person now". If it has not appeared yet, hand out the witness-not-available card and do not charge. Witnesses tell the truth.
- **A confrontation gives one card only.** If several apply, give the most specific one.
- **Procedures:** with no grounds in what they have seen (the cameras of a bank no document mentions), turn the request down and do not charge. With grounds but nothing to find (the cameras of a pharmacy in the report that has none), answer "no findings" and the token is spent. If they ask for something they already have: "you already have that", no charge.
- **Asking whether a source exists is free:** if they ask whether a place has cameras, a logbook or an access record, answer yes or no for free without saying what it shows; seeing what it shows is the procedure, and it is charged. This does not apply to searches or forensic tests. What is obvious in the fiction (whether someone has a vehicle, what they do for a living) is also free; everything else costs a token.
{% if alibi %}
- **Alibi tokens:** each team has {{ alibi }}, with a dashed border. They are only good for asking for evidence of where a suspect was at the time of the crime: phone towers, cameras or a witness who places them. Those left over do not score.
{% endif %}
- **What places a person:** evidence that names or identifies them, or that places a vehicle another piece of evidence links to them. A vehicle nothing links to anyone places no one.
{% if hints %}
- **Hints:** they are given in order to whoever asks and cost points ({{ m.hint_costs(hint_groups) }}); write them on the control sheet.
{% endif %}
