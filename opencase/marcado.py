"""Markdown de las hojas y de los textos cortos, con los agregados de Open Case.

Además del Markdown de siempre (negrita, cursiva, listas, tablas):
  ==texto==            resaltador amarillo sobre lo impreso
  [verdad] [mentira]   pastillas de la guía del director (también [clave], [adjunta],
  [pista falsa]        [diligencia], [pendiente])
  `E01`                un código en la tipografía de códigos
"""
import html
import re

import markdown as _markdown

PASTILLAS = {
    "verdad": "oc-pastilla--v",
    "mentira": "oc-pastilla--m",
    "clave": "oc-pastilla--k",
    "pista falsa": "oc-pastilla--k",
    "adjunta": "oc-pastilla--d",
    "diligencia": "oc-pastilla--d",
    "pendiente": "",
}
_RE_PASTILLA = re.compile(r"\[(" + "|".join(re.escape(k) for k in PASTILLAS) + r")\](?!\()", re.I)
_RE_RESALTADO = re.compile(r"==(?=\S)(.+?)(?<=\S)==")


def e(texto):
    """Escapa texto plano para HTML."""
    return html.escape("" if texto is None else str(texto), quote=True)


def _pastilla(m):
    palabra = m.group(1)
    clase = PASTILLAS[palabra.lower()]
    return f'<span class="oc-pastilla {clase}">{palabra.lower()}</span>'


def _despues(htm):
    htm = _RE_RESALTADO.sub(r'<mark class="oc-resaltado">\1</mark>', htm)
    htm = _RE_PASTILLA.sub(_pastilla, htm)
    # Las tablas de Markdown se envuelven como las del sistema de diseño.
    htm = re.sub(r"<table>", '<div class="oc-tabla"><table>', htm)
    htm = re.sub(r"</table>", "</table></div>", htm)
    return htm


def _md():
    return _markdown.Markdown(extensions=["tables", "sane_lists", "attr_list"], output_format="html")


def md(texto):
    """Markdown de bloque: párrafos, listas, tablas, títulos."""
    if not texto:
        return ""
    texto = re.sub(r"(?m)^\{\.(\w[\w-]*)\}[ \t]*$", lambda m: "{: .oc-" + m.group(1) + "}", texto)
    return _despues(_md().convert(str(texto)))


def linea(texto):
    """Markdown en línea para campos cortos (una respuesta, un pie de foto). Respeta saltos de línea."""
    if texto is None:
        return ""
    texto = str(texto).strip()
    if not texto:
        return ""
    partes = [p for p in re.split(r"\n\s*\n", texto)]
    salida = []
    for p in partes:
        htm = _md().convert(p.replace("\n", "  \n"))
        htm = re.sub(r"^<p>(.*)</p>$", r"\1", htm.strip(), flags=re.S)
        salida.append(htm)
    return _despues("<br><br>".join(salida) if len(salida) > 1 else salida[0])


def linea_pre(texto):
    """Para bloques que respetan los saltos de línea tal cual (declaraciones, guiones, citas):
    Markdown en línea en cada renglón, sin agregar <br>."""
    if texto is None:
        return ""
    renglones = []
    for r in str(texto).strip("\n").split("\n"):
        htm = _md().convert(r) if r.strip() else ""
        renglones.append(re.sub(r"^<p>(.*)</p>$", r"\1", htm.strip(), flags=re.S))
    return _despues("\n".join(renglones))


def texto_plano(texto):
    """Quita las marcas de Markdown (para contar caracteres o para un atributo alt)."""
    t = re.sub(r"[*_`]|==", "", str(texto or ""))
    return re.sub(r"\s+", " ", t).strip()
