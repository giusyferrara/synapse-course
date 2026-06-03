#!/usr/bin/env python3
"""Require login on /tools page"""
from pathlib import Path

p = Path('web/handlers.py')
content = p.read_text(encoding='utf-8')

old = '''async def handle_advanced_tools(request):
    """NEW: Serve advanced learning tools page"""
    try:
        with open("templates/advanced_tools.html", "r", encoding="utf-8") as f:
            return web.Response(text=f.read(), content_type="text/html")
    except FileNotFoundError:
        return web.Response(text="<h1>Error: advanced_tools.html not found.</h1>", status=500, content_type="text/html")'''

new = '''async def handle_advanced_tools(request):
    """NEW: Serve advanced learning tools page"""
    if not request.cookies.get('synapse_user'):
        raise web.HTTPFound('/login?next=/tools')
    try:
        with open("templates/advanced_tools.html", "r", encoding="utf-8") as f:
            return web.Response(text=f.read(), content_type="text/html")
    except FileNotFoundError:
        return web.Response(text="<h1>Error: advanced_tools.html not found.</h1>", status=500, content_type="text/html")'''

if old not in content:
    print("ERROR: handler not found")
    exit(1)
content = content.replace(old, new)
p.write_text(content, encoding='utf-8')
print("OK /tools now requires login")
