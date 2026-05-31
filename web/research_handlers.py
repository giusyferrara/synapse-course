"""
Research Study Routes — ShopSecure Vulnerability Assessment
===========================================================
Handles participant signup, task submission, post-test, and data collection.

Experimental Design: 2x2 Factorial (Group A/B × ND/NT)
References:
  - Kestin et al. (2025) Harvard RCT
  - Bloom (1984) 2 Sigma
  - Hart & Staveland (1988) NASA-TLX
  - Brooke (1996) SUS
  - Anderson & Krathwohl (2001) Bloom's Taxonomy
  - Hake (1998) Normalised Learning Gain
"""
import os
from sqlalchemy.orm.attributes import flag_modified
from aiohttp import web
import random
import string
import json
from datetime import datetime
from pathlib import Path

# Database imports
from database.models import ResearchParticipant
from database.config import SessionLocal


def generate_participant_code():
    """Generate unique 8-character participant code"""
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))


# ============================================================================
# HTML PAGE ROUTES
# ============================================================================

async def research_signup_page(request):
    """GET /research/signup — Show signup form with pre-test"""
    html_path = Path(__file__).parent.parent / 'templates' / 'research' / 'research_signup.html'
    if not html_path.exists():
        return web.Response(text="Signup page not found.", status=404)
    with open(html_path, 'r', encoding='utf-8') as f:
        return web.Response(text=f.read(), content_type='text/html')


async def research_welcome_page(request):
    """GET /research/welcome — Show participant code after signup"""
    html_path = Path(__file__).parent.parent / 'templates' / 'research' / 'research_welcome.html'
    if not html_path.exists():
        return web.Response(text="Welcome page not found.", status=404)
    with open(html_path, 'r', encoding='utf-8') as f:
        return web.Response(text=f.read(), content_type='text/html')


async def research_task_page(request):
    """GET /research/task?participant=XXX — Show vulnerability assessment task"""
    participant_code = request.query.get('participant', '')
    admin_key = request.query.get('admin', '')
    if admin_key == os.getenv('ADMIN_KEY', ''):
        participant_code = participant_code or 'ADMIN_VIEW'
    if not participant_code:
        return web.Response(text="No participant code provided.", status=400)

    db = SessionLocal()
    try:
        participant = db.query(ResearchParticipant).filter_by(
            participant_code=participant_code
        ).first()
        if not participant and admin_key != os.getenv('ADMIN_KEY', ''):
            return web.Response(text="Invalid participant code.", status=404)
    finally:
        db.close()

    html_path = Path(__file__).parent.parent / 'templates' / 'research' / 'research_task.html'
    if not html_path.exists():
        return web.Response(text="Task page not found.", status=404)
    with open(html_path, 'r', encoding='utf-8') as f:
        html_content = f.read()
    print("Task loaded: " + str(participant_code))
    print("Task loaded: " + str(participant_code))
    return web.Response(text=html_content, content_type='text/html')


async def research_post_test_page(request):
    """GET /research/post_test?participant=XXX — Post-test questionnaires"""
    participant_code = request.query.get('participant', '')
    if not participant_code:
        return web.Response(text="No participant code provided.", status=400)

    db = SessionLocal()
    try:
        participant = db.query(ResearchParticipant).filter_by(
            participant_code=participant_code
        ).first()
        if not participant:
            return web.Response(text="Invalid participant code.", status=404)
    finally:
        db.close()

    html_path = Path(__file__).parent.parent / 'templates' / 'research' / 'research_post_test.html'
    if not html_path.exists():
        return web.Response(text="Post-test page not found.", status=404)
    with open(html_path, 'r', encoding='utf-8') as f:
        return web.Response(text=f.read(), content_type='text/html')


# ============================================================================
# API: SIGNUP
# ============================================================================

