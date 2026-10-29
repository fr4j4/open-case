"""Tarjetas recortables (63 × 88 mm), placas, solicitudes, etiquetas de sobre, fichas y pliegos."""
import re

from .cargar import ErrorCaso
from .marcado import e, linea, texto_plano

TIPOS = {
    # tipo: (clase modificadora, sufijo de la cabecera)
    "respuesta": ("", ""),
    "seguimiento": ("", "seguimiento"),
    "confrontacion": ("oc-tarjeta--confrontacion", "confrontación"),
    "confrontación": ("oc-tarjeta--confrontacion", "confrontación"),
    "fallida": ("oc-tarjeta--fallida", "confrontación fallida"),
    "testigo": ("oc-tarjeta--testigo", ""),
    "comodin": ("oc-tarjeta--comodin", ""),
    "comodín": ("oc-tarjeta--comodin", ""),
    "aviso": ("oc-tarjeta--aviso", ""),
    "prensa": ("oc-tarjeta--prensa", ""),
    "pista": ("oc-tarjeta--pista", ""),
    "cierre": ("oc-tarjeta--cierre", ""),
}
# Estas van en pliegos aparte (Norma de tarjetas: avisos, prensa y pistas juntos).
TIPOS_APARTE = {"aviso", "prensa", "pista", "cierre"}


def marca(caso, derecha=None):
    return (f'<div class="oc-tarjeta__marca"><span>{e(caso.get("marca", "Open Case"))}</span>'
            f'<span>{e(derecha or caso.titulo)}</span></div>')


def tarjeta(t, grupo, caso):
    tipo = str(t.get("tipo", grupo.get("tipo", "respuesta"))).lower()
    if tipo not in TIPOS:
        raise ErrorCaso(f"la tarjeta {t.get('codigo')} tiene tipo '{tipo}'; los tipos son: "
                        + ", ".join(k for k in TIPOS if k.isascii()), caso.raiz / "tarjetas.yaml")
    clase, sufijo = TIPOS[tipo]
    estilo = t.get("estilo")
    if estilo:
        clase = TIPOS.get(estilo, (f"oc-tarjeta--{estilo}", ""))[0]
    codigo = str(t["codigo"])
    letra = t.get("personaje", grupo.get("personaje"))
    if tipo.startswith("confront") and letra and "◆" not in codigo:
        codigo = f"{letra}◆ · {codigo}"
    quien = t.get("quien")
    if not quien:
        if sufijo:
            quien = f'{grupo.get("corto") or grupo.get("quien") or grupo.get("titulo", "")} · {sufijo}'
        else:
            quien = grupo.get("quien") or grupo.get("titulo", "")
    partes = [f'<div class="oc-tarjeta__banda"></div>',
              f'<div class="oc-tarjeta__cab"><b>{e(codigo)}</b><span>{linea(quien)}</span></div>']
    if t.get("titular"):
        partes.append(f'<div class="oc-tarjeta__titular">{linea(t["titular"])}</div>')
    if t.get("pregunta"):
        partes.append(f'<div class="oc-tarjeta__pregunta">{linea(t["pregunta"])}</div>')
    partes.append(f'<div class="oc-tarjeta__respuesta">{linea(t.get("respuesta", ""))}</div>')
    if t.get("aclaracion"):
        partes.append(f'<div class="oc-tarjeta__pregunta">{linea(t["aclaracion"])}</div>')
    for adj in _lista(t.get("adjunta")):
        partes.append(f'<div class="oc-tarjeta__pie">Adjunta {e(adj)}</div>')
    for seg in _lista(t.get("seguimiento")):
        partes.append(f'<div class="oc-tarjeta__pie oc-tarjeta__pie--seg">Seguimiento disponible: {e(seg)}</div>')
    if t.get("pie"):
        partes.append(f'<div class="oc-tarjeta__pie oc-tarjeta__pie--seg">{linea(t["pie"])}</div>')
    partes.append(marca(caso))
    return (f'<div class="oc-tarjeta {clase}" data-codigo="{e(t["codigo"])}" '
            f'data-largo="{len(texto_plano(t.get("respuesta", "")))}">{"".join(partes)}</div>')


def _lista(v):
    if not v:
        return []
    if isinstance(v, (list, tuple)):
        return [str(x) for x in v]
    return [str(v)]


