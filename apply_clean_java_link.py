#!/usr/bin/env python3
"""Don't propagate participant code from Mission to Java Course link"""
from pathlib import Path

p = Path('templates/research/research_task.html')
content = p.read_text(encoding='utf-8')

old = "if(p) btn.href = '/course/java-security?participant=' + p;"
new = "// MISSION mode: don't propagate participant code to Java Course"

if old not in content:
    print("ERROR: line not found")
    exit(1)
content = content.replace(old, new)
p.write_text(content, encoding='utf-8')
print("OK Java Course link no longer carries participant code")
