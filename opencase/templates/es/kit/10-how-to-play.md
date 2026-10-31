---
place: anchor
join: true
---
{% set alibi = f.alibi_tokens_per_team %}

### Cómo se juega

Parten con **{{ f.tokens_per_team }} fichas**{% if alibi %}, **{{ alibi }} fichas de coartada**{% endif %} y el **sobre 1**, con lo que se sabe hasta ahora y las declaraciones de los {{ n_suspects }} sospechosos. Son cuatro fases, entre {{ f.session_minutes[0] }} y {{ f.session_minutes[1] }} minutos en total:

```table compact
| Fase | Qué pasa |
|---|---|
| **1 · Escena** · {{ f.phases.scene }} min | El director lee el parte y entrega el sobre 1. Lean y anoten; todavía no se hacen preguntas ni diligencias. |
| **2 · Investigación** · {{ f.phases.investigation }} min | {{ "Abran el sobre 2. " if envelopes|length > 1 else "" }}Pidan preguntas y diligencias con una solicitud y una ficha. El director lee los avisos. |
| **3 · Acusación** · {{ f.phases.accusation }} min | {{ f.accusation_writing }} min para llenar las hojas de acusación y de descarte, que el director recoge antes de que alguien exponga. Luego {{ f.pitch_minutes }} min de exposición por equipo (empieza el que tenga más fichas). |
| **4 · Cierre** | El director cuenta los puntos, lee la confesión si la consiguieron y cierra la historia. |
```

### Palabras del juego

```small
- **Pregunta:** lo que le preguntan a una persona. Cuesta 1 ficha y se pide con un código del menú (por ejemplo, la letra de un sospechoso y un número).
- **Diligencia:** un pedido a la policía o a un laboratorio, como revisar un teléfono, pedir cámaras o peritar un objeto. Hay que escribir qué buscan y por qué. Cuesta lo que indica el menú.
- **Ficha:** lo que gastan para pedir algo. Cada equipo parte con {{ f.tokens_per_team }}.
- **Coartada:** dónde dice una persona que estaba cuando ocurrió el crimen y qué permite comprobarlo.
{% if alibi %}
- **Ficha de coartada** (borde punteado): solo sirve para comprobar dónde estaba una persona. Cada inocente descartado con coartada comprobada suma puntos; el que queda en blanco resta; las fichas de coartada que sobran no suman.
{% endif %}
- **Códigos de las pruebas:** "E" y un número (E01, E02…) numeran las pruebas del expediente del director y "DEC" las declaraciones. Lo que viene en el sobre 1 ya lo tienen; el resto se pide con una pregunta o una diligencia.
```
