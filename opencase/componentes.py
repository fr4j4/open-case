"""Un bloque ```componente de una hoja -> el HTML del componente del sistema de diseño.

Cada función recibe el bloque y el contexto, y devuelve HTML con las clases oc- de
diseno/open-case.css. Los nombres de los bloques son los de docs/formato-de-casos.md."""
import re
from pathlib import Path

from .cargar import ErrorCaso, leer_yaml, normalizar_codigo
from .marcado import e, linea, linea_pre, md, texto_plano

FLECHAS = {"entrante": "↘", "saliente": "↗", "perdida": "✕", "perdida entrante": "✕"}


class Contexto:
    """Lo que un componente necesita saber del caso y de dónde se está dibujando."""

    def __init__(self, caso, raiz_repo):
        self.caso = caso
        self.raiz_repo = Path(raiz_repo)
        self.hoja = None

    def ruta(self, ref):
        p = (self.caso.raiz / str(ref)).resolve()
        if not p.exists():
            raise ErrorCaso(f"no existe el archivo '{ref}'", self.hoja.ruta if self.hoja else None)
        return p

    def url(self, ref):
        return self.ruta(ref).as_uri()

    def diseno(self, ref):
        return (self.raiz_repo / "diseno" / ref).as_uri()

    def svg(self, ref, clase="", etiqueta=None):
        return svg_en_linea(self.ruta(ref).read_text(encoding="utf-8"), clase, etiqueta)


def svg_en_linea(fuente, clase="", etiqueta=None):
    s = re.sub(r"<\?xml[^>]*\?>|<!DOCTYPE[^>]*>", "", fuente)
    s = re.sub(r"<metadata>.*?</metadata>", "", s, flags=re.S)
    s = s.strip()
    if clase:
        s = re.sub(r"<svg\b", f'<svg class="{clase}"', s, count=1)
    if etiqueta and "aria-label" not in s[:400]:
        s = re.sub(r"<svg\b", f'<svg role="img" aria-label="{e(etiqueta)}"', s, count=1)
    # Las tipografías genéricas de los dibujos pasan a las del sistema.
    s = re.sub(r'font-family="(?:monospace|IBM Plex Mono, monospace)"', 'font-family="IBM Plex Mono, monospace"', s)
    s = re.sub(r'font-family="sans-serif"', 'font-family="Public Sans, Arial, sans-serif"', s)
    return s


def _datos(bloque, ctx, tipo=(list, dict)):
    datos = leer_yaml(bloque.contenido, ctx.hoja.ruta if ctx.hoja else None, bloque.linea)
    if datos is None:
        datos = [] if tipo is list or (isinstance(tipo, tuple) and list in tipo) else {}
    if not isinstance(datos, tipo):
        nombres = {list: "una lista (líneas que empiezan con '- ')", dict: "campos clave: valor"}
        esperado = nombres.get(tipo, " o ".join(nombres[t] for t in tipo) if isinstance(tipo, tuple) else str(tipo))
        raise ErrorCaso(f"el bloque {bloque.tipo} debe ser {esperado}", ctx.hoja.ruta if ctx.hoja else None, bloque.linea)
    return datos


def _pares(datos):
    """Acepta un diccionario o una lista de pares [clave, valor] / {clave: valor}."""
    if isinstance(datos, dict):
        return list(datos.items())
    pares = []
    for it in datos:
        if isinstance(it, dict):
            pares.extend(it.items())
        elif isinstance(it, (list, tuple)) and len(it) == 2:
            pares.append(tuple(it))
        else:
            pares.append((str(it), ""))
    return pares


def _columnas(arg, defecto=None):
    m = re.search(r"(\d+)\s*columnas?", arg or "")
    n = int(m.group(1)) if m else defecto
    return f' style="--oc-columnas:{n}"' if n else ""


# --- Documentos -----------------------------------------------------------------

def c_meta(b, ctx):
    filas = "".join(f"<div><span>{e(k)}</span>{linea(v)}</div>" for k, v in _pares(_datos(b, ctx)))
    return f'<div class="oc-meta">{filas}</div>'


