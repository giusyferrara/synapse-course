#!/usr/bin/env python3
"""Remove creepy 'AI still remembers' from clear chat confirm"""
from pathlib import Path

p = Path('templates/course_java_security.html')
content = p.read_text(encoding='utf-8')

old = "'Clear visible chat? (AI still remembers)'"
new = "'Clear chat history?'"

if old not in content:
    print("ERROR: target string not found")
    exit(1)
content = content.replace(old, new)
p.write_text(content, encoding='utf-8')
print("OK creepy AI remembers message removed")
