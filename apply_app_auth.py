#!/usr/bin/env python3
"""Add login required check to serve_app handler"""
import re
from pathlib import Path

p = Path('app.py')
content = p.read_text(encoding='utf-8')

pattern = re.compile(
    r'(async def serve_app\(request\):\s*\n)(\s+)("""Python AI Tool"""\s*\n)'
)
content, n = pattern.subn(
    r"\1\2\3\2if not request.cookies.get('synapse_user'):\n\2    raise web.HTTPFound('/login?next=/app')\n",
    content, count=1
)
assert n == 1, f"Patch failed: {n}"

p.write_text(content, encoding='utf-8')
print(f"OK app.py  auth_check_added={n}")
