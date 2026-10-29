# Norma de tarjetas

**Una sola medida para todo recortable: 63 × 88 mm**, el formato póker. Apaisada (88 de ancho) para lo que se lee; vertical para lo que se muestra (placas, sospechosos). Cabe en fundas estándar, se mezcla sin que se note cuál es cuál boca abajo y entra en un sobre americano.

## Anatomía de una tarjeta apaisada

De arriba abajo, dentro de un margen de 5 mm:

1. **Banda** de 4 px (`.oc-tarjeta__banda`), del color que dice qué tarjeta es.
2. **Cabecera** (`.oc-tarjeta__cab`): código en `mono` 600 a la izquierda; a la derecha, en `tinta-suave`, quién habla o de qué se trata. Cerrada por un filete `regla`.
3. **Pregunta** (`.oc-tarjeta__pregunta`): en cursiva y `tinta-suave`. En una confrontación, la frase que dice el detective.
4. **Respuesta** (`.oc-tarjeta__respuesta`): el contenido, entre comillas si es una cita. Ocupa el espacio que sobra.
5. **Pie** (`.oc-tarjeta__pie`): en `mono` 10,5 px. En `sello`, lo que se adjunta ("Adjunta E30"); en `marino` (`--seg`), los seguimientos ("Seguimiento disponible: B1+").
6. **Línea de marca** (`.oc-tarjeta__marca`): "Open Case" a la izquierda y el nombre del caso a la derecha, en `display` 9 px y `tinta-suave`, sobre un filete. Va en **todas** las tarjetas; es lo único de la marca que entra en la mesa durante la partida.

## Tipos y colores

| Tipo | Clase | Banda | Código | Quién la recibe |
|---|---|---|---|---|
| Respuesta | `.oc-tarjeta` | `marino` | `B1`, `H3` | El equipo que pagó la pregunta. |
| Seguimiento | `.oc-tarjeta` | `marino` | `B1+` | Ídem; la cabecera dice "Seguimiento". |
| Fallida | `--fallida` | `regla-fuerte`, fondo `papel-2` | `B✕` | El equipo cuya confrontación no sirvió; la ficha se cobra. |
| Confrontación | `--confrontacion` | `sello` | `B◆ · B5` | El equipo que mostró la prueba correcta. |
| Testigo | `--testigo` | `bosque` | `R1`, `TESTIGO` | El equipo que entrevistó. |
| Aviso | `--aviso` | `ambar` | `Aviso 1` | Los dos equipos, en un minuto fijo. |
| Prensa | `--prensa` | `tinta` | `Prensa` | Los dos equipos, al minuto 20. |
| Pista | `--pista` | `laton`, fondo `laton-suave` | `Pista` | El equipo que la pidió; resta 1 punto. |
| Cierre o confesión | `--cierre` | `sello`, marco de 2 px | `Cierre` | Se lee en voz alta al final. Texto en `maquina`. |
| Sospechoso | `--vertical --sospechoso` | `marino` | letra del sospechoso | Ambos equipos, desde el inicio. |
| Placa | `--vertical .oc-placa` | marco doble `laton` | — | Cada jugador. |
| Solicitud | `.oc-solicitud` | — | — | Cada equipo, 30 unidades. |
| Etiqueta de sobre | `.oc-sobre` | — | `Sobre 1` | Pegada en cada sobre. |
| Etiqueta de bolsa | `.oc-bolsa` | cabecera `tinta` | `N° 07 · E18` | Pegada en una bolsa con un objeto. |

## Límites de texto

- Respuesta: **420 caracteres** como máximo en `tarjeta-respuesta` (12,5 px / 9,5 pt). Con pregunta larga o dos líneas de pie, 360. Si no cabe, se parte en "(1 de 2)" y "(2 de 2)", nunca se achica la letra por debajo de 8,5 pt.
- Pregunta: 110 caracteres. Cabecera derecha: 36. Pie: dos líneas.
- Sospechoso: cinco datos de una línea cada uno. Aviso: una sola novedad.

## Reverso

Todas las tarjetas apaisadas comparten un reverso: el sello Open Case (`oc-sello-sello.svg`) centrado a 40 mm de ancho sobre blanco, con el nombre del caso en `rotulo` debajo. Así ninguna tarjeta se reconoce boca abajo, y el director puede repartirlas sin mirar. Las verticales llevan el mismo reverso girado.

## Pliego

El pliego (`.oc-pliego`) es la hoja carta con 2 × 4 tarjetas apaisadas y calle de 3 mm; márgenes resultantes de 18,5 mm a los lados y 7,5 mm arriba y abajo. Las verticales usan `--vertical` (3 × 3 en A4, 3 × 2 en carta) o se giran 90° dentro de la rejilla apaisada. Cada pliego lleva al pie: caso, qué tarjetas contiene y "pliego N de M · imprimir al 100 %". Las tarjetas de un mismo sospechoso van juntas y en orden de código; las de aviso, prensa y pista, en un pliego aparte; las solicitudes y placas, en los suyos.

## Fichas

Círculo de 30 mm (`.oc-ficha`), anillo de 2 px en `laton`, fondo `laton-suave`, número en `display` y la palabra FICHA en `mono`. Reverso en `laton` liso con el monograma. Variantes por equipo `--a` (`marino`) y `--b` (`bosque`). Se imprimen 35 por hoja en cartulina y se recortan con sacabocados de 30 mm o tijera; también valen fichas de póker siguiendo los mismos colores.
