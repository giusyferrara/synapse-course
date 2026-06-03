#!/usr/bin/env python3
"""Dark mode: uniform dark backgrounds for all clean-btn"""
from pathlib import Path

p = Path('templates/index.html')
content = p.read_text(encoding='utf-8')

old_css = """<style>
/* Dark mode: pastel buttons need white text and slightly darker gradients */
body.dark-mode .clean-btn,
body.dark-mode a.clean-btn {
    color: #ffffff !important;
    text-shadow: 0 1px 2px rgba(0,0,0,0.5);
    filter: brightness(0.85) saturate(1.1);
}
body.dark-mode .clean-btn:hover,
body.dark-mode a.clean-btn:hover {
    filter: brightness(0.95) saturate(1.2);
}
</style>
"""

new_css = """<style>
/* Dark mode: uniform dark buttons across /app */
body.dark-mode .clean-btn,
body.dark-mode a.clean-btn {
    background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%) !important;
    color: #ffffff !important;
    border: 1px solid #334155 !important;
    text-shadow: none !important;
    filter: none !important;
}
body.dark-mode .clean-btn:hover,
body.dark-mode a.clean-btn:hover {
    background: linear-gradient(135deg, #334155 0%, #1e293b 100%) !important;
    border-color: #475569 !important;
}
</style>
"""

if old_css in content:
    content = content.replace(old_css, new_css)
    print("OK replaced old fix with uniform dark buttons")
elif new_css in content:
    print("Already applied")
else:
    content = content.replace('</head>', new_css + '</head>', 1)
    print("OK uniform dark buttons applied")

p.write_text(content, encoding='utf-8')
