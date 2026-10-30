# Catálogo de artefactos

Cada pieza de un caso es uno de estos tipos. La columna "componente" nombra el componente de esta guía (con su ejemplo visual); "código" dice cómo se identifica; "quién la emite" recuerda que los documentos del caso hablan en la voz de una institución ficticia; la marca solo va en el pie de la hoja (`.oc-hoja__marca`).

## Documentos del caso (hojas carta)

| Artefacto | Componente | Código | Tipografía | Quién la emite | Campos obligatorios |
|---|---|---|---|---|---|
| Parte policial | `Hoja` | `E01` | `sans` + `.oc-meta` | La policía ficticia | Fecha y hora, lugar, denunciante, relato, observaciones, funcionario a cargo |
| Informe pericial (autopsia, laboratorio, clima) | `Informe` | `E06`, `E07` | `sans`, tablas en `mono` | Servicio médico legal, laboratorio, estación | Perito, fecha, resultado principal, hallazgos, firma y plazo |
| Declaración | `Declaracion` | `DEC · B` | `maquina` | La unidad que la toma | Ficha de cinco campos, cuerpo en primera persona, firma del declarante |
| Registro o libro | `Registro` | `E14` | `mono` en tabla | Portería, banco, operador | Columnas fijas por tipo; 6 a 12 filas |
| Carta, póliza, contrato | `Carta` | `E24` | `sans`, cuerpo en `.oc-cita` | Empresa ficticia | Membrete de la empresa, fecha y lugar, destinatario, firma con cargo |
| Croquis o mapa | `Hoja` con SVG | `E05` | rótulos en `mono` | La policía ficticia | "Sin escala", norte, distancias clave, leyenda |
| Nota manuscrita | `Manuscrito` | `E11` | `manuscrita`, `garabato`, `cursiva` | Un personaje | Registro de escritura fijo por persona |
| Nota adhesiva, cartel | `Postit` | dentro de otra prueba | `garabato`, `plumon` | Un personaje | 1 a 3 líneas |
| Recorte de prensa | `Prensa` | `E__` o tarjeta | `prensa` | Medio ficticio | Medio, fecha, titular, cuerpo a dos columnas |
| Correo electrónico | `Correo` | `E__` | `pantalla` | Un personaje | De, Para, Fecha, Asunto, firma con cargo |

## Evidencia visual

| Artefacto | Componente | Código | Campos obligatorios |
|---|---|---|---|
| Set fotográfico | `FotoRotulada` | `E02` | Numeración "Foto N · título", vista general primero, testigo métrico en detalles, pie descriptivo |
| Captura de cámara o dron | `CapturaCCTV` | `E28` | Reloj con segundos y nombre de cámara sobreimpresos, pie sin interpretación |
| Objeto físico | `BolsaEvidencia` | `N° __ · E__` | Objeto, lugar, fecha y hora, quién lo recogió; rótulo a `plumon` |

## Pantallas

| Artefacto | Componente | Código | Campos obligatorios |
|---|---|---|---|
| Chat (grupo o 1:1) | `Chat` | `E04`, `E13b` | Barra con nombre del chat, pastillas de día, hora en cada mensaje, dueño del teléfono a la derecha, mensajes borrados marcados |
| Llamadas, calendario, app | `Llamadas` | `E13a` | Flechas de sentido, duración, orden cronológico inverso |
| Video en vivo | `Publicacion` (`.oc-video`) | `E08` | Distintivo EN VIVO, reloj, cita de lo que dice, 1 a 2 comentarios |
| Publicación | `Publicacion` (`.oc-post`) | `E03`, `E21` | Usuario, imagen cuadrada, pie, fecha relativa |
| Boleta, voucher, ticket | `Boleta` | `E30` | Razón social, fecha y hora con segundos, número, detalle, total, medio de pago |

## Material del juego (lleva la marca)

| Artefacto | Componente | Formato | Notas |
|---|---|---|---|
| Kit: misión y reglas, menú, diligencias | `Hoja` + `Membrete` con wordmark | Carta | Cuadro "Equipo: ____" en lugar de código |
| Hojas de trabajo (línea de tiempo, acusación, descarte, control de fichas) | `HojaTrabajo` | Carta | Campos en blanco, instrucciones en una frase |
| Tarjetas de respuesta, seguimiento, fallida | `TarjetaRespuesta` | 88 × 63 | Ver Norma de tarjetas |
| Tarjetas de confrontación | `TarjetaConfrontacion` | 88 × 63 | Banda `sello` |
| Avisos, prensa, pistas, cierre | `TarjetaAviso` | 88 × 63 | Se leen en voz alta |
| Tarjetas de sospechoso | `TarjetaSospechoso` | 63 × 88 | Retrato o silueta, cinco datos |
| Placas | `Placa` | 63 × 88 | Una por jugador, cuadro de equipo |
| Solicitudes | `Solicitud` | 88 × 63 | 30 por equipo |
| Etiquetas de sobre | `EtiquetaSobre` | 88 × 63 | Numeradas en orden de apertura |
| Fichas | `Ficha` | Ø 30 | 35 por hoja |
| Pliegos | `Pliego` | Carta | 8 tarjetas, pie con número de pliego |
| Guía del director | `Hoja --reservada`, `NotaDirector` | Carta | Franja roja, rótulo "Solo director", diagramas a todo el ancho |

## Para casos futuros

Antes de crear un tipo nuevo, comprueba que no sea una variante: un telegrama es una `Boleta` con otro membrete; un fax es un `Correo` en `termica`; un diario íntimo es `Manuscrito --carta` sobre `papel-viejo`; una ficha médica es un `Informe`; un mensaje de voz transcrito es un `Chat` con `__adjunto`. Si de verdad hace falta un tipo nuevo, se añade aquí con su componente y su ejemplo, y se respeta la regla de que el tipo de letra dice quién escribió.
