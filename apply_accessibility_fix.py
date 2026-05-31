#!/usr/bin/env python3
"""Add focus_assistant CSS+JS to Mission page (match working pages like index.html)"""
from pathlib import Path

p = Path('templates/research/research_task.html')
content = p.read_text(encoding='utf-8')

# 1) Add focus_assistant.css before synapse_a11y.css
old_css = '<link rel="stylesheet" href="/static/synapse_a11y.css?v=9">'
new_css = '<link rel="stylesheet" href="/static/focus_assistant.css">\n    <link rel="stylesheet" href="/static/synapse_a11y.css?v=9">'

if old_css not in content:
    print("ERROR: synapse_a11y.css link not found")
    exit(1)
content = content.replace(old_css, new_css)

# 2) Add focus_assistant.js before synapse_a11y.js
old_js = '<script src="/static/synapse_a11y.js?v=9"></script>'
new_js = '<script src="/static/focus_assistant.js"></script>\n<script src="/static/synapse_a11y.js?v=9"></script>'

if old_js not in content:
    print("ERROR: synapse_a11y.js script not found")
    exit(1)
content = content.replace(old_js, new_js)

p.write_text(content, encoding='utf-8')
print("OK focus_assistant added to Mission page")
