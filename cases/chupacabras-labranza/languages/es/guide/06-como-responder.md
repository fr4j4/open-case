---
institution: 6 · Cómo responder
description: Qué entregar ante cada código
title: Tabla de respuestas
pages: 6
---

[true] dice la verdad[false] miente para proteger su secreto[key] pista importante[attached] entrega un documento
{.small}

### Preguntas a sospechosos (1 ficha)

| Código | Qué entregar | Nota para ti |
|---|---|---|
| `B1` | Tarjeta B1 + E30 | [false] [attached] Dice que estuvo en su depto y muestra la boleta del delivery (E30, verdadera: 21:40). Nombra al conserje, así que desbloquea al testigo Luis Riquelme (L1). Trae el seguimiento B1+. |
| `B2` | Tarjeta B2 | [true] Socio solo "de palabra". |
| `B3` | Tarjeta B3 | [false] Dice que Matías lo llamó. E13a muestra que la llamada la hizo Benjamín. Trae el seguimiento B3+ (los $40 millones). |
| `B4` | Tarjeta B4 | [true] Empuja hacia Hernán y Toto. El lapsus ("quién le *pegaría* así") está en su declaración escrita DEC·B, de las 11:20; la autopsia es de las 14:30. |
| `H1` | Tarjeta H1 | [true] El comprobante del hospital (E20) sale con DG11 hospital. |
| `H2 · H3` | Tarjetas H2 y H3 | [true] H2 trae el seguimiento H2+ (los papeles: se pone nervioso). |
| `H4` | Tarjeta H4 | [false] Firmó una promesa de venta (E25·b) y quiso arrepentirse (E13b). |
| `J1` | Tarjeta J1 | [true] Ofrece el live; las capturas (E08) salen con J2 o con DG12 de Javiera (E29·J). |
| `J2 · J4` | Tarjetas J2 + E08 y J4 | [true] [attached] [key] J2 entrega el live (E08), igual que DG12 de Javiera (E29·J + E08). Sobre las luces, no sabe que eran un dron. |
| `J3` | Tarjeta J3 (incluye los DMs) | [key] Para el bonus: @vecino_asustado_lab es Matías (E13c). Trae el seguimiento J3+. |
| `P1` | Tarjeta P1 | [true] Las historias (E23) las entrega Fernanda (F1). E23 también trae la story de las 21:55. |
| `P2 · P3` | Tarjetas P2 y P3 | [false] Estuvo en El Arrayán de 21:00 a 21:50, más o menos. P2 trae el seguimiento P2+ (la llamada de las 18:05). |
| `P4` | Tarjeta P4 | [false] Dice que nadie escribe en el grupo; leyó el mensaje de las 22:15 (E29·P, F1). Del seguro (E24) no sabe nada y ya había caducado. |
| `T1` | Tarjeta T1 | [true] Las historias de la fiesta (E21) las entrega Maca (M1). |
| `T2` | Tarjeta T2 | [true] |
| `T3` | Tarjeta T3 | [false] |
| `T4` | Tarjeta T4 | [key] Algo desapareció el martes. Trae el seguimiento T4+ (era una horqueta). |
| `C1` | Tarjeta C1 | [true] La ficha y la cámara de la clínica (E22) salen con DG11 clínica o con C6. |
| `C2` | Tarjeta C2 + E10 | [false] [attached] Es el informe maquillado. |
| `C3` | Tarjeta C3 | [false] Recibió $800.000. Trae el seguimiento C3+. |
| `C4` | Tarjeta C4 | [key] Insinúa que no es un perro. |

<!-- La tabla sale de las tarjetas de seguimiento de cards.yaml (pregunta, follow_up, unlocked_by y guide_note). -->
```follow-ups
```

<!-- La tabla sale de las reglas opens_with de las tarjetas de confrontación de cards.yaml (qué prueba abre cada una y cuál gana). -->
```confrontations
```

Una confrontación entrega una sola tarjeta. Si lo que muestran sirve para varias, entrega la de la combinación más específica (por ejemplo, E13b junto con T5 abre B11, no B9). Las otras se consiguen con otra confrontación. Si muestran E29·B, pregúntales qué quieren señalar: la lectura del mensaje y la llamada abren B7; la búsqueda del barro abre B13. Si muestran E19·B, igual: la pintura blanca de las suelas abre B13; la boleta del Copec abre B8.
{.small}

<!-- La tabla sale de las tarjetas de testigo de cards.yaml (who, appears_in, attach y guide_note); aquí solo va la fila de los demás nombres. -->
```witnesses
others:
  names: Jorge P8, la Dra. Ulloa, M. Fuentealba, el encargado del Copec u otro nombre del material
  appears_in: [E04, E06, E12, E28]
  card: NADA QUE APORTAR
```

<!-- Las diligencias salen de procedures.yaml, con sus textos en languages/es/procedures.yaml. -->
```procedure-answers
```

### Preguntas fuera del menú

- Si te preguntan algo directo, como "¿había cámaras?", responde solo con lo que dice el material: "No, la parcela no tiene cámaras" (E01).
- Si preguntan por alguien que no aparece en el material, responde: "No hay registro de esa persona en la investigación".
- Cualquier pregunta fuera del menú que sí tenga respuesta en el material cuesta 1 ficha, igual que las del menú.
- Si piden algo que es obvio dentro de la ficción, como "¿Benjamín tiene vehículo?", contesta sí o no sin cobrar. El tipo, el color y la patente solo salen con DG5 o con L1, porque son parte del camino del vehículo.
