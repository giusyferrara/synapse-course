#!/usr/bin/env python3
"""Remove duplicate </select> after fix"""
from pathlib import Path

p = Path('templates/feedback.html')
content = p.read_text(encoding='utf-8')

duplicate = """                </select>
                </select>"""
single = """                </select>"""

if duplicate not in content:
    print("ERROR: duplicate </select> not found - check the file manually")
    exit(1)
content = content.replace(duplicate, single)
p.write_text(content, encoding='utf-8')
print("OK duplicate </select> removed")
