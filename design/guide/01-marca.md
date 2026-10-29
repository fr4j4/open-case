# Marca

**Nombre:** Open Case. Se escribe con dos palabras y mayúsculas iniciales en texto corrido; en el logotipo va en mayúsculas. No se traduce ni se abrevia en texto ("OC" solo en el monograma).

**Lema:** "Todos mienten. Las pruebas no." En inglés, "People lie. Evidence doesn't." Va bajo el sello y en la portada del kit; nunca dentro de un documento del caso. Es también la regla central del juego: los sospechosos pueden mentir, los peritajes y documentos oficiales no. Ambas versiones viven en `tokens.json` (`marca.lema`) y como variables `--marca-lema-es` y `--marca-lema-en`.

**Nombre del caso:** cada caso tiene su propio título ("El Chupacabras de Labranza"), siempre en la segunda línea, después de la marca, y en `sans` o `display` según el soporte: la marca es el juego, el caso es la partida. En las tarjetas, el nombre del caso va en la línea de marca inferior, a la derecha.

## Logotipo

Tres formas, en `assets/Logos/` (SVG con contornos; usa el archivo, no lo redibujes):

| Forma | Archivo | Uso |
|---|---|---|
| Sello | `oc-sello-sello.svg`, `-tinta`, `-papel` | Portadas, contratapa del kit, reverso de tarjetas, créditos. La forma principal. |
| Wordmark | `oc-wordmark-tinta.svg`, `-sello`, `-papel` | Membrete del kit y de la guía (`.oc-membrete__logo`), pies de página, pantalla. |
| Monograma | `oc-monograma-tinta.svg`, `-sello`, `-papel` | Pequeño: placas, fichas (reverso), íconos. Mínimo 8 mm en papel, 24 px en pantalla. |

- La tinta del logotipo es `tinta` sobre papel y blanco, `sello` en portadas y pliegos, `papel` sobre la `mesa`. Nunca otro color, nunca degradado, sombra ni contorno.
- El sello ya viene girado −4°; no se gira más ni se endereza. Zona de respeto: la altura de la pestaña de la carpeta.
- En los documentos del mundo del caso (partes, declaraciones, informes, cartas) el logotipo va **solo en el pie de la hoja** (`.oc-hoja__marca`): el monograma a 6 mm, "Open Case" y el nombre del caso en `display` 9 px y `tinta-suave`, sobre un filete `regla`. Es el mismo pie que llevan las tarjetas. Nunca en el membrete ni en el cuerpo de esos documentos, que pertenecen a una institución ficticia. Las capturas de pantalla y las fotos sueltas no llevan pie de marca: lo lleva la hoja que las contiene.
- En el material del juego (kit, guía, sobres, placas, fichas) el wordmark va en el membrete y el sello en las portadas.
- Sobre fotografía solo la versión `papel` dentro de una franja `mesa`, nunca directo sobre la imagen.

## Voz de la marca

Cuando habla el juego (kit, tarjetas de aviso, portadas), habla corto y directo, en segunda persona del plural, sin adjetivos de marketing: "Ustedes son detectives. Los otros equipos investigan el mismo caso. Gana el que presente la teoría mejor sustentada." Nunca "¡Prepárate para la aventura!".

Cuando habla el mundo del caso, la marca se queda en el pie y habla la institución: "Policía de Investigaciones de Chile · Brigada de Homicidios". El jugador debe poder olvidar que está leyendo un juego.

## Lo que no se hace

- Lupas, huellas digitales, siluetas con sombrero y cinta amarilla como decoración: son clichés de "detective" y Open Case no los usa. La cinta de peligro puede existir como objeto dentro de una foto, no como motivo gráfico.
- Sangre, salpicaduras, tipografías "de terror", fondos negros con rojo chorreado.
- Degradados, sombras de color, íconos emoji como adorno, tarjetas con borde de color a la izquierda.
