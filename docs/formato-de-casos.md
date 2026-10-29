# Formato de los casos

Un caso es una carpeta. Adentro hay unos pocos archivos YAML con los datos generales, una carpeta por cada documento del juego con una hoja por archivo, y las fotos y dibujos que esas hojas usan. El exportador lee todo eso y arma los PDF.

El caso de ejemplo, `casos/chupacabras-labranza/`, usa casi todo lo que se describe acá. Si algo no queda claro, lo más rápido es abrir el archivo equivalente del chupacabras y copiarlo.

```
casos/mi-caso/
├── caso.yaml          título, papel, equipos, qué va en cada sobre
├── personajes.yaml    los sospechosos (tarjetas y menú de preguntas)
├── tarjetas.yaml      las tarjetas de respuesta
├── kit/               hojas del kit del equipo, una por archivo .md
├── expediente/        una prueba por archivo .md (E01.md, E02.md…)
├── guia/              hojas de la guía del director
├── fotos/             imágenes .jpg / .png
├── diagramas/         dibujos .svg (croquis, líneas de tiempo)
└── estilos.css        opcional: CSS extra solo para este caso
```

Las carpetas `fotos/` y `diagramas/` son una costumbre, no una regla. Las rutas a imágenes siempre se escriben desde la carpeta del caso (`fotos/e02_f1.jpg`), y puedes ordenarlas como quieras.

Antes de exportar conviene correr `python exportar.py casos/mi-caso --revisar`. Revisa referencias cruzadas sin abrir el navegador y avisa con nombre de archivo y número de línea.

## caso.yaml

```yaml
titulo: El Chupacabras de Labranza     # obligatorio
version: Versión 5 · octubre de 2026   # sale en las tapas
papel: carta                           # carta o a4
marca: Open Case
lema: Dos equipos, un culpable

equipos: [A, B]
fichas_por_equipo: 16
jugadores_por_equipo: 7                # cuántas placas por equipo

marca_en_hojas: [kit, guia, expediente]
ahorro_de_tinta: true

placa:
  titulo: Detective
  unidad: [Brigada de Homicidios, Temuco]

kit:
  descripcion: …
  nota_tapa: Una copia por equipo. No incluye respuestas ni pruebas.

guia:
  descripcion: …
  nota_tapa: Contiene la solución. No la muestres ni la mandes a los equipos.

expediente:
  titulo: Expediente El Arrayán
  sobrelinea: PDI · Brigada de Homicidios Temuco
  descripcion: …               # texto de la portada en pantalla
  descripcion_impresa: …       # texto de la carátula impresa del director
  archivo: Expediente_completo # nombre del PDF, opcional
  secciones: …

sobres: …
```

**marca_en_hojas** dice qué documentos llevan, al pie de cada hoja, el monograma con la marca y el nombre del caso. Los valores posibles son `kit`, `guia` y `expediente`, y si no lo pones quedan `[kit, guia]`. La guía de marca deja el expediente sin logo, porque son papeles del mundo del caso: un parte policial no viene con el logo de un juego. Si prefieres que cada hoja quede identificada (para no mezclar casos, por ejemplo), agrega `expediente`.

**ahorro_de_tinta** viene activado. Más abajo está explicado.

### Secciones del expediente

Las secciones dan el orden de las pruebas y deciden qué se entrega a quién:

```yaml
expediente:
  secciones:
    - titulo: Sobre 1
      nota: Se entrega a ambos equipos al comenzar
      equipos: Sobre_1
      pruebas: [E01, E02, E03, E04, E05, E07]
    - titulo: Diligencias
      nota: Se entregan al equipo que paga la ficha
      pruebas: [E12, E13a, E13b]
```

Cada id de `pruebas` es el nombre de un archivo de `expediente/` sin el `.md`. Un id solo puede estar en una sección, y una hoja que no está en ninguna se avisa y no se exporta.

Las secciones con `equipos: Sobre_1` se juntan en un PDF aparte, `equipos/02_Sobre_1.pdf`, que es lo único del expediente que va a la carpeta de los equipos. Varias secciones pueden apuntar al mismo sobre. Todo lo demás queda solo en `director/02_Expediente_completo.pdf`, que trae todas las secciones con un índice al principio.

### Etiquetas de sobre

