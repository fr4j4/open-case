# Formatos e impresión

## Soportes

| Soporte | Medida | Token | Qué va ahí |
|---|---|---|---|
| Hoja carta | 216 × 279 mm, márgenes 14 mm | `hoja-ancho`, `hoja-alto`, `margen-hoja` | Toda hoja: pruebas, declaraciones, informes, hojas de trabajo, guía. A4 (210 × 297) se acepta con la misma retícula. |
| Tarjeta | 63 × 88 mm (póker), margen interior 5 mm | `tarjeta-ancho`, `tarjeta-alto`, `margen-tarjeta` | Todo recortable: respuestas, confrontaciones, avisos, pistas, sospechosos, placas, solicitudes, etiquetas de sobre y de bolsa. |
| Pliego | Carta, 2 × 4 tarjetas apaisadas, calle 3 mm | `calle` | 8 tarjetas por hoja. |
| Ficha | Ø 30 mm | `ficha-diametro` | 35 por hoja (5 × 7, calle 4 mm). |
| Foto impresa | 120 mm de ancho, 4:3 | `foto-ancho` | Dos por hoja, con pie. |
| Captura de celular | 70 mm de ancho, 9:19,5 | `captura-ancho` | Dos por hoja, o una imagen por mensaje de chat. |
| Captura de cámara | 120 mm de ancho, 16:9 | `foto-ancho` | Con reloj sobreimpreso. |
| Boleta | 58 mm de ancho | — | Pegada en una hoja con su código o dentro de una bolsa. |

## Retícula de la hoja

Una columna de texto de 68 caracteres como máximo (`.oc-hoja p{max-width:68ch}`). Bloques separados por 14 px en pantalla (4 mm en papel). Orden fijo: membrete → título → campos → cuerpo → firma/fuente → sello. Las tablas ocupan el ancho completo; las fotos van en una rejilla de dos columnas (`.oc-fotos`); los celulares en rejilla de dos (`.oc-celulares`); los videos en rejilla de hasta cuatro (`.oc-videos`).

## En pantalla

- Las hojas se apilan sobre la `mesa` con 28 px entre ellas (`space-7`) y un ancho máximo de 800 px (860 en la guía del director).
- La portada lleva `.oc-sobrelinea` (institución), un `h1` en `sans` 800 y un párrafo de ayuda que no se imprime; debajo, un índice de pastillas (`.oc-indice`) con anclas a cada hoja.
- Entre secciones, `.oc-seccion` en `mono` mayúsculas.
- Márgenes laterales de 16 px en celular; ninguna tabla desborda: va dentro de `.oc-tabla` con desplazamiento.

## Al imprimir

- `@media print` ya está en `bundle.css`: la mesa se vuelve blanca, cada `.oc-hoja` y cada `.oc-pliego` corta en página nueva, las sombras desaparecen, los pies de celular y video no se parten.
- Imprimir al **100 %** ("tamaño real"), nunca "ajustar a página": las tarjetas deben medir 88 × 63 mm al salir.
- Papel: bond 90 g para hojas; cartulina 200 a 250 g para pliegos de tarjetas y fichas; las placas se pueden plastificar o enfundar (funda tamaño póker).
- Color: las hojas se pueden imprimir en escala de grises sin perder significado (los códigos tienen marco, las bandas tienen posición). Los pliegos de tarjetas se imprimen en color.
- PDF: una hoja por página, carta, sin encabezado ni pie del navegador. Cada artefacto publicado (kit, expediente, guía) tiene su PDF generado desde el mismo HTML.

## Por chat

Cuando una prueba se manda por el grupo de WhatsApp de un equipo: una captura por hoja (ancho completo, sin recortar el membrete ni el código) y, si trae foto, la foto aparte en calidad original con el pie copiado como texto del mensaje.
