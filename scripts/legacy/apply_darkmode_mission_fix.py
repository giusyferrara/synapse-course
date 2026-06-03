#!/usr/bin/env python3
"""Add dark-mode support to Mission page (best-effort override)"""
from pathlib import Path

p = Path('templates/research/research_task.html')
content = p.read_text(encoding='utf-8')

dark_css = """<style>
/* Mission page: dark-mode support — readable text and panels */
body.dark-mode {
    background: #0f172a !important;
    color: #e2e8f0 !important;
}
body.dark-mode .main-content,
body.dark-mode main,
body.dark-mode section,
body.dark-mode .task-info,
body.dark-mode .finding-card,
body.dark-mode .form-group,
body.dark-mode .research-task-card,
body.dark-mode .card,
body.dark-mode .tab-content {
    background: #1e293b !important;
    color: #e2e8f0 !important;
    border-color: #334155 !important;
}
body.dark-mode p,
body.dark-mode li,
body.dark-mode span,
body.dark-mode label,
body.dark-mode div {
    color: #e2e8f0 !important;
}
body.dark-mode h1, body.dark-mode h2, body.dark-mode h3, body.dark-mode h4,
body.dark-mode strong {
    color: #ffffff !important;
}
body.dark-mode select, body.dark-mode input, body.dark-mode textarea {
    background: #0f172a !important;
    color: #e2e8f0 !important;
    border-color: #475569 !important;
}
body.dark-mode a { color: #93c5fd !important; }
/* Keep top bar gradients intact */
body.dark-mode .synapse-header, 
body.dark-mode .synapse-header *,
body.dark-mode .nav-action-btn,
body.dark-mode .submit-btn,
body.dark-mode .tab-btn {
    color: inherit !important;
}
</style>
"""

if dark_css in content:
    print("Dark mode fix already present")
else:
    content = content.replace('</head>', dark_css + '</head>', 1)
    p.write_text(content, encoding='utf-8')
    print("OK dark-mode fix applied to Mission page")