def tarjeta_sospechoso(p, caso, ctx):
    if p.get("retrato"):
        retrato = f'<img class="oc-tarjeta__retrato" src="{ctx.url(p["retrato"])}" alt="{e(p["nombre"])}">'
    else:
        retrato = (f'<div class="oc-tarjeta__retrato-vacio"><img src="{ctx.diseno("iconos/carpeta.svg")}" alt=""></div>')
    datos = "".join(f"<span>{e(k)}</span><div>{linea(v)}</div>" for k, v in list((p.get("datos") or {}).items())[:5])
    codigos = [t["codigo"] for g in caso.tarjetas for t in g.get("tarjetas", []) or []
               if t.get("menu") and t.get("personaje", g.get("personaje")) == p["letra"]]
    preguntas = ""
    if codigos:
        rango = codigos[0] if len(codigos) == 1 else f"{codigos[0]}–{codigos[-1]}"
        preguntas = f'<div class="oc-tarjeta__pie oc-tarjeta__pie--seg">Preguntas: {e(rango)} · {e(p["letra"])}◆</div>'
    rol = " · ".join(x for x in (p.get("rol", ""), f'sospechoso {p["letra"]}') if x)
    return ('<div class="oc-tarjeta oc-tarjeta--vertical oc-tarjeta--sospechoso"><div class="oc-tarjeta__banda"></div>'
            f'{retrato}<div class="oc-tarjeta__nombre">{e(p.get("nombre_corto") or p["nombre"])}</div>'
            f'<div class="oc-tarjeta__rol">{e(rol)}</div><div class="oc-tarjeta__datos">{datos}</div>'
            f'{preguntas}{marca(caso)}</div>')


ESTRELLA = ('<svg class="oc-placa__estrella" viewBox="0 0 60 60" aria-hidden="true"><path d="M30 3l7 17 18 1-14 11 '
            '5 18-16-10-16 10 5-18L5 21l18-1z" fill="#b48a2c" stroke="#7a5d1c"/></svg>')


def placa(caso, ctx, equipo):
    p = caso.get("placa", {}) or {}
    unidad = "<br>".join(e(x) for x in _lista(p.get("unidad", "")) if x) if isinstance(p.get("unidad"), list) \
        else e(p.get("unidad", "")).replace("\n", "<br>")
    mod = " oc-equipo--b" if equipo == "B" else ""
    return ('<div class="oc-tarjeta oc-tarjeta--vertical oc-placa">'
            f'{ESTRELLA}<div class="oc-placa__titulo">{e(p.get("titulo", "Detective"))}</div>'
            f'<div class="oc-placa__unidad">{unidad}</div><span class="oc-equipo{mod}">Equipo {e(equipo)}</span>'
            '<div class="oc-placa__nombre"></div><div class="oc-placa__nombre-rotulo">Nombre</div>'
            f'<img class="oc-placa__mono" src="{ctx.diseno("logos/oc-monograma-tinta.svg")}" alt="Open Case"></div>')


def solicitud(caso):
    s = caso.get("solicitud", {}) or {}
    ayuda = s.get("ayuda", "1 ficha por pregunta · diligencias según menú")
    return ('<div class="oc-tarjeta oc-solicitud">'
            f'<div class="oc-solicitud__titulo">Solicitud <small>{e(ayuda)}</small></div>'
            '<div class="oc-campo"><span>Equipo</span><i></i><span>Código</span><i></i></div>'
            '<div class="oc-campo"><span>Prueba que mostramos / de quién</span><i></i></div>'
            '<div class="oc-campo oc-campo--corto"><span>Por qué</span><i></i></div>'
            '<div class="oc-campo oc-campo--corto"><span></span><i></i></div>'
            '<div class="oc-solicitud__ficha">Ficha aquí</div>'
            f'{marca(caso, "Solicitud N° ____")}</div>')


def etiqueta_sobre(s, caso, equipo):
    lista = "".join(f"<li>{linea(x)}</li>" for x in s.get("contenido", []) or [])
    mod = " oc-equipo--b" if equipo == "B" else ""
    eq = f'<span class="oc-equipo{mod}">Equipo {e(equipo)}</span>' if equipo else "<span></span>"
    pie = f'<span class="oc-tarjeta__pie oc-tarjeta__pie--seg">{linea(s["pie"])}</span>' if s.get("pie") else ""
    desc = f'<div class="oc-tarjeta__pregunta">{linea(s["descripcion"])}</div>' if s.get("descripcion") else ""
    return ('<div class="oc-tarjeta oc-sobre">'
            f'<div class="oc-sobre__numero">Sobre {e(s.get("numero", ""))} <small>{e(s.get("cuando", ""))}</small></div>'
            f'{desc}<ul class="oc-sobre__lista">{lista}</ul>'
            f'<div style="display:flex;justify-content:space-between;align-items:center;margin-top:auto;gap:8px">{eq}{pie}</div>'
            f'{marca(caso)}</div>')


