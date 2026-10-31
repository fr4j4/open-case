---
place: after-block control
institution: Rules for the director
description: Optional · one line per request
title: Request log
---

Write down each request in the order it arrives and answer it before taking the next. That way no message goes unanswered and at the end you know what each team got. If it fills up, print another copy.
{.small}

```work-table
columns: ["No.", Team, Code, "Token{{ ' (normal or alibi)' if f.alibi_tokens_per_team else '' }}", Delivered]
height: 18px
rows: [{% for i in range(1, f.request_log_rows + 1) %}"{{ i }}"{{ ", " if not loop.last else "" }}{% endfor %}]
```
