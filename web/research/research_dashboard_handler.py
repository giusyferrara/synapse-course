"""
Research Dashboard — PostgreSQL-based
Reads directly from research_participants table via SQLAlchemy
"""
from aiohttp import web
import json
from datetime import datetime
from database.models import ResearchParticipant
from database.config import SessionLocal
from sqlalchemy import func


async def dashboard_html_handler(request):
    """GET /research/dashboard — Serves dashboard HTML"""
    try:
        from pathlib import Path
        p = Path(__file__).parent.parent.parent / 'templates' / 'research' / 'research_dashboard.html'
        if not p.exists():
            return web.Response(text='Dashboard not found', status=404)
        with open(p, 'r', encoding='utf-8') as f:
            return web.Response(text=f.read(), content_type='text/html')
    except Exception as e:
        return web.Response(text=f'Error: {e}', status=500)


async def dashboard_data_handler(request):
    """GET /api/research/dashboard_data — All data from DB"""
    db = SessionLocal()
    try:
        participants = db.query(ResearchParticipant).all()
        
        result = {
            'total': len(participants),
            'completed': 0,
            'participants': [],
            'summary': {
                'group_a': {'total': 0, 'nd': 0, 'nt': 0, 'completed': 0},
                'group_b': {'total': 0, 'nd': 0, 'nt': 0, 'completed': 0},
                'path_beginner': 0,
                'path_experienced': 0,
            },
            'metrics': {
                'pre_scores': [], 'post_scores': [], 'gains': [],
                'nasa_mental': [], 'nasa_temporal': [], 'nasa_performance': [],
                'nasa_effort': [], 'nasa_frustration': [], 'nasa_avg': [],
                'sus_scores': [], 'perception_avgs': [],
                'vuln_counts': [], 'ai_msg_counts': [],
            },
            'bloom': {
                'pre': {'remember': [], 'understand': [], 'apply': [], 'analyse': []},
                'post': {'remember': [], 'understand': [], 'apply': [], 'analyse': []},
            },
            'by_group': {'A': [], 'B': []},
            'by_nd': {'nd': [], 'nt': []},
            'cells': {
                'A_ND': [], 'A_NT': [], 'B_ND': [], 'B_NT': []
            },
            'qualitative': [],
            'accessibility': {'dyslexia_font': 0, 'reading_pointer': 0, 'dark_mode': 0, 'tts': 0},
        }
        
        for p in participants:
            completed = p.post_test_score is not None
            if completed:
                result['completed'] += 1
            
            grp = p.group_assignment or '?'
            nd = bool(p.is_neurodivergent)
            nd_label = 'nd' if nd else 'nt'
            cell = f'{grp}_{nd_label.upper()}'
            
            # Path counts
            path = getattr(p, 'chosen_path', '') or ''
            if path == 'beginner':
                result['summary']['path_beginner'] += 1
            elif path == 'experienced':
                result['summary']['path_experienced'] += 1

            # Summary counts
            if grp == 'A':
                result['summary']['group_a']['total'] += 1
                if nd: result['summary']['group_a']['nd'] += 1
                else: result['summary']['group_a']['nt'] += 1
                if completed: result['summary']['group_a']['completed'] += 1
            elif grp == 'B':
                result['summary']['group_b']['total'] += 1
                if nd: result['summary']['group_b']['nd'] += 1
                else: result['summary']['group_b']['nt'] += 1
                if completed: result['summary']['group_b']['completed'] += 1
            
            # Participant record
            rec = {
                'code': p.participant_code,
                'nickname': p.nickname,
                'group': grp,
                'is_nd': nd,
                'nd_type': p.neurodivergence_type,
                'age': p.age,
                'gender': p.gender,
                'program': p.study_program,
                'prog_exp': p.programming_experience,
                'sec_exp': p.security_experience,
                'ai_exp': p.ai_chatbot_experience,
                'chosen_path': getattr(p, 'chosen_path', ''),
                'ai_for_learning': getattr(p, 'ai_for_learning', ''),
                'platforms_used': getattr(p, 'platforms_used', ''),
                'when_stuck': getattr(p, 'when_stuck', ''),
                'learning_style': getattr(p, 'learning_style', ''),
                'self_confidence_pre': getattr(p, 'self_confidence_pre', None),
                'completed': completed,
                'created': str(p.created_at) if p.created_at else None,
                # Pre-test
                'pre_score': p.pre_test_score,
                'pre_max': p.pre_test_max,
                'pre_bloom': {
                    'remember': p.pre_test_bloom_remember,
                    'understand': p.pre_test_bloom_understand,
                    'apply': p.pre_test_bloom_apply,
                    'analyse': p.pre_test_bloom_analyse,
                },
                # Post-test
                'post_score': p.post_test_score,
                'post_max': p.post_test_max,
                'post_bloom': {
                    'remember': p.post_test_bloom_remember,
                    'understand': p.post_test_bloom_understand,
                    'apply': p.post_test_bloom_apply,
                    'analyse': p.post_test_bloom_analyse,
                },
                'gain': p.normalised_gain,
                # NASA-TLX
                'nasa': {
                    'mental': p.nasa_mental_demand,
                    'temporal': p.nasa_temporal_demand,
                    'performance': p.nasa_performance,
                    'effort': p.nasa_effort,
                    'frustration': p.nasa_frustration,
                    'avg': p.nasa_tlx_avg,
                },
                # SUS
                'sus_total': p.sus_total,
                # Perception
                'perception_avg': p.perception_avg,
                # Vulnerability findings
                'vuln_count': p.vuln_count or 0,
                'vuln_total_score': p.vuln_total_score,
                'vuln_avg_quality': p.vuln_avg_quality,
                'vuln_findings': p.vulnerability_findings,
                # AI interaction
                'ai_messages': p.ai_messages_count or 0,
                'ai_hints': p.ai_hints_requested or 0,
                'ai_encouragements': p.ai_encouragements_sent or 0,
                'ai_avg_response': p.ai_avg_response_time,
                # Task timing
                'task_elapsed': p.task_elapsed_time,
                'task_start': str(p.task_start_time) if p.task_start_time else None,
                'exercises_completed': 0,
                'exercise_list': [],
                'session_duration_min': None,
                'task_remaining': p.task_time_remaining,
                # Qualitative
                'qual': {
                    'easiest': p.qual_easiest_vuln,
                    'hardest': p.qual_hardest_vuln,
                    'strategy': p.qual_strategy,
                    'different': p.qual_different_next,
                    'confidence': p.qual_confidence_rating,
                    'ai_helpfulness': p.qual_ai_helpfulness,
                    'ai_moment': p.qual_ai_moment,
                    'ai_why': p.qual_ai_understand_why,
                    'resources_adequate': p.qual_resources_adequate,
                    'stuck': p.qual_stuck_moment,
                },
                # Accessibility
                'accessibility': {
                    'dyslexia_font': bool(p.accessibility_dyslexia_font),
                    'reading_pointer': bool(p.accessibility_reading_pointer),
                    'dark_mode': bool(p.accessibility_dark_mode),
                    'tts': bool(p.accessibility_tts),
                },
            }
            
            # Compute exercises completed + session duration from logs
            logs = p.interaction_logs or []
            if isinstance(logs, list):
                exercises = [l for l in logs if isinstance(l, dict) and l.get('type') == 'exercise_complete']
                seen = set()
                unique_ex = []
                for ex in exercises:
                    t = ex.get('content', '')[:60]
                    if t not in seen:
                        seen.add(t)
                        unique_ex.append(t)
                rec['exercises_completed'] = len(unique_ex)
                rec['exercise_list'] = unique_ex

                # Session duration: first to last ACTIVE interaction (skip accessibility checks)
                timestamps = []
                for l in logs:
                    if isinstance(l, dict) and l.get('timestamp'):
                        ltype = l.get('type', '') or l.get('role', '')
                        if ltype not in ('accessibility', 'accessibility_check', 'accessibility_feature', 'accessibility_menu_toggle'):
                            timestamps.append(l['timestamp'])
                if p.task_start_time:
                    timestamps.append(str(p.task_start_time))
                if timestamps:
                    try:
                        from datetime import datetime as _dt
                        parsed = []
                        for t in timestamps:
                            try:
                                if 'T' in str(t):
                                    parsed.append(_dt.fromisoformat(str(t).replace('Z', '+00:00').split('+')[0]))
                                else:
                                    parsed.append(_dt.fromisoformat(str(t).split('+')[0]))
                            except:
                                pass
                        if parsed:
                            parsed.sort()
                            active = sum((parsed[j] - parsed[j-1]).total_seconds() for j in range(1, len(parsed)) if (parsed[j] - parsed[j-1]).total_seconds() < 120)
                            rec['session_duration_min'] = round(active / 60, 1) if active > 0 else None
                    except:
                        pass

            result['participants'].append(rec)
            
            # Group arrays
            if grp in ('A', 'B'):
                result['by_group'][grp].append(rec)
            result['by_nd'][nd_label].append(rec)
            if cell in result['cells']:
                result['cells'][cell].append(rec)
            
            # Aggregate metrics (only completed)
            if completed:
                if p.pre_test_score is not None:
                    result['metrics']['pre_scores'].append(p.pre_test_score)
                if p.post_test_score is not None:
                    result['metrics']['post_scores'].append(p.post_test_score)
                if p.normalised_gain is not None:
                    result['metrics']['gains'].append(p.normalised_gain)
                if p.nasa_mental_demand is not None:
                    result['metrics']['nasa_mental'].append(p.nasa_mental_demand)
                    result['metrics']['nasa_temporal'].append(p.nasa_temporal_demand)
                    result['metrics']['nasa_performance'].append(p.nasa_performance)
                    result['metrics']['nasa_effort'].append(p.nasa_effort)
                    result['metrics']['nasa_frustration'].append(p.nasa_frustration)
                    result['metrics']['nasa_avg'].append(p.nasa_tlx_avg)
                if p.sus_total is not None:
                    result['metrics']['sus_scores'].append(p.sus_total)
                if p.perception_avg is not None:
                    result['metrics']['perception_avgs'].append(p.perception_avg)
                result['metrics']['vuln_counts'].append(p.vuln_count or 0)
                result['metrics']['ai_msg_counts'].append(p.ai_messages_count or 0)
                
                # Bloom
                for level in ['remember', 'understand', 'apply', 'analyse']:
                    pre_val = getattr(p, f'pre_test_bloom_{level}', None)
                    post_val = getattr(p, f'post_test_bloom_{level}', None)
                    if pre_val is not None:
                        result['bloom']['pre'][level].append(pre_val)
                    if post_val is not None:
                        result['bloom']['post'][level].append(post_val)
                
                # Qualitative
                if p.qual_strategy or p.qual_easiest_vuln:
                    result['qualitative'].append({
                        'code': p.participant_code,
                        'group': grp,
                        'nd': nd,
                        'easiest': p.qual_easiest_vuln,
                        'hardest': p.qual_hardest_vuln,
                        'strategy': p.qual_strategy,
                        'different': p.qual_different_next,
                        'confidence': p.qual_confidence_rating,
                    })
            
            # Accessibility counts
            if p.accessibility_dyslexia_font: result['accessibility']['dyslexia_font'] += 1
            if p.accessibility_reading_pointer: result['accessibility']['reading_pointer'] += 1
            if p.accessibility_dark_mode: result['accessibility']['dark_mode'] += 1
            if p.accessibility_tts: result['accessibility']['tts'] += 1
        
        return web.json_response(result)
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        return web.json_response({'error': str(e)}, status=500)
    finally:
        db.close()