def c_firma(b, ctx):
    partes = []
    for it in _datos(b, ctx, list):
        if isinstance(it, dict) and ("trazo" in it or "rotulo" in it):
            trazo = f'<span class="oc-firma__trazo">{e(it.get("trazo", ""))}</span>' if it.get("trazo") else ""
            partes.append(f'<div>{trazo}<span>{linea(it.get("rotulo", ""))}</span></div>')
        else:
            if isinstance(it, dict):
                it = ": ".join(f"{k}: {v}" for k, v in it.items())
            partes.append(f"<span>{linea(it)}</span>")
    if len(partes) == 1:
        partes.append("<span></span>")
    return f'<div class="oc-firma">{"".join(partes)}</div>'


def c_declaracion(b, ctx):
    return f'<div class="oc-declaracion">{linea_pre(b.contenido)}</div>'


def c_cita(b, ctx):
    return f'<div class="oc-cita">{linea_pre(b.contenido)}</div>'


def c_manuscrito(b, ctx):
    variantes = {"libreta": "", "garabato": "oc-manuscrito--garabato", "lapiz": "oc-manuscrito--lapiz",
                 "lápiz": "oc-manuscrito--lapiz", "carta": "oc-manuscrito--carta",
                 "sin-lineas": "oc-manuscrito--sin-lineas", "sin-líneas": "oc-manuscrito--sin-lineas"}
    clases = ["oc-manuscrito"]
    for v in (b.argumento or "").split():
        if v.lower() not in variantes:
            raise ErrorCaso(f"manuscrito: variante '{v}' desconocida (usa {', '.join(sorted(variantes))})",
                            ctx.hoja.ruta, b.linea)
        if variantes[v.lower()]:
            clases.append(variantes[v.lower()])
    return f'<div class="{" ".join(clases)}">{e(b.contenido.strip())}</div>'


def c_postit(b, ctx):
    return f'<div class="oc-postit">{e(b.contenido.strip())}</div>'


def c_plumon(b, ctx):
    return "".join(f'<div class="oc-plumon">{e(l)}</div>' for l in b.contenido.strip().split("\n") if l.strip())


def c_mono(b, ctx):
    return f'<div class="oc-mono oc-bloque-mono">{md(b.contenido)}</div>'


def c_pequeno(b, ctx):
    return f'<div class="oc-pequeno">{md(b.contenido)}</div>'


def c_tabla(b, ctx):
    variantes = [v for v in (b.argumento or "").split() if v]
    htm = md(b.contenido)
    clases = " ".join(f"oc-tabla--{v}" for v in variantes)
    return htm.replace('<div class="oc-tabla">', f'<div class="oc-tabla {clases}">')


def c_sello(b, ctx):
    variantes = {"sello": "", "tinta": "oc-sello--tinta", "laton": "oc-sello--laton", "latón": "oc-sello--laton",
                 "bosque": "oc-sello--bosque", "grande": "oc-sello--grande", "esquina": "oc-sello--esquina"}
    clases = ["oc-sello"] + [variantes.get(v.lower(), "") for v in (b.argumento or "").split()]
    return f'<span class="{" ".join(c for c in clases if c)}">{e(b.contenido.strip())}</span>'


def c_bolsa(b, ctx):
    d = _datos(b, ctx, dict)
    cab = f'Evidencia <small>{e(d.get("numero", ""))}</small>'
    campos = "".join(f'<div class="oc-bolsa__campo"><span>{e(k)}</span><b>{e(v)}</b></div>'
                     for k, v in _pares(d.get("campos", {})))
    return f'<div class="oc-bolsa"><div class="oc-bolsa__cab">{cab}</div>{campos}</div>'


def c_prensa(b, ctx):
    d = _datos(b, ctx, dict)
    cuerpo = d.get("cuerpo", "")
    return ('<article class="oc-prensa">'
            f'<div class="oc-prensa__kicker"><span>{e(d.get("medio", ""))}</span><span>{e(d.get("fecha", ""))}</span></div>'
            f'<h3>{linea(d.get("titular", ""))}</h3>'
            f'<div class="oc-prensa__cuerpo">{md(cuerpo)}</div></article>')


def c_correo(b, ctx):
    d = _datos(b, ctx, dict)
    cab = "".join(f"<span>{k}</span><div>{e(d[c])}</div>" for k, c in
                  (("De", "de"), ("Para", "para"), ("CC", "cc"), ("Fecha", "fecha"), ("Asunto", "asunto")) if d.get(c))
    adj = "".join(f'<span class="oc-msg__adjunto">📎 {e(a)}</span>' for a in d.get("adjuntos", []) or [])
    return (f'<div class="oc-correo"><div class="oc-correo__cab">{cab}</div>'
            f'<div class="oc-correo__cuerpo">{linea(d.get("cuerpo", ""))}{adj}</div></div>')


