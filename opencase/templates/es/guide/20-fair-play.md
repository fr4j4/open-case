---
place: anchor
institution: Reglas para dirigir
description: Cómo responder sin improvisar
title: Para que sea parejo
---
{% import "_macros.j2" as m %}
{% set alibi = f.alibi_tokens_per_team %}

```note-warning Regla de oro
Como narrador nunca mientes y nunca inventas una pista nueva. Si te preguntan algo que no está en el material, contesta "no hay información sobre eso" o "esa persona no lo sabe".
```

- **Atiende en orden de llegada, por turnos entre los equipos.** Responde cada solicitud antes de tomar la siguiente; si un equipo junta varias, responde una y pasa al siguiente.
- **Solo se pregunta en la investigación,** nunca en la escena. Los sospechosos se pueden entrevistar desde que empieza, a 1 ficha por pregunta; la declaración del sobre 1 no es una entrevista.
- **Testigos:** se piden cuando su nombre ya apareció en el material del equipo, aunque sea en una lista o un registro. La primera vez que un nombre nuevo aparezca en algo que entregas, dilo en voz alta: "a esa persona ya la pueden entrevistar". Si todavía no apareció, entrega la tarjeta de testigo no disponible y no cobres. Los testigos dicen la verdad.
- **Una confrontación entrega una sola tarjeta.** Si hay varias posibles, entrega la más específica.
- **Diligencias:** sin base en lo que ya vieron (las cámaras de un banco que ningún documento menciona), rechaza la solicitud y no cobres. Con base pero sin nada que encontrar (las cámaras de una farmacia del parte que no tiene), responde "sin hallazgos" y la ficha se gasta. Si piden algo que ya tienen: "eso ya lo tienen", sin cobrar.
- **Preguntar si existe una fuente es gratis:** si te preguntan si un lugar tiene cámaras, un libro o un registro de acceso, contesta sí o no sin cobrar y sin decir qué muestra; ver lo que muestra es la diligencia y se cobra. No vale para rastreos ni peritajes. Lo obvio de la ficción (si alguien tiene vehículo, a qué se dedica) también es gratis; todo lo demás cuesta ficha.
{% if alibi %}
- **Fichas de coartada:** cada equipo tiene {{ alibi }}, de borde punteado. Solo sirven para pedir una prueba de dónde estaba un sospechoso a la hora del crimen: antenas, cámaras o un testigo que lo ubique. Las que sobren no suman.
{% endif %}
- **Qué ubica a una persona:** una prueba que la nombra o la identifica, o que ubica un vehículo ligado a ella por otra prueba. Un vehículo que nada liga a alguien no ubica a nadie.
{% if hints %}
- **Pistas:** se entregan en orden a quien las pida y restan puntos ({{ m.hint_costs(hint_groups) }}); anótalas en la hoja de control.
{% endif %}
