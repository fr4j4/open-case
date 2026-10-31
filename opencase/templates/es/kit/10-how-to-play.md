---
place: anchor
join: true
---
{% import "_macros.j2" as m %}
{% set alibi = f.alibi_tokens_per_team %}

### Cómo se juega

Parten con **{{ f.tokens_per_team }} fichas**{% if alibi %}, **{{ alibi }} fichas de coartada**{% endif %} y el **sobre 1**, con lo que se sabe y las declaraciones de los {{ n_suspects }} sospechosos. Son cuatro fases, entre {{ f.session_minutes[0] }} y {{ f.session_minutes[1] }} minutos en total:

```table compact
| Fase | Qué pasa |
|---|---|
| **1 · Escena** · {{ f.phases.scene }} min | El director lee el parte y entrega el sobre 1. Lean y anoten: aún no se pide nada. |
| **2 · Investigación** · {{ f.phases.investigation }} min | {{ "Abran el sobre 2. " if envelopes|length > 1 else "" }}Pidan preguntas y diligencias con una solicitud y sus fichas. El director lee los avisos. |
| **3 · Acusación** · {{ f.phases.accusation }} min | {{ f.accusation_writing }} min para llenar las hojas de acusación y de descarte, que el director recoge antes de que alguien exponga. Luego {{ f.pitch_minutes }} min de exposición por equipo (empieza el que tenga más fichas). |
| **4 · Cierre** | El director cuenta los puntos, lee la confesión si la consiguieron y cierra la historia. |
```

### Palabras del juego

```small
- **Pregunta:** lo que le preguntan a una persona. Cuesta {{ m.tok(f.costs.question) }} y se pide con un código del menú (por ejemplo, la letra de un sospechoso y un número).
- **Diligencia:** un pedido a la policía o a un laboratorio, como revisar un teléfono, pedir cámaras o peritar un objeto. Hay que escribir qué buscan y por qué. Cuesta lo que indica el menú.
- **Solicitud:** el papel donde anotan el código y por qué lo piden. Se entrega al director con las fichas que cuesta, y él les da la tarjeta de respuesta o la prueba.
- **Coartada:** dónde dice una persona que estaba cuando ocurrió el crimen y qué permite comprobarlo.{{ " Las **fichas de coartada** (borde punteado) solo sirven para eso, y las que sobran no suman." if alibi else "" }}
- **Códigos de las pruebas:** "E" y un número (E01, E02…) son las pruebas del expediente del director y "DEC" las declaraciones. Lo del sobre 1 ya lo tienen; el resto se pide con una pregunta o diligencia.
```
