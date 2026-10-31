"""F2: the team's digital folder and the delivery by QR or link (site/play/equipo, site/play/director).

The site is built into a temporary folder (the app + the Chupacabras compiled by opencase.web) and served over
http://localhost, because module scripts and service workers do not run from file://. Every test uses a fresh
browser context per device: the IndexedDB and the cache of one phone are not the other's.
"""
import json
import shutil
import time
from pathlib import Path

import pytest


REPO = Path(__file__).resolve().parent.parent.parent
CASE = "chupacabras-labranza"
FIXTURES = Path(__file__).resolve().parent / "fixtures"

pytestmark = pytest.mark.web


def _index(folder):
    return json.loads((folder / "play" / "cases" / "index.json").read_text(encoding="utf-8"))["cases"][0]


def _director(ctx, base, teams=2):
    """A director's device with a started game."""
    page = ctx.new_page()
    page.goto(base + "play/director/")
    page.wait_for_selector("#oc-start")
    page.select_option("#oc-teams", str(teams))
    page.click("#oc-start")
    page.wait_for_selector(".oc-tabs")
    return page


def _hand_out(page, team, codes):
    """Marks `codes` for `team` and returns the link of the delivery."""
    page.click("#oc-tab-give")
    page.wait_for_selector("#oc-search")
    page.evaluate("document.querySelector('.oc-chips').querySelectorAll('button').forEach(b => { if (b.dataset.team && b.getAttribute('aria-pressed') === 'true') b.click(); })")
    page.click(f".oc-chip[data-team='{team}']")
    for code in codes:
        page.fill("#oc-search", code)
        page.locator(".oc-sel", has=page.locator("strong", has_text=code)).first.locator("input").check()
    page.fill("#oc-search", "")
    page.click("#oc-give")
    page.wait_for_selector("#oc-delivery")
    link = page.get_attribute(f"#oc-delivery [data-open='{team}']", "href")
    qr = page.locator("#oc-delivery section canvas").first.evaluate("c => c.toDataURL('image/png')")
    page.click("#oc-delivery-close")
    return link, qr


def _join_link(page, team):
    page.click("#oc-tab-teams")
    return page.get_attribute(f"[data-join='{team}']", "href")


def _files(page):
    return set(page.eval_on_selector_all(".oc-item[data-file]", "els => els.map(e => e.dataset.file)"))


def _team(ctx, link, wait=True):
    page = ctx.new_page()
    reqs, sizes = [], []
    page.on("request", lambda r: reqs.append(r.url))
    page.on("requestfinished", lambda r: sizes.append(r.sizes()["responseBodySize"]))
    page.goto(link)
    if wait:
        page.wait_for_selector(".oc-tabs")
        page.wait_for_function("!document.querySelector('.oc-progress')", timeout=30000)
    return page, reqs, sizes


# --- The criteria of the plan ------------------------------------------------------------------------------------

def test_a_team_sees_only_its_delivery_works_offline_and_never_downloads_the_directors_file(site, browser):
    folder, base = site
    director_ctx = browser.new_context()
    director = _director(director_ctx, base)
    link_a, link_b = _join_link(director, "A"), _join_link(director, "B")
    delivery, _ = _hand_out(director, "B", ["E28", "B10"])
    assert "E28" not in link_b and link_b != delivery

    team_b_ctx, team_a_ctx = browser.new_context(), browser.new_context()

    # Team B joins: kit, envelope 1 and the suspects; first load under 3 MB, with photos.
    b, reqs_b, sizes_b = _team(team_b_ctx, link_b)
    folder_b = _files(b)
    assert "sheets/E01.html" in folder_b and "sheets/E28.html" not in folder_b and "cards/B10.html" not in folder_b
    assert sum(sizes_b) < 3_000_000, f"first load is {sum(sizes_b)} bytes"
    assert not any("director.json" in u for u in reqs_b)
    assert not any(("E28" in u or "B10" in u or "E06" in u) for u in reqs_b if "/cases/" in u)

    # The delivery shows up in under a second.
    t0 = time.perf_counter()
    b.goto(delivery)
    b.wait_for_selector(".oc-item[data-file='sheets/E28.html']")
    b.wait_for_selector(".oc-item[data-file='cards/B10.html']")
    assert time.perf_counter() - t0 < 1.0
    assert not any("director.json" in u for u in reqs_b)
    assert {"sheets/E28.html", "cards/B10.html"} <= _files(b)

    # Team A sees neither, and its network never asked for them.
    a, reqs_a, _ = _team(team_a_ctx, link_a)
    assert not ({"sheets/E28.html", "cards/B10.html"} & _files(a))
    assert not any(("E28" in u or "B10" in u) for u in reqs_a if "/cases/" in u)
    assert not any("director.json" in u for u in reqs_a)

    # Reload without a connection: the folder stays, and a sheet opens with its photo.
    team_b_ctx.set_offline(True)
    b.reload()
    b.wait_for_selector(".oc-item[data-file='sheets/E28.html']")
    assert {"sheets/E28.html", "cards/B10.html"} <= _files(b)
    b.click(".oc-item[data-file='sheets/E28.html'] button")
    frame = b.wait_for_selector(".oc-viewer__frame").content_frame()
    frame.wait_for_selector("article")
    frame.wait_for_function("[...document.images].length > 0 && [...document.images].every(i => i.complete && i.naturalWidth > 0)")
    assert b.is_visible("#oc-offline")


