#!/usr/bin/env python3
"""Add Focus Assistant button to /app accessibility bar"""
from pathlib import Path

p = Path('templates/index.html')
content = p.read_text(encoding='utf-8')

old = '<button id="focusModeBtn" onclick="toggleFocusMode()" title="Focus Mode" style="width:34px;height:34px;border:none;border-radius:50%;background:rgba(255,255,255,0.2);cursor:pointer;font-size:16px;color:white;">🎯</button>'

new = old + '\n                <button id="focusAssistantBtn" onclick="toggleFocusAssistant()" title="Focus Assistant" data-tooltip="Focus Assistant" style="width:34px;height:34px;border:none;border-radius:50%;background:rgba(255,255,255,0.2);cursor:pointer;font-size:16px;color:white;">💡</button>'

if old not in content:
    print("ERROR: Focus Mode button not found")
    exit(1)
if 'focusAssistantBtn' in content:
    print("Focus Assistant button already present, skipping")
    exit(0)
content = content.replace(old, new)
p.write_text(content, encoding='utf-8')
print("OK Focus Assistant button added next to Focus Mode")
