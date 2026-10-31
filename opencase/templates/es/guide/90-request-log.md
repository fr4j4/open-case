---
place: after-block control
institution: Reglas para dirigir
description: Opcional · una línea por solicitud
title: Registro de solicitudes
---

Anota cada solicitud en el orden en que llega y respóndela antes de tomar la siguiente. Así ningún mensaje queda sin respuesta y al final sabes qué recibió cada equipo. Si se llena, imprime otra copia.
{.small}

```work-table
columns: ["N°", Equipo, Código, "Ficha{{ ' (normal o coartada)' if f.alibi_tokens_per_team else '' }}", Entregado]
height: 18px
rows: [{% for i in range(1, f.request_log_rows + 1) %}"{{ i }}"{{ ", " if not loop.last else "" }}{% endfor %}]
```
