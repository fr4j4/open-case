---
institution: Reglas del juego
description: Iguales en todos los casos de Open Case
title: Durante la partida
---
{% import "_macros.j2" as m %}
{% set alibi = f.alibi_tokens_per_team %}

### Por dónde empezar

1. Lean el sobre 1 entre todos y anoten en la línea de tiempo dónde dice estar cada persona a cada hora.
2. Busquen lo que no calza (una hora, un lugar, algo que alguien dijo de otro) y elijan a quién preguntar primero.
3. Comprueben cada versión con diligencias y testigos antes de acusar, y vayan llenando la hoja de descarte.

### Lo que reciben

Es solo para su equipo: no se lo muestren a los demás. **Los sospechosos pueden mentir**; los peritajes y los documentos oficiales, no. Lo que aporta un sospechoso puede estar elegido para que lo vean así.

### Seguimientos

Algunas tarjetas traen al pie un recuadro de seguimiento: un código terminado en +. Se pide como cualquier pregunta y cuesta {{ m.tok(f.costs.follow_up) }}.{{ ' Si el recuadro dice "si ya tienen" una prueba, solo se puede pedir cuando la tengan.' if follow_ups|selectattr("unlocked_by")|list else "" }}

{% if notice_minutes %}
### Avisos

Durante la investigación el director lee {{ "un aviso" if notice_minutes|length == 1 else "%d avisos" % notice_minutes|length }} con información nueva a todos los equipos{{ "; el último viene con una tarjeta de prensa." if has_press else "." }}

{% endif %}
{% if hints %}
### Pistas

Si se estancan, pueden pedirle una pista al director. Hay {{ hints|length }} y restan puntos: {{ m.hint_costs(hint_groups) }}.
{% endif %}

### Confesión

Para que el culpable confiese, la acusación tiene que apoyarse en pruebas de **distinto tipo** (por ejemplo: dónde estaba, cómo se movió, qué sabía o qué quedó en sus cosas), haberlo confrontado (◆) con ellas y tener una prueba del motivo. Una sola prueba no basta. La confesión no suma puntos: es el cierre de la historia.
