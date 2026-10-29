---
institution: Menú de preguntas
description: Cada pregunta cuesta 1 ficha
title: Sospechosos
---

La primera pregunta de cada sospechoso es dónde estuvo esa noche. Lo que diga hay que comprobarlo con diligencias, testigos o seguimientos.
{.small}

<!-- El menú de cada sospechoso se arma solo con las tarjetas marcadas "menu: true" en tarjetas.yaml. -->
```menu
```

## Testigos

Al comienzo solo pueden entrevistar a Rosa. A cualquier otra persona la pueden entrevistar cuando aparezca nombrada en una prueba, una declaración o una tarjeta. Un nombre en una lista de llamadas, una cartola o un registro también cuenta.
{.small}

| Código | Persona | Pregunta |
|---|---|---|
| `R1` | Rosa Huenchumilla, vecina del frente | ¿Qué escuchó esa noche? |
| `R2` | Rosa Huenchumilla | ¿Vio a alguien? |
| `TESTIGO` | Cualquier persona que haya aparecido en su material | Escriban el nombre, dónde apareció y qué le quieren preguntar. Si todavía no apareció, no se cobra. |
| `PER1` | Perito informático del laboratorio | Consultar al perito sobre un dato del informe del celular (solo después de tener ese informe). |

## Seguimientos

Algunas tarjetas de respuesta traen al pie una pregunta de seguimiento con un código terminado en + (por ejemplo B3+). Se piden igual que una pregunta y cuestan 1 ficha.
{.small}
