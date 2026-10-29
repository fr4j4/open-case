"""Línea de comandos: python3 exportar.py casos/<caso> [opciones]"""
import argparse
import shutil
import sys
import time
from pathlib import Path

from .cargar import ErrorCaso, cargar_caso
from .documentos import PAPELES, documentos

LEEME = """{titulo}
Material generado por el exportador de Open Case ({fecha}).

equipos/   Lo que pueden ver los equipos. Sin spoilers.
  01_Kit_del_equipo        Una copia por equipo. Hojas carta en papel normal.
  02… (sobres)             Lo que reciben al comenzar. Una copia por equipo.
  10_Tarjetas_de_sospechosos, 11_Placas, 12_Fichas, 13_Solicitudes, 14_Etiquetas_de_sobre
                           Recortables en cartulina de 200 a 250 g.

director/  Solo para quien dirige. Nunca se entrega completo a un equipo.
  01_Guia_del_director     La solución, los diagramas, el guion y las pautas.
  02_Expediente_completo   Todas las pruebas, ordenadas por sección. Se entregan de a una.
  03_Tarjetas_de_respuesta Pliegos de 8 tarjetas. Una copia por equipo.
  04_Reverso_de_tarjetas   Opcional: imprímelo en el dorso de cada pliego.

Imprime siempre al 100 % ("tamaño real"), nunca "ajustar a la página": las tarjetas
deben medir 88 × 63 mm y las fichas 30 mm de diámetro.

{modo}
"""


def main(argv=None):
    p = argparse.ArgumentParser(prog="exportar", description="Exporta un caso de Open Case a PDF listos para imprimir.")
    p.add_argument("caso", help="carpeta del caso, por ejemplo casos/chupacabras-labranza")
    p.add_argument("--salida", default="salida", help="carpeta donde dejar los PDF (por defecto: salida/)")
    p.add_argument("--solo", help="exportar solo algunos documentos, separados por coma: kit, sobres, expediente, guia, "
                                  "tarjetas, reverso, sospechosos, placas, fichas, solicitudes, etiquetas. "
                                  "Ejemplo: --solo kit,sobres")
    p.add_argument("--revisar", action="store_true", help="solo revisa los archivos del caso, sin generar PDF")
    tinta = p.add_mutually_exclusive_group()
    tinta.add_argument("--color", dest="ahorro", action="store_false", default=None,
                       help="PDF a todo color, con los fondos de las hojas, tarjetas y pantallas. Por defecto los PDF "
                            "salen en modo ahorro de tinta: sin fondos ni rellenos grandes, con el color solo en "
                            "bandas, códigos, sellos y textos (se puede fijar con ahorro_de_tinta en caso.yaml)")
    tinta.add_argument("--ahorro", dest="ahorro", action="store_true",
                       help="fuerza el modo ahorro de tinta aunque caso.yaml diga ahorro_de_tinta: false")
    p.add_argument("--imagenes", action="store_true", help="además, una imagen PNG por prueba para mandar por chat")
    a = p.parse_args(argv)

    inicio = time.time()
    try:
        caso = cargar_caso(a.caso)
        if a.ahorro is not None:
            caso.datos["_ahorro"] = a.ahorro
        docs = documentos(caso)
    except ErrorCaso as ex:
        print(f"Error: {ex}", file=sys.stderr)
        sys.exit(2)
    print(f"Caso: {caso.titulo}  ({len(caso.expediente)} hojas de expediente, "
          f"{sum(len(g.get('tarjetas') or []) for g in caso.tarjetas)} tarjetas, {len(caso.kit)} hojas de kit, "
          f"{len(caso.guia)} de guía)")
    ahorro = caso.get("_ahorro", caso.get("ahorro_de_tinta", True))
    print("  modo: ahorro de tinta (sin fondos). Usa --color para la versión a todo color." if ahorro
          else "  modo: a todo color, con fondos.")
    for aviso in caso.avisos:
        print(f"  ! {aviso}")
    if a.revisar:
        print("Revisión terminada." if not caso.avisos else "Revisión terminada, con avisos.")
        return

    if a.solo:
        pedidos = {x.strip() for x in a.solo.split(",") if x.strip()}
        docs = [d for d in docs if d.clave in pedidos or d.clave.split(":")[0] in pedidos]
        if not docs:
            print("Error: --solo no coincide con ningún documento.", file=sys.stderr)
            sys.exit(2)

    salida = Path(a.salida) / caso.raiz.name
    for sub in ("equipos", "director"):
        if not a.solo and (salida / sub).exists():
            shutil.rmtree(salida / sub)
    from .pdf import ErrorNavegador, contar_paginas, exportar
    alto = 297 if str(caso.get("papel", "carta")).lower() == "a4" else 279
    try:
        resultados = exportar(docs, salida / "html", salida, papel_alto_mm=alto, imagenes=a.imagenes)
    except ErrorNavegador as ex:
        print(f"Error: {ex}", file=sys.stderr)
        sys.exit(3)
    problemas = 0
    for r in resultados:
        n = contar_paginas(r["pdf"])
        print(f"  {r['pdf'].relative_to(salida)}  ({n} pág.)" if n else f"  {r['pdf'].relative_to(salida)}")
        for aj in r["ajustes"]:
            if aj["estado"] == "no cabe":
                problemas += 1
                print(f"    ! la tarjeta {aj['codigo']} no cabe ni con la letra mínima: pártela en (1 de 2) y (2 de 2)")
        for h in r["largas"]:
            print(f"    · {h['codigo'].strip()} ocupa {h['paginas']} páginas")
    (salida / "LEEME.txt").write_text(LEEME.format(
        titulo=caso.titulo, fecha=time.strftime("%d-%m-%Y"),
        modo="Modo ahorro de tinta: sin fondos. Para la versión a todo color, exporta con --color." if ahorro
        else "Versión a todo color, con fondos. Sin --color sale en modo ahorro de tinta."), encoding="utf-8")
    print(f"Listo en {time.time() - inicio:.0f} s: {salida}/")
    if problemas:
        sys.exit(1)
