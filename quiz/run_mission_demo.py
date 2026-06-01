import os,sys
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0,ROOT); os.chdir(ROOT)
from aiohttp import web
FILE=os.path.join(ROOT,"templates","research","research_task.html")
app=web.Application()
async def m(req): return web.FileResponse(FILE)
app.router.add_get("/mission", m)
app.router.add_static("/static/", os.path.join(ROOT,"static"))
app.router.add_static("/icons/", os.path.join(ROOT,"icons"))
web.run_app(app, host="127.0.0.1", port=8095, print=None)
