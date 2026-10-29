<p align="center">
  <img src="assets/portada.svg" alt="Carpeta de expediente de Open Case con sello de confidencial" width="760">
</p>

Alguien miente. Los dos equipos tienen el mismo expediente, el mismo tiempo y las mismas preguntas posibles. Solo uno va a llegar primero al culpable.

**Open Case** es un formato para jugar casos policiales en grupo. Dos equipos investigan el mismo crimen y compiten entre sí. Una persona hace de director: es el comisario, interpreta a los sospechosos y sabe la verdad desde el principio.

No necesitas tablero ni aplicación. Basta con papel, una mesa y gente con ganas de discutir.

<p align="center">
  <img src="assets/cinta.svg" alt="Cinta policial" width="100%">
</p>

## Cómo se juega

Cada equipo recibe el expediente: qué pasó, quiénes estaban y las primeras pruebas. Desde ahí, investigan.

Investigar cuesta. Cada interrogatorio, cada prueba extra y cada careo con un sospechoso gasta recursos que no alcanzan para todo. Elegir bien a quién preguntar es la mitad del juego.

Al final, cada equipo acusa a alguien y tiene que demostrarlo con lo que encontró. Gana quien arma el caso más sólido, no quien grita más fuerte.

Una partida dura más o menos una hora, con equipos de cinco a siete personas. Cada caso ajusta esos números.

## Lo que hace bueno a un caso

Hay una sola solución, y se puede llegar a ella razonando. Ninguna prueba entrega al culpable por sí sola, pero todas juntas no dejan otra salida. Las pistas falsas confunden, aunque se pueden descartar. Y el director nunca tiene que improvisar la verdad, porque está escrita en su guía.

## Arma tu propio caso

<img src="assets/evidencia.svg" alt="Etiqueta de evidencia en blanco" width="340" align="right">

La idea es que cualquiera pueda escribir casos y ambientarlos donde quiera: su barrio, la oficina, un pueblo que no existe.

Para empezar te basta con:

1. **La verdad.** Qué pasó, quién fue, cómo y por qué. Escríbela antes que nada y no se la muestres a nadie.
2. **Una cronología.** Dónde estaba cada persona y a qué hora. Ahí aparecen las coartadas y las contradicciones.
3. **Sospechosos.** Varios con motivo u oportunidad. Si el culpable es el único raro de la lista, el caso dura cinco minutos.
4. **Pruebas.** Decide cuáles se entregan al inicio y cuáles hay que ganarse.
5. **Dos carpetas.** Una para los equipos, sin spoilers, y otra para el director, con todo.
6. **Una prueba antes de la real.** Juégalo con alguien. Los casos se arreglan jugándolos.

Cuando lo tengas, pásalo al formato de Open Case (está en [docs/formato-de-casos.md](docs/formato-de-casos.md)) y el exportador arma todo el material impreso. El caso de ejemplo sirve de plantilla: copia la carpeta y ve cambiando.

<br clear="right">

## Reglas de la casa

- Cualquier lugar sirve. Open Case no está atado a ninguna ciudad.
- Se escribe en español y se va a traducir al inglés, así que conviene no depender de modismos imposibles de traducir.
- Es policial, no de terror. La tensión viene de la deducción, no de los sustos.
- El material de los equipos nunca trae la solución.

## Imprimir un caso

Cada caso vive en una carpeta de texto: unos archivos YAML con los datos y una hoja Markdown por cada prueba, cada página del kit y cada página de la guía, más sus fotos. Un script lo convierte todo en PDF listos para imprimir, con el diseño de Open Case.

Necesitas Python 3.10 o más nuevo. La primera vez:

```
make instalar
```

Eso crea un entorno en `.venv`, instala las dependencias y descarga el Chromium con el que se arman los PDF. Después, cada vez que quieras exportar:

```
make exportar                               # el caso de ejemplo
make exportar CASO=casos/mi-caso            # otro caso
```

En Windows, o si no tienes `make`:

```
py -m venv .venv
.venv\Scripts\pip install -r requirements.txt
.venv\Scripts\python -m playwright install chromium
.venv\Scripts\python exportar.py casos\chupacabras-labranza
```

Si ya tienes Chrome o Edge instalado y no quieres bajar otro navegador, sáltate el `playwright install`: el exportador los busca solo. También puedes indicarle uno con la variable `OPENCASE_CHROMIUM`.

Los PDF quedan en `salida/<caso>/`, separados en dos carpetas:

- **equipos/** es lo que reciben los jugadores: el kit, los sobres, las tarjetas de sospechoso, las placas, las fichas, las solicitudes y las etiquetas de los sobres. Nada de esto trae la solución.
- **director/** es lo que no ven: la guía, el expediente completo con todas las pruebas, las tarjetas de respuesta y su reverso.

Imprime siempre al 100 %, sin "ajustar a la página". Las tarjetas miden 63 × 88 mm y las fichas 30 mm, y solo calzan con las líneas de corte si nadie las escala.

**Ahorro de tinta.** Por defecto los PDF salen sin fondos: hojas blancas y el color solo donde dice algo (bandas de tarjetas, códigos, sellos, filetes). Para la versión a todo color:

```
make color
python exportar.py casos/chupacabras-labranza --color
```

Si un caso se imprime siempre a color, pon `ahorro_de_tinta: false` en su `caso.yaml`.

Otras opciones útiles:

```
python exportar.py casos/mi-caso --revisar        # revisa el caso sin generar PDF
python exportar.py casos/mi-caso --solo kit,sobres
python exportar.py casos/mi-caso --imagenes       # además, un PNG por prueba para mandar por chat
python exportar.py --help
```

Cuando algo está mal escrito, el exportador se detiene y dice en qué archivo y en qué línea. Si una tarjeta no cabe o una hoja pasa a una segunda página, lo avisa al final.

## Estado

<img src="assets/sello-pendiente.svg" alt="Sello: diligencias pendientes" width="230" align="right">

El sistema de diseño está cerrado y el exportador funciona. Ya hay un caso completo, **El Chupacabras de Labranza**, listo para jugar. Sirve también como ejemplo de cómo se escribe uno.

Las imágenes de este README son provisionales.

<br clear="right">

## Cómo está ordenado el repo

```
open-case/
├── casos/
│   └── chupacabras-labranza/   el caso de ejemplo, en formato de texto
├── diseno/        sistema de diseño: CSS, colores, logos, fuentes y la guía de marca
├── docs/          el formato de los casos
├── opencase/      el exportador
├── herramientas/  scripts de mantenimiento (por ejemplo, bajar las fuentes)
├── exportar.py    el comando para exportar
└── Makefile
```

<p align="center">
  <img src="assets/cinta.svg" alt="Cinta policial" width="100%">
</p>
