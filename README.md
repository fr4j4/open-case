# Open Case

> **Dos equipos, un culpable.** *(lema provisional)*

**Open Case** es un framework para crear y dirigir juegos de investigación: casos policiales que dos equipos resuelven compitiendo entre sí, con un director que conduce la partida.

Cada caso se arma con material impreso o digital (expedientes, pruebas, fotografías y declaraciones) que los equipos analizan para reconstruir lo que pasó y acusar al culpable. El tono es policial y deductivo, no de terror.

## Cómo se juega (en líneas generales)

- **Dos equipos** compiten por resolver el mismo caso.
- **Un director** hace de comisario, interpreta a los sospechosos y controla el ritmo de la partida.
- Los equipos **investigan con recursos limitados**: eligen qué preguntar, qué pruebas pedir y a quién confrontar.
- Al final, cada equipo presenta su **acusación** y gana el que mejor sostiene su caso con la evidencia.

Los detalles (duración, puntaje, número de jugadores) los define cada caso.

## Principios

- **Agnóstico a la localidad.** El framework no depende de un lugar; cada caso puede ambientarse donde quiera.
- **Pensado para traducirse.** Por ahora todo está en español, pero la estructura se diseña para publicar también en inglés más adelante.
- **Sin spoilers para los jugadores.** El material de los equipos y el del director van siempre separados.

## Estado del proyecto

🚧 **En construcción.**

- La identidad visual de Open Case (y la estética de los artefactos de cada caso) está en definición.
- Los casos aún no se publican en este repositorio. Se subirán cuando el formato visual esté cerrado.

## Estructura prevista

Esta es solo una intención y puede cambiar:

```
open-case/
├── docs/          # Reglas generales, guía para crear casos, identidad visual
├── plantillas/    # Plantillas de expediente, kit del equipo y guía del director
└── casos/
    └── <nombre-del-caso>/
        ├── equipo/    # Material para los equipos (sin spoilers)
        └── director/  # Solución y guía del director
```
