#!/usr/bin/env python3
"""Inject display_name into Java Security course page"""
from pathlib import Path

# Patch 1: app.py handler
app_py = Path('app.py')
content = app_py.read_text(encoding='utf-8')

old_handler = """        async def serve_java_security_course(request):
            \"\"\"Java Security course page - requires auth\"\"\"
            user_cookie = request.cookies.get('synapse_user')
            participant_code = request.query.get('participant') or request.cookies.get('participant_code')
            admin_key = request.query.get('admin')
            if not user_cookie and not participant_code and admin_key != os.getenv('ADMIN_KEY', ''):
                raise web.HTTPFound('/login?next=/course/java-security')
            course_path = Path(__file__).parent / 'templates' / 'course_java_security.html'
            try:
                with open(course_path, 'r', encoding='utf-8', errors='ignore') as f:
                    response = web.Response(text=f.read(), content_type='text/html')
                if participant_code:
                    response.set_cookie('participant_code', participant_code, max_age=90*24*60*60)
                    print(f\"\u2705 Java Security Participant: {participant_code}\")
                return response
            except FileNotFoundError:
                return web.Response(text=\"<h1>Java Security course not found</h1>\", status=404)"""

new_handler = """        async def serve_java_security_course(request):
            \"\"\"Java Security course page - requires auth\"\"\"
            user_cookie = request.cookies.get('synapse_user')
            participant_code = request.query.get('participant') or request.cookies.get('participant_code')
            admin_key = request.query.get('admin')
            if not user_cookie and not participant_code and admin_key != os.getenv('ADMIN_KEY', ''):
                raise web.HTTPFound('/login?next=/course/java-security')
            from sqlalchemy import text as sql_text
            from database.config import SessionLocal
            display_name = ''
            if user_cookie:
                db = SessionLocal()
                try:
                    result = db.execute(sql_text(\"SELECT display_name FROM users WHERE id = :uid\"), {'uid': int(user_cookie)}).fetchone()
                    if result and result.display_name:
                        display_name = result.display_name
                except Exception:
                    pass
                finally:
                    db.close()
            course_path = Path(__file__).parent / 'templates' / 'course_java_security.html'
            try:
                with open(course_path, 'r', encoding='utf-8', errors='ignore') as f:
                    html_content = f.read()
                safe_name = display_name.replace('\"', '').replace('<', '').replace('>', '')
                if safe_name:
                    injection = f'<script>window.SYNAPSE_USER_NAME = \"{safe_name}\";</script>\\n'
                    html_content = html_content.replace('</head>', injection + '</head>', 1)
                response = web.Response(text=html_content, content_type='text/html')
                if participant_code:
                    response.set_cookie('participant_code', participant_code, max_age=90*24*60*60)
                    print(f\"\u2705 Java Security Participant: {participant_code}\")
                return response
            except FileNotFoundError:
                return web.Response(text=\"<h1>Java Security course not found</h1>\", status=404)"""

if old_handler not in content:
    print("ERROR: handler not found")
    exit(1)
content = content.replace(old_handler, new_handler)
app_py.write_text(content, encoding='utf-8')
print("OK app.py patched")

# Patch 2: template
tmpl = Path('templates/course_java_security.html')
tcontent = tmpl.read_text(encoding='utf-8')

old_line = "                var pName = sessionStorage.getItem('ss_nickname') || '';"
new_line = "                var pName = window.SYNAPSE_USER_NAME || sessionStorage.getItem('ss_nickname') || '';"

if old_line not in tcontent:
    print("ERROR: pName line not found")
    exit(1)
tcontent = tcontent.replace(old_line, new_line)
tmpl.write_text(tcontent, encoding='utf-8')
print("OK template patched")
