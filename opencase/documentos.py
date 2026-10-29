"""Arma el HTML de cada documento del caso: kit, sobres, expediente, guía y pliegos."""
from dataclasses import dataclass
from pathlib import Path

from . import tarjetas as T
from .componentes import Contexto, render_bloques
from .marcado import e, linea

RAIZ_REPO = Path(__file__).resolve().parent.parent
PAPELES = {"carta": ("letter", "216mm", "279mm"), "letter": ("letter", "216mm", "279mm"),
           "a4": ("A4", "210mm", "297mm")}


@dataclass
class Documento:
    clave: str        # nombre corto para --solo (kit, guia, tarjetas…)
    carpeta: str      # equipos | director
    archivo: str      # nombre del PDF sin extensión
    titulo: str
    html: str
    tipo: str         # hojas | pliegos
    revisar_hojas: bool = False   # avisar si una hoja ocupa más de una página


def _pagina(caso, titulo, cuerpo, clase_mesa="oc-mesa"):
    tam, ancho, alto = PAPELES.get(str(caso.get("papel", "carta")).lower(), PAPELES["carta"])
    hojas_css = [(RAIZ_REPO / "diseno" / "open-case.css").as_uri(),
                 (RAIZ_REPO / "opencase" / "estilos" / "exportador.css").as_uri()]
    if caso.get("_ahorro", caso.get("ahorro_de_tinta", True)):
        hojas_css.append((RAIZ_REPO / "opencase" / "estilos" / "ahorro.css").as_uri())
    extra = caso.raiz / "estilos.css"
    if extra.exists():
        hojas_css.append(extra.as_uri())
    links = "".join(f'<link rel="stylesheet" href="{h}">' for h in hojas_css)
    return (f'<!doctype html><html lang="{e(caso.get("idioma", "es"))}"><head><meta charset="utf-8">'
            f'<meta name="viewport" content="width=device-width,initial-scale=1"><title>{e(titulo)}</title>{links}'
            f'<style>@page{{size:{tam}}}:root{{--hoja-ancho:{ancho};--hoja-alto:{alto};--pagina-ancho:{ancho};--pagina-alto:{alto}}}</style>'
            f'</head><body><main class="{clase_mesa}">{cuerpo}</main></body></html>')


def _portada_pantalla(sobrelinea, titulo, texto=""):
    p = f"<p>{linea(texto)}</p>" if texto else ""
    return (f'<header class="oc-portada"><span class="oc-sobrelinea">{e(sobrelinea)}</span>'
            f"<h1>{e(titulo)}</h1>{p}</header>")


def hoja(h, ctx, defectos=None):
    d = dict(defectos or {})
    d.update(h.datos)
    clases = ["oc-hoja"]
    if d.get("reservada"):
        clases.append("oc-hoja--reservada")
    if d.get("vieja") or d.get("papel") == "viejo":
        clases.append("oc-hoja--vieja")
    memb_cl = "oc-membrete oc-membrete--reservado" if d.get("reservada") else "oc-membrete"
    logo = ""
    if d.get("logo"):
        logo = (f'<img class="oc-membrete__logo" src="{ctx.diseno("logos/oc-wordmark-tinta.svg")}" alt="Open Case">'
                f'<span class="oc-membrete__caso">{e(ctx.caso.titulo)}</span>')
    if d.get("codigo"):
        derecha = f'<span class="oc-codigo">{e(d["codigo"])}</span>'
    elif d.get("equipo"):
        derecha = '<span class="oc-equipo-linea">Equipo: ____________</span>'
    elif d.get("etiqueta"):
        mod = " oc-tag--marino" if d.get("etiqueta_marino") else ""
        derecha = f'<span class="oc-tag{mod}">{e(d["etiqueta"])}</span>'
    else:
        derecha = ""
    membrete = ""
    if d.get("institucion") or d.get("descripcion") or derecha:
        membrete = (f'<div class="{memb_cl}"><div class="oc-membrete__inst">{logo}<b>{linea(d.get("institucion", ""))}</b>'
                    f'{linea(d.get("descripcion", ""))}</div>{derecha}</div>')
    titulo = f'<h2>{linea(d["titulo"])}</h2>' if d.get("titulo") else ""
    sello = ""
    if d.get("sello"):
        s = d["sello"] if isinstance(d["sello"], dict) else {"texto": d["sello"]}
        color = {"tinta": " oc-sello--tinta", "laton": " oc-sello--laton", "bosque": " oc-sello--bosque"}.get(s.get("color", ""), "")
        sello = f'<span class="oc-sello oc-sello--esquina{color}">{e(s["texto"])}</span>'
    if d.get("aviso"):
        clases.append("oc-hoja--aviso")
    cuerpo = render_bloques(h, ctx)
    pie = ""
    if d.get("marca_en_hoja"):
        mono = ctx.diseno("logos/oc-monograma-tinta.svg")
        pie = (f'<div class="oc-hoja__marca"><span><img src="{mono}" alt="">{e(ctx.caso.get("marca", "Open Case"))} · '
               f'{e(ctx.caso.titulo)}</span><span>{e(d.get("codigo", ""))}</span></div>')
    return f'<article class="{" ".join(clases)}" id="{e(h.id)}">{membrete}{titulo}{cuerpo}{sello}{pie}</article>'


