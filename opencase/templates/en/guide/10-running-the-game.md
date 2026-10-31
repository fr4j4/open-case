---
place: anchor
institution: Rules for the director
description: The same in every case · with this case's figures
title: How to run the game
---
{% import "_macros.j2" as m %}
{% set alibi = f.alibi_tokens_per_team %}
{% set p = f.phases %}

```table compact
| Phase | What you do |
|---|---|
| **0 · Setup** · {{ p.setup }} min | Form the teams and give each one the kit, {{ f.tokens_per_team }} tokens{{ (', %d alibi tokens' % alibi) if alibi else '' }} and one badge per player. Read "How to play" aloud (it is in the kit). |
| **1 · Scene** · {{ p.scene }} min | Read the report (it is in the script) and hand out envelope 1. They read; you do not take questions or procedures yet. |
| **2 · Investigation** · {{ p.investigation }} min | {{ 'Hand envelope 2 to every team: that is minute 0. ' if envelopes|length > 1 else '' }}Take the requests, charge, hand out and mark everything on the control sheet. Read the notices when you see fit; the suggestion is {{ m.notice_plan(f.notice_minutes) }}. The last one goes with the press card. |
| **3 · Accusation** · {{ p.accusation }} min | {{ f.accusation_writing }} min to fill in the sheets. Collect everyone's accusation and discard sheets before anyone presents; no changes after that. Then {{ f.pitch_minutes }} min per team to present (the team with the most tokens goes first); while one presents, score another on the score sheet. |
| **4 · Closing** · {{ f.closing_minutes[0] }} to {{ f.closing_minutes[1] }} min | Read the confession if it applies, and the closing. |
```

### Before they arrive

- Keep a timer in sight: {{ m.and_list([p.scene, p.investigation, p.accusation]) }} minutes. Within the investigation, mark the suggested minutes for the notices ({{ m.and_list(f.notice_minutes) }}).
- Set a table for each team, far enough apart that they cannot hear each other. Teams of {{ f.team_size_min }} or more people are recommended, so there is talk inside each team.
{% if teams|length > 2 %}
- It can be played with 2 to {{ teams|length }} teams: this case has material for {{ teams|length }}. With more than two, ask someone to help hand out cards or use a chat group per team.
{% else %}
- This case has material for 2 teams.
{% endif %}
- Read the solution and the diagrams once. That is enough to run the game without memorising anything else.

```note Recommended figures
This case uses {{ f.tokens_per_team }} tokens{{ (' and %d alibi tokens' % alibi) if alibi else '' }} per team, phases of {{ m.and_list([p.scene, p.investigation, p.accusation]) }} minutes and {{ f.hint_penalties|length }} hints. They are the recommended ones to play it; if your teams are smaller or it is their first game, they can be changed in case.yaml and every document comes out with the new ones.
```
