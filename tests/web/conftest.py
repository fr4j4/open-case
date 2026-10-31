"""Shared setup for the web tests: the site folder served over http://localhost and a Chromium to open it.

Module scripts and service workers do not work from file://, and localhost counts as a secure page, so
every web test (and the phases that follow) opens the site through this server. Tests that use a browser
carry the `web` mark (`pytest -m web` runs only them).
"""
import functools
import http.server
import shutil
import threading
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent.parent
SITE = REPO / "site"
TEST_JS = Path(__file__).resolve().parent / "js"


class _Handler(http.server.SimpleHTTPRequestHandler):
    """Serves site/ and, under /__tests__/, the helper scripts of tests/web/js/."""

    def translate_path(self, path):
        if path.startswith("/__tests__/"):
            return str(TEST_JS / path[len("/__tests__/"):].split("?")[0])
        return super().translate_path(path)

    def end_headers(self):
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def log_message(self, *args):
        pass


@pytest.fixture(scope="session")
def site_url():
    """http://localhost:PORT/ serving site/ (what assemble_site copies as is), in a thread."""
    handler = functools.partial(_Handler, directory=str(SITE))
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    yield f"http://localhost:{server.server_address[1]}/"
    server.shutdown()


@pytest.fixture(scope="session")
def browser():
    from playwright.sync_api import sync_playwright
    from opencase.pdf import open_browser      # the same search the exporter does (OPENCASE_CHROMIUM, Playwright, Chrome)
    with sync_playwright() as p:
        b, _name = open_browser(p)
        yield b
        b.close()


@pytest.fixture
def context(browser):
    """A fresh browser context (the pages of one context share BroadcastChannel and localStorage)."""
    ctx = browser.new_context()
    yield ctx
    ctx.close()


def pytest_collection_modifyitems(items):
    for item in items:
        if "tests/web/" in str(item.fspath).replace("\\", "/") or "tests\\web\\" in str(item.fspath):
            item.add_marker(pytest.mark.web)


# --- The built site: the app + the compiled case, as the CI deploys it (without the PDFs) ---------------------------

class _PlainHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


def serve_folder(folder):
    """Serve `folder` over http://localhost in a thread. Returns the server (call .shutdown() when done)."""
    handler = functools.partial(_PlainHandler, directory=str(folder))
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server


@pytest.fixture(scope="session")
def built(tmp_path_factory):
    """site/ (the app) + the Chupacabras compiled by opencase.web, in a temporary folder."""
    from opencase import web
    out = tmp_path_factory.mktemp("site")
    shutil.copytree(SITE, out, dirs_exist_ok=True)
    web.build_cases([REPO / "cases" / "chupacabras-labranza"], out)
    return out


@pytest.fixture
def site(built, tmp_path):
    """A private copy of the built site (some tests change it, as a new deployment would) and its URL."""
    folder = tmp_path / "site"
    shutil.copytree(built, folder)
    server = serve_folder(folder)
    yield folder, f"http://localhost:{server.server_address[1]}/"
    server.shutdown()
