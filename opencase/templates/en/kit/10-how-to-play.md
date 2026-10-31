---
place: anchor
join: true
---
{% set alibi = f.alibi_tokens_per_team %}

### How to play

You start with **{{ f.tokens_per_team }} tokens**{% if alibi %}, **{{ alibi }} alibi tokens**{% endif %} and **envelope 1**, with what is known so far and the statements of the {{ n_suspects }} suspects. There are four phases, {{ f.session_minutes[0] }} to {{ f.session_minutes[1] }} minutes in all:

```table compact
| Phase | What happens |
|---|---|
| **1 · Scene** · {{ f.phases.scene }} min | The director reads the report and hands out envelope 1. Read and take notes; no questions or procedures yet. |
| **2 · Investigation** · {{ f.phases.investigation }} min | {{ "Open envelope 2. " if envelopes|length > 1 else "" }}Ask questions and request procedures with a request slip and its tokens. The director reads the notices. |
| **3 · Accusation** · {{ f.phases.accusation }} min | {{ f.accusation_writing }} min to fill in the accusation and discard sheets, which the director collects before anyone presents. Then {{ f.pitch_minutes }} min per team to present (the team with the most tokens goes first). |
| **4 · Closing** | The director counts the points, reads the confession if you got it and closes the story. |
```

### Words of the game

```small
- **Question:** what you ask a person. It costs 1 token and you ask it with a code from the menu (for example, a suspect's letter and a number).
- **Procedure:** a request to the police or a lab, such as searching a phone, getting camera footage or examining an object. Write what you are looking for and why. It costs what the menu says.
- **Request slip:** where you write the code and why you ask for it. Hand it to the director with the tokens it costs, and you get the answer card or the evidence.
- **Alibi:** where a person says they were when the crime happened, and what can prove it.{{ " **Alibi tokens** (dashed border) are only good for that, and spare ones do not score." if alibi else "" }}
- **Evidence codes:** "E" and a number (E01, E02…) number the evidence in the director's dossier, and "DEC" the statements. You already have envelope 1; the rest you get with a question or procedure.
```
