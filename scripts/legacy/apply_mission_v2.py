#!/usr/bin/env python3
"""Update mission_page: require login + auto-redirect with generated participant code"""
from pathlib import Path

p = Path('web/research_handlers.py')
content = p.read_text(encoding='utf-8')

old_func = '''async def mission_page(request):
    """GET /mission — Show vulnerability mission (no research enrollment, no data collection)"""
    html_path = Path(__file__).parent.parent / 'templates' / 'research' / 'research_task.html'
    if not html_path.exists():
        return web.Response(text="Mission page not found.", status=404)
    with open(html_path, 'r', encoding='utf-8') as f:
        html_content = f.read()
    return web.Response(text=html_content, content_type='text/html')
'''

new_func = '''async def mission_page(request):
    """GET /mission — Show vulnerability mission (logged-in users only, no research enrollment)"""
    user_id = request.cookies.get('synapse_user')
    if not user_id:
        raise web.HTTPFound('/login?next=/mission')
    if not request.query.get('participant'):
        mission_code = f'MISSION_U{user_id}'
        raise web.HTTPFound(f'/mission?participant={mission_code}')
    html_path = Path(__file__).parent.parent / 'templates' / 'research' / 'research_task.html'
    if not html_path.exists():
        return web.Response(text="Mission page not found.", status=404)
    with open(html_path, 'r', encoding='utf-8') as f:
        html_content = f.read()
    return web.Response(text=html_content, content_type='text/html')
'''

if old_func not in content:
    print("ERROR: old function not found!")
    exit(1)

content = content.replace(old_func, new_func, 1)
p.write_text(content, encoding='utf-8')
print("OK mission_page updated")