def c_boleta(b, ctx):
    filas = []
    for it in _datos(b, ctx, list):
        if it in ("---", "-", "linea", "línea"):
            filas.append("<hr>")
        elif isinstance(it, dict) and "centro" in it:
            filas.append(f'<div class="oc-boleta__centro">{linea(it["centro"])}</div>')
        elif isinstance(it, dict) and "total" in it:
            a, z = it["total"]
            filas.append(f'<div class="oc-boleta__fila"><b>{e(a)}</b><b>{e(z)}</b></div>')
        elif isinstance(it, (list, tuple)) and len(it) == 2:
            filas.append(f'<div class="oc-boleta__fila"><span>{e(it[0])}</span><span>{e(it[1])}</span></div>')
        else:
            filas.append(f'<div class="oc-boleta__centro">{e(it)}</div>')
    return f'<div class="oc-boleta">{"".join(filas)}</div>'


# --- Fotos y cámaras ------------------------------------------------------------

def _img(ctx, ref, alt, clase=""):
    cl = f' class="{clase}"' if clase else ""
    return f'<img{cl} src="{ctx.url(ref)}" alt="{e(alt)}" loading="eager">'


def c_fotos(b, ctx):
    figuras = []
    for f in _datos(b, ctx, list):
        titulo = f.get("titulo", "")
        texto = f.get("texto", "")
        alt = f.get("alt") or texto_plano(f"{titulo} {texto}")
        rotulo = f'<span class="oc-foto__rotulo">{e(f["rotulo"])}</span>' if f.get("rotulo") else ""
        pie = (f"<b>{linea(titulo)}</b> " if titulo else "") + linea(texto)
        figuras.append(f'<figure class="oc-foto"><div class="oc-foto__cuadro">{_img(ctx, f["imagen"], alt)}{rotulo}</div>'
                       f"<figcaption>{pie}</figcaption></figure>")
    return f'<div class="oc-fotos"{_columnas(b.argumento)}>{"".join(figuras)}</div>'


def c_cctv(b, ctx):
    figuras = []
    for f in _datos(b, ctx, list):
        texto = f.get("texto", "")
        titulo = f.get("titulo", "")
        alt = f.get("alt") or texto_plano(f"{titulo} {texto}")
        osd = "".join(f'<span class="oc-cctv__osd{" oc-cctv__osd--d" if lado == "der" else ""}">{e(f[k])}</span>'
                      for k, lado in (("osd", "izq"), ("osd_der", "der")) if f.get(k))
        pie = (f"<b>{linea(titulo)}</b> " if titulo else "") + linea(texto)
        figuras.append(f'<figure class="oc-cctv">{_img(ctx, f["imagen"], alt)}{osd}<figcaption>{pie}</figcaption></figure>')
    return f'<div class="oc-cctvs"{_columnas(b.argumento)}>{"".join(figuras)}</div>'


def c_imagen(b, ctx):
    d = _datos(b, ctx, dict)
    ancho = f' style="width:{e(d["ancho"])}"' if d.get("ancho") else ""
    pie = f"<figcaption>{linea(d['pie'])}</figcaption>" if d.get("pie") else ""
    return f'<figure class="oc-imagen"{ancho}>{_img(ctx, d["imagen"], d.get("alt") or texto_plano(d.get("pie", "")))}{pie}</figure>'


def c_svg(b, ctx):
    """Un dibujo SVG del caso (croquis, diagramas). Argumento: la ruta del archivo."""
    ref = (b.argumento or b.contenido).strip()
    if not ref:
        raise ErrorCaso("svg: falta la ruta del archivo (```svg diagramas/croquis.svg```)", ctx.hoja.ruta, b.linea)
    return f'<div class="oc-dibujo">{ctx.svg(ref)}</div>'


def c_leyenda(b, ctx):
    items = []
    for color, texto in _pares(_datos(b, ctx)):
        items.append(f'<span><i style="background:{e(color)}"></i>{linea(texto)}</span>')
    return f'<div class="oc-leyenda">{"".join(items)}</div>'


# --- Pantallas ------------------------------------------------------------------