def tapa(caso, ctx, doc, nota="", reservada=False, equipo=False):
    clases = "oc-hoja oc-tapa" + (" oc-hoja--reservada oc-tapa--reservada" if reservada else "")
    eq = '<span class="oc-equipo-linea">Equipo: ____________</span>' if equipo else ""
    tag = '<span class="oc-tag">Solo director</span>' if reservada else ""
    version = f'<div class="oc-tapa__version">{e(caso.get("version"))}</div>' if caso.get("version") else ""
    return (f'<article class="{clases}"><img class="oc-tapa__sello" src="{ctx.diseno("logos/oc-sello-sello.svg")}" alt="Open Case. {e(caso.get("lema", ""))}">'
            f'<div class="oc-tapa__caso">{e(caso.titulo)}</div><div class="oc-tapa__doc">{e(doc)}</div>{tag}'
            f'{"<p class=oc-tapa__nota>" + linea(nota) + "</p>" if nota else ""}{eq}'
            f'<div class="oc-tapa__lema">{e(caso.get("lema", "Dos equipos, un culpable"))}</div>{version}</article>')


def documentos(caso):
    ctx = Contexto(caso, RAIZ_REPO)
    docs = []
    titulo = caso.titulo

    # --- Kit del equipo ----------------------------------------------------------
    kit_cfg = caso.get("kit", {}) or {}
    if caso.kit:
        cuerpo = _portada_pantalla(f"{caso.get('marca', 'Open Case')} · {titulo}", "Kit del equipo", kit_cfg.get("descripcion", ""))
        cuerpo += tapa(caso, ctx, "Kit del equipo", kit_cfg.get("nota_tapa", ""), equipo=True)
        defectos = {"logo": True, "equipo": True, "marca_en_hoja": _marca(caso, "kit")}
        cuerpo += "".join(hoja(h, ctx, defectos) for h in caso.kit)
        docs.append(Documento("kit", "equipos", "01_Kit_del_equipo", f"Kit del equipo · {titulo}",
                              _pagina(caso, f"Kit del equipo · {titulo}", cuerpo), "hojas", True))

    # --- Expediente: por sección, y completo para el director ----------------------
    exp = caso.get("expediente", {}) or {}
    secciones = exp.get("secciones", []) or []
    por_archivo = {}
    for sec in secciones:
        if sec.get("equipos"):
            por_archivo.setdefault(sec["equipos"], []).append(sec)
    for n, (archivo, secs) in enumerate(por_archivo.items(), start=2):
        cuerpo = _portada_pantalla(exp.get("sobrelinea", ""), archivo.replace("_", " "), secs[0].get("nota", ""))
        for sec in secs:
            cuerpo += f'<div class="oc-seccion"><b>{e(sec.get("titulo", ""))}</b><span>{e(sec.get("nota", ""))}</span></div>'
            cuerpo += "".join(hoja(caso.expediente[p], ctx, {"marca_en_hoja": _marca(caso, "expediente")}) for p in sec.get("pruebas", []))
        docs.append(Documento(f"sobres:{archivo}", "equipos", f"{n:02d}_{archivo}", archivo.replace("_", " "),
                              _pagina(caso, f"{archivo.replace('_', ' ')} · {titulo}", cuerpo), "hojas", True))

    if secciones:
        cuerpo = _portada_pantalla(exp.get("sobrelinea", ""), exp.get("titulo", "Expediente"), exp.get("descripcion", ""))
        cuerpo += _caratula(caso, exp, secciones)
        for sec in secciones:
            cuerpo += f'<div class="oc-seccion"><b>{e(sec.get("titulo", ""))}</b><span>{e(sec.get("nota", ""))}</span></div>'
            cuerpo += "".join(hoja(caso.expediente[p], ctx, {"marca_en_hoja": _marca(caso, "expediente")}) for p in sec.get("pruebas", []))
        nombre = exp.get("archivo", "Expediente_completo")
        docs.append(Documento("expediente", "director", f"02_{nombre}", exp.get("titulo", "Expediente"),
                              _pagina(caso, f"{exp.get('titulo', 'Expediente')} · {titulo}", cuerpo), "hojas", True))

    # --- Guía del director ---------------------------------------------------------
    guia_cfg = caso.get("guia", {}) or {}
    if caso.guia:
        cuerpo = _portada_pantalla("Reservado · solo para el director", "Guía del director", guia_cfg.get("descripcion", ""))
        cuerpo += tapa(caso, ctx, "Guía del director", guia_cfg.get("nota_tapa", ""), reservada=True)
        defectos = {"logo": True, "reservada": True, "etiqueta": "Solo director", "marca_en_hoja": _marca(caso, "guia")}
        cuerpo += "".join(hoja(h, ctx, defectos) for h in caso.guia)
        docs.append(Documento("guia", "director", "01_Guia_del_director", f"Guía del director · {titulo}",
                              _pagina(caso, f"Guía del director · {titulo}", cuerpo), "hojas"))

    # --- Tarjetas de respuesta y avisos ---------------------------------------------
    respuestas, aparte = T.grupos_de_tarjetas(caso)
    if respuestas or aparte:
        html_t = [T.tarjeta(t, g, caso) for t, g in respuestas]
        cods = [T.codigo_corto(t) for t, g in respuestas]
        pl = T.pliegos(html_t, caso, "Tarjetas", cods)
        if aparte:
            pl += T.pliegos([T.tarjeta(t, g, caso) for t, g in aparte], caso, "Avisos, prensa y pistas")
        # Se renumeran los pies para que "Pliego N de M" cuente todos.
        pl = _renumerar(pl)
        cuerpo = _portada_pantalla(f"{caso.get('marca', 'Open Case')} · {titulo}", "Tarjetas de respuesta",
                                   "Pliegos carta de 8 tarjetas de 88 × 63 mm. Imprimir al 100 % en cartulina, "
                                   "una copia por equipo.")
        docs.append(Documento("tarjetas", "director", "03_Tarjetas_de_respuesta", "Tarjetas de respuesta",
                              _pagina(caso, f"Tarjetas · {titulo}", cuerpo + "".join(pl), "oc-mesa oc-mesa--pliegos"), "pliegos"))

    # --- Reverso común --------------------------------------------------------------
    rev = T.pliegos([T.reverso(caso, ctx)] * 8, caso, "Reverso común: imprimir en el dorso de cada pliego")
    docs.append(Documento("reverso", "director", "04_Reverso_de_tarjetas", "Reverso de tarjetas",
                          _pagina(caso, f"Reverso · {titulo}", _portada_pantalla("Open Case", "Reverso común", "") + "".join(rev),
                                  "oc-mesa oc-mesa--pliegos"), "pliegos"))

    # --- Material del juego para los equipos -----------------------------------------
    equipos = caso.get("equipos", ["A", "B"])
    if caso.personajes:
        sosp = [T.tarjeta_sospechoso(p, caso, ctx) for p in caso.personajes]
        pl = T.pliegos(sosp, caso, "Sospechosos", [p["letra"] for p in caso.personajes], vertical=True)
        docs.append(Documento("sospechosos", "equipos", "10_Tarjetas_de_sospechosos", "Tarjetas de sospechosos",
                              _pagina(caso, f"Sospechosos · {titulo}", _portada_pantalla(titulo, "Sospechosos", "Una copia por equipo.") + "".join(pl),
                                      "oc-mesa oc-mesa--pliegos"), "pliegos"))
    n_placas = int(caso.get("jugadores_por_equipo", 7))
    pl = []
    for eq in equipos:
        pl += T.pliegos([T.placa(caso, ctx, eq)] * n_placas, caso, f"Placas del equipo {eq}", vertical=True)
    docs.append(Documento("placas", "equipos", "11_Placas", "Placas",
                          _pagina(caso, f"Placas · {titulo}", _portada_pantalla(titulo, "Placas de detective", "") + "".join(_renumerar(pl)),
                                  "oc-mesa oc-mesa--pliegos"), "pliegos"))
    fichas = T.pliego_fichas(caso, ctx)
    docs.append(Documento("fichas", "equipos", "12_Fichas", "Fichas",
                          _pagina(caso, f"Fichas · {titulo}", _portada_pantalla(titulo, "Fichas", "") + "".join(fichas),
                                  "oc-mesa oc-mesa--pliegos"), "pliegos"))
    pl = T.pliegos([T.solicitud(caso)] * 8, caso, "Solicitudes")
    docs.append(Documento("solicitudes", "equipos", "13_Solicitudes", "Solicitudes",
                          _pagina(caso, f"Solicitudes · {titulo}", _portada_pantalla(titulo, "Solicitudes", "") + "".join(pl),
                                  "oc-mesa oc-mesa--pliegos"), "pliegos"))
    sobres = caso.get("sobres", []) or []
    if sobres:
        etiquetas = [T.etiqueta_sobre(s, caso, eq) for s in sobres for eq in equipos]
        pl = T.pliegos(etiquetas, caso, "Etiquetas de sobre")
        docs.append(Documento("etiquetas", "equipos", "14_Etiquetas_de_sobre", "Etiquetas de sobre",
                              _pagina(caso, f"Sobres · {titulo}", _portada_pantalla(titulo, "Etiquetas de sobre", "") + "".join(pl),
                                      "oc-mesa oc-mesa--pliegos"), "pliegos"))
    return docs


