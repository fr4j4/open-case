# Redacción y códigos

## Nomenclatura

| Qué | Forma | Ejemplos |
|---|---|---|
| Prueba | `E` + dos dígitos, letra minúscula si se divide, `·` + letra del sospechoso si es específica | `E01`, `E13b`, `E17·B` |
| Declaración | `DEC · ` + letra | `DEC · B` |
| Sospechoso | Una letra única por persona, la inicial del nombre si no se repite | B, H, J, P, T, C |
| Pregunta | letra + número | `B1`…`B4` |
| Confrontación | letra + `◆`; la tarjeta obtenida lleva número | `B◆` → `B5`, `B6` |
| Seguimiento | código + `+` | `B3+` |
| Fallida | letra + `✕` | `B✕` |
| Diligencia | `DG` + número, letra opcional | `DG2`, `DG2W` |
| Testigo | `R1`, `TESTIGO`, `PER1` | según el menú |
| Aviso, prensa, pista, cierre | palabra + número | `Aviso 1`, `Prensa`, `Pista`, `Cierre` |
| Sobre | `Sobre` + número en orden de apertura | `Sobre 1` |
| Equipo | `Equipo A` … `Equipo D` (de 2 a 4 equipos) | nunca colores como nombre |

El punto medio `·` separa partes de un código y de un membrete ("Brigada de Homicidios · Parte policial"). Las comillas son dobles rectas o tipográficas, pero iguales en todo el caso. Los puntos suspensivos van como un carácter (…).

## Tono por tipo de documento

- **Oficial** (partes, informes): tercera persona, frases cortas, sin adjetivos, sin exclamaciones. "Dos perforaciones circulares de 4 mm, separadas por 4,5 cm entre centros."
- **Declaración**: primera persona, oralidad contenida, puede mentir. Cuatro a seis párrafos. "Yo no lo maté, y quiero que eso quede escrito."
- **Tarjeta de respuesta**: lo que el sospechoso dice, entre comillas, en su voz; acotaciones entre paréntesis solo en confrontaciones. 420 caracteres.
- **Chat**: como escribe esa persona: con o sin tildes, con sus muletillas, con los emojis que usaría. Un personaje mayor escribe distinto que uno de 24.
- **Kit y avisos**: la voz del juego, en "ustedes", directa. "Tienen 16 fichas. Cada pregunta cuesta una."
- **Guía del director**: en "tú", práctica, sin adornos: "Entrega E06 a todos los equipos. Cobra las fichas."

## Verdad y mentira

Los peritajes y documentos oficiales no mienten nunca; los sospechosos sí. Esta regla es de diseño además de juego: por eso lo oficial va en `sans` y `mono`, y lo declarado va en `maquina` y entre comillas. No se rompe ni para una pista falsa: la pista falsa es algo que alguien **eligió mostrar**, no un documento falso.

## Localización

- La localidad vive en los nombres (instituciones, calles, comidas, apellidos) y en los formatos locales de fecha, moneda y patente. Un caso en otro país cambia esos nombres y nada más.
- Las instituciones pueden ser reales (PDI, Fiscalía, SML) si solo cumplen su función normal; las empresas, medios y personas son siempre ficticias.
- Para traducir un caso al inglés se traducen los textos y los rótulos (`Equipo A` → `Team A`, `Sobre 1` → `Envelope 1`, `Pista` → `Hint`), se conservan los códigos (`E01`, `B◆`) y la marca, y se cambia el formato de papel a carta o A4 según el país. Los componentes no cambian.

## Accesibilidad

Todo texto cumple 4,5:1 sobre su fondo (3:1 para rótulos grandes y marcos). Nada se distingue solo por color: las tarjetas tienen banda **y** código, los equipos tienen color **y** letra, las pastillas tienen color **y** palabra. Cuerpo impreso mínimo 10,5 pt; en tarjetas 9,5 pt. Las imágenes llevan texto alternativo igual a su pie.
