#!/usr/bin/env python3
"""Broaden accepted CIA answers in Self-Check (resolves AI-vs-quiz mismatch)"""
from pathlib import Path

p = Path('templates/research/research_task.html')
content = p.read_text(encoding='utf-8')

old = """    const ciaPreferred = {
        'CWE-502': ['Confidentiality + Integrity + Availability', 'Integrity + Availability'],
        'CWE-22': ['Confidentiality', 'Confidentiality + Integrity'],
        'CWE-352': ['Integrity', 'Confidentiality + Integrity', 'Integrity + Availability']
    };"""

new = """    const ciaPreferred = {
        'CWE-502': ['Confidentiality + Integrity', 'Confidentiality + Integrity + Availability', 'Integrity + Availability'],
        'CWE-22': ['Confidentiality', 'Confidentiality + Integrity'],
        'CWE-352': ['Integrity', 'Confidentiality + Integrity', 'Integrity + Availability']
    };"""

if old not in content:
    print("ERROR: ciaPreferred block not found")
    exit(1)
content = content.replace(old, new)
p.write_text(content, encoding='utf-8')
print("OK CWE-502 now accepts 'Confidentiality + Integrity' as appropriate")

