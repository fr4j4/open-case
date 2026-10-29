# Tarjeta de aviso, prensa y pista
Tarjetas que lee el director en voz alta o entrega sin que nadie las pida. Comparten la anatomía de la tarjeta de respuesta con el código en `display` y una banda de color propio.

- **Aviso** (`--aviso`, banda `ambar`): información nueva de la Fiscalía que llega a todos los equipos a la vez, en un minuto fijo del guion ("AVISO 1 · minuto 10").
- **Prensa** (`--prensa`, banda `tinta`): la noticia que marca los últimos 10 minutos; titular en `prensa` y cuerpo en `prensa-texto`.
- **Pista** (`--pista`, fondo `laton-suave`): se entrega cuando un equipo la pide y resta 1 punto; lo dice en la cabecera.
- Un aviso tiene una sola novedad; si hay dos, son dos avisos.
