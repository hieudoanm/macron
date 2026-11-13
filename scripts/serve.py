"""Serve docs/ on :8765, printing localhost / LAN / external URLs first.

Run directly:

    python3 scripts/serve.py [port]
"""

import socket
import sys
import urllib.request
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).parent.parent
DOCS = ROOT / "docs"
PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8765


def lan_ip() -> str:
    """Primary LAN IPv4 address (best-effort)."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))  # no traffic actually sent
            return s.getsockname()[0]
    except OSError:
        try:
            return socket.gethostbyname(socket.gethostname())
        except OSError:
            return "unknown"


def external_ip() -> str:
    """Public IP as seen from outside (best-effort)."""
    for url in ("https://api.ipify.org", "https://ifconfig.me/ip"):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "curl/8"})
            with urllib.request.urlopen(req, timeout=3) as r:
                return r.read().decode().strip()
        except Exception:
            continue
    return "unavailable (offline or blocked)"


def make_qr(url: str):
    """Build a segno QR code for url. None if segno isn't installed."""
    try:
        import segno
    except ImportError:
        return None
    return segno.make(url, error="m")


def boxed(lines: list[str]) -> list[str]:
    width = max(len(line) for line in lines)
    top = "┌" + "─" * (width + 2) + "┐"
    bottom = "└" + "─" * (width + 2) + "┘"
    body = [f"│ {line:<{width}} │" for line in lines]
    return [top, *body, bottom]


def main() -> None:
    ip = lan_ip()
    ext = external_ip()
    lan_url = f"http://{ip}:{PORT}/"

    qr = make_qr(lan_url)
    qr_line = "QR (LAN): scannable below" if qr is not None else "QR: skipped (segno not installed)"

    lines = [
        f"Serving macron docs on port {PORT}:",
        f"  local:    http://localhost:{PORT}/",
        f"  lan:      {lan_url}",
        f"  external: http://{ext}:{PORT}/  (requires port forwarding)",
        f"  {qr_line}",
    ]
    for line in boxed(lines):
        print(line, flush=True)
    if qr is not None:
        print(flush=True)
        qr.terminal(compact=True)
        sys.stdout.flush()

    class Handler(SimpleHTTPRequestHandler):
        def __init__(self, *a, **kw):
            super().__init__(*a, directory=str(DOCS), **kw)

        def log_message(self, fmt, *args):
            host = self.headers.get("Host", f"localhost:{self.server.server_port}")
            print(
                f'{self.address_string()} - "{self.requestline}"  '
                f"http://{host}{self.path}",
                flush=True,
            )

    server = ThreadingHTTPServer(("", PORT), Handler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
