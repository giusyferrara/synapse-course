#!/usr/bin/env python3
"""Include idle system in Python Course"""
from pathlib import Path

script_tag = '<script src="/static/idle_encouragement.js"></script>'

p = Path('templates/course.html')
content = p.read_text(encoding='utf-8')

if script_tag in content:
    print("OK already present")
elif '</body>' in content:
    content = content.replace('</body>', '    ' + script_tag + '\n</body>', 1)
    p.write_text(content, encoding='utf-8')
    print("OK added to course.html (Python Course)")
else:
    print("WARN no </body> tag found")
