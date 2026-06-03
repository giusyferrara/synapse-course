#!/usr/bin/env python3
"""Include idle_encouragement.js in Java Course, Mission, and /app"""
from pathlib import Path

script_tag = '<script src="/static/idle_encouragement.js"></script>'

targets = [
    'templates/course_java_security.html',
    'templates/research/research_task.html',
    'templates/index.html'
]

for path_str in targets:
    p = Path(path_str)
    if not p.exists():
        print(f"SKIP (not found): {path_str}")
        continue
    content = p.read_text(encoding='utf-8')
    if script_tag in content:
        print(f"OK already present: {path_str}")
        continue
    if '</body>' in content:
        content = content.replace('</body>', '    ' + script_tag + '\n</body>', 1)
        p.write_text(content, encoding='utf-8')
        print(f"OK added to: {path_str}")
    else:
        print(f"WARN no </body>: {path_str}")
