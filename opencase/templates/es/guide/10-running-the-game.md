---
place: anchor
institution: Reglas para dirigir
description: "Una partida dura de {{ f.session_minutes[0] }} a {{ f.session_minutes[1] }} minutos · con las cifras de este caso"
title: Cómo dirigir la partida
---
{% import "_macros.j2" as m %}
{% set alibi = f.alibi_tokens_per_team %}
{% set p = f.phases %}

```table compact
| Fase | Qué haces |
|---|---|
| **0 · Preparación** · {{ p.setup }} min | Arma los equipos y entrega a cada uno el kit, {{ f.tokens_per_team }} fichas{{ (', %d fichas de coartada' % alibi) if alibi else '' }} y una placa por jugador.{{ ' Lee en voz alta "Cómo se juega" (está en el kit).' if how_to_play_in_kit else "" }} |
| **1 · Escena** · {{ p.scene }} min | Lee el parte (está en el guion) y entrega el sobre 1. Ellos leen; tú todavía no atiendes preguntas ni diligencias. |
| **2 · Investigación** · {{ p.investigation }} min | {{ 'Entrega el sobre 2 a todos los equipos: ese es el minuto 0. ' if envelopes|length > 1 else '' }}Recibe las solicitudes, cobra, entrega y marca todo en la hoja de control. {{ ("Lee los avisos cuando te parezca; se sugiere " ~ m.notice_plan(notice_minutes) ~ ".") if notice_minutes else "" }}{{ " El último va con la tarjeta de prensa." if has_press else "" }} |
| **3 · Acusación** · {{ p.accusation }} min | {{ f.accusation_writing }} min para llenar las hojas. Recoge las hojas de acusación y de descarte de todos antes de que alguien exponga; luego no hay cambios. Luego {{ f.pitch_minutes }} min por equipo para exponer (empieza el que tenga más fichas); mientras uno expone, puntúa a otro en la hoja de puntaje. |
| **4 · Cierre** · {{ f.closing_minutes[0] }} a {{ f.closing_minutes[1] }} min | Lee la confesión si corresponde y el cierre. |
```

### Antes de que lleguen

- Ten un temporizador a la vista: {{ m.and_list([p.scene, p.investigation, p.accusation]) }} minutos.{{ (" Dentro de la investigación, marca los minutos sugeridos para los avisos (" ~ m.and_list(notice_minutes) ~ ").") if notice_minutes else "" }}
- Pon una mesa para cada equipo, separadas para que no se escuchen. Se recomienda jugar en equipos de {{ f.team_size_min }} o más personas, para que haya conversación dentro de cada equipo.
{% if teams|length > 2 %}
- Se puede jugar con 2 a {{ teams|length }} equipos: este caso trae material para {{ teams|length }}. Con más de dos, pide ayuda a alguien para entregar tarjetas o usa un grupo de WhatsApp por equipo.
{% else %}
- Este caso trae material para 2 equipos.
{% endif %}
- Lee una vez la solución y los diagramas. Con eso puedes dirigir sin memorizar nada más.

```note Cifras recomendadas
Este caso usa {{ f.tokens_per_team }} fichas{{ (' y %d de coartada' % alibi) if alibi else '' }} por equipo, fases de {{ m.and_list([p.scene, p.investigation, p.accusation]) }} minutos{{ (" y %d pistas" % hints|length) if hints else "" }}. Son las recomendadas para jugarlo; si tus equipos son más chicos o es su primera partida, se pueden cambiar en el case.yaml y todos los documentos salen con las nuevas.
```
