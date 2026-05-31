#!/usr/bin/env python3
"""Remove Research Study banner from landing.html"""
import re
from pathlib import Path

p = Path('templates/landing.html')
content = p.read_text(encoding='utf-8')

pat = re.compile(
    r'\s*<!-- RESEARCH STUDY BANNER.*?Limited spots.*?</p>',
    re.DOTALL
)
content, n = pat.subn('', content, count=1)
assert n == 1, f"Patch failed: {n}"

p.write_text(content, encoding='utf-8')
print(f"OK landing.html  banner_removed={n}")
