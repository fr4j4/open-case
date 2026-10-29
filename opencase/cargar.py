"""Lectura de la carpeta de un caso: YAML, hojas en Markdown con bloques y validaciones."""
import re
from dataclasses import dataclass, field
from pathlib import Path

import yaml


class ErrorCaso(Exception):
    """Un error en los archivos del caso, con el archivo y la línea si se conocen."""

    def __init__(self, mensaje, archivo=None, linea=None):
        self.archivo = archivo
        self.linea = linea
        donde = ""
        if archivo:
            donde = str(archivo) + (f":{linea}" if linea else "") + ": "
        super().__init__(donde + mensaje)


# --- YAML sin sorpresas -------------------------------------------------------
# YAML 1.1 convierte 07:12 en un número (sexagesimal) y "no" en False. En un caso
# hay horas y respuestas cortas por todas partes, así que el cargador solo
# reconoce enteros decimales, decimales con punto y true/false.

class _Cargador(yaml.SafeLoader):
    pass


_Cargador.yaml_implicit_resolvers = {
    k: [r for r in v if r[0] not in ("tag:yaml.org,2002:bool", "tag:yaml.org,2002:int",
                                      "tag:yaml.org,2002:float", "tag:yaml.org,2002:timestamp")]
    for k, v in yaml.SafeLoader.yaml_implicit_resolvers.items()
}
_Cargador.add_implicit_resolver("tag:yaml.org,2002:bool", re.compile(r"^(?:true|false)$"), list("tf"))
_Cargador.add_implicit_resolver("tag:yaml.org,2002:int", re.compile(r"^-?(?:0|[1-9][0-9]*)$"), list("-0123456789"))
_Cargador.add_implicit_resolver("tag:yaml.org,2002:float", re.compile(r"^-?(?:0|[1-9][0-9]*)\.[0-9]+$"), list("-0123456789"))


def leer_yaml(texto, archivo=None, linea_base=0):
    try:
        return yaml.load(texto, Loader=_Cargador)
    except yaml.YAMLError as e:
        linea = None
        marca = getattr(e, "problem_mark", None)
        if marca is not None:
            linea = linea_base + marca.line + 1
        raise ErrorCaso("YAML inválido: " + str(getattr(e, "problem", e)), archivo, linea) from None


def leer_archivo_yaml(ruta):
    ruta = Path(ruta)
    if not ruta.exists():
        raise ErrorCaso("no existe", ruta)
    datos = leer_yaml(ruta.read_text(encoding="utf-8"), ruta)
    return datos if datos is not None else {}


# --- Hojas en Markdown ----------------------------------------------------------

@dataclass
class Bloque:
    tipo: str            # "md" para prosa; si no, el nombre del componente
    argumento: str       # lo que va después del nombre en la línea ```nombre argumento
    contenido: str
    linea: int


@dataclass
class Hoja:
    id: str              # nombre del archivo sin extensión
    ruta: Path
    datos: dict          # encabezado YAML
    bloques: list = field(default_factory=list)

    def get(self, clave, defecto=None):
        return self.datos.get(clave, defecto)


_CERCO = re.compile(r"^(`{3,}|~{3,})\s*([A-Za-z][\w-]*)?[ \t]*(.*?)\s*$")


def partir_bloques(texto, linea_base=1):
    """Separa el cuerpo en prosa Markdown y bloques ```componente.

    Un bloque cercado sin nombre, o con un nombre de lenguaje que no es un componente,
    se deja como código dentro de la prosa (lo decide quien renderiza)."""
    bloques = []
    prosa, inicio_prosa = [], linea_base
    lineas = texto.split("\n")
    i = 0
    while i < len(lineas):
        m = _CERCO.match(lineas[i])
        if m and m.group(2):
            cerco, tipo, arg = m.group(1), m.group(2), m.group(3)
            j = i + 1
            while j < len(lineas) and not lineas[j].strip().startswith(cerco[0] * len(cerco)):
                j += 1
            if j >= len(lineas):
                raise ErrorCaso(f"el bloque ```{tipo} no se cierra", None, linea_base + i)
            if any(l.strip() for l in prosa):
                bloques.append(Bloque("md", "", "\n".join(prosa), inicio_prosa))
            bloques.append(Bloque(tipo.lower(), arg, "\n".join(lineas[i + 1:j]), linea_base + i))
            prosa, inicio_prosa = [], linea_base + j + 1
            i = j + 1
            continue
        prosa.append(lineas[i])
        i += 1
    if any(l.strip() for l in prosa):
        bloques.append(Bloque("md", "", "\n".join(prosa), inicio_prosa))
    return bloques


def leer_hoja(ruta):
    ruta = Path(ruta)
    texto = ruta.read_text(encoding="utf-8").replace("\r\n", "\n")
    datos, cuerpo, linea_cuerpo = {}, texto, 1
    if texto.startswith("---\n"):
        fin = texto.find("\n---", 4)
        if fin < 0:
            raise ErrorCaso("el encabezado (---) no se cierra", ruta, 1)
        datos = leer_yaml(texto[4:fin], ruta, 1) or {}
        if not isinstance(datos, dict):
            raise ErrorCaso("el encabezado debe ser una lista de campos clave: valor", ruta, 2)
        resto = texto[fin + 4:]
        linea_cuerpo = texto[:fin + 4].count("\n") + 1
        if resto.startswith("\n"):
            resto = resto[1:]
            linea_cuerpo += 1
        cuerpo = resto
    try:
        bloques = partir_bloques(cuerpo, linea_cuerpo)
    except ErrorCaso as e:
        raise ErrorCaso(str(e).split(": ", 1)[-1], ruta, e.linea) from None
    return Hoja(ruta.stem, ruta, datos, bloques)


