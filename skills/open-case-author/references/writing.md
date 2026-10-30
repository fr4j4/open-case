# Writing the case

Tone, voice and conventions for every piece of text, taken from the brand guide (`design/guide/08-redaccion.md`) and the sample case. The case language is whatever the person chose; these rules hold in any language.

## Tone by document

| Document | Voice | Notes |
|---|---|---|
| Official (police report, autopsy, lab, logs) | Third person, short sentences, no adjectives, no exclamation marks. | "Two circular punctures of 4 mm, 4.5 cm between centres." Metadata in a `meta` block, signature in a `signature` block. |
| Statement (`DEC · X`) | First person, contained orality, four to six paragraphs, may lie. | Five identity fields in `meta` (age · occupation, relation, address, description), then a `statement` block, then a signature. The lie sits among true, checkable things. |
| Answer card | What the suspect says, in quotes, in their voice. | ≤ 420 characters. A stage direction in brackets only on confrontations: "(Long pause.)". Never a director's note. |
| Confrontation card | A new lie, a partial admission or a deflection. | Starts from the evidence shown, ends without confessing the whole. |
| Witness card | Honest, a little rambling, with one useful fact and one name or place. | Witnesses never lie; they can be wrong about what they did not see. |
| Chat | As that person types: with or without accents, their fillers, their emojis. | A 70-year-old farmer writes differently from a 24-year-old. Every message has a time; deleted ones are marked. |
| Kit and notices | The game's voice, direct, addressed to "you" plural. | "You have 16 tokens. Each question costs one." |
| Director's guide | Addressed to "you" singular, practical, no ornament. | "Hand E06 to both teams. Charge the tokens." |
| Script (`script` block) | Spoken, short lines, in character (the commissioner). | 60 to 120 words for the opening; 30 to 50 for a notice. |
| Press card | Headline + two sentences, the register of a local radio or newspaper. | Pushes the red herring; never a code. |

## Truth and lies in the text

- The lie in a statement is specific and checkable ("I was home all night, I fell asleep early"), never vague. Around it, three or four true facts that other sheets confirm, so the liar is credible.
- A suspect's secret colours everything they say: they deflect toward the person they fear, they volunteer the alibi that protects the secret, they get nervous on the follow-up.
- The culprit's statement contains at most one slip, and the slip is worth a contradiction point, never a confession path (see `design-rules.md` §3).
- Honest documents can still mislead by what they choose to show: a receipt that proves presence at 21:40 when the crime is at 23:15; a post with a visible earring near the scene at 21:55.

## Codes in text

Backticks for codes in Markdown (`` `E13a` ``), bare codes in YAML fields (`attach: E30`). The middle dot `·` separates parts of a code and the two lines of a letterhead. Quotes are straight or typographic but consistent across the case. Ellipsis is one character (…).

## Names

- Each suspect has a unique initial; if two share one, pick a nickname or a surname initial and keep it everywhere.
- Every person named in any sheet is either a suspect, a witness with a card, or someone with a "nothing to add" card. Keep the list in the bible (section 10) and check it at generation.
- Companies, media, accounts and people are fictional. Real public institutions (police, prosecutor, forensic service, agriculture agency) only in their normal role.

## Translation readiness

- Avoid idioms that do not travel; a little local flavour in chats is fine because chats are rewritten per language anyway.
- Codes, file names and the dossier order are shared by every language; only `languages/<lang>/` changes. Translated images with text go in the language folder with the same path.
- Formats (dates, currency, plates, paper size) follow the case's locality, not the author's.

## Lengths

| Piece | Length |
|---|---|
| Card answer | ≤ 420 characters; aim for 200–350 |
| Statement | 4–6 paragraphs, 120–220 words |
| Police report | one sheet: meta, victim, account, observations (6–10 lines in `mono`), signature |
| Autopsy | one sheet: cause, time of death, other injuries, clothing and position, toxicology |
| Register (log, statement, tower) | 6–12 rows; the datum never first or last |
| Kit mission | one or two sheets: story in two paragraphs, "How to play" in 8–11 numbered rules, timing, scoring table |
| Solution page | one sheet: the note with what happened, why, the telling detail, the hidden plot, a table of what each suspect hides and their alibi |
| Confession | 120–200 words, first person, no code names |
| Closing | 60–100 words, the commissioner's voice, one line per suspect's fate |

## Headers of a sheet

Every Markdown sheet starts with YAML front matter. The fields that matter most:

```yaml
---
code: E07                 # evidence code; statements use "DEC · B"
institution: Dirección Meteorológica   # first line of the letterhead
description: Estación Temuco · Registro horario   # second line
title: Viernes 30 de octubre          # the big title
---
```

Kit sheets use `institution` for the sheet kind ("Orden de investigar", "Menú de preguntas"), `description` for a subtitle and `title` for the name; the exporter adds the team line and the logo. Guide sheets use `institution: "3 · Guion"`, so the section number travels with the sheet. Notices set `notice: true`; aged letters set `aged: true`; stamps use `stamp:`.