def reverso(caso, ctx):
    return ('<div class="oc-tarjeta oc-reverso">'
            f'<img class="oc-reverso__sello" src="{ctx.diseno("logos/oc-sello-sello.svg")}" alt="Open Case">'
            f'<div class="oc-reverso__caso">{e(caso.titulo)}</div></div>')


def rotar(htm):
    """Una tarjeta vertical girada 90° para que entre en la rejilla apaisada de 2 × 4."""
    return f'<div class="oc-tarjeta oc-tarjeta--rotada">{htm}</div>'


def pliegos(tarjetas, caso, etiqueta, codigos=None, vertical=False):
    """Reparte tarjetas en pliegos de 8 y devuelve [(html, n_tarjetas)].

    `codigos` es una lista paralela con el código de cada tarjeta, para el pie."""
    salida = []
    for i in range(0, len(tarjetas), 8):
        lote = tarjetas[i:i + 8]
        lote_cod = codigos[i:i + 8] if codigos else None
        celdas = [rotar(t) if vertical else t for t in lote]
        celdas += ['<div class="oc-tarjeta oc-tarjeta--vacia"></div>'] * (8 - len(lote))
        salida.append((celdas, lote_cod))
    total = len(salida)
    html = []
    for n, (celdas, lote_cod) in enumerate(salida, 1):
        rango = ""
        if lote_cod:
            rango = f" · {etiqueta} {lote_cod[0]}–{lote_cod[-1]}" if len(lote_cod) > 1 else f" · {etiqueta} {lote_cod[0]}"
        elif etiqueta:
            rango = f" · {etiqueta}"
        pie = f'{e(caso.titulo)} · Pliego {n} de {total}{e(rango)} · imprimir al 100 %'
        html.append(f'<section class="oc-pliego">{"".join(celdas)}<div class="oc-pliego__pie">{pie}</div></section>')
    return html


def pliego_fichas(caso, ctx):
    """Una hoja de 35 fichas (5 × 7): las de cada equipo numeradas y, si sobra lugar, fichas de reserva."""
    n = int(caso.get("fichas_por_equipo", 16))
    equipos = caso.get("equipos", ["A", "B"])
    fichas = []
    for eq in equipos:
        mod = " oc-ficha--a" if eq == "A" else " oc-ficha--b" if eq == "B" else ""
        fichas += [f'<span class="oc-ficha{mod}"><b>{i}</b>Ficha<small>Equipo {e(eq)}</small></span>' for i in range(1, n + 1)]
    hojas_frente, hojas_dorso = [], []
    for i in range(0, len(fichas), 35):
        lote = fichas[i:i + 35]
        reserva = 35 - len(lote)
        lote += ['<span class="oc-ficha"><b>&nbsp;</b>Ficha<small>reserva</small></span>'] * reserva
        hojas_frente.append(lote)
    total = len(hojas_frente)
    salida = []
    # Dos monogramas: el claro va sobre el latón (a color) y el de tinta sobre blanco (ahorro).
    mono = (f'<img class="oc-ficha__mono-color" src="{ctx.diseno("logos/oc-monograma-papel.svg")}" alt="">'
            f'<img class="oc-ficha__mono-ahorro" src="{ctx.diseno("logos/oc-monograma-tinta.svg")}" alt="">')
    for k, lote in enumerate(hojas_frente, 1):
        pie = f"{e(caso.titulo)} · Fichas · hoja {k} de {total} · frente · cartulina, imprimir al 100 %"
        salida.append(f'<section class="oc-pliego oc-pliego--fichas">{"".join(lote)}<div class="oc-pliego__pie">{pie}</div></section>')
        dorso = "".join(f'<span class="oc-ficha oc-ficha--reverso">{mono}</span>' for _ in lote)
        pie = f"{e(caso.titulo)} · Fichas · hoja {k} de {total} · dorso (opcional)"
        salida.append(f'<section class="oc-pliego oc-pliego--fichas">{dorso}<div class="oc-pliego__pie">{pie}</div></section>')
    return salida


def grupos_de_tarjetas(caso):
    """Separa las tarjetas en (respuestas, aparte) conservando el orden del archivo."""
    respuestas, aparte = [], []
    for g in caso.tarjetas:
        for t in g.get("tarjetas", []) or []:
            tipo = str(t.get("tipo", g.get("tipo", "respuesta"))).lower()
            (aparte if tipo in TIPOS_APARTE else respuestas).append((t, g))
    return respuestas, aparte


def codigo_corto(t):
    return re.sub(r"\s+", " ", str(t["codigo"]))