async def research_signup_api(request):
    """
    POST /api/research/signup
    Collects demographics, ND profile, experience levels, pre-test scores,
    and assigns group (A or B).
    """
    try:
        data = await request.json()

        # ── Validate consent ────────────────────────────────────────
        if not data.get('consent'):
            return web.json_response({
                'success': False, 'error': 'Consent is required'
            }, status=400)

        # ── Validate nickname ───────────────────────────────────────
        nickname = data.get('nickname', '').strip()
        if not nickname or len(nickname) < 3:
            return web.json_response({
                'success': False, 'error': 'Username must be at least 3 characters'
            }, status=400)

        if len(nickname) > 50:
            return web.json_response({
                'success': False, 'error': 'Username must be under 50 characters'
            }, status=400)

        # Check nickname uniqueness
        db_check = SessionLocal()
        try:
            existing = db_check.query(ResearchParticipant).filter_by(
                nickname=nickname.lower()
            ).first()
            if existing:
                return web.json_response({
                    'success': False,
                    'error': f'Username "{nickname}" is already taken',
                    'participant_code': existing.participant_code
                }, status=400)
        finally:
            db_check.close()

        # ── Validate email (optional) ───────────────────────────────
        email = data.get('email', '').strip().lower()
        if email:
            db_check = SessionLocal()
            try:
                existing_email = db_check.query(ResearchParticipant).filter_by(
                    email=email
                ).first()
                if existing_email:
                    return web.json_response({
                        'success': False,
                        'error': 'This email is already registered',
                        'participant_code': existing_email.participant_code
                    }, status=400)
            finally:
                db_check.close()

        # ── Generate participant code ───────────────────────────────
        participant_code = generate_participant_code()

        # ── Determine ND status ─────────────────────────────────────
        nd_selections = data.get('neurodivergence', [])
        is_nd = any(v not in ['no', 'prefer_not_say'] for v in nd_selections)

        # ── Group assignment ────────────────────────────────────────
        group = data.get('group_assignment', '')
        if group not in ['A', 'B']:
            group = random.choice(['A', 'B'])

        # ── Pre-test scoring ────────────────────────────────────────
        pre_test_answers = data.get('pre_test_answers', {})
        pre_test_score = int(data.get('pre_test_score', 0))
        pre_test_max = int(data.get('pre_test_max', 16))

        # ── Create participant record ───────────────────────────────
        db = SessionLocal()
        try:
            participant = ResearchParticipant(
                participant_code=participant_code,
                nickname=nickname.lower(),
                email=email,

                # Group Assignment
                group_assignment=group,

                # Demographics
                age=data.get('age', ''),
                gender=data.get('gender', 'prefer_not_say'),
                study_program=data.get('study_program', ''),

                # ND Profile
                neurodivergence_type=','.join(nd_selections) if nd_selections else 'no',
                neurodivergence_details=data.get('other_details', ''),
                nd_formal_diagnosis=data.get('diagnosis', 'n/a'),
                is_neurodivergent=is_nd,

                # Experience
                programming_experience=data.get('programming_experience', ''),
                security_experience=data.get('security_experience', ''),
                ai_chatbot_experience=data.get('ai_chatbot_experience', ''),
                # New pre-survey fields
                chosen_path=data.get('chosen_path', ''),
                ai_for_learning=data.get('ai_for_learning', ''),
                platforms_used=data.get('platforms_used', ''),
                when_stuck=str(data.get('when_stuck', '')),
                learning_style=str(data.get('learning_style', '')),
                self_confidence_pre=int(data.get('self_confidence_pre', 0) or 0),

                # Pre-Test (Bloom's Taxonomy mapped)
                pre_test_answers=pre_test_answers,
                pre_test_score=pre_test_score,
                pre_test_max=pre_test_max,
                pre_test_bloom_remember=int(data.get('pre_test_bloom_remember', 0)),
                pre_test_bloom_understand=int(data.get('pre_test_bloom_understand', 0)),
                pre_test_bloom_apply=int(data.get('pre_test_bloom_apply', 0)),
                pre_test_bloom_analyse=int(data.get('pre_test_bloom_analyse', 0)),

                # Consent
                consent_given=True,
            )

            db.add(participant)
            db.commit()
            db.refresh(participant)

            print(f"✅ Participant registered: {participant_code}")
            print(f"   Group: {group} | ND: {is_nd} | Nickname: {nickname}")
            print(f"   Security Exp: {data.get('security_experience')}")
            print(f"   Pre-Test: {pre_test_score}/{pre_test_max}")
            print(f"     Remember: {data.get('pre_test_bloom_remember', 0)}/4")
            print(f"     Understand: {data.get('pre_test_bloom_understand', 0)}/4")
            print(f"     Apply: {data.get('pre_test_bloom_apply', 0)}/4")
            print(f"     Analyse: {data.get('pre_test_bloom_analyse', 0)}/4")

            return web.json_response({
                'success': True,
                'participant_code': participant_code
            })

        except Exception as e:
            db.rollback()
            raise e
        finally:
            db.close()

    except Exception as e:
        print(f"❌ Signup error: {e}")
        import traceback
        traceback.print_exc()
        return web.json_response({
            'success': False, 'error': str(e)
        }, status=500)


