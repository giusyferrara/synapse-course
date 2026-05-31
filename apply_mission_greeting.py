#!/usr/bin/env python3
"""Set aiGreeting message in MISSION mode (fixes Loading... ghost)"""
from pathlib import Path

p = Path('templates/research/research_task.html')
content = p.read_text(encoding='utf-8')

old = """        const chat = document.getElementById('aiChatPanel');
        if (chat) chat.style.display = 'flex';
        taskStartTime = new Date();"""

new = """        const chat = document.getElementById('aiChatPanel');
        if (chat) chat.style.display = 'flex';
        const greeting = document.getElementById('aiGreeting');
        if (greeting) greeting.innerHTML = 'Hi ' + (participantNickname || 'there') + '! I am your SYNAPSE AI Security Tutor.<br><br>I am here to help you find 3 vulnerabilities in ShopSecure: <strong>Insecure Deserialisation (CWE-502)</strong>, <strong>Path Traversal (CWE-22)</strong>, and <strong>CSRF (CWE-352)</strong>.<br><br>Click <strong>Open ShopSecure</strong> to start exploring, then ask me anything!';
        taskStartTime = new Date();"""

if old not in content:
    print("ERROR: target block not found!")
    exit(1)
content = content.replace(old, new, 1)
p.write_text(content, encoding='utf-8')
print("OK aiGreeting now set in MISSION mode")
