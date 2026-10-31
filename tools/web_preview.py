"""Previews the website on phones through a free HTTPS tunnel.

    python3 tools/web_preview.py             (or: make web-preview)
    python3 tools/web_preview.py --port 9000 --no-tunnel

Phones need the pages over HTTPS (WebRTC libraries, the service worker and crypto.subtle only work in
secure pages), and GitHub Pages only publishes `main`. So this script builds the light site (the static
files of site/, no PDFs and no Chromium), serves it from this computer and, if `cloudflared` is installed,
opens a Cloudflare Quick Tunnel (no account) that gives a public https URL for as long as the script runs.

When `opencase/web.py` exists (phase F1) and the Makefile has a `web` target, its output (play/cases/) is
added to the preview too.

Install cloudflared once:  https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/downloads/
  macOS: brew install cloudflared      Windows: winget install Cloudflare.cloudflared
"""
import argparse
import http.server
import re
import shutil
import subprocess
import sys
import threading
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

TUNNEL_URL = re.compile(r"https://[a-z0-9-]+\.trycloudflare\.com")
LAB_PATH = "lab/red/"


def parse_tunnel_url(line):
    """The https URL cloudflared prints when the tunnel is up, or None."""
    m = TUNNEL_URL.search(line)
    return m.group(0) if m else None


def build(out):
    """Assembles the site in `out` (emptied first). Returns the folder."""
    from opencase.site import assemble_site
    out = Path(out)
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    assemble_site(out)
    makefile = ROOT / "Makefile"
    if (ROOT / "opencase" / "web.py").exists() and makefile.exists() and re.search(r"^web:", makefile.read_text(encoding="utf-8"), re.M):
        r = subprocess.run(["make", "-s", "web", f"ARGS=--out {out}"], cwd=ROOT)
        if r.returncode != 0:
            print("Aviso: `make web` falló; la vista previa sigue sin play/cases/.", file=sys.stderr)
    return out


class Handler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header("Cache-Control", "no-store")     # what you edit is what the phone loads
        super().end_headers()

    def log_message(self, fmt, *args):
        pass


def serve(directory, port=0):
    """Serves `directory` on localhost in a thread. Returns (server, port)."""
    handler = lambda *a, **k: Handler(*a, directory=str(directory), **k)
    server = http.server.ThreadingHTTPServer(("127.0.0.1", port), handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server, server.server_address[1]


def open_tunnel(port, timeout=40):
    """Starts cloudflared. Returns (process, url) or (None, None) when it is not installed or gives no URL."""
    exe = shutil.which("cloudflared")
    if not exe:
        return None, None
    proc = subprocess.Popen([exe, "tunnel", "--no-autoupdate", "--url", f"http://127.0.0.1:{port}"],
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    found = []

    def read():
        for line in proc.stdout:
            url = parse_tunnel_url(line)
            if url and not found:
                found.append(url)

    threading.Thread(target=read, daemon=True).start()
    for _ in range(timeout * 10):
        if found or proc.poll() is not None:
            break
        threading.Event().wait(0.1)
    if not found:
        proc.terminate()
        return None, None
    return proc, found[0]


def show_qr(url):
    """A QR in the terminal when `qrencode` is installed (the lab page draws its own for the phones)."""
    exe = shutil.which("qrencode")
    if exe:
        subprocess.run([exe, "-t", "ANSIUTF8", url])


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--port", type=int, default=8765, help="local port (default 8765)")
    ap.add_argument("--out", default=str(ROOT / "_preview"), help="folder for the built preview (default _preview/)")
    ap.add_argument("--no-tunnel", action="store_true", help="only serve on localhost (no phones)")
    args = ap.parse_args(argv)

    out = build(args.out)
    try:
        server, port = serve(out, args.port)
    except OSError as e:
        sys.exit(f"No se pudo abrir el puerto {args.port}: {e}. Prueba con --port.")
    local = f"http://localhost:{port}/"
    print(f"Sitio listo en {local}  (carpeta {out})")
    tunnel = None
    if not args.no_tunnel:
        tunnel, url = open_tunnel(port)
        if url:
            print(f"\nURL pública (HTTPS) para los teléfonos:\n  {url}/")
            print(f"\nPrueba de red, en el teléfono del director:\n  {url}/{LAB_PATH}?rol=director")
            print("\nLos demás teléfonos entran escaneando el QR que muestra esa página.")
            show_qr(f"{url}/{LAB_PATH}?rol=director")
        else:
            print("\nNo hay túnel: falta `cloudflared` (o no entregó una URL). Instálalo y vuelve a correr esto:")
            print("  macOS: brew install cloudflared   ·   Windows: winget install Cloudflare.cloudflared")
            print("Mientras tanto, solo este computador ve el sitio (localhost cuenta como página segura).")
    print(f"\nEn este computador: {local}{LAB_PATH}?rol=director\nCtrl+C para terminar.")
    try:
        threading.Event().wait()
    except KeyboardInterrupt:
        pass
    finally:
        if tunnel:
            tunnel.terminate()
        server.shutdown()


if __name__ == "__main__":
    main()