```yaml
sobres:
  - numero: 1
    cuando: se entrega al comenzar
    descripcion: Lo que sabemos hasta ahora. No incluye respuestas.
    contenido: [E01 Parte policial, E02 Set fotográfico, Kit del equipo]
    pie: 16 fichas · 1 placa por jugador
```

Se imprime una etiqueta por sobre y por equipo, para pegarla en el sobre de papel.

## personajes.yaml

```yaml
sospechosos:
  - letra: B                    # la letra de sus códigos: B1, B◆, DEC · B
    nombre: Benjamín Ferrada
    nombre_corto: Benja         # opcional, para la tarjeta si el nombre es largo
    rol: hermano de la víctima
    retrato: fotos/benjamin.jpg # opcional; sin retrato sale una silueta de carpeta
    confrontar: Confrontar con una prueba (indiquen cuál)   # opcional, texto del menú
    datos:                      # hasta cinco, de una línea cada uno
      Edad: 41
      Oficio: Ingeniero comercial
      Relación: Hermano mayor de la víctima
```

Con esto salen las tarjetas de sospechoso y los títulos del menú de preguntas del kit. El retrato nunca debe mostrar un rostro reconocible: de espaldas, de lejos o en sombra.

## tarjetas.yaml

Las tarjetas van en grupos. Cada grupo se imprime junto y en el orden del archivo:

```yaml
grupos:
  - titulo: Benjamín Ferrada
    personaje: B         # las tarjetas del grupo son de B
    quien: Benjamín Ferrada
    corto: Benjamín      # para "Benjamín · confrontación"
    tarjetas:
      - codigo: B1
        menu: true       # la pregunta aparece en el menú del kit
        pregunta: ¿Dónde estuvo el viernes entre las 22:00 y la 01:00?
        respuesta: '"En mi departamento, en la Torre Alemania…"'
        adjunta: E30     # el director entrega también esa prueba
        seguimiento: B1+ # habilita otra pregunta
      - codigo: B5
        tipo: confrontacion
        pregunta: '"Usted estuvo en Labranza esa noche."'
        respuesta: '"Ya, sí… fui."'
```

Los campos de una tarjeta son estos:

| Campo | Para qué |
|---|---|
| `codigo` | Obligatorio. En las confrontaciones se le antepone la letra con el rombo: `B◆ · B5`. |
| `tipo` | `respuesta` (el valor por defecto), `seguimiento`, `confrontacion`, `fallida`, `testigo`, `comodin`, `aviso`, `prensa`, `pista` o `cierre`. Cambia el color de la banda. Se puede poner en el grupo para todas sus tarjetas. |
| `pregunta` | Lo que preguntó el equipo, en cursiva arriba. |
| `pregunta_menu` | Otra redacción para el menú del kit, si hace falta. |
| `respuesta` | El texto principal. Máximo 420 caracteres: más no cabe en 63 × 88 mm. |
| `aclaracion` | Una línea chica después de la respuesta ("No se cobra ficha"). |
| `titular` | Un titular grande antes del texto (lo usan las de prensa). |
| `quien` | Lo que va a la derecha del código. Si falta, se arma con el grupo. |
| `adjunta` | Uno o varios códigos de prueba que se entregan con la tarjeta. |
| `seguimiento` | Uno o varios códigos de preguntas que la tarjeta habilita. |
| `pie` | Una línea libre al final. |
| `menu` | `true` para que la pregunta salga en el menú del kit. |
| `personaje` | Si la tarjeta es de otro personaje que el del grupo. |

Las de tipo `aviso`, `prensa`, `pista` y `cierre` salen en un pliego aparte al final, porque se usan en otro momento del juego. El exportador valida que cada `adjunta` exista en el expediente y avisa si una respuesta pasa de 420 caracteres. Si al imprimir una tarjeta no cabe, achica la letra hasta 8,5 pt; si ni así entra, la marca con un borde rojo y lo dice en la consola.

## Hojas: kit, expediente y guía

Cada archivo `.md` es una hoja. Arriba lleva un encabezado YAML entre `---` y abajo el contenido:

```markdown
---
codigo: E01
institucion: Policía de Investigaciones de Chile
descripcion: Brigada de Homicidios Temuco · Parte policial
titulo: Parte N° 4471 · Hallazgo de cadáver
---

**Matías Ferrada Soto**, 38 años, corredor de propiedades…
```

