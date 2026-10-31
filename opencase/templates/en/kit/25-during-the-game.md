---
institution: Rules of the game
description: The same in every Open Case case
title: During the game
---
{% import "_macros.j2" as m %}
{% set alibi = f.alibi_tokens_per_team %}

### Where to start

1. Read envelope 1 together and write on the timeline where each person says they were at each hour.
2. Look for what does not fit (a time, a place, something someone said about someone else) and choose whom to ask first.
3. Check each story with procedures and witnesses before you accuse, and fill in the discard sheet as you go.

### What you receive

It is for your team only: do not show it to the others. **Suspects can lie**; forensic reports and official documents cannot. What a suspect hands over may have been chosen to be seen that way.

### Follow-ups

Some cards have a follow-up at the bottom: a code ending in +. You ask for it like any question and it costs 1 token.

{% if notice_minutes %}
### Notices

During the investigation the director reads {{ "one notice" if notice_minutes|length == 1 else "%d notices" % notice_minutes|length }} with new information to every team{{ "; the last one comes with a press card." if has_press else "." }}

{% endif %}
{% if hints %}
### Hints

If you get stuck, you can ask the director for a hint. There are {{ hints|length }} and they cost points: {{ m.hint_costs(hint_groups) }}.
{% endif %}

### Confession

For the culprit to confess, the accusation has to rest on evidence of **different kinds** (for example: where they were, how they moved, what they knew or what was left on their things), you must have confronted them (◆) with it, and you need evidence of the motive. One piece of evidence is not enough. The confession scores no points: it closes the story.
