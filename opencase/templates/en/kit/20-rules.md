---
institution: Rules of the game
description: The same in every Open Case case
title: Rules
---
{% import "_macros.j2" as m %}
{% set alibi = f.alibi_tokens_per_team %}

1. **Questions.** Each question costs **{{ m.tok(f.costs.question) }}**, including the ones not on the menu. You only ask during the investigation, never in the scene: the {{ n_suspects }} suspects can be interviewed from its start (the statement in envelope 1 is not an interview). The director answers what is obvious in the story (for example, whether someone has a vehicle) for free.
2. **Witnesses.** Anyone else can be interviewed once they are named in a piece of evidence, a statement or a card (a name in a call log, a bank statement or a register also counts). Each question costs {{ m.tok(f.costs.witness) }}, and witnesses tell the truth.
3. **Confront (◆).** You confront someone by showing one or more pieces of evidence you already have; say what you want to point out with each. If the evidence does not work against that person, the answer will be "that proves nothing" and the token is spent anyway. Each confrontation gives one card only, and you can confront again with other evidence.
4. **Procedures.** They cost what the menu says. On the request slip write **what you are looking for and why**, and the director answers in one of these ways:
    - **No grounds: no charge.** What you ask for rests on nothing you have seen. Example: you ask for a bank's cameras, but no document or statement mentions a bank. The director turns the request down and you keep the token.
    - **Grounds, but nothing there: charged.** What you ask for makes sense with your material, but there is nothing to find. Example: a pharmacy appears in the report and you ask for its cameras, but it has none. The director answers "no findings" and the token is spent. Taking risks is part of the game.
    - If you ask for something you already have, the director tells you so without charging.
5. **Asking whether a source exists is free.** You can ask the director whether a place has cameras, a logbook or an access record: the answer is yes or no, without saying what it shows. Seeing what it shows is the procedure, and it is charged. This does not apply to searches or forensic tests.
{% if alibi %}
6. **Alibi tokens** (dashed border). They are only good for checking where a suspect was at the time of the crime (phone towers, cameras or a witness who places them), not for questioning a suspect, confronting or other procedures. Those left over do not score.
{% endif %}
7. **What places a person.** Evidence that names or identifies them, or that places a vehicle another piece of evidence links to them: a camera records a car and other evidence says whose it is, it counts; if nothing links the car to anyone, it does not.
