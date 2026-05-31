#!/usr/bin/env python3
"""Remove research-task-card banner from java security course template"""
import re
from pathlib import Path

p = Path('templates/course_java_security.html')
content = p.read_text(encoding='utf-8')

pat = re.compile(
    r'\s*<div class="research-task-card">.*?<!-- END RESEARCH TASK SECTION -->',
    re.DOTALL
)
content, n = pat.subn('', content, count=1)
assert n == 1, f"Patch failed: {n}"

p.write_text(content, encoding='utf-8')
print(f"OK banner removed (n={n})")
