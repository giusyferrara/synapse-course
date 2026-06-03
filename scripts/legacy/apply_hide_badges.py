#!/usr/bin/env python3
"""Hide participant code badge and group badge in MISSION mode"""
from pathlib import Path

p = Path('templates/research/research_task.html')
content = p.read_text(encoding='utf-8')

# Find the MISSION mode block and add badge hiding
old = """        const badge = document.getElementById('groupBadgeTop');
        if (badge) {
            badge.className = 'group-badge group-a';
            badge.textContent = '\U0001f98b AI Tutored';
        }"""

new = """        const badge = document.getElementById('groupBadgeTop');
        if (badge) badge.style.display = 'none';
        const partBadge = document.getElementById('participantBadge');
        if (partBadge) partBadge.style.display = 'none';"""

if old not in content:
    print("ERROR: badge block not found - trying alternative match")
    # Try with hex emoji
    old2 = """        const badge = document.getElementById('groupBadgeTop');
        if (badge) {
            badge.className = 'group-badge group-a';
            badge.textContent = '🦋 AI Tutored';
        }"""
    if old2 not in content:
        print("ERROR: also alternative not found")
        exit(1)
    content = content.replace(old2, new)
else:
    content = content.replace(old, new)

p.write_text(content, encoding='utf-8')
print("OK badges hidden in MISSION mode")
