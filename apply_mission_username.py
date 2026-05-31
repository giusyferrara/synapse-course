#!/usr/bin/env python3
"""Mission v3: inject user display_name from DB"""
from pathlib import Path

# === Patch 1: research_handlers.py — mission_page recupera display_name ===
p1 = Path('web/research_handlers.py')
c1 = p1.read_text(encoding='utf-8')

old_func = '''async def mission_page(request):
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

new_func = '''async def mission_page(request):
    """GET /mission — Show vulnerability mission (logged-in users only, no research enrollment)"""
    user_id = request.cookies.get('synapse_user')
    if not user_id:
        raise web.HTTPFound('/login?next=/mission')
    if not request.query.get('participant'):
        mission_code = f'MISSION_U{user_id}'
        raise web.HTTPFound(f'/mission?participant={mission_code}')
    # Get user display_name from DB
    from sqlalchemy import text
    display_name = 'Learner'
    db = SessionLocal()
    try:
        result = db.execute(
            text("SELECT display_name FROM users WHERE id = :uid"),
            {'uid': int(user_id)}
        ).fetchone()
        if result and result.display_name:
            display_name = result.display_name
    except Exception:
        pass
    finally:
        db.close()
    html_path = Path(__file__).parent.parent / 'templates' / 'research' / 'research_task.html'
    if not html_path.exists():
        return web.Response(text="Mission page not found.", status=404)
    with open(html_path, 'r', encoding='utf-8') as f:
        html_content = f.read()
    # Inject user display_name as window variable so template can use it
    safe_name = display_name.replace('"', '').replace('<', '').replace('>', '')
    injection = f'<script>window.MISSION_USER_NAME = "{safe_name}";</script>\\n'
    html_content = html_content.replace('</head>', injection + '</head>', 1)
    return web.Response(text=html_content, content_type='text/html')
'''

if old_func not in c1:
    print("ERROR: old mission_page not found in research_handlers.py!")
    exit(1)
c1 = c1.replace(old_func, new_func, 1)
p1.write_text(c1, encoding='utf-8')
print("OK research_handlers.py  mission_page upgraded")

# === Patch 2: template — usa window.MISSION_USER_NAME al posto di 'Learner' ===
p2 = Path('templates/research/research_task.html')
c2 = p2.read_text(encoding='utf-8')

old_line = "        participantNickname = 'Learner';"
new_line = "        participantNickname = window.MISSION_USER_NAME || 'Learner';"

if old_line not in c2:
    print("ERROR: target line not found in template!")
    exit(1)
c2 = c2.replace(old_line, new_line, 1)
p2.write_text(c2, encoding='utf-8')
print("OK template  uses window.MISSION_USER_NAME")