def test_a_second_delivery_adds_and_a_repeated_one_changes_nothing(site, browser):
    folder, base = site
    director = _director(browser.new_context(), base)
    join = _join_link(director, "A")
    first, _ = _hand_out(director, "A", ["E28"])
    second, _ = _hand_out(director, "A", ["E28", "B10"])
    team, _, _ = _team(browser.new_context(), join)
    team.goto(first)
    team.wait_for_selector(".oc-item[data-file='sheets/E28.html']")
    n = len(_files(team))
    team.goto(second)
    team.wait_for_selector(".oc-item[data-file='cards/B10.html']")
    assert len(_files(team)) == n + 1
    team.goto(second)
    team.wait_for_selector(".oc-item[data-file='cards/B10.html']")
    assert len(_files(team)) == n + 1


def test_envelope_two_is_one_button(site, browser):
    folder, base = site
    director = _director(browser.new_context(), base)
    join = _join_link(director, "A")
    director.click("#oc-tab-give")
    director.click("[data-envelope='2']")
    director.click("#oc-give")
    director.wait_for_selector("#oc-delivery")
    link = director.get_attribute("#oc-delivery [data-open='A']", "href")
    team, _, _ = _team(browser.new_context(), join)
    assert "sheets/E06.html" not in _files(team)
    team.goto(link)
    team.wait_for_selector(".oc-item[data-file='sheets/E06.html']")


def test_a_link_for_another_team_asks_before_replacing_the_folder(site, browser):
    folder, base = site
    director = _director(browser.new_context(), base)
    link_a, link_b = _join_link(director, "A"), _join_link(director, "B")
    team, _, _ = _team(browser.new_context(), link_a)
    assert "Equipo A" in team.text_content("header")
    team.goto(link_b)
    team.wait_for_selector(".oc-modal")
    team.click(".oc-modal .oc-btn--ghost")
    assert "Equipo A" in team.text_content("header")


def test_bad_links_are_refused(site, browser):
    folder, base = site
    ctx = browser.new_context()
    page = ctx.new_page()
    page.goto(base + "play/equipo/#oc1.%7Bnope")
    page.wait_for_selector(".oc-toast")
    page.goto(base + "play/equipo/")
    page.evaluate("""async () => {
      const { decode, encode } = await import('/play/js/delivery.js');
      const ok = { slug: 'x', lang: 'es', version: 'abcdef012345', team: 'A', seq: 1, items: [['sheets/E01.html', 'E01']] };
      if (!decode(encode(ok))) throw new Error('a good message is refused');
      for (const items of [[['../../etc/passwd', 'x']], [['sheets/a/b.html', 'x']], [['http://evil.example/x.html', 'x']], [['director.json', 'x']]])
        if (decode(encode({ ...ok, items }))) throw new Error('accepted ' + items[0][0]);
      if (decode(encode({ ...ok, version: '../' }))) throw new Error('accepted a made-up version');
    }""")


# --- The QR ------------------------------------------------------------------------------------------------------

