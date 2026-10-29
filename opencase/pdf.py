"""HTML -> PDF with Chromium (through Playwright), checking cards and sheets before printing."""
import os
import shutil
import re
from pathlib import Path

MM = 96 / 25.4   # px per millimetre

# Runs in the page before printing. If a card's text does not fit, it lowers the type in three
# steps (12.5 px -> 11.34 px = 8.5 pt, the minimum of the card standard). If it still does not fit,
# the card is marked.
JS_FIT_CARDS = """
() => {
  const report = [];
  const overflows = (t) => {
    const r = t.querySelector('.oc-tarjeta__respuesta');
    return t.scrollHeight > t.clientHeight + 1 || (r && r.scrollHeight > r.clientHeight + 1);
  };
  for (const t of document.querySelectorAll('.oc-tarjeta[data-code]')) {
    let step = 0;
    while (overflows(t) && step < 3) {
      if (step) t.classList.remove('oc-tarjeta--ajuste-' + step);
      step += 1;
      t.classList.add('oc-tarjeta--ajuste-' + step);
    }
    if (overflows(t)) { t.classList.add('oc-tarjeta--desborda'); report.push({code: t.dataset.code, status: 'overflow'}); }
    else if (step) report.push({code: t.dataset.code, status: 'smaller type ' + step});
  }
  return report;
}
"""

JS_MEASURE_SHEETS = """
(pageHeight) => {
  const out = [];
  for (const h of document.querySelectorAll('article.oc-hoja')) {
    const height = h.getBoundingClientRect().height;
    const code = (h.querySelector('.oc-codigo') || {}).textContent || h.id;
    out.push({id: h.id, code: code, pages: Math.ceil((height - 2) / pageHeight)});
  }
  return out;
}
"""

JS_WAIT = """
async () => {
  await document.fonts.ready;
  await Promise.all([...document.images].map(i => i.complete ? null : new Promise(r => { i.onload = i.onerror = r; })));
  const broken = [...document.images].filter(i => !i.naturalWidth).map(i => i.getAttribute('src'));
  return broken;
}
"""


class BrowserError(Exception):
    pass


def open_browser(pw):
    """Finds a Chromium: the one in OPENCASE_CHROMIUM, Playwright's own, or an installed Chrome/Edge."""
    attempts = []
    path = os.environ.get("OPENCASE_CHROMIUM")
    if path:
        attempts.append(("OPENCASE_CHROMIUM", dict(executable_path=path)))
    attempts.append(("Playwright Chromium", {}))
    attempts.append(("Google Chrome", dict(channel="chrome")))
    attempts.append(("Microsoft Edge", dict(channel="msedge")))
    for executable in ("chromium", "chromium-browser", "google-chrome"):
        found = shutil.which(executable)
        if found:
            attempts.append((found, dict(executable_path=found)))
    errors = []
    for name, options in attempts:
        try:
            return pw.chromium.launch(**options), name
        except Exception as ex:  # noqa: BLE001 - reported at the end
            errors.append(f"  {name}: {str(ex).splitlines()[0][:160]}")
    raise BrowserError("I could not find a browser to make the PDFs. Run `python -m playwright install chromium` "
                       "(or `make install`), or point OPENCASE_CHROMIUM at one.\n" + "\n".join(errors))


def export(docs, html_dir, pdf_dir, paper_height_mm=279, margin_mm=14, images=False, report=print):
    from playwright.sync_api import sync_playwright

    html_dir = Path(html_dir).resolve()
    html_dir.mkdir(parents=True, exist_ok=True)
    results = []
    with sync_playwright() as pw:
        browser, name = open_browser(pw)
        report(f"  browser: {name}")
        context = browser.new_context(viewport={"width": 900, "height": 1200}, device_scale_factor=2)
        page = context.new_page()
        for doc in docs:
            html_path = html_dir / f"{doc.file}.html"
            html_path.write_text(doc.html, encoding="utf-8")
            target = Path(pdf_dir) / doc.folder / f"{doc.file}.pdf"
            target.parent.mkdir(parents=True, exist_ok=True)
            page.emulate_media(media="print")
            page.set_viewport_size({"width": round((216 - 2 * margin_mm) * MM), "height": 1200})
            page.goto(html_path.as_uri(), wait_until="load")
            broken = page.evaluate(JS_WAIT)
            for r in broken:
                report(f"  ! {doc.file}: could not load the image {r}")
            fits = page.evaluate(JS_FIT_CARDS)
            long_sheets = []
            if doc.check_sheets:
                long_sheets = [h for h in page.evaluate(JS_MEASURE_SHEETS, (paper_height_mm - 2 * margin_mm) * MM)
                               if h["pages"] > 1]
            page.pdf(path=str(target), prefer_css_page_size=True, print_background=True)
            if images and doc.folder and doc.check_sheets:
                _chat_images(page, doc, Path(pdf_dir) / "chat-images")
            results.append({"doc": doc, "pdf": target, "fits": fits, "long_sheets": long_sheets})
        browser.close()
    return results


def _chat_images(page, doc, folder):
    """One image per sheet, to send through the team's chat group."""
    folder = folder / doc.file
    folder.mkdir(parents=True, exist_ok=True)
    page.emulate_media(media="screen")
    page.set_viewport_size({"width": 860, "height": 1200})
    page.evaluate(JS_WAIT)
    used = {}
    for h in page.query_selector_all("article.oc-hoja:not(.oc-tapa):not(.oc-caratula)"):
        code = (h.eval_on_selector(".oc-codigo", "e => e.textContent") if h.query_selector(".oc-codigo") else h.get_attribute("id")) or "sheet"
        name = re.sub(r"_+", "_", "".join(c if c.isalnum() else "_" for c in code)).strip("_")
        used[name] = used.get(name, 0) + 1
        if used[name] > 1:
            name += f"_{used[name]}"
        h.screenshot(path=str(folder / f"{name}.png"))


def count_pages(path):
    try:
        from pypdf import PdfReader
        return len(PdfReader(str(path)).pages)
    except Exception:  # noqa: BLE001
        return None
