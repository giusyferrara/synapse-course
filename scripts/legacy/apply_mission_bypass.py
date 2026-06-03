#!/usr/bin/env python3
"""Bypass participantCode API validation for MISSION_* codes"""
from pathlib import Path

p = Path('templates/research/research_task.html')
content = p.read_text(encoding='utf-8')

old = """    const resp = await fetch('/api/research/participant?code=' + participantCode);"""

new = """    // MISSION mode: skip research API validation (no DB entry needed)
    if (participantCode.startsWith('MISSION_')) {
        participantGroup = 'A';
        participantNickname = 'Learner';
        const badge = document.getElementById('groupBadgeTop');
        if (badge) {
            badge.className = 'group-badge group-a';
            badge.textContent = '🦋 AI Tutored';
        }
        const gi = document.getElementById('groupInstructions');
        if (gi) gi.innerHTML = '🦋 You have an <strong>AI Security Tutor</strong>. Ask questions anytime!';
        const chat = document.getElementById('aiChatPanel');
        if (chat) chat.style.display = 'flex';
        taskStartTime = new Date();
        return;
    }
    const resp = await fetch('/api/research/participant?code=' + participantCode);"""

if old not in content:
    print("ERROR: target line not found!")
    exit(1)

content = content.replace(old, new, 1)
p.write_text(content, encoding='utf-8')
print("OK template patched with MISSION_* bypass")
