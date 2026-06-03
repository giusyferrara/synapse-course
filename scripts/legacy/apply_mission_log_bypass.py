#!/usr/bin/env python3
"""Make log_interaction_api accept MISSION_* codes silently"""
from pathlib import Path

p = Path('web/research_handlers.py')
content = p.read_text(encoding='utf-8')

old = """        if not participant_code:
            return web.json_response({
                'success': False, 'error': 'Participant code required'
            }, status=400)

        db = SessionLocal()
        try:
            participant = db.query(ResearchParticipant).filter_by(
                participant_code=participant_code
            ).first()

            if not participant:
                return web.json_response({
                    'success': False, 'error': 'Invalid participant code'
                }, status=404)

            # Append to existing logs - accept both old and new format"""

new = """        if not participant_code:
            return web.json_response({
                'success': False, 'error': 'Participant code required'
            }, status=400)

        # Mission mode: silently accept without DB write
        if participant_code.startswith('MISSION_'):
            return web.json_response({'success': True, 'logged': False, 'mode': 'mission'})

        db = SessionLocal()
        try:
            participant = db.query(ResearchParticipant).filter_by(
                participant_code=participant_code
            ).first()

            if not participant:
                return web.json_response({
                    'success': False, 'error': 'Invalid participant code'
                }, status=404)

            # Append to existing logs - accept both old and new format"""

if old not in content:
    print("ERROR: target block not found!")
    exit(1)

content = content.replace(old, new, 1)
p.write_text(content, encoding='utf-8')
print("OK log_interaction_api patched with MISSION_* bypass")
