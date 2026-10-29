Open Case es la marca y el marco de diseño de una familia de juegos de investigación para dos a cuatro equipos: casos policiales, acertijos y misterios que se juegan con papel, fichas y un director. Esta guía fija cómo se ve y cómo se escribe **todo** artefacto de cualquier caso, para que un expediente de 2026 en Labranza y un caso de archivo de 1950 en otro país se reconozcan como el mismo juego. El primer caso es "El Chupacabras de Labranza"; sus materiales sirven de ejemplo en cada componente.

## La idea en tres frases

- **La mesa es oscura y el papel es claro.** En pantalla, cada documento es una hoja de `papel` apoyada en la `mesa`; impreso, es una hoja carta o una tarjeta blanca recortable. Nunca hay un tema oscuro para el papel.
- **Dos mundos, dos voces.** Los documentos *del caso* (partes, declaraciones, chats, boletas) pertenecen a instituciones y personas ficticias: no llevan la marca y se ven como el objeto real. El material *del juego* (kit, tarjetas, placas, fichas, sobres, guía) lleva Open Case y habla en la voz del juego.
- **La escritura dice quién habla.** Lo impreso oficial no miente; lo tipeado a máquina es lo que alguien declaró; lo manuscrito es íntimo o apurado; lo de pantalla es lo que alguien publicó. El jugador reconoce la fuente antes de leerla.

## Cómo usar esta guía

1. Lee **Marca** antes de poner el nombre en cualquier parte, y **Redacción y códigos** antes de escribir una línea.
2. Elige el componente que corresponde a cada pieza en **Catálogo de artefactos**: cada tipo tiene un formato, una tipografía y campos obligatorios. No inventes un tipo nuevo si uno existente sirve.
3. Construye con `components/bundle.css` (clases `oc-`) y los tokens de `tokens.json`. Los nombres de los tokens son los nombres de las variables CSS: `var(--sello)`, `var(--font-mono)`, `var(--tarjeta-ancho)`.
4. Todo recortable mide 63 × 88 mm o es una ficha de 30 mm: ver **Norma de tarjetas**.
5. Antes de publicar un caso, pasa la **Lista de verificación**.

## Fundamentos de contenido

- Español neutro con sabor local. El caso puede situarse en cualquier lugar; la localidad vive en los nombres de instituciones, calles y comidas, no en la tipografía ni en los colores. El nombre Open Case no se traduce; el lema sí ("Todos mienten. Las pruebas no." / "People lie. Evidence doesn't."). Las dos versiones están en `tokens.json` bajo `marca.lema`.
- Los equipos se tratan de **ustedes** en el kit ("Ustedes son detectives"); los sospechosos hablan en primera persona y tratan de **usted** a los detectives; el director lee el guion tal cual.
- Tono policial, no de terror: lo inquietante se sugiere. Sin sangre explícita, sin descripciones de heridas más allá de lo que diría un informe, sin personas reales, sin religiones ni pueblos usados como monstruo.
- Horas en formato 24 h (`22:52`); fechas `viernes 30-10-2026` en documentos y "viernes 30 de octubre" en diálogo; cifras con coma decimal y punto de miles (`4,5 cm`, `$60.000.000`).
- Sin signos de exclamación en documentos oficiales. Sin emojis salvo dentro de un chat, y solo los que escribiría ese personaje.

## Fundamentos visuales

- **Color.** El rojo `sello` es la marca y señala lo que importa: códigos de prueba, sellos, confrontaciones, lo reservado al director. El `marino` es la institución: subtítulos, códigos de pregunta, Equipo A. El `laton` es el juego físico: placas y fichas. El `bosque` es lo verificado y el Equipo B. `violeta` y `cobre` existen solo para los equipos C y D. El `ambar` avisa. Todo lo demás es `tinta` sobre `papel`. Ver **Color**.
- **Tipografía.** Trece familias, una por tipo de escritura, todas de Google Fonts. Public Sans para lo impreso, IBM Plex Mono para códigos y registros, Special Elite para lo mecanografiado, Caveat y tres manos más para lo manuscrito, Playfair Display para la prensa, Roboto para las pantallas, Barlow Condensed solo para la marca y los rótulos grandes. Ver **Tipografía por tipo de escritura**.
- **Espacio y formato.** En pantalla, múltiplos de 4 px. En papel, milímetros: hoja carta con márgenes de 14 mm, tarjetas de 63 × 88 mm con margen interior de 5 mm, pliegos de 8 tarjetas. Ver **Formatos e impresión**.
- **Esquinas y sombras.** Lo que se imprime tiene esquinas vivas (`radio-0`); en pantalla la hoja tiene 3 px y `sombra-hoja`. Las únicas curvas grandes son las de las pantallas imitadas (globos de chat, marco del celular) y las fichas redondas.
- **Imágenes.** Fotos con aspecto de registro: luz real, grano, flash directo de noche, testigo métrico en los detalles, nunca rostros reconocibles. Las capturas de pantalla imitan la forma de la app, nunca su logotipo. Ver **Fotos y pantallas**.

## Iconografía

Open Case no usa un sistema de íconos. Los signos son tipográficos y forman parte de la norma de códigos: `◆` confrontación, `+` seguimiento, `✕` fallida, `·` separador, `→` en manuscritos, `↘ ↗ ✕` en registros de llamadas. Los únicos dibujos son los cinco de `assets/Iconos/` (estrella de placa, carpeta, ficha, rombo y la lupa tachada que recuerda que la lupa está prohibida como símbolo del juego: es un cliché de detective y Open Case no lo usa). Son SVG de una tinta (`tinta`), se muestran con `<img>` y no cambian de color; para otra tinta, se edita el archivo.

## Lo que esta guía no decide

Las reglas de juego (fichas, puntaje, fases) pertenecen al marco de juego, no al diseño. Esta guía fija cómo se ven las fichas, no cuántas hay.
