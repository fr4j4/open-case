# Tarjeta de respuesta
La tarjeta que el director entrega cuando un equipo paga una pregunta. Mide 88 × 63 mm (apaisada) y es blanca con borde punteado de corte.

Anatomía: banda superior de 4 px (`marino`) → cabecera con el código (`B1`) y el nombre del personaje → la pregunta en cursiva gris → la respuesta entre comillas → pie en `mono` con lo que se adjunta ("Adjunta E30") → recuadro de seguimiento (`oc-tarjeta__seguimiento`, `mono` en `marino` con borde fino: "Seguimiento H2+ · 1 ficha · si ya tienen E13b"; solo código, costo y condición, nunca la pregunta) → línea de marca con "Open Case" y el nombre del caso.

- La respuesta tiene **420 caracteres como máximo** en `tarjeta-respuesta` (12,5 px en pantalla, 9,5 pt impresa). Más largo: se divide en dos tarjetas "B10 (1 de 2)" y "B10 (2 de 2)".
- Variantes por sufijo del código: `+` seguimiento (misma tarjeta, cabecera "Seguimiento"), `✕` fallida (`--fallida`, fondo `papel-2`, respuesta "Eso no prueba nada").
- Una tarjeta responde una sola pregunta. Nunca trae notas del director: se entrega tal cual, o se fotografía y se manda por chat.
- El reverso es común a todas: el sello Open Case en `sello` centrado, para que no se distingan boca abajo.
