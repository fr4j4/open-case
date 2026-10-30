# Tipografía por tipo de escritura

La regla central: **el tipo de letra dice quién escribió y cómo**. Antes de elegir una familia, pregunta qué objeto es.

| Tipo de escritura | Familia (`tokens.json`) | Fuente | Estilos | Se usa en |
|---|---|---|---|---|
| Impreso oficial | `sans` | Public Sans | `titulo-hoja`, `subtitulo-hoja`, `cuerpo`, `cuerpo-impreso`, `pequeno`, `tarjeta-respuesta`, `tarjeta-pregunta` | Partes, informes, cartas de empresa, kit, tarjetas de respuesta. Lo que una institución imprimió. |
| Códigos y registros | `mono` | IBM Plex Mono | `codigo`, `rotulo`, `etiqueta`, `tabla`, `transcripcion` | Códigos (E01, B◆), membretes, campos, libros de portería, cartolas, listas de llamadas, cintas rotuladoras, guion del director. |
| Mecanografiado | `maquina` | Special Elite | `declaracion` | Declaraciones y actas: lo que alguien dijo y un funcionario tipeó. También documentos de época. |
| Impresora térmica | `termica` | Courier Prime | `boleta` | Boletas, vouchers, tickets, fax. |
| Manuscrito legible | `manuscrita` | Caveat | `libreta` | Libretas, agendas, notas de perito, observaciones al pie de un registro. |
| Garabato | `garabato` | Nothing You Could Do | `garabato` | Notas apuradas, servilletas, márgenes, notas adhesivas. |
| Plumón | `plumon` | Permanent Marker | `plumon` | Rótulos de bolsas, cajas, carteles. Mayúsculas. |
| Firma | `firma` | Homemade Apple | `firma` | Firmas al pie de declaraciones y cartas. |
| Cursiva de carta | `cursiva` | Dancing Script | `carta` | Cartas personales, esquelas, dedicatorias. |
| Prensa | `prensa` / `prensa-texto` | Playfair Display / Libre Baskerville | `titular`, `prensa-cuerpo` | Recortes de diario, tarjeta de prensa. |
| Pantalla | `pantalla` | Roboto | `chat`, `chat-nombre`, `chat-hora`, `app-titulo` | Chats, llamadas, calendario, publicaciones, correo. Imita un teléfono. |
| Marca y rótulos grandes | `display` | Barlow Condensed | `portada`, `titulo-tarjeta`, `sello`, `numeral` | Logotipo, portadas, sellos, placas, número de sobre, cabecera de bolsa, códigos de aviso/pista/prensa. |

Todas son de Google Fonts (sin archivos propios): la hoja de estilos las importa con una sola línea. Fuera de línea, las alternativas están en cada pila (`"Arial Narrow"`, `"Courier New"`, `cursive`).

## Reglas

- **Un registro por persona.** Si la veterinaria escribe en `libreta`, todas sus notas del caso son `libreta`. Si el cuidador garabatea, siempre garabatea.
- **No se mezclan** dos tipos de escritura en un mismo bloque. Una nota manuscrita sobre un registro impreso son dos bloques (`.oc-tabla` y luego `.oc-manuscrito`).
- **Tamaños mínimos.** En pantalla: 13 px el texto pequeño, 12,5 px en tarjetas, 18 px los manuscritos. En papel: 10,5 pt el cuerpo, 9,5 pt en tarjetas, nunca menos de 8,5 pt; manuscritos desde 13 pt.
- **Mayúsculas** solo en `rotulo`, `etiqueta`, `subtitulo-hoja`, `sello`, `plumon` y la marca. El cuerpo nunca va en mayúsculas.
- **Barlow Condensed es de la marca.** No aparece dentro de un documento del caso: un parte policial no tiene nada en Barlow. Sí aparece en lo que el jugador sabe que es del juego (tarjetas de aviso, placas, sobres, portadas) y en objetos del mundo que llevan rótulos grandes (la cabecera de la bolsa de evidencia).
- **Cifras tabulares** (`font-variant-numeric: tabular-nums`) en toda tabla y registro; las horas se alinean.
- Cursiva (`italic`) solo para la pregunta de una tarjeta y acotaciones breves. Negrita para títulos, nombres de campo en meta y el total de una boleta.
