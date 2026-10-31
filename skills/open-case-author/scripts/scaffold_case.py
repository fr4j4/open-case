#!/usr/bin/env python3
"""Creates the folder of a new Open Case case with placeholder files that already pass
`python export.py <case> --check`, so you can fill them in from the bible.

    python scaffold_case.py cases/<slug> --lang es --title "Mi caso" --suspects B,H,J,P [--tokens 16] [--paper letter]

Every placeholder is the word TODO; `grep -rn TODO cases/<slug>` lists what is left.
Standard library only. Refuses to overwrite an existing folder.
"""
import argparse
import sys
from pathlib import Path

KIT = [
    ("01-mission.md", "Orden de investigar", "TODO · fecha", "Misión", "TODO: la historia en dos párrafos. Debajo, el motor agrega 'Cómo se juega', y después de esta hoja las reglas, el puntaje y el resto de lo fijo del juego (opencase/templates)."),
    ("02-menu.md", "Menú de preguntas", "Cada pregunta cuesta 1 ficha", "Sospechosos", "TODO: una línea de instrucción.\n{.small}\n\n```menu\n```\n\n## Testigos\n\nTODO: tabla de testigos con códigos (la regla de los testigos y la de los seguimientos las pone el motor)."),
    ("03-procedures.md", "Menú de diligencias", "Indiquen qué buscan y por qué", "Diligencias", "| Código | Diligencia | Fichas |\n|---|---|---|\n| `DG1` | TODO | 1 |\n\n### Control de fichas\n\nTachen una casilla por cada ficha gastada.\n{.small}\n\n```checkboxes\n```"),
    ("04-timeline.md", "Hoja de trabajo", "Línea de tiempo · TODO noche", "¿Dónde estaba cada uno?", "Anoten en cada casilla lo que sepan y la prueba que lo respalda.\n{.small}\n\n```work-table\nschedule: true\ncolumns: [Persona, \"21:00\", \"22:00\", \"23:00\", \"00:00\"]\nrows:\n  - TODO víctima\n  - TODO sospechosos, uno por fila\n  - Otros / vehículos\n  - Clima\n```"),
    ("05-accusation.md", "Hoja de acusación", "Se entrega al director al final", "Nuestra teoría del caso", "```fields\n- label: 1. ¿Quién? TODO\n- label: 2. ¿Cómo?\n  type: box\n- label: 3. ¿Por qué?\n  type: box\n- label: 4. ¿Entre qué horas?\n- label: 5. Las tres pruebas más fuertes (códigos)\n- label: 6. Contradicciones del culpable\n- label: \"7. Pistas falsas explicadas: pista → prueba\"\n  type: box\n```"),
    ("06-discard.md", "Hoja de descarte", "Se entrega junto con la acusación", "¿Por qué no fue cada uno?", "```discard-rule\n```\n\n```work-table\ncolumns: [Sospechoso, Dónde estaba en el momento del crimen, Pruebas (códigos)]\nrows:\n  - TODO un sospechoso por fila\n```"),
]

GUIDE = [
    ("01-preparation.md", "1 · Preparación", "El día antes y 20 minutos antes", "Qué imprimir y qué preparar", "TODO: tabla de impresión (material, copias, notas).\n\n### Lo propio de este caso\n\n- TODO solo lo que cambia en este caso. Las fases, antes de que lleguen, la regla de oro y la equidad las agrega el motor después de esta hoja."),
    ("02-solution.md", "2 · La solución en una página", "Léela antes de jugar", "", "```note Lo que pasó\nTODO: quién, cómo, cuándo, dónde.\n```\n\n### Por qué\n\nTODO\n\n### El detalle que lo delata\n\nTODO\n\n### Lo que oculta cada sospechoso\n\n| Sospechoso | Secreto | Coartada (verdadera) |\n|---|---|---|\n| TODO | | |"),
    ("03-script.md", "3 · Guion de la sesión", "El parte, los avisos y las pistas", "Para leer en voz alta", "### Para leer al comenzar\n\n```script\nTODO\n```\n\n```notices\n```\n\n### Si un equipo se estanca\n\n```hints\n```"),
    ("04-responses.md", "4 · Cómo responder", "Qué entregar ante cada código", "Tabla de respuestas", "[true] dice la verdad[false] miente[key] pista importante[attached] entrega un documento\n{.small}\n\n### Preguntas (1 ficha)\n\n| Código | Qué entregar | Nota para ti |\n|---|---|---|\n| TODO | | |\n\n### Confrontaciones ◆\n\n| Código | Si muestran… | Entrega |\n|---|---|---|\n| TODO | | |\n\n### Testigos\n\n| Testigo | Aparece en | Entrega |\n|---|---|---|\n| TODO | | |\n\n### Diligencias\n\n| Código | Si piden… | Entrega |\n|---|---|---|\n| TODO | | |"),
    ("05-control.md", "5 · Hoja de control", "Marca cada entrega · imprime 1 copia", "Qué tiene cada equipo", "```control\nrows:\n  - [TODO, TODO qué es, 1]\n```"),
    ("06-evaluation.md", "6 · Evaluar la acusación", "Qué cuenta como correcto", "Pauta de corrección", "| Punto | Pts | Se acepta si… |\n|---|---|---|\n| TODO | | |\n\n### Hoja de descarte\n\n| Inocente | Pruebas que lo ubican lejos |\n|---|---|\n| TODO | |\n\n### Pistas falsas\n\n| Pista falsa | Pruebas que la explican |\n|---|---|\n| TODO | |\n\n```note-ok\nTODO: cuándo confiesa.\n```\n\n```score-sheet\n```"),
    ("07-confession.md", "7 · Confesión y cierre", "Para leer en voz alta", "Confesión", "```script\nTODO confesión en primera persona.\n```\n\n### Cierre\n\n```script\nTODO\n```"),
]