# ============================================================================
# API: SUBMIT TASK (Vulnerability Findings)
# ============================================================================

async def submit_task_api(request):
    """
    POST /api/research/submit_task
    Saves vulnerability findings, timing data, and interaction logs.

    Expected JSON:
    {
        "participant_code": "ABC12345",
        "vulnerability_findings": [...],
        "elapsed_time": 4500,
        "time_remaining": 0,
        "interaction_logs": [...],
        "ai_messages_count": 15,
        "ai_hints_requested": 5,
        "ai_encouragements_sent": 3
    }
    """
    try:
        data = await request.json()
        participant_code = data.get('participant_code')

        if not participant_code:
            return web.json_response({
                'success': False, 'error': 'Participant code is required'
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

            # ── Save task data ──────────────────────────────────────
            participant.task_end_time = datetime.utcnow()
            participant.task_elapsed_time = data.get('elapsed_time', 0)
            participant.task_time_remaining = data.get('time_remaining', 0)
            participant.task_submission_time = datetime.utcnow()
            participant.task_completed = True

            # ── Vulnerability findings ──────────────────────────────
            findings = data.get('vulnerability_findings', [])
            participant.vulnerability_findings = findings
            participant.vuln_count = len(findings)
            participant.compute_vuln_scores()

            # Count unique OWASP categories
            owasp_cats = list(set(
                f.get('owasp_category', '') for f in findings
                if f.get('owasp_category')
            ))
            participant.vuln_owasp_categories_found = owasp_cats

            # ── AI Interaction logs (Group A only) ──────────────────
            if participant.group_assignment == 'A':
                pass  # All counters managed by log_interaction API
                # DON'T overwrite — log_interaction API already populates this
                # participant.interaction_logs = data.get('interaction_logs', [])
                # DON'T overwrite — log_interaction API already increments this
                # participant.ai_messages_count = data.get('ai_messages_count', 0)
                # DON'T overwrite — log_interaction API already increments this
                # participant.ai_hints_requested = data.get('ai_hints_requested', 0)
                # DON'T overwrite — log_interaction API already increments this
                # participant.ai_encouragements_sent = data.get('ai_encouragements_sent', 0)
                # DON'T overwrite — log_interaction API already populates this
                # participant.ai_idle_triggers = data.get('ai_idle_triggers', [])

            # ── Commit ──────────────────────────────────────────────
            db.flush()
            db.commit()
            db.refresh(participant)

            print(f"✅ Task submitted: {participant_code}")
            print(f"   Group: {participant.group_assignment}")
            print(f"   Time: {data.get('elapsed_time', 0)}s")
            print(f"   Vulnerabilities found: {len(findings)}")
            print(f"   OWASP categories: {owasp_cats}")
            if participant.group_assignment == 'A':
                print(f"   AI messages: {participant.ai_messages_count}")
                print(f"   Hints requested: {participant.ai_hints_requested}")

            return web.json_response({
                'success': True,
                'message': 'Task submitted successfully',
                'vuln_count': len(findings)
            })

        except Exception as e:
            db.rollback()
            raise e
        finally:
            db.close()

    except Exception as e:
        print(f"❌ Task submission error: {e}")
        import traceback
        traceback.print_exc()
        return web.json_response({
            'success': False, 'error': str(e)
        }, status=500)


# ============================================================================
# API: SUBMIT POST-TEST
# ============================================================================

async def submit_post_test_api(request):
    """
    POST /api/research/submit_post_test
    Saves post-test knowledge, NASA-TLX, SUS, perception, qualitative.

    Expected JSON:
    {
        "participant_code": "ABC12345",
        "post_test_answers": {...},
        "post_test_score": 14,
        "post_test_max": 16,
        "post_test_bloom_remember": 4,
        "post_test_bloom_understand": 4,
        "post_test_bloom_apply": 3,
        "post_test_bloom_analyse": 3,
        "nasa_mental_demand": 65,
        "nasa_temporal_demand": 50,
        "nasa_performance": 70,
        "nasa_effort": 55,
        "nasa_frustration": 30,
        "sus_q1": 4, ... "sus_q10": 2,
        "perception_q1": 4, ... "perception_q12": 5,
        "qual_easiest_vuln": "...",
        "qual_hardest_vuln": "...",
        "qual_strategy": "...",
        "qual_different_next": "...",
        "qual_confidence_rating": 4,
        "qual_ai_helpfulness": 5,       (Group A only)
        "qual_ai_moment": "...",         (Group A only)
        "qual_ai_understand_why": "...", (Group A only)
        "qual_resources_adequate": 3,    (Group B only)
        "qual_stuck_moment": "..."       (Group B only)
    }
    """
    try:
        data = await request.json()
        participant_code = data.get('participant_code')

        if not participant_code:
            return web.json_response({
                'success': False, 'error': 'Participant code is required'
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

            # ── Post-Test Knowledge ─────────────────────────────────
            participant.post_test_answers = data.get('post_test_answers', {})
            participant.post_test_score = int(data.get('post_test_score', 0))
            participant.post_test_max = int(data.get('post_test_max', 16))
            participant.post_test_bloom_remember = int(data.get('post_test_bloom_remember', 0))
            participant.post_test_bloom_understand = int(data.get('post_test_bloom_understand', 0))
            participant.post_test_bloom_apply = int(data.get('post_test_bloom_apply', 0))
            participant.post_test_bloom_analyse = int(data.get('post_test_bloom_analyse', 0))

            # Compute normalised gain: G = (post - pre) / (max - pre)
            participant.compute_normalised_gain()

            # ── NASA-TLX (Hart & Staveland 1988) ────────────────────
            participant.nasa_mental_demand = data.get('nasa_mental_demand')
            participant.nasa_temporal_demand = data.get('nasa_temporal_demand')
            participant.nasa_performance = data.get('nasa_performance')
            participant.nasa_effort = data.get('nasa_effort')
            participant.nasa_frustration = data.get('nasa_frustration')
            participant.compute_nasa_tlx_avg()

            # ── SUS (Brooke 1996) — All participants ────────────────
            for i in range(1, 11):
                setattr(participant, f'sus_q{i}', data.get(f'sus_q{i}'))
            participant.compute_sus_score()

            # ── Perception Questionnaire ────────────────────────────
            perception_values = []
            for i in range(1, 13):
                val = data.get(f'perception_q{i}')
                setattr(participant, f'perception_q{i}', val)
                if val is not None:
                    perception_values.append(int(val))

            if perception_values:
                participant.perception_avg = round(
                    sum(perception_values) / len(perception_values), 2
                )

            # ── Qualitative Reflection ──────────────────────────────
            participant.qual_easiest_vuln = data.get('qual_easiest_vuln', '')
            participant.qual_hardest_vuln = data.get('qual_hardest_vuln', '')
            participant.qual_strategy = data.get('qual_strategy', '')
            participant.qual_different_next = data.get('qual_different_next', '')
            participant.qual_confidence_rating = data.get('qual_confidence_rating')

            # Group A specific
            if participant.group_assignment == 'A':
                participant.qual_ai_helpfulness = data.get('qual_ai_helpfulness')
                participant.qual_ai_moment = data.get('qual_ai_moment', '')
                participant.qual_ai_understand_why = data.get('qual_ai_understand_why', '')

            # Group B specific
            if participant.group_assignment == 'B':
                participant.qual_resources_adequate = data.get('qual_resources_adequate')
                participant.qual_stuck_moment = data.get('qual_stuck_moment', '')

            # ── Commit ──────────────────────────────────────────────
            db.flush()
            db.commit()
            db.refresh(participant)

            print(f"✅ Post-test submitted: {participant_code}")
            print(f"   Post-Test Score: {participant.post_test_score}/{participant.post_test_max}")
            print(f"   Normalised Gain: {participant.normalised_gain}")
            print(f"   NASA-TLX Avg: {participant.nasa_tlx_avg}")
            if participant.group_assignment == 'A':
                print(f"   SUS Score: {participant.sus_total}")
            print(f"   Perception Avg: {participant.perception_avg}")

            return web.json_response({
                'success': True,
                'message': 'Post-test submitted successfully',
                'normalised_gain': participant.normalised_gain,
                'nasa_tlx_avg': participant.nasa_tlx_avg,
                'sus_total': participant.sus_total
            })

        except Exception as e:
            db.rollback()
            raise e
        finally:
            db.close()

    except Exception as e:
        print(f"❌ Post-test error: {e}")
        import traceback
        traceback.print_exc()
        return web.json_response({
            'success': False, 'error': str(e)
        }, status=500)


# ============================================================================
# API: SAVE INDIVIDUAL FINDING (auto-save during task)
# ============================================================================

async def save_finding_api(request):
    """
    POST /api/research/save_finding
    Auto-saves a single vulnerability finding with timestamp.
    Called each time participant adds/updates a finding.

    Expected JSON:
    {
        "participant_code": "ABC12345",
        "findings": [{ finding1 }, { finding2 }, ...]
    }
    """
    try:
        data = await request.json()
        participant_code = data.get('participant_code')

        if not participant_code:
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

            findings = data.get('findings', [])
            participant.vulnerability_findings = findings
            participant.vuln_count = len(findings)

            db.commit()

            return web.json_response({
                'success': True,
                'saved_count': len(findings)
            })

        except Exception as e:
            db.rollback()
            raise e
        finally:
            db.close()

    except Exception as e:
        print(f"❌ Save finding error: {e}")
        return web.json_response({
            'success': False, 'error': str(e)
        }, status=500)


# ============================================================================
# API: LOG INTERACTION (real-time AI chat logging)
# ============================================================================

async def log_interaction_api(request):
    """
    POST /api/research/log_interaction
    Logs a single AI interaction event (Group A only).

    Expected JSON:
    {
        "participant_code": "ABC12345",
        "event": {
            "timestamp": "...",
            "role": "user|assistant|system",
            "message": "...",
            "type": "question|hint_request|encouragement|explanation|nudge"
        }
    }
    """
    try:
        data = await request.json()
        participant_code = data.get('participant_code')

        if not participant_code:
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

            # Append to existing logs - accept both old and new format
            logs = participant.interaction_logs or []
            event = data.get('event', {})
            # New format from frontend: flat structure
            interaction_type = data.get('interaction_type', '')
            content = data.get('content', '')
            context = data.get('context', '')
            page = data.get('page', '')
            
            if interaction_type:
                # Frontend sends flat format
                event = {
                    'role': interaction_type,
                    'type': interaction_type,
                    'content': content,
                    'context': context,
                    'page': page,
                    'timestamp': datetime.utcnow().isoformat()
                }
            
            logs.append(event)
            participant.interaction_logs = logs
            flag_modified(participant, 'interaction_logs')

            # Track start time on first interaction (works for both paths)
            if not participant.task_start_time:
                participant.task_start_time = datetime.utcnow()

            # Update counters
            role = event.get('role', '') or interaction_type
            event_type = event.get('type', '')

            if role in ('assistant', 'ai'):
                participant.ai_messages_count = (participant.ai_messages_count or 0) + 1
            if role == 'user':
                participant.ai_messages_count = (participant.ai_messages_count or 0) + 1
            if interaction_type == 'exercise_complete':
                # Track exercise completion - count in ai_messages for now
                pass
            # Update accessibility columns if this is an accessibility check
            if role == 'accessibility' or interaction_type == 'accessibility':
                try:
                    import json as _json
                    acc = _json.loads(content) if isinstance(content, str) else content
                    if acc.get('dark_mode'):
                        participant.accessibility_dark_mode = True
                    if acc.get('dyslexia_font'):
                        participant.accessibility_dyslexia_font = True
                    if acc.get('focus_mode'):
                        participant.accessibility_tts = True
                    if acc.get('reading_mask'):
                        participant.accessibility_reading_pointer = True
                    if acc.get('high_contrast'):
                        participant.accessibility_dark_mode = True
                except:
                    pass

            if role == 'hint_request' or event_type == 'hint_request':
                participant.ai_hints_requested = (participant.ai_hints_requested or 0) + 1
            if role == 'system' or event_type in ('encouragement', 'nudge') or 'nudge' in content.lower():
                participant.ai_encouragements_sent = (participant.ai_encouragements_sent or 0) + 1
                triggers = participant.ai_idle_triggers or []
                triggers.append(event.get('timestamp', ''))
                participant.ai_idle_triggers = triggers
                flag_modified(participant, 'ai_idle_triggers')

            db.commit()

            return web.json_response({'success': True})

        except Exception as e:
            db.rollback()
            raise e
        finally:
            db.close()

    except Exception as e:
        print(f"❌ Log interaction error: {e}")
        return web.json_response({
            'success': False, 'error': str(e)
        }, status=500)


# ============================================================================
# API: GET PARTICIPANT INFO
# ============================================================================

async def get_participant_api(request):
    """
    GET /api/research/participant?code=XXX
    Returns participant info (group, ND status, pre-test score).
    Used by task page to configure UI.
    """
    code = request.query.get('code', '')
    if not code:
        return web.json_response({'error': 'No code'}, status=400)

    db = SessionLocal()
    try:
        p = db.query(ResearchParticipant).filter_by(participant_code=code).first()
        if not p:
            return web.json_response({'error': 'Not found'}, status=404)

        # Set task_start_time on first task page load + reset ShopSecure
        if not p.task_start_time:
            from datetime import datetime as _dt
            p.task_start_time = _dt.now()
            db.commit()
            # Auto-reset ShopSecure for fresh participant
            import subprocess
            try:
                subprocess.run(['docker', 'exec', 'shopsecure', 'rm', '-f', '/app/data/shop.db'], timeout=5)
                subprocess.run(['docker', 'exec', 'shopsecure', 'rm', '-rf', '/app/data/invoices/'], timeout=5)
                subprocess.run(['docker', 'restart', 'shopsecure'], timeout=10)
                print(f"[+] ShopSecure auto-reset for participant {p.participant_code}")
            except Exception as e:
                print(f"[-] ShopSecure reset failed: {e}")

        return web.json_response({
            'participant_code': p.participant_code,
            'nickname': p.nickname,
            'group': p.group_assignment,
            'is_neurodivergent': p.is_neurodivergent,
            'security_experience': p.security_experience,
            'pre_test_score': p.pre_test_score,
            'pre_test_max': p.pre_test_max,
            'task_completed': p.task_completed or False,
            'vulnerability_findings': p.vulnerability_findings or [],
            'interaction_logs': p.interaction_logs or []
        })
    finally:
        db.close()


# ============================================================================
# API: CHECK NICKNAME / EMAIL (kept from original)
# ============================================================================

async def check_nickname_api(request):
    """POST /api/research/check_nickname"""
    try:
        data = await request.json()
        nickname = data.get('nickname', '').strip().lower()

        if not nickname or len(nickname) < 3:
            return web.json_response({'available': False})

        db = SessionLocal()
        try:
            existing = db.query(ResearchParticipant).filter_by(nickname=nickname).first()
            return web.json_response({'available': existing is None})
        finally:
            db.close()

    except Exception as e:
        return web.json_response({'available': False, 'error': str(e)})


async def check_email_api(request):
    """POST /api/research/check_email"""
    try:
        data = await request.json()
        email = data.get('email', '').strip().lower()

        if not email:
            return web.json_response({'available': True})

        db = SessionLocal()
        try:
            existing = db.query(ResearchParticipant).filter_by(email=email).first()
            return web.json_response({'available': existing is None})
        finally:
            db.close()

    except Exception as e:
        return web.json_response({'available': True, 'error': str(e)})


async def recover_code_nickname_api(request):
    """POST /api/research/recover_code_nickname"""
    try:
        data = await request.json()
        nickname = data.get('nickname', '').strip().lower()

        if not nickname:
            return web.json_response({'success': False, 'error': 'Nickname required'})

        db = SessionLocal()
        try:
            participant = db.query(ResearchParticipant).filter_by(nickname=nickname).first()
            if participant:
                return web.json_response({
                    'success': True,
                    'participant_code': participant.participant_code
                })
            return web.json_response({'success': False, 'error': 'Nickname not found'})
        finally:
            db.close()

    except Exception as e:
        return web.json_response({'success': False, 'error': str(e)})


async def validate_code_api(request):
    """POST /api/research/validate_code"""
    try:
        data = await request.json()
        code = data.get('participant_code', '').strip().upper()

        db = SessionLocal()
        try:
            participant = db.query(ResearchParticipant).filter_by(
                participant_code=code
            ).first()

            if participant:
                return web.json_response({
                    'valid': True,
                    'nickname': participant.nickname,
                    'group': participant.group_assignment
                })
            return web.json_response({'valid': False})
        finally:
            db.close()

    except Exception as e:
        return web.json_response({'valid': False, 'error': str(e)})


# ============================================================================
# ROUTE SETUP
# ============================================================================


async def research_experiment_page(request):
    """GET /research/experiment — Show experiment flow with pre/post quiz"""
    html_path = Path(__file__).parent.parent / 'templates' / 'research' / 'experiment_flow.html'
    return web.FileResponse(html_path)

async def mission_page(request):
    """GET /mission — Show vulnerability mission (logged-in users only, no research enrollment)"""
    user_id = request.cookies.get('synapse_user')
    if not user_id:
        raise web.HTTPFound('/login?next=/mission')
    if not request.query.get('participant'):
        mission_code = f'MISSION_U{user_id}'
        raise web.HTTPFound(f'/mission?participant={mission_code}')
    # Get user display_name from DB
    from sqlalchemy import text
    display_name = 'Learner'
    db = SessionLocal()
    try:
        result = db.execute(
            text("SELECT display_name FROM users WHERE id = :uid"),
            {'uid': int(user_id)}
        ).fetchone()
        if result and result.display_name:
            display_name = result.display_name
    except Exception:
        pass
    finally:
        db.close()
    html_path = Path(__file__).parent.parent / 'templates' / 'research' / 'research_task.html'
    if not html_path.exists():
        return web.Response(text="Mission page not found.", status=404)
    with open(html_path, 'r', encoding='utf-8') as f:
        html_content = f.read()
    # Inject user display_name as window variable so template can use it
    safe_name = display_name.replace('"', '').replace('<', '').replace('>', '')
    injection = f'<script>window.MISSION_USER_NAME = "{safe_name}";</script>\n'
    html_content = html_content.replace('</head>', injection + '</head>', 1)
    return web.Response(text=html_content, content_type='text/html')

def setup_research_routes(app):
    """Register all research routes"""

    # HTML Pages
    app.router.add_get('/research/signup', research_signup_page)
    app.router.add_get('/research/welcome', research_welcome_page)
    app.router.add_get('/research/task', research_task_page)
    app.router.add_get('/mission', mission_page)
    app.router.add_get('/research/experiment', research_experiment_page)
    app.router.add_get('/research/post_test', research_post_test_page)

    # API — Signup & Auth
    app.router.add_post('/api/research/signup', research_signup_api)
    app.router.add_post('/api/research/check_nickname', check_nickname_api)
    app.router.add_post('/api/research/check_email', check_email_api)
    app.router.add_post('/api/research/validate_code', validate_code_api)
    app.router.add_post('/api/research/recover_code_nickname', recover_code_nickname_api)

    # API — Task & Data Collection
    app.router.add_post('/api/research/submit_task', submit_task_api)
    app.router.add_post('/api/research/submit_post_test', submit_post_test_api)
    app.router.add_post('/api/research/save_finding', save_finding_api)
    app.router.add_post('/api/research/log_interaction', log_interaction_api)

    # API — Participant Info
    app.router.add_get('/api/research/participant', get_participant_api)

    print("✅ Research routes configured (ShopSecure Study)")
    print("   Pages:")
    print("   • GET  /research/signup")
    print("   • GET  /research/welcome")
    print("   • GET  /research/task")
    print("   • GET  /research/post_test")
    print("   API:")
    print("   • POST /api/research/signup")
    print("   • POST /api/research/submit_task")
    print("   • POST /api/research/submit_post_test")
    print("   • POST /api/research/save_finding")
    print("   • POST /api/research/log_interaction")
    print("   • GET  /api/research/participant")
    print("   • POST /api/research/check_nickname")
    print("   • POST /api/research/validate_code")