def test_the_vendored_reader_reads_a_fixed_qr_image(site, browser):
    folder, base = site
    page = browser.new_context().new_page()
    page.goto(base + "play/equipo/")
    data = (FIXTURES / "qr_fixed.png").read_bytes()
    text = page.evaluate("""async (bytes) => {
      const { decodeImageData } = await import('/play/js/qr.js');
      const bitmap = await createImageBitmap(new Blob([new Uint8Array(bytes)], { type: 'image/png' }));
      const c = document.createElement('canvas'); c.width = bitmap.width; c.height = bitmap.height;
      const ctx = c.getContext('2d'); ctx.drawImage(bitmap, 0, 0);
      return decodeImageData(ctx.getImageData(0, 0, c.width, c.height));
    }""", list(data))
    assert text == (FIXTURES / "qr_fixed.txt").read_text(encoding="utf-8").strip()


def test_the_directors_qr_is_read_back_from_an_image(site, browser, tmp_path):
    folder, base = site
    director = _director(browser.new_context(), base)
    join = _join_link(director, "B")
    _, qr = _hand_out(director, "B", ["E28"])
    png = tmp_path / "qr.png"
    import base64
    png.write_bytes(base64.b64decode(qr.split(",", 1)[1]))
    team = browser.new_context().new_page()
    team.goto(join)
    team.wait_for_selector(".oc-tabs")
    team.wait_for_function("!document.querySelector('.oc-progress')", timeout=30000)
    team.click("#oc-scan")
    team.set_input_files("#oc-qr-file", str(png))
    team.wait_for_selector(".oc-item[data-file='sheets/E28.html']")


# --- A new deployment in the middle of the game ----------------------------------------------------------------------

def _redeploy(folder, schema_version=None):
    """What Pages does with a new deployment: the folder of the old version disappears and a new one takes its place."""
    cases = folder / "play" / "cases"
    entry = _index(folder)
    old = cases / entry["path"].removeprefix("cases/")
    new_version = "0" * 12
    new = old.parent / new_version
    shutil.copytree(old, new)
    shutil.rmtree(old)
    manifest = json.loads((new / "manifest.json").read_text(encoding="utf-8"))
    manifest["version"] = new_version
    if schema_version:
        manifest["schema_version"] = schema_version
    (new / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    index = json.loads((cases / "index.json").read_text(encoding="utf-8"))
    index["cases"][0].update(version=new_version, path=entry["path"].replace(entry["version"], new_version))
    (cases / "index.json").write_text(json.dumps(index), encoding="utf-8")


def test_a_deployment_mid_game_with_the_same_format_goes_on_with_the_new_version(site, browser):
    folder, base = site
    director = _director(browser.new_context(), base)
    join = _join_link(director, "A")
    delivery, _ = _hand_out(director, "A", ["E28"])
    team, _, _ = _team(browser.new_context(), join)
    _redeploy(folder)
    team.goto(delivery)                        # the delivery names the old version, which is gone
    team.wait_for_selector(".oc-item[data-file='sheets/E28.html']")
    team.wait_for_function("!document.querySelector('.oc-item[data-file=\"sheets/E28.html\"] .oc-pending')")
    assert team.locator(".oc-notice").count() >= 1
    team.click(".oc-item[data-file='sheets/E28.html'] button")
    team.wait_for_selector(".oc-viewer__frame").content_frame().wait_for_selector("article")
    # what was loaded before still opens
    team.click(".oc-viewer__bar button")
    team.click(".oc-item[data-file='sheets/E01.html'] button")
    team.wait_for_selector(".oc-viewer__frame").content_frame().wait_for_selector("article")


def test_a_deployment_mid_game_with_another_format_tells_the_team_to_finish_with_what_it_has(site, browser):
    folder, base = site
    director = _director(browser.new_context(), base)
    join = _join_link(director, "A")
    delivery, _ = _hand_out(director, "A", ["E28"])
    team, _, _ = _team(browser.new_context(), join)
    _redeploy(folder, schema_version=99)
    team.goto(delivery)
    team.wait_for_selector(".oc-notice--bad")
    team.wait_for_selector(".oc-item[data-file='sheets/E28.html'] .oc-pending")
    team.click(".oc-tab:nth-child(1)")
    team.click(".oc-item[data-file='sheets/E01.html'] button")        # the loaded sheets still open
    team.wait_for_selector(".oc-viewer__frame").content_frame().wait_for_selector("article")


def test_the_director_is_told_when_the_case_was_updated(site, browser):
    folder, base = site
    director = _director(browser.new_context(), base)
    _redeploy(folder)
    director.reload()
    director.wait_for_selector(".oc-notice")
