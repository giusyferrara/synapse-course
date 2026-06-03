#!/usr/bin/env python3
"""Fix broken <select> tag in feedback form"""
from pathlib import Path

p = Path('templates/feedback.html')
content = p.read_text(encoding='utf-8')

# 1) Remove the wrong closing tag right after the opening
old1 = '<select name="background" required title="Select your programming experience level"></select>'
new1 = '<select name="background" required title="Select your programming experience level">'

if old1 not in content:
    print("ERROR: opening select line not found")
    exit(1)
content = content.replace(old1, new1)

# 2) Add the </select> after the last option
old2 = '<option value="professional">Professional developer</option>'
new2 = '<option value="professional">Professional developer</option>\n                </select>'

if content.count(old2) != 1:
    print(f"ERROR: 'professional' option found {content.count(old2)} times (expected 1)")
    exit(1)
content = content.replace(old2, new2)

p.write_text(content, encoding='utf-8')
print("OK select tag fixed - dropdown should work now")
