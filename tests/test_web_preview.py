"""tools/web_preview.py: the light site build, the local server and the tunnel's URL (with a fake cloudflared)."""
import os
import stat
import sys
import urllib.request

import pytest

sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent.parent / "tools"))
import web_preview  # noqa: E402


def test_parse_tunnel_url():
    line = "2026-11-01T10:00:00Z INF |  https://quiet-river-happy-cat.trycloudflare.com  |"
    assert web_preview.parse_tunnel_url(line) == "https://quiet-river-happy-cat.trycloudflare.com"
    assert web_preview.parse_tunnel_url("INF Requesting new quick Tunnel on trycloudflare.com...") is None


def test_build_and_serve(tmp_path):
    out = web_preview.build(tmp_path / "preview")
    for f in ("index.html", "lab/red/index.html", "lab/red/red.js", "play/js/transport/config.js", "play/vendor/trystero-nostr.js"):
        assert (out / f).exists(), f
    server, port = web_preview.serve(out, 0)
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/lab/red/index.html") as r:
            assert r.status == 200
            assert r.headers["Cache-Control"] == "no-store"
            assert b"Prueba de red" in r.read()
    finally:
        server.shutdown()


def test_no_tunnel_without_cloudflared(monkeypatch):
    monkeypatch.setattr(web_preview.shutil, "which", lambda name: None)
    assert web_preview.open_tunnel(1234, timeout=1) == (None, None)


@pytest.mark.skipif(os.name == "nt", reason="the fake cloudflared is a shell script")
def test_tunnel_url_is_read_from_cloudflared(tmp_path, monkeypatch):
    fake = tmp_path / "cloudflared"
    fake.write_text('#!/bin/sh\necho "INF starting"\necho "INF |  https://fake-name-123.trycloudflare.com  |"\nsleep 30\n')
    fake.chmod(fake.stat().st_mode | stat.S_IEXEC)
    monkeypatch.setenv("PATH", f"{tmp_path}{os.pathsep}{os.environ['PATH']}")
    proc, url = web_preview.open_tunnel(1234, timeout=10)
    try:
        assert url == "https://fake-name-123.trycloudflare.com"
    finally:
        proc.terminate()
