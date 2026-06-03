#!/usr/bin/env python3
"""Force opacity:1 on access menu when open"""
from pathlib import Path

p = Path('templates/research/research_task.html')
content = p.read_text(encoding='utf-8')

# Insert CSS override right before </head>
override = """<style>
/* MISSION mode: force accessibility menu to be visible when toggled open */
#accessMenuInline { opacity: 1 !important; transition: opacity 0.2s ease; }
</style>
"""

if '</head>' not in content:
    print("ERROR: </head> not found")
    exit(1)
if override in content:
    print("Override already present, skipping")
else:
    content = content.replace('</head>', override + '</head>', 1)
    p.write_text(content, encoding='utf-8')
    print("OK opacity override added")