async def export_csv_handler(request):
    """GET /api/research/export/csv — Export all data as CSV"""
    db = SessionLocal()
    try:
        participants = db.query(ResearchParticipant).all()
        
        cols = [
            'participant_code','group_assignment','is_neurodivergent','neurodivergence_type',
            'age','gender','study_program','programming_experience','security_experience',
            'ai_chatbot_experience','pre_test_score','pre_test_max',
            'pre_test_bloom_remember','pre_test_bloom_understand','pre_test_bloom_apply','pre_test_bloom_analyse',
            'post_test_score','post_test_max',
            'post_test_bloom_remember','post_test_bloom_understand','post_test_bloom_apply','post_test_bloom_analyse',
            'normalised_gain',
            'nasa_mental_demand','nasa_temporal_demand','nasa_performance','nasa_effort','nasa_frustration','nasa_tlx_avg',
            'sus_total','perception_avg',
            'vuln_count','vuln_total_score','vuln_avg_quality',
            'ai_messages_count','ai_hints_requested','ai_encouragements_sent','ai_avg_response_time',
            'task_elapsed_time','task_time_remaining',
            'qual_easiest_vuln','qual_hardest_vuln','qual_strategy','qual_different_next',
            'qual_confidence_rating','qual_ai_helpfulness','qual_resources_adequate',
            'accessibility_dyslexia_font','accessibility_reading_pointer','accessibility_dark_mode','accessibility_tts',
        ]
        
        lines = [','.join(cols)]
        for p in participants:
            row = []
            for c in cols:
                val = getattr(p, c, '')
                if val is None:
                    row.append('')
                elif isinstance(val, bool):
                    row.append('1' if val else '0')
                elif isinstance(val, str) and (',' in val or '"' in val or '\n' in val):
                    row.append(f'"{val.replace(chr(34), chr(34)+chr(34))}"')
                else:
                    row.append(str(val))
            lines.append(','.join(row))
        
        csv_text = '\n'.join(lines)
        
        return web.Response(
            text=csv_text,
            content_type='text/csv',
            headers={'Content-Disposition': f'attachment; filename="synapse_research_{datetime.now().strftime("%Y%m%d")}.csv"'}
        )
    except Exception as e:
        return web.json_response({'error': str(e)}, status=500)
    finally:
        db.close()


def setup_research_routes(app):
    """Register dashboard routes"""
    app.router.add_get('/research/dashboard', dashboard_html_handler)
    app.router.add_get('/api/research/dashboard_data', dashboard_data_handler)
    app.router.add_get('/api/research/export/csv', export_csv_handler)
    print("\u2705 Research dashboard routes registered (DB-based)")