Las hojas del kit y de la guía se ordenan por nombre de archivo (`01-mision.md`, `02-menu.md`…). Las del expediente, por las secciones de `caso.yaml`.

| Campo | Para qué |
|---|---|
| `codigo` | El código de la prueba, en el recuadro rojo de arriba a la derecha. |
| `institucion` | Primera línea del membrete, en mayúsculas. |
| `descripcion` | Segunda línea del membrete. |
| `titulo` | El título grande de la hoja. |
| `etiqueta` | Una etiqueta en el lugar del código (la guía usa "Solo director"). |
| `equipo` | `true` para poner "Equipo: ______" (viene así en el kit). |
| `logo` | `true` para el wordmark de Open Case en el membrete (viene así en el kit y la guía). |
| `reservada` | `true` para la franja roja de material reservado (viene así en la guía). |
| `sello` | Un sello en la esquina: `sello: Confidencial` o `sello: {texto: Anulado, color: tinta}`. |
| `aviso` | `true` para la franja ámbar de los avisos de la Fiscalía. |
| `vieja` | `true` para papel envejecido (cartas, documentos antiguos). |

### El contenido

El cuerpo es Markdown común: párrafos, **negrita**, *cursiva*, listas, `### subtítulos` y tablas. Además:

- `==texto==` marca con resaltador.
- `` `E01` `` escribe un código con la letra de los códigos.
- `[verdad]`, `[mentira]`, `[clave]`, `[pista falsa]`, `[adjunta]`, `[diligencia]` y `[pendiente]` son pastillas de colores para la guía del director.
- `{.pequeno}` en la línea siguiente a un párrafo, sin línea en blanco entre medio, lo deja en letra chica.
- `![pie](diagramas/croquis.svg)` inserta una imagen; si es SVG queda dentro de la hoja y usa las fuentes del sistema de diseño.

### Bloques

Para lo que no es texto corrido se usan bloques entre tres comillas invertidas con el nombre del bloque. Los que llevan datos se escriben en YAML:

````markdown
```meta
Fecha y hora del parte: Sábado 31-10-2026, 07:42
Lugar: Parcela El Arrayán, Camino Los Copihues km 3,2
```
````

Un detalle de YAML que conviene saber: si un texto tiene `: `, `#` o empieza con comillas, ponlo entre comillas simples o usa `>-` para escribirlo en varias líneas. El lector del exportador no convierte horas como `22:30` ni fechas: quedan tal como las escribiste.

**Documentos**

| Bloque | Qué dibuja | Contenido |
|---|---|---|
| `meta` | La grilla de datos del encabezado de un parte | `Rótulo: valor`, uno por línea |
| `firma` | Firmas al pie | Lista de `{trazo: I. Painemal, rotulo: Comisario a cargo}` o textos sueltos |
| `declaracion` | Texto de declaración, en máquina de escribir | Texto libre, respeta los saltos de línea |
| `cita` | Una cita destacada | Texto libre |
| `manuscrito` | Letra a mano. Argumento opcional: `libreta`, `garabato`, `lapiz`, `carta`, `sin-lineas` | Texto libre |
| `postit` | Una nota adhesiva | Texto libre |
| `plumon` | Letra de plumón, una línea por renglón | Texto libre |
| `mono` | Un bloque en letra de máquina (registros, listados) | Markdown |
| `pequeno` | Un bloque en letra chica | Markdown |
| `tabla` | Una tabla Markdown con variante: `control`, `trabajo`, `puntaje`, `compacta`, `angosta` | Tabla Markdown |
| `sello` | Un sello de goma. Argumento: `tinta`, `laton`, `bosque`, `grande` | El texto del sello |
| `bolsa` | Etiqueta de bolsa de evidencia | `numero:` y `campos:` |
| `prensa` | Recorte de diario | `medio:`, `fecha:`, `titular:`, `cuerpo:` |
| `correo` | Un correo impreso | `de:`, `para:`, `cc:`, `fecha:`, `asunto:`, `cuerpo:`, `adjuntos:` |
| `boleta` | Una boleta o ticket | Lista de `[ítem, monto]`, `{centro: texto}`, `{total: [Total, $12.990]}` o `---` |

**Fotos, cámaras y dibujos**

