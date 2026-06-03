#!/usr/bin/env python3
"""Send email notification when feedback is submitted"""
from pathlib import Path

p = Path('web/handlers.py')
content = p.read_text(encoding='utf-8')

# 1) Ensure imports
imports_to_add = []
if "from .email_utils import send_email" not in content and "from web.email_utils import send_email" not in content:
    imports_to_add.append("from .email_utils import send_email")
if "import os" not in content:
    imports_to_add.append("import os")

if imports_to_add:
    # Add imports near the top
    lines = content.split('\n')
    for i, line in enumerate(lines):
        if line.startswith('from ') or line.startswith('import '):
            insert_idx = i
            break
    for imp in reversed(imports_to_add):
        lines.insert(insert_idx, imp)
    content = '\n'.join(lines)

# 2) Replace the feedback handler body
old = '''        db.add(new_feedback)
        db.commit()
        return web.Response(text="Feedback received, thank you!")'''

new = '''        db.add(new_feedback)
        db.commit()
        # Send email notification (non-blocking on failure)
        try:
            to_email = os.environ.get("FEEDBACK_TO_EMAIL", "synapse_4AI@outlook.com")
            html_body = f"""<h2>New SYNAPSE Feedback</h2>
<p><strong>Student ID:</strong> {student_id_str}</p>
<p><strong>Most helpful:</strong><br>{data.get("most_helpful") or "—"}</p>
<p><strong>Improvements:</strong><br>{data.get("improvements") or "—"}</p>
<p><strong>Background:</strong><br>{data.get("background") or "—"}</p>"""
            text_body = f"""New SYNAPSE Feedback

Student ID: {student_id_str}
Most helpful: {data.get("most_helpful") or "—"}
Improvements: {data.get("improvements") or "—"}
Background: {data.get("background") or "—"}"""
            send_email(to_email, "New SYNAPSE feedback received", html_body, text_body)
        except Exception as e:
            print(f"[!] Feedback email notification failed: {e}")
        return web.Response(text="Feedback received, thank you!")'''

if old not in content:
    print("ERROR: target block not found")
    exit(1)
content = content.replace(old, new)
p.write_text(content, encoding='utf-8')
print("OK feedback handler now sends email")
