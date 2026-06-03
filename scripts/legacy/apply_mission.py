#!/usr/bin/env python3
"""Add /mission route + button in index.html"""
import re
from pathlib import Path

# === Patch research_handlers.py ===
rh_path = Path('web/research_handlers.py')
rh = rh_path.read_text(encoding='utf-8')

new_handler = '''async def mission_page(request):
    """GET /mission — Show vulnerability mission (no research enrollment, no data collection)"""
    html_path = Path(__file__).parent.parent / 'templates' / 'research' / 'research_task.html'
    if not html_path.exists():
        return web.Response(text="Mission page not found.", status=404)
    with open(html_path, 'r', encoding='utf-8') as f:
        html_content = f.read()
    return web.Response(text=html_content, content_type='text/html')

'''

rh, n1 = re.subn(r'(def setup_research_routes\(app\):)',
                 new_handler + r'\1', rh, count=1)
assert n1 == 1, f"Handler insert failed: {n1}"

rh, n2 = re.subn(r"(app\.router\.add_get\('/research/task', research_task_page\))",
                 r"\1\n    app.router.add_get('/mission', mission_page)", rh, count=1)
assert n2 == 1, f"Route insert failed: {n2}"

rh_path.write_text(rh, encoding='utf-8')
print(f"OK research_handlers.py  handler={n1}  route={n2}")

# === Patch templates/index.html ===
idx_path = Path('templates/index.html')
idx = idx_path.read_text(encoding='utf-8')

new_btn = '<a href="/mission" target="_blank" class="clean-btn security">🎯 Mission</a>\n                '

idx, n3 = re.subn(
    r'(<button class="clean-btn test" id="testAIBtn">🤖 Test AI</button>\n\s+)',
    r'\1' + new_btn, idx, count=1)
assert n3 == 1, f"Button insert failed: {n3}"

idx_path.write_text(idx, encoding='utf-8')
print(f"OK index.html  button={n3}")
print("DONE. Restart service to load new route.")
