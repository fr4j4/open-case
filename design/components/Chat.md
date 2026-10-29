# Captura de chat
Conversaciones de mensajería en un marco de celular (`.oc-celular`): barra `chat-cabecera`, fondo `chat-fondo`, globos entrantes en blanco y salientes en `chat-saliente`. La tipografía es `pantalla` (Roboto) porque imita un teléfono, no porque sea la del juego.

- El dueño del teléfono siempre está a la derecha. En un grupo, cada remitente lleva su nombre en un color fijo (`__quien`, variantes b–e) durante todo el caso.
- Cada mensaje lleva hora. Las pastillas de día separan fechas.
- Un mensaje borrado se muestra con `--borrado` ("Se eliminó este mensaje") y la hora original: es una pista en sí mismo.
- Adjuntos en `__adjunto` con el nombre del archivo. Emojis solo los que escribiría esa persona (y pocos).
- No se imitan logotipos ni íconos de ninguna app real; basta el color de la barra y la forma de los globos.
- En papel: 70 mm de ancho (`captura-ancho`), hasta dos por hoja. Se puede enviar como imagen por el grupo de WhatsApp del equipo.