def _chat(mensajes, ctx, b):
    colores, siguiente = {}, iter("abcde" * 4)
    salida = []
    for m in mensajes or []:
        if isinstance(m, str):
            salida.append(f'<span class="oc-dia">{e(m)}</span>')
            continue
        if "dia" in m or "día" in m:
            salida.append(f'<span class="oc-dia">{e(m.get("dia", m.get("día")))}</span>')
            continue
        clases = ["oc-msg"]
        if m.get("saliente") or m.get("yo"):
            clases.append("oc-msg--saliente")
        texto = m.get("texto", "")
        if m.get("borrado"):
            clases.append("oc-msg--borrado")
            texto = texto or "⊘ Se eliminó este mensaje"
        quien = ""
        if m.get("de"):
            letra = m.get("color") or colores.setdefault(m["de"], next(siguiente))
            mod = "" if letra == "a" else f" oc-msg__quien--{letra}"
            quien = f'<span class="oc-msg__quien{mod}">{e(m["de"])}</span>'
        adj = f'<span class="oc-msg__adjunto">📎 {e(m["adjunto"])}</span>' if m.get("adjunto") else ""
        hora = f'<time>{e(m["hora"])}</time>' if m.get("hora") is not None else ""
        if m.get("hora") is None:
            raise ErrorCaso("un mensaje de chat no tiene hora (la guía pide hora en cada mensaje)",
                            ctx.hoja.ruta, b.linea)
        salida.append(f'<div class="{" ".join(clases)}">{quien}{linea(texto)}{adj}{hora}</div>')
    return f'<div class="oc-chat">{"".join(salida)}</div>'


def _llamadas(filas):
    salida = []
    for f in filas or []:
        if isinstance(f, dict) and "texto" not in f:
            tipo = str(f.get("tipo", "")).lower()
            partes = [f"{FLECHAS.get(tipo, '')} {f.get('quien', '')}".strip()]
            if tipo:
                partes.append("perdida" if tipo.startswith("perdida") else tipo)
            if f.get("duracion"):
                partes.append(str(f["duracion"]))
            izq, der = " · ".join(partes), f.get("hora", "")
        elif isinstance(f, dict):
            izq, der = f.get("texto", ""), f.get("hora", "")
        else:
            izq, der = f
        salida.append(f"<div><span>{linea(izq)}</span><span>{e(der)}</span></div>")
    return f'<div class="oc-llamadas">{"".join(salida)}</div>'


def _app(filas):
    salida = "".join(f'<div class="oc-app__fila"><span>{linea(a)}</span><span>{linea(z)}</span></div>'
                     for a, z in _pares(filas or []))
    return f'<div class="oc-app">{salida}</div>'


def _celular(c, ctx, b):
    barra = f'<div class="oc-celular__barra">{e(c.get("barra", ""))}<small>{e(c.get("sub", ""))}</small></div>'
    if "chat" in c:
        cuerpo = _chat(c["chat"], ctx, b)
    elif "llamadas" in c:
        cuerpo = _llamadas(c["llamadas"])
    elif "app" in c:
        cuerpo = _app(c["app"])
    else:
        raise ErrorCaso("cada celular necesita chat:, llamadas: o app:", ctx.hoja.ruta, b.linea)
    return f'<div class="oc-celular">{barra}{cuerpo}</div>'


def c_celulares(b, ctx):
    datos = _datos(b, ctx)
    if isinstance(datos, dict):
        datos = [datos]
    return f'<div class="oc-celulares"{_columnas(b.argumento)}>{"".join(_celular(c, ctx, b) for c in datos)}</div>'


def c_videos(b, ctx):
    cuadros = []
    for v in _datos(b, ctx, list):
        alt = v.get("alt") or texto_plano(v.get("texto", ""))
        img = _img(ctx, v["imagen"], alt) if v.get("imagen") else ""
        vivo = v.get("en_vivo")
        distintivo = f'<span class="oc-video__live">{e(vivo if isinstance(vivo, str) else "EN VIVO")}</span>' if vivo else ""
        reloj = f'<span class="oc-video__reloj">{e(v["reloj"])}</span>' if v.get("reloj") else ""
        coments = "".join(f"<span><b>{e(u)}</b> {e(t)}</span>" for u, t in _pares(v.get("comentarios", []) or []))
        coments = f'<div class="oc-video__coments">{coments}</div>' if coments else ""
        pie = f'<small class="oc-video__meta">{e(v["pie"])}</small>' if v.get("pie") else ""
        texto = f'<b>{linea(v["texto"])}</b>' if v.get("texto") else ""
        cuadros.append(f'<div class="oc-video"><div class="oc-video__cuadro">{img}{distintivo}{reloj}</div>'
                       f'<div class="oc-video__pie">{texto}{pie}{coments}</div></div>')
    return f'<div class="oc-videos"{_columnas(b.argumento)}>{"".join(cuadros)}</div>'


