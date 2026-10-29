"""Descarga las fuentes de Google Fonts que usa Open Case y las deja en diseno/fuentes/.

Solo hace falta correrlo si se agrega una familia o se quiere actualizar las que ya están:
el repo trae los archivos .woff2 y sus licencias, así que el exportador funciona sin conexión.

    python3 herramientas/bajar_fuentes.py
"""
import re
import urllib.request
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
DESTINO = RAIZ / "diseno" / "fuentes"

FAMILIAS = [
    ("Barlow Condensed", "wght@500;600;700", "ofl/barlowcondensed"),
    ("Public Sans", "ital,wght@0,400;0,600;0,800;1,400", "ofl/publicsans"),
    ("IBM Plex Mono", "wght@400;600", "ofl/ibmplexmono"),
    ("Special Elite", None, "apache/specialelite"),
    ("Courier Prime", "wght@400;700", "ofl/courierprime"),
    ("Caveat", "wght@500;700", "ofl/caveat"),
    ("Nothing You Could Do", None, "ofl/nothingyoucoulddo"),
    ("Permanent Marker", None, "apache/permanentmarker"),
    ("Homemade Apple", None, "apache/homemadeapple"),
    ("Dancing Script", "wght@500", "ofl/dancingscript"),
    ("Playfair Display", "wght@700;900", "ofl/playfairdisplay"),
    ("Libre Baskerville", "ital,wght@0,400;0,700;1,400", "ofl/librebaskerville"),
    ("Roboto", "wght@400;500;700", "ofl/roboto"),
]
# Solo los alfabetos que usa un caso en español o inglés, más flechas y signos.
SUBCONJUNTOS = {"latin", "latin-ext", "symbols", "math"}
NAVEGADOR = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"


def bajar(url):
    req = urllib.request.Request(url, headers={"User-Agent": NAVEGADOR})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read()


def slug(nombre):
    return nombre.lower().replace(" ", "-")


def main():
    DESTINO.mkdir(parents=True, exist_ok=True)
    reglas = ["/* Fuentes de Open Case, servidas desde el repo. Generado por herramientas/bajar_fuentes.py */"]
    for familia, ejes, repo in FAMILIAS:
        q = familia.replace(" ", "+") + (":" + ejes if ejes else "")
        css = bajar(f"https://fonts.googleapis.com/css2?family={q}&display=swap").decode()
        for sub, cuerpo in re.findall(r"/\* ([a-z-]+) \*/\s*@font-face\s*\{(.*?)\}", css, re.S):
            if sub not in SUBCONJUNTOS:
                continue
            estilo = re.search(r"font-style:\s*(\w+)", cuerpo).group(1)
            peso = re.search(r"font-weight:\s*(\d+)", cuerpo).group(1)
            url = re.search(r"url\((https://[^)]+)\)", cuerpo).group(1)
            rango = re.search(r"unicode-range:\s*([^;]+);", cuerpo).group(1)
            archivo = f"{slug(familia)}-{peso}{'-italic' if estilo == 'italic' else ''}-{sub}.woff2"
            (DESTINO / archivo).write_bytes(bajar(url))
            reglas.append(
                "@font-face{font-family:'%s';font-style:%s;font-weight:%s;font-display:block;"
                "src:url(%s) format('woff2');unicode-range:%s}" % (familia, estilo, peso, archivo, rango)
            )
        carpeta = DESTINO / "licencias"
        carpeta.mkdir(exist_ok=True)
        nombre_lic = "OFL.txt" if repo.startswith("ofl/") else "LICENSE.txt"
        lic = bajar(f"https://raw.githubusercontent.com/google/fonts/main/{repo}/{nombre_lic}")
        (carpeta / f"{slug(familia)}-{nombre_lic}").write_bytes(lic)
        print("ok", familia)
    (DESTINO / "fuentes.css").write_text("\n".join(reglas) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
