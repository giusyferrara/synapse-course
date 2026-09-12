#!/usr/bin/env python3
"""Local preview of the Synapse pages, with the same routes as the live app.

Run from the synapse-repo directory:
    python preview.py

Then open http://127.0.0.1:8899/privacy in your browser.

This only reads files off disk — it never touches the server, the database,
or the AI. It is a preview, not the app: anything needing a login or an API
call will not work here.
"""
import http.server
import socketserver
import webbrowser
from pathlib import Path

PORT = 8899
ROOT = Path(__file__).resolve().parent

# url path -> template file, mirroring app.py's serve_* handlers
ROUTES = {
    "/": "templates/landing.html",
    "/privacy": "templates/privacy.html",
    "/terms": "templates/terms.html",
    "/cookies": "templates/cookies.html",
    "/about": "templates/about.html",
    "/mcp": "templates/mcp.html",
    "/flashcards": "templates/flashcards.html",
    "/app": "templates/index.html",
}


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw):
        super().__init__(*a, directory=str(ROOT), **kw)

    def do_GET(self):
        path = self.path.split("?")[0].rstrip("/") or "/"
        target = ROUTES.get(path)
        if target:
            f = ROOT / target
            if not f.is_file():
                self.send_error(404, "missing %s" % target)
                return
            body = f.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")   # always show the latest edit
            self.end_headers()
            self.wfile.write(body)
            return
        # /icons/... and /static/... fall through to plain file serving
        super().do_GET()

    def log_message(self, *a):
        pass


socketserver.TCPServer.allow_reuse_address = True
with socketserver.TCPServer(("127.0.0.1", PORT), Handler) as httpd:
    base = "http://127.0.0.1:%d" % PORT
    print("Anteprima Synapse attiva su %s" % base)
    print()
    for p in ("/privacy", "/terms", "/cookies", "/flashcards", "/about", "/", "/app"):
        print("   %s%s" % (base, p))
    print()
    print("Ctrl+C per fermarla.")
    try:
        webbrowser.open(base + "/privacy")
    except Exception:
        pass
    httpd.serve_forever()