def c_posts(b, ctx):
    posts = []
    for p in _datos(b, ctx, list):
        if p.get("imagen"):
            visual = _img(ctx, p["imagen"], p.get("alt") or texto_plano(p.get("texto", "")))
        elif p.get("historia"):
            visual = f'<div class="oc-historia" role="img" aria-label="{e(texto_plano(p["historia"]))}">{linea(p["historia"])}</div>'
        else:
            visual = ""
        meta = f"<small>{e(p['meta'])}</small>" if p.get("meta") else ""
        posts.append(f'<div class="oc-post"><div class="oc-post__cab"><i></i>{e(p.get("usuario", ""))}</div>{visual}'
                     f'<div class="oc-post__pie">{linea(p.get("texto", ""))}{meta}</div></div>')
    return f'<div class="oc-publicaciones"{_columnas(b.argumento)}>{"".join(posts)}</div>'


# --- Guía del director ------------------------------------------------------------

def _nota(b, ctx, clase, rotulo_def):
    rotulo = (b.argumento or rotulo_def).strip()
    r = f'<span class="oc-nota__rotulo">{e(rotulo)}</span>' if rotulo else ""
    return f'<div class="oc-nota {clase}">{r}<div class="oc-nota__cuerpo">{md(b.contenido)}</div></div>'


def c_nota(b, ctx):
    return _nota(b, ctx, "", "")


def c_nota_ok(b, ctx):
    return _nota(b, ctx, "oc-nota--ok", "")


def c_nota_aviso(b, ctx):
    return _nota(b, ctx, "oc-nota--aviso", "")


def c_guion(b, ctx):
    rot = f' data-rotulo="{e(b.argumento)}"' if b.argumento else ""
    return f'<div class="oc-guion"{rot}>{linea_pre(b.contenido)}</div>'


def c_pasos(b, ctx):
    pasos = "".join(f'<div class="oc-paso"><b>{e(p.get("titulo", ""))}</b><span>{linea(p.get("texto", ""))}</span></div>'
                    for p in _datos(b, ctx, list))
    return f'<div class="oc-pasos">{pasos}</div>'


# --- Hojas de trabajo del kit ------------------------------------------------------

def c_campos(b, ctx):
    salida = []
    for c in _datos(b, ctx, list):
        if isinstance(c, str):
            c = {"rotulo": c}
        tipo = c.get("tipo", "linea")
        alto = f' style="min-height:{e(c["alto"])}"' if c.get("alto") else ""
        caja = '<div class="oc-caja"%s></div>' % alto if tipo == "caja" else '<div class="oc-linea"></div>'
        salida.append(f'<div class="oc-campo-hoja"><label>{linea(c.get("rotulo", ""))}</label>{caja}</div>')
    return "".join(salida)


def c_tabla_trabajo(b, ctx):
    d = _datos(b, ctx, dict)
    cols = d.get("columnas", [])
    alto = d.get("alto")
    estilo = f' style="height:{e(alto)}"' if alto else ""
    cab = "".join(f"<th>{e(c)}</th>" for c in cols)
    filas = "".join("<tr><td>%s</td>%s</tr>" % (linea(f), f"<td{estilo}></td>" * (len(cols) - 1))
                    for f in d.get("filas", []))
    clase = "oc-tabla oc-linea-tiempo" if d.get("horario") else "oc-tabla oc-tabla--trabajo"
    return f'<div class="{clase}"><table><thead><tr>{cab}</tr></thead><tbody>{filas}</tbody></table></div>'


def c_casillas(b, ctx):
    arg = (b.argumento or "").strip()
    n = int(arg) if arg.isdigit() else int(ctx.caso.get("fichas_por_equipo", 16))
    return '<div class="oc-casillas">' + "".join(f"<span>{i}</span>" for i in range(1, n + 1)) + "</div>"


