---
institution: Reglas del juego
description: Iguales en todos los casos de Open Case
title: Durante la partida
---
{% import "_macros.j2" as m %}
{% set alibi = f.alibi_tokens_per_team %}

### Por dónde empezar

1. Lean el sobre 1 entre todos y anoten en la línea de tiempo dónde dice cada persona que estuvo.
2. Busquen lo que no calza (una hora, un lugar, algo que alguien dijo de otro) y elijan a quién preguntar primero.
3. Comprueben cada versión con diligencias y testigos antes de acusar, y vayan llenando la hoja de descarte.

### Lo que reciben

Es solo para su equipo: no se lo muestren a los demás. **Los sospechosos pueden mentir**; los peritajes y los documentos oficiales, no. Lo que aporta un sospechoso puede estar elegido para que lo vean así.

### Seguimientos

Algunas tarjetas traen al pie un seguimiento: un código terminado en +. Se pide como cualquier pregunta y cuesta 1 ficha.

### Avisos

Durante la investigación el director lee {{ f.notice_minutes|length }} avisos con información nueva a todos los equipos; el último viene con una tarjeta de prensa.{{ (" Cuando el director lea la tarjeta de prensa, quedan unos %d minutos." % press_minutes_left) if press_minutes_left else "" }}

### Pistas

Si se estancan, pueden pedirle una pista al director. Hay {{ f.hint_penalties|length }} y restan puntos: {{ m.hint_costs(hint_groups) }}.

### Confesión

Para que el culpable confiese, la acusación tiene que apoyarse en pruebas de **distinto tipo** (por ejemplo: dónde estaba, cómo se movió, qué sabía o qué quedó en sus cosas), haberlo confrontado (◆) con ellas y tener una prueba del motivo. La confesión no suma puntos: es el cierre de la historia.
