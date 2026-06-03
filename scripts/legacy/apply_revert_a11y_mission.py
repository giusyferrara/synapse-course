#!/usr/bin/env python3
"""Revert opacity hack + hide butterfly button in Mission page"""
from pathlib import Path

p = Path('templates/research/research_task.html')
content = p.read_text(encoding='utf-8')

# 1) Remove the opacity override
old_override = """<style>
/* MISSION mode: force accessibility menu to be visible when toggled open */
#accessMenuInline { opacity: 1 !important; transition: opacity 0.2s ease; }
</style>
"""
if old_override in content:
    content = content.replace(old_override, '')
    print("OK opacity override removed")
else:
    print("(opacity override not found - skipping)")

# 2) Hide butterfly access button on Mission page
hide_btn = """<style>
/* MISSION mode: hide butterfly access button (use /app for accessibility settings) */
#butterflyAccessBtn, .access-toggle-wrap { display: none !important; }
</style>
"""
if hide_btn not in content:
    content = content.replace('</head>', hide_btn + '</head>', 1)
    print("OK butterfly button hidden on Mission page")
else:
    print("(hide rule already present)")

p.write_text(content, encoding='utf-8')