def leer_carpeta_hojas(carpeta):
    carpeta = Path(carpeta)
    if not carpeta.is_dir():
        return []
    return [leer_hoja(p) for p in sorted(carpeta.glob("*.md"))]


# --- El caso completo -----------------------------------------------------------

@dataclass
class Caso:
    raiz: Path
    datos: dict
    personajes: list
    tarjetas: list          # grupos de tarjetas
    kit: list               # hojas
    expediente: dict        # id -> Hoja
    guia: list              # hojas
    avisos: list = field(default_factory=list)   # advertencias de validación

    @property
    def titulo(self):
        return self.datos["titulo"]

    def get(self, clave, defecto=None):
        return self.datos.get(clave, defecto)

    def personaje(self, letra):
        for p in self.personajes:
            if p.get("letra") == letra:
                return p
        return None


def normalizar_codigo(codigo):
    """E17·B, E17 · B y E17-B se consideran el mismo código."""
    return re.sub(r"\s*[·\-]\s*", "·", str(codigo).strip()).upper()


def cargar_caso(raiz):
    raiz = Path(raiz).resolve()
    if not (raiz / "caso.yaml").exists():
        raise ErrorCaso("no hay un caso.yaml en esta carpeta", raiz)
    datos = leer_archivo_yaml(raiz / "caso.yaml")
    for campo in ("titulo",):
        if not datos.get(campo):
            raise ErrorCaso(f"falta el campo '{campo}'", raiz / "caso.yaml")
    personajes = []
    if (raiz / "personajes.yaml").exists():
        personajes = leer_archivo_yaml(raiz / "personajes.yaml").get("sospechosos", []) or []
    tarjetas = []
    if (raiz / "tarjetas.yaml").exists():
        tarjetas = leer_archivo_yaml(raiz / "tarjetas.yaml").get("grupos", []) or []
    expediente = {h.id: h for h in leer_carpeta_hojas(raiz / "expediente")}
    caso = Caso(raiz, datos, personajes, tarjetas,
                leer_carpeta_hojas(raiz / "kit"), expediente, leer_carpeta_hojas(raiz / "guia"))
    validar(caso)
    return caso


def validar(caso):
    """Revisa referencias cruzadas. Los errores detienen la exportación; los avisos no."""
    archivo_caso = caso.raiz / "caso.yaml"
    # Secciones del expediente: cada id debe existir y aparecer una sola vez.
    vistos = {}
    for sec in caso.get("expediente", {}).get("secciones", []) or []:
        for pid in sec.get("pruebas", []) or []:
            if pid not in caso.expediente:
                raise ErrorCaso(f"la sección '{sec.get('titulo')}' nombra '{pid}', pero no existe expediente/{pid}.md",
                                archivo_caso)
            if pid in vistos:
                raise ErrorCaso(f"'{pid}' aparece en dos secciones ('{vistos[pid]}' y '{sec.get('titulo')}')",
                                archivo_caso)
            vistos[pid] = sec.get("titulo")
    for pid in caso.expediente:
        if pid not in vistos:
            caso.avisos.append(f"expediente/{pid}.md no está en ninguna sección de caso.yaml y no se exporta")
    # Códigos que entregan las tarjetas.
    codigos = {normalizar_codigo(h.get("codigo", h.id)) for h in caso.expediente.values()}
    vistos_tarjetas = set()
    for g in caso.tarjetas:
        for t in g.get("tarjetas", []) or []:
            cod = t.get("codigo")
            if not cod:
                raise ErrorCaso(f"una tarjeta del grupo '{g.get('titulo')}' no tiene código", caso.raiz / "tarjetas.yaml")
            if cod in vistos_tarjetas:
                caso.avisos.append(f"la tarjeta {cod} está repetida en tarjetas.yaml")
            vistos_tarjetas.add(cod)
            for adj in _lista(t.get("adjunta")):
                if normalizar_codigo(adj) not in codigos:
                    caso.avisos.append(f"la tarjeta {cod} adjunta {adj}, que no está en el expediente")
            largo = len(re.sub(r"[*_`]", "", str(t.get("respuesta", ""))))
            if largo > 420:
                caso.avisos.append(f"la tarjeta {cod} tiene {largo} caracteres (la norma es 420 como máximo)")
    # Fotos e imágenes referenciadas.
    for hoja in list(caso.expediente.values()) + caso.kit + caso.guia:
        for b in hoja.bloques:
            for ref in re.findall(r"(?:imagen|retrato|archivo):\s*[\"']?([^\s\"'\n]+\.(?:jpe?g|png|webp|svg|gif))", b.contenido) + \
                    re.findall(r"!\[[^\]]*\]\(([^)\s]+)\)", b.contenido):
                if not (caso.raiz / ref).exists():
                    raise ErrorCaso(f"la imagen '{ref}' no existe en la carpeta del caso", hoja.ruta, b.linea)


def _lista(v):
    if v is None:
        return []
    if isinstance(v, (list, tuple)):
        return list(v)
    return [x.strip() for x in str(v).split(",") if x.strip()]
