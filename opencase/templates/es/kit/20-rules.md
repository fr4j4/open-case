---
institution: Reglas del juego
description: Iguales en todos los casos de Open Case
title: Reglas
---
{% import "_macros.j2" as m %}
{% set alibi = f.alibi_tokens_per_team %}

1. **Preguntas.** Cada pregunta cuesta **1 ficha**, también las que no están en el menú. Solo se pregunta durante la investigación, nunca en la escena: los {{ n_suspects }} sospechosos se pueden entrevistar desde que empieza (la declaración del sobre 1 no es una entrevista). Lo obvio dentro de la historia (por ejemplo, si alguien tiene vehículo) el director lo contesta sin cobrar.
2. **Testigos.** Cualquier otra persona se puede entrevistar cuando aparezca nombrada en una prueba, una declaración o una tarjeta (también cuenta un nombre en una lista de llamadas, una cartola o un registro). Cada pregunta cuesta 1 ficha y los testigos dicen la verdad.
3. **Confrontar (◆).** Se confronta mostrando una o más pruebas que ya tienen; digan qué quieren señalar con cada una. Si la prueba no sirve contra esa persona, la respuesta será "eso no prueba nada" y la ficha se cobra igual. Cada confrontación entrega una sola tarjeta, y se puede volver a confrontar con otra prueba.
4. **Diligencias.** Cuestan lo que indica el menú. En la solicitud escriban **qué buscan y por qué**, y el director responde de una de estas formas:
    - **No tiene base: no se cobra.** Lo que piden no se apoya en nada de lo que ya vieron. Ejemplo: piden las cámaras de un banco, pero ningún documento ni declaración menciona un banco. El director rechaza la solicitud y se quedan con la ficha.
    - **Tiene base, pero no hay nada: se cobra.** Lo que piden tiene sentido con su material, pero no existe nada que encontrar. Ejemplo: en el parte aparece una farmacia y piden sus cámaras, pero la farmacia no tiene. El director responde "sin hallazgos" y la ficha se gasta. Arriesgar es parte del juego.
    - Si piden algo que ya tienen, el director se lo dice sin cobrar.
5. **Preguntar si existe una fuente es gratis.** Pueden preguntarle al director si un lugar tiene cámaras, un libro o un registro de acceso: contesta sí o no, sin decir qué muestra. Ver lo que muestra es la diligencia y se cobra. No vale para rastreos ni peritajes.
{% if alibi %}
6. **Fichas de coartada** (borde punteado). Solo sirven para comprobar dónde estaba un sospechoso a la hora del crimen (antenas, cámaras o un testigo que lo ubique), no para preguntarle a un sospechoso, confrontar ni pedir otras diligencias. Las que sobren no suman.
{% endif %}
7. **Qué ubica a una persona.** Una prueba que la nombra o la identifica, o que ubica un vehículo que otra prueba liga a ella: una cámara registra un auto y otra prueba dice de quién es, cuenta; si nada liga el auto a alguien, no.
