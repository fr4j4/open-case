# Hoja
La unidad básica de todo material: una hoja de `papel` sobre la `mesa`. En pantalla tiene sombra y esquinas de 3 px; impresa ocupa una carta completa con márgenes de 14 mm (`--carta`) y se corta en página nueva.

Anatomía, de arriba abajo: membrete → título (`titulo-hoja`) → campos de ficha (`.oc-meta`) → cuerpo (párrafos, subtítulos en `subtitulo-hoja`, listas, tablas) → firma o fuente (`.oc-firma`) → sello de esquina opcional → pie de marca (`.oc-hoja__marca`: monograma, "Open Case" y el nombre del caso).

- Una hoja = una prueba, una declaración o una sección del kit. Nunca dos pruebas en una hoja.
- `--reservada` (franja roja superior) marca el material del director. `--vieja` (fondo `papel-viejo`) para documentos de archivo.
- Párrafos de 68 caracteres como máximo. Los datos que un equipo tiene que encontrar van en el cuerpo, nunca en el membrete.
- La hoja no lleva número de página: se identifica por su código. El pie de marca va en **todas** las hojas, también en las del caso: es la única presencia de Open Case en un documento del caso.