def c_menu(b, ctx):
    """Menú de preguntas generado desde personajes.yaml y tarjetas.yaml (tarjetas con menu: true)."""
    caso = ctx.caso
    salida = []
    for p in caso.personajes:
        letra = p["letra"]
        filas = []
        for g in caso.tarjetas:
            for t in g.get("tarjetas", []) or []:
                if t.get("menu") and (t.get("personaje", g.get("personaje")) == letra):
                    filas.append((t["codigo"], t.get("pregunta_menu") or t.get("pregunta", "")))
        if not filas:
            continue
        filas.append((f"{letra}◆", p.get("confrontar", "Confrontar con una prueba (indiquen cuál)")))
        quien = f'{p["nombre"]} · {p.get("rol", "")}'.strip(" ·")
        cuerpo = "".join(f'<tr><td class="c">{e(c)}</td><td>{linea(q)}</td></tr>' for c, q in filas)
        salida.append(f'<div class="oc-quien">{e(quien)}</div><div class="oc-tabla oc-tabla--menu"><table><tbody>{cuerpo}</tbody></table></div>')
    return "".join(salida)


def c_html(b, ctx):
    return b.contenido


COMPONENTES = {
    "meta": c_meta, "firma": c_firma, "declaracion": c_declaracion, "declaración": c_declaracion,
    "cita": c_cita, "manuscrito": c_manuscrito, "postit": c_postit, "plumon": c_plumon, "plumón": c_plumon,
    "mono": c_mono, "pequeno": c_pequeno, "pequeño": c_pequeno, "tabla": c_tabla, "sello": c_sello,
    "bolsa": c_bolsa, "prensa": c_prensa, "correo": c_correo, "boleta": c_boleta,
    "fotos": c_fotos, "cctv": c_cctv, "imagen": c_imagen, "svg": c_svg, "leyenda": c_leyenda,
    "celulares": c_celulares, "chat": c_celulares, "videos": c_videos, "posts": c_posts, "publicaciones": c_posts,
    "nota": c_nota, "nota-ok": c_nota_ok, "nota-aviso": c_nota_aviso, "guion": c_guion, "guión": c_guion,
    "pasos": c_pasos, "campos": c_campos, "tabla-trabajo": c_tabla_trabajo, "casillas": c_casillas,
    "menu": c_menu, "menú": c_menu, "html": c_html,
}


def render_bloques(hoja, ctx):
    ctx.hoja = hoja
    salida = []
    for b in hoja.bloques:
        if b.tipo == "md":
            salida.append(_md_con_imagenes(b.contenido, ctx))
            continue
        fn = COMPONENTES.get(b.tipo)
        if fn is None:
            raise ErrorCaso(f"no conozco el bloque ```{b.tipo}. Los disponibles son: "
                            + ", ".join(sorted(k for k in COMPONENTES if k.isascii())), hoja.ruta, b.linea)
        try:
            salida.append(fn(b, ctx))
        except ErrorCaso:
            raise
        except (KeyError, TypeError, ValueError, AttributeError) as ex:
            raise ErrorCaso(f"el bloque ```{b.tipo} tiene un dato que no entiendo ({type(ex).__name__}: {ex})",
                            hoja.ruta, b.linea) from None
    return "\n".join(salida)


def _md_con_imagenes(texto, ctx):
    htm = md(texto)

    def reemplazar(m):
        alt, src = m.group(2), m.group(1)
        if src.startswith(("http:", "https:", "file:", "data:")):
            return m.group(0)
        if src.lower().endswith(".svg"):
            return f'<span class="oc-dibujo">{ctx.svg(src, etiqueta=alt)}</span>'
        return f'<img src="{ctx.url(src)}" alt="{alt}">'

    htm = re.sub(r'<img alt="([^"]*)" src="([^"]+)"\s*/?>', lambda m: reemplazar(_swap(m)), htm)
    htm = re.sub(r'<img src="([^"]+)" alt="([^"]*)"\s*/?>', reemplazar, htm)
    # Una imagen sola en su párrafo no lleva el <p>.
    htm = re.sub(r"<p>(<span class=\"oc-dibujo\">.*?</span>)</p>", r"\1", htm, flags=re.S)
    return htm


class _swap:
    def __init__(self, m):
        self.m = m

    def group(self, i):
        return {0: self.m.group(0), 1: self.m.group(2), 2: self.m.group(1)}[i]