| Bloque | Qué dibuja | Contenido |
|---|---|---|
| `fotos` | Fotos con su pie. Argumento opcional: `2 columnas`, `3 columnas` | Lista de `imagen:`, `titulo:`, `texto:`, `alt:`, `rotulo:` |
| `cctv` | Cuadros de cámara con la sobreimpresión | Lista de `imagen:`, `osd:`, `osd_der:`, `titulo:`, `texto:` |
| `imagen` | Una imagen suelta | `imagen:`, `pie:`, `ancho:` (por ejemplo `60%`), `alt:` |
| `svg` | Un dibujo SVG del caso | La ruta en el argumento: ` ```svg diagramas/e05.svg ``` ` |
| `leyenda` | Leyenda de colores de un croquis | `color: texto` |

**Pantallas**

| Bloque | Qué dibuja | Contenido |
|---|---|---|
| `celulares` (o `chat`) | Uno o varios celulares | Lista de celulares con `barra:`, `sub:` y uno de `chat:`, `llamadas:` o `app:` |
| `videos` | Cuadros de video o transmisiones | Lista de `imagen:`, `texto:`, `pie:`, `reloj:`, `en_vivo:`, `comentarios:` |
| `posts` (o `publicaciones`) | Publicaciones de redes | Lista de `usuario:`, `imagen:` o `historia:`, `texto:`, `meta:` |

Un chat es una lista de mensajes. Cada mensaje necesita hora, y un texto suelto en la lista es un separador de día:

```yaml
- barra: Vecinos Camino Los Copihues
  sub: 34 participantes
  chat:
    - 28 de octubre
    - de: Hernán Carrasco
      hora: "21:02"
      texto: Me robaron otra oveja.
    - de: Matías
      hora: "23:18"
      borrado: true          # sale como "Se eliminó este mensaje"
    - yo: true               # mensaje propio, a la derecha
      hora: "23:20"
      texto: ¿Alguien vio algo?
```

También se puede escribir un mensaje en una línea, `{de: Rosa, hora: "21:04", texto: "Sí, yo"}`, pero entonces el texto va entre comillas: dentro de las llaves, las comas y los signos de pregunta confunden a YAML.

**Guía del director**

| Bloque | Qué dibuja | Contenido |
|---|---|---|
| `nota`, `nota-ok`, `nota-aviso` | Recuadros de nota neutra, verde o ámbar. Argumento: el rótulo | Markdown |
| `guion` | Lo que el director lee en voz alta. Argumento opcional: el rótulo | Texto libre |
| `pasos` | Pasos numerados | Lista de `titulo:` y `texto:` |

**Hojas de trabajo del kit**

| Bloque | Qué dibuja | Contenido |
|---|---|---|
| `campos` | Renglones o cajas para escribir | Lista de `rotulo:`, `tipo: caja` y `alto:` (o solo el rótulo) |
| `tabla-trabajo` | Una tabla vacía para llenar | `columnas:`, `filas:`, `alto:`, `horario: true` para la línea de tiempo |
| `casillas` | Casillas para tachar fichas. Argumento opcional: cuántas | Nada; por defecto usa `fichas_por_equipo` |
| `menu` | El menú de preguntas, armado con `personajes.yaml` y las tarjetas con `menu: true` | Nada |
| `html` | HTML tal cual, para casos raros | HTML |

Si escribes un bloque que no existe, el exportador se detiene y te dice cuáles hay.

## Ahorro de tinta

Por defecto los PDF salen sin fondos: hojas blancas, sin el gris de los encabezados de tabla ni el relleno de las notas, los celulares o las fichas. El color queda donde significa algo: las bandas de las tarjetas, los códigos, los sellos, los anillos de las fichas, los filetes y los textos. Imprimir los fondos gasta mucha tinta y no ayuda a jugar.

Para la versión a todo color, por ejemplo para una imprenta o para mirarlo en pantalla:

```
python exportar.py casos/mi-caso --color
```

Si un caso siempre se imprime a color, pon `ahorro_de_tinta: false` en su `caso.yaml`. En ese caso, `--ahorro` vuelve a forzar el modo sin fondos. Las fotos se imprimen igual en los dos modos, y las imágenes para chat (`--imagenes`) salen siempre a color, porque no se imprimen.

## Estilos propios de un caso

Si un caso necesita algo que el sistema de diseño no trae, crea `estilos.css` en su carpeta. Se carga después de todo lo demás. Úsalo poco: lo que sirva para más de un caso debería ir a `diseno/open-case.css`.
