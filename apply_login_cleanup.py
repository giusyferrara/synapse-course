#!/usr/bin/env python3
"""Remove research blocks from login.html"""
import re
from pathlib import Path

p = Path('templates/login.html')
content = p.read_text(encoding='utf-8')

# Block 1: Research Participant box + orphaned divider "or sign in with email"
pat1 = re.compile(
    r'\s*<div style="background:linear-gradient\(135deg,rgba\(16,185,129,0\.06\),rgba\(5,150,105,0\.06\)\);.*?<div class="divider">or sign in with email</div>',
    re.DOTALL
)
content, n1 = pat1.subn('', content, count=1)
assert n1 == 1, f"Patch 1 (Research box) failed: {n1}"

# Block 2: "Join Research Study" button wrapper
pat2 = re.compile(
    r'\s*<div style="margin-top: 24px; text-align: center;">.*?Join Research Study.*?</div>',
    re.DOTALL
)
content, n2 = pat2.subn('', content, count=1)
assert n2 == 1, f"Patch 2 (Join Research btn) failed: {n2}"

p.write_text(content, encoding='utf-8')
print(f"OK login.html  research_box+divider={n1}  join_btn={n2}")
