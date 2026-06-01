import os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT); os.chdir(ROOT)
from aiohttp import web
app = web.Application()
async def fc(req): return web.FileResponse("templates/flashcards.html")
app.router.add_get("/flashcards", fc)
app.router.add_static("/static/", os.path.join(ROOT, "static"))
app.router.add_static("/icons/", os.path.join(ROOT, "icons"))
web.run_app(app, host="127.0.0.1", port=8097, print=None)
