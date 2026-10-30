# Color

Un solo tema: **Papel**. La mesa oscura existe solo en pantalla, detrás de las hojas; ninguna hoja, tarjeta ni foto se imprime en oscuro. Cada token tiene en `tokens.json` una nota de uso que dice sobre qué fondo se lee; los pares de texto cumplen 4,5:1 (los de `laton` y `ambar` no son para texto y se usan como borde, franja o relleno).

## Superficies

| Token | Valor | Uso |
|---|---|---|
| `papel` | #f7f5ef | Toda hoja. Texto en `tinta` y `tinta-suave`. |
| `papel-2` | #efece3 | Franjas de tabla, citas, tarjeta fallida. |
| `papel-viejo` | #efe4c6 | Documentos de archivo o de época; cartas personales. |
| `blanco` | #ffffff | Tarjetas recortables, bolsa de evidencia, pie de foto impreso. |
| `mesa` / `mesa-2` | #22282a / #2f373a | Fondo de pantalla y botones del índice. Texto en `mesa-texto` y `mesa-texto-suave`. |

## Tinta

`tinta` (#1e2224) para todo el texto de lectura; `tinta-suave` (#5b6266) para rótulos, metadatos y la pregunta en cursiva de una tarjeta; `regla` (#d2ccbe) para filetes; `regla-fuerte` (#8d9396) solo para el borde punteado de corte.

## Los cinco colores con significado

| Token | Valor | Significa | Dónde |
|---|---|---|---|
| `sello` | #9e2a2b | La marca y lo que importa | Sellos, códigos de prueba, franja de reservado, tarjeta de confrontación, pastilla "mentira", logotipo en portadas. |
| `marino` | #1d3557 | La institución | Subtítulos de hoja, códigos de pregunta, banda de la tarjeta de respuesta, Equipo A, cita del guion. |
| `laton` | #b48a2c | El juego físico | Marco de placas, anillo de fichas, estrella, tarjeta de pista. Texto a su lado en `laton-oscuro`. |
| `bosque` | #2f6b3f | Verificado | Pastilla "verdad", sello "Verificado", tarjeta de testigo, Equipo B. |
| `violeta` | #5a3d8a | Equipo C | Solo cuadro de equipo, placa y fichas del Equipo C. |
| `cobre` | #8a4b12 | Equipo D | Solo cuadro de equipo, placa y fichas del Equipo D. |
| `ambar` | #b77a12 | Aviso | Banda de la tarjeta de aviso, notas de alerta del director. Texto en `ambar-texto`. |

Cada uno tiene un tono `-suave` para fondos tenues (`sello-suave`, `marino-suave`, `laton-suave`, `bosque-suave`, `ambar-suave`). Un fondo suave siempre lleva su texto fuerte encima, nunca blanco.

Reglas:
- Un color de significado por elemento. Una tarjeta tiene una banda; una hoja, una franja; un sello, una tinta.
- Una partida tiene de 2 a 4 equipos: A en `marino`, B en `bosque`, C en `violeta`, D en `cobre`. Se distinguen por color **y** por letra, nunca solo por color. `violeta` y `cobre` no se usan para nada más.
- El `sello` no se usa como fondo grande. Lo máximo es la franja de 6 px de la hoja reservada y el reverso de las tarjetas (logotipo sobre blanco).

## Escritura a mano

`boligrafo` (#1f3b75) para manuscritos y firmas; `lapiz` (#4a4f52) para borradores; `plumon` (#141516) para rótulos gruesos. `postit` (#fbf0a0) es la nota adhesiva; `resaltador` (#f3e08a), el marcador sobre una línea impresa.

## Pantallas

Los colores de chat y video (`chat-fondo`, `chat-entrante`, `chat-saliente`, `chat-cabecera`, `chat-meta`, `video-fondo`, `video-acento`) imitan la forma de las apps sin copiar ninguna marca: se parecen lo justo para que el jugador reconozca "un chat" o "un live". No se añaden logotipos reales. `foto-marco` y `cctv-fondo` enmarcan fotos y capturas.