def _marca(caso, doc):
    """marca_en_hojas en caso.yaml: lista de documentos (kit, guia, expediente) que llevan el pie con la marca."""
    valor = caso.get("marca_en_hojas", ["kit", "guia"])
    if valor is True:
        return True
    if not valor:
        return False
    return doc in valor


def _renumerar(pliegos_html):
    import re
    total = len(pliegos_html)
    salida = []
    for n, p in enumerate(pliegos_html, 1):
        salida.append(re.sub(r"Pliego \d+ de \d+", f"Pliego {n} de {total}", p, count=1))
    return salida


def _caratula(caso, exp, secciones):
    filas = []
    for sec in secciones:
        filas.append(f'<tr><th colspan="2">{e(sec.get("titulo", ""))}{" · " + e(sec["nota"]) if sec.get("nota") else ""}</th></tr>')
        for pid in sec.get("pruebas", []):
            h = caso.expediente[pid]
            filas.append(f'<tr><td class="c">{e(h.get("codigo", pid))}</td><td>{linea(h.get("titulo", ""))}'
                         f'<span class="oc-pequeno"> · {linea(h.get("institucion", ""))}</span></td></tr>')
    sobre = f'<div class="oc-caratula__sobre">{e(exp.get("sobrelinea", ""))}</div>' if exp.get("sobrelinea") else ""
    desc = f"<p>{linea(exp.get('descripcion_impresa', ''))}</p>" if exp.get("descripcion_impresa") else ""
    return (f'<article class="oc-hoja oc-caratula" id="indice">{sobre}<h1>{e(exp.get("titulo", "Expediente"))}</h1>{desc}'
            f'<div class="oc-tabla oc-indice-tabla oc-tabla--compacta"><table><tbody>{"".join(filas)}</tbody></table></div>'
            '<span class="oc-sello oc-sello--esquina">Reservado</span></article>')