def sheet(institution, description, title, body, **extra):
    fm = [f"institution: {institution}", f"description: {description}"]
    if title:
        fm.append(f"title: {title}")
    for k, v in extra.items():
        fm.append(f"{k}: {v}")
    return "---\n" + "\n".join(fm) + "\n---\n\n" + body + "\n"


def main():
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    p.add_argument("case", help="folder to create, for example cases/mi-caso")
    p.add_argument("--lang", default="es")
    p.add_argument("--title", default="TODO título del caso")
    p.add_argument("--suspects", default="A,B,C,D", help="letters, comma separated")
    p.add_argument("--tokens", type=int, default=16)
    p.add_argument("--paper", default="letter", choices=["letter", "a4"])
    a = p.parse_args()

    root = Path(a.case)
    if root.exists():
        print(f"Error: {root} already exists; refusing to overwrite.", file=sys.stderr)
        return 2
    letters = [s.strip().upper() for s in a.suspects.split(",") if s.strip()]
    if len(set(letters)) != len(letters):
        print("Error: suspect letters must be unique.", file=sys.stderr)
        return 2
    lang = root / "languages" / a.lang
    for d in (root / "photos", root / "diagrams", lang / "kit", lang / "dossier", lang / "guide"):
        d.mkdir(parents=True)

    decs = ", ".join(f"DEC-{l}" for l in letters)
    (root / "case.yaml").write_text(f"""# {a.title}: neutral data of the case. Format: docs/case-format.md
brand: Open Case
paper: {a.paper}

base_language: {a.lang}
languages: [{a.lang}]

# Hidden from the website until the case has been played with real teams. Remove this line (or set it
# to true) and fill `site:` and the language `summary` once it is validated. See docs/case-format.md.
published: false

teams: [A, B]
tokens_per_team: {a.tokens}
players_per_team: 7
# The other figures of the game (minutes, notices, hints, score) are the engine's (opencase/defaults.yaml);
# write one here, with the same key, to change it for this case. The rules come from opencase/templates.

brand_footer: [kit, guide, dossier]

dossier:
  sections:
    - id: start
      envelope: 1
      items: [E01]
    - id: statements
      envelope: 1
      items: [{decs}]
    - id: investigation
      envelope: 2
      items: []
    - id: with-answer
      items: []
    - id: procedures
      items: []
    - id: notices
      items: []
""", encoding="utf-8")

    (lang / "case.yaml").write_text(f"""title: {a.title}
version: Versión 0.1 · TODO mes y año
tagline: Todos mienten. Las pruebas no.

badge:
  title: Detective
  unit: [TODO unidad, TODO ciudad]

kit:
  description: Una copia por equipo. Reglas, menú y hojas de trabajo. No incluye respuestas ni pruebas.
  cover_note: Una copia por equipo. No incluye respuestas ni pruebas.

guide:
  description: Todo lo necesario para dirigir el caso.
  cover_note: Contiene la solución. No la muestres ni la mandes a los equipos.

dossier:
  title: Expediente TODO
  kicker: TODO institución
  description: TODO resumen del caso en una línea.
  printed_description: TODO índice de pruebas para el director.
  sections:
    start: {{title: Sobre 1, note: Se entrega a ambos equipos al comenzar}}
    statements: {{title: Declaraciones iniciales, note: Van en el sobre 1 · gratis}}
    investigation: {{title: Comienzo de la investigación, note: Sobre 2 · gratis para ambos equipos}}
    with-answer: {{title: Pruebas que se entregan junto con una respuesta, note: Solo al equipo que preguntó}}
    procedures: {{title: Diligencias, note: Se entregan al equipo que paga la ficha}}
    notices: {{title: Avisos, note: El director los lee a todos a la vez}}

envelope_labels:
  - number: 1
    when: se entrega al comenzar
    description: Lo que sabemos hasta ahora. No incluye respuestas.
    contents: [E01 TODO, "DEC · {', '.join(letters)}", Kit del equipo]
    token_footer: true
""", encoding="utf-8")

    susp = "suspects:\n"
    for l in letters:
        susp += f"""  - letter: {l}
    name: TODO nombre {l}
    role: TODO rol
    facts:
      Edad: TODO
      Oficio: TODO
      Relación: TODO
      Vive en: TODO
      Descripción: TODO
"""
    (lang / "suspects.yaml").write_text(susp, encoding="utf-8")

    cards = "groups:\n"
    for l in letters:
        cards += f"""  - title: TODO nombre {l}
    suspect: {l}
    who: TODO nombre {l}
    short: TODO
    cards:
      - code: {l}1
        menu: true
        question: ¿Dónde estuvo esa noche?
        answer: '"TODO respuesta en su voz, 420 caracteres como máximo."'
      - code: {l}2
        type: confrontation
        question: '"TODO acusación que se le muestra."'
        answer: '"TODO nueva mentira o admisión parcial."'
      - code: {l}✕
        type: failed
        answer: '"TODO qué dice cuando la prueba no alcanza, sin notas del director."'
"""
    cards += """  - title: Comodines
    cards:
      - code: ◆
        type: wildcard
        who: Confrontación fallida
        answer: '"Eso no prueba nada, detective."'
      - code: TESTIGO
        type: wildcard
        who: Testigo no disponible
        answer: Esa persona todavía no aparece en su material. No se cobra la ficha.
  - title: Avisos
    cards:
      - code: AVISO 1
        type: notice
        answer: TODO texto del aviso.
  - title: Pistas
    cards:
      - code: PISTA 1
        type: hint
        answer: TODO pregunta que orienta sin resolver.
  - title: Cierre
    cards:
      - code: CIERRE
        type: closing
        who: TODO
        answer: TODO una línea de cierre.
"""
    (lang / "cards.yaml").write_text(cards, encoding="utf-8")

    for name, inst, desc, title, body in KIT:
        (lang / "kit" / name).write_text(sheet(inst, desc, title, body), encoding="utf-8")
    for name, inst, desc, title, body in GUIDE:
        (lang / "guide" / name).write_text(sheet(inst, desc, title, body), encoding="utf-8")

    (lang / "dossier" / "E01.md").write_text(sheet(
        "TODO Policía", "TODO unidad · Parte policial", "Parte N° TODO · Hallazgo",
        "```meta\nFecha y hora del parte: TODO\nLugar: TODO\nDenunciante: TODO\n```\n\n### Víctima\n\nTODO\n\n### Relato\n\nTODO\n\n### Observaciones en el sitio\n\n```mono\n- TODO\n```\n\n```signature\n- {scrawl: TODO, label: Comisario a cargo}\n```",
        code="E01"), encoding="utf-8")
    for l in letters:
        (lang / "dossier" / f"DEC-{l}.md").write_text(sheet(
            "TODO unidad", "Declaración voluntaria · TODO fecha y hora", f"TODO nombre {l}",
            "```meta\nEdad · oficio: TODO\nRelación: TODO\nDomicilio: TODO\nDescripción: TODO\n```\n\n```statement\nTODO cuatro a seis párrafos en primera persona. Una mentira concreta entre verdades comprobables.\n```\n\n```signature\n- {scrawl: TODO, label: Firma del declarante}\n- Detective a cargo\n```",
            code=f'"DEC · {l}"'), encoding="utf-8")
    (root / "diagrams" / ".gitkeep").write_text("", encoding="utf-8")
    (root / "photos" / ".gitkeep").write_text("", encoding="utf-8")

    print(f"Created {root}/ with {len(letters)} suspects. Next: fill the TODOs from the bible, then "
          f"python export.py {root} --check")
    return 0


if __name__ == "__main__":
    sys.exit(main())
