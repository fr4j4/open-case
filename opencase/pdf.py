"""HTML -> PDF con Chromium (vía Playwright), con revisión de tarjetas y hojas antes de imprimir."""
import os
import shutil
import re
from pathlib import Path

MM = 96 / 25.4   # px por milímetro

# Se ejecuta en la página antes de imprimir. Si el texto de una tarjeta no cabe, baja la letra
# en tres pasos (12,5 px -> 11,34 px = 8,5 pt, el mínimo de la norma). Si igual no cabe, la marca.
JS_AJUSTAR_TARJETAS = """
() => {
  const informe = [];
  const rebalsa = (t) => {
    const r = t.querySelector('.oc-tarjeta__respuesta');
    return t.scrollHeight > t.clientHeight + 1 || (r && r.scrollHeight > r.clientHeight + 1);
  };
  for (const t of document.querySelectorAll('.oc-tarjeta[data-codigo]')) {
    let paso = 0;
    while (rebalsa(t) && paso < 3) {
      if (paso) t.classList.remove('oc-tarjeta--ajuste-' + paso);
      paso += 1;
      t.classList.add('oc-tarjeta--ajuste-' + paso);
    }
    if (rebalsa(t)) { t.classList.add('oc-tarjeta--desborda'); informe.push({codigo: t.dataset.codigo, estado: 'no cabe'}); }
    else if (paso) informe.push({codigo: t.dataset.codigo, estado: 'letra reducida ' + paso});
  }
  return informe;
}
"""

JS_MEDIR_HOJAS = """
(altoPagina) => {
  const out = [];
  for (const h of document.querySelectorAll('article.oc-hoja')) {
    const alto = h.getBoundingClientRect().height;
    const codigo = (h.querySelector('.oc-codigo') || {}).textContent || h.id;
    out.push({id: h.id, codigo: codigo, paginas: Math.ceil((alto - 2) / altoPagina)});
  }
  return out;
}
"""

JS_ESPERAR = """
async () => {
  await document.fonts.ready;
  await Promise.all([...document.images].map(i => i.complete ? null : new Promise(r => { i.onload = i.onerror = r; })));
  const rotas = [...document.images].filter(i => !i.naturalWidth).map(i => i.getAttribute('src'));
  return rotas;
}
"""


class ErrorNavegador(Exception):
    pass


def abrir_navegador(pw):
    """Busca un Chromium: el que indique OPENCASE_CHROMIUM, el de Playwright, o Chrome/Edge instalados."""
    intentos = []
    ruta = os.environ.get("OPENCASE_CHROMIUM")
    if ruta:
        intentos.append(("OPENCASE_CHROMIUM", dict(executable_path=ruta)))
    intentos.append(("Chromium de Playwright", {}))
    intentos.append(("Google Chrome", dict(channel="chrome")))
    intentos.append(("Microsoft Edge", dict(channel="msedge")))
    for ejecutable in ("chromium", "chromium-browser", "google-chrome"):
        encontrado = shutil.which(ejecutable)
        if encontrado:
            intentos.append((encontrado, dict(executable_path=encontrado)))
    errores = []
    for nombre, opciones in intentos:
        try:
            return pw.chromium.launch(**opciones), nombre
        except Exception as ex:  # noqa: BLE001 - se informa al final
            errores.append(f"  {nombre}: {str(ex).splitlines()[0][:160]}")
    raise ErrorNavegador("No encontré un navegador para generar los PDF. Corre `python -m playwright install chromium` "
                         "(o `make instalar`), o indica uno con la variable OPENCASE_CHROMIUM.\n" + "\n".join(errores))


def exportar(docs, carpeta_html, carpeta_pdf, papel_alto_mm=279, margen_mm=14, imagenes=False, avisar=print):
    from playwright.sync_api import sync_playwright

    carpeta_html = Path(carpeta_html).resolve()
    carpeta_html.mkdir(parents=True, exist_ok=True)
    resultados = []
    with sync_playwright() as pw:
        navegador, nombre = abrir_navegador(pw)
        avisar(f"  navegador: {nombre}")
        contexto = navegador.new_context(viewport={"width": 900, "height": 1200}, device_scale_factor=2)
        pagina = contexto.new_page()
        for doc in docs:
            ruta_html = carpeta_html / f"{doc.archivo}.html"
            ruta_html.write_text(doc.html, encoding="utf-8")
            destino = Path(carpeta_pdf) / doc.carpeta / f"{doc.archivo}.pdf"
            destino.parent.mkdir(parents=True, exist_ok=True)
            pagina.emulate_media(media="print")
            pagina.set_viewport_size({"width": round((216 - 2 * margen_mm) * MM), "height": 1200})
            pagina.goto(ruta_html.as_uri(), wait_until="load")
            rotas = pagina.evaluate(JS_ESPERAR)
            for r in rotas:
                avisar(f"  ! {doc.archivo}: no se pudo cargar la imagen {r}")
            ajustes = pagina.evaluate(JS_AJUSTAR_TARJETAS)
            largas = []
            if doc.revisar_hojas:
                largas = [h for h in pagina.evaluate(JS_MEDIR_HOJAS, (papel_alto_mm - 2 * margen_mm) * MM)
                          if h["paginas"] > 1]
            pagina.pdf(path=str(destino), prefer_css_page_size=True, print_background=True)
            if imagenes and doc.carpeta and doc.revisar_hojas:
                _imagenes(pagina, doc, Path(carpeta_pdf) / "whatsapp")
            resultados.append({"doc": doc, "pdf": destino, "ajustes": ajustes, "largas": largas})
        navegador.close()
    return resultados


def _imagenes(pagina, doc, carpeta):
    """Una imagen por hoja, para mandarla por el grupo de WhatsApp del equipo."""
    carpeta = carpeta / doc.archivo
    carpeta.mkdir(parents=True, exist_ok=True)
    pagina.emulate_media(media="screen")
    pagina.set_viewport_size({"width": 860, "height": 1200})
    pagina.evaluate(JS_ESPERAR)
    usados = {}
    for h in pagina.query_selector_all("article.oc-hoja:not(.oc-tapa):not(.oc-caratula)"):
        cod = (h.eval_on_selector(".oc-codigo", "e => e.textContent") if h.query_selector(".oc-codigo") else h.get_attribute("id")) or "hoja"
        nombre = re.sub(r"_+", "_", "".join(c if c.isalnum() else "_" for c in cod)).strip("_")
        usados[nombre] = usados.get(nombre, 0) + 1
        if usados[nombre] > 1:
            nombre += f"_{usados[nombre]}"
        h.screenshot(path=str(carpeta / f"{nombre}.png"))


def contar_paginas(ruta):
    try:
        from pypdf import PdfReader
        return len(PdfReader(str(ruta)).pages)
    except Exception:  # noqa: BLE001
        return None
