"""
web/metrics_handlers_VALIDATED.py

OBJECTIVE BEHAVIORAL METRICS - RESEARCH VALIDATED
==================================================

This implementation tracks ONLY objective, measurable behaviors.
NO subjective metric calculation (attention, emotion) from behavior.

Research Foundation:
--------------------
1. Task Switching: Becker et al. (2019) "Sluggish cognitive tempo and ADHD"
2. Error Patterns: Jadalla & Elnagar (2020) "Programming difficulties in ADHD students"  
3. Time on Task: Rapport et al. (2013) "On-task behavior in ADHD"
4. Keystroke Dynamics: Monaco et al. (2018) "Keystroke biometrics"
5. Help-Seeking: Roll et al. (2011) "Help seeking in intelligent tutoring"

Methodology:
------------
✅ TRACK: Objective behaviors (clicks, keystrokes, errors, time)
✅ MEASURE: Self-reported emotional states (ground truth)
✅ ANALYZE: Compare ADHD vs Control on objective metrics
❌ DON'T: Calculate subjective states from behavior

Export Format:
--------------
CSV with columns for statistical analysis in R/Python:
- participant_id, group (ADHD/Control), session_id
- Objective metrics: task_switches, error_rate, time_on_task, etc.
- Self-reported: attention_rating, stress_rating, emotion_rating
"""

from aiohttp import web
import time
import json
import csv
import io
from datetime import datetime
from typing import Dict, Any, List
import os


class ObjectiveBehavioralMetrics:
    """
    Tracks ONLY objective, observable behaviors.
    No algorithmic inference of subjective states.
    """

    def __init__(self, research_data_dir='research_data'):
        self.sessions = {}
        self.research_data_dir = research_data_dir
        os.makedirs(research_data_dir, exist_ok=True)

    def init_session(self, session_id: str, user_id=None, group=None):
        """
        Initialize tracking session
        
        Args:
            session_id: Unique session identifier
            user_id: Participant code (e.g., 'P001', 'P002')
            group: 'ADHD' or 'Control' (for research comparison)
        """
        if session_id in self.sessions:
            return self.sessions[session_id]

        self.sessions[session_id] = {
            'session_id': session_id,
            'user_id': user_id,
            'group': group,  # ADHD or Control
            'start_time': time.time(),
            'end_time': None,
            
            # ========================================
            # OBJECTIVE BEHAVIORAL DATA
            # ========================================
            
            'events': {
                # 1. TASK SWITCHING (Becker et al. 2019)
                'tab_switches': [],  # {time, from, to, duration_on_previous}
                
                # 2. CODE EXECUTION & ERRORS (Jadalla & Elnagar 2020)
                'code_executions': [],  # {time, success, error_type, code_length}
                
                # 3. TIME ON TASK (Rapport et al. 2013)
                'section_time': [],  # {time, section, duration_seconds}
                
                # 4. KEYSTROKE PATTERNS (Monaco et al. 2018)
                'keystroke_intervals': [],  # {time, interval_ms, burst_detected}
                
                # 5. HELP-SEEKING (Roll et al. 2011)
                'help_requests': [],  # {time, type, context}
                
                # 6. IDLE/PAUSE DETECTION
                'pauses': [],  # {time, duration_seconds, context}
                
                # 7. RAW INTERACTIONS (for exploratory analysis)
                'clicks': [],
                'scrolls': []
            },
            
            # ========================================
            # SELF-REPORTED DATA (GROUND TRUTH)
            # ========================================
            
            'self_reports': [],  # {time, attention_1_10, difficulty_1_10, emotion, stress}
            
            # ========================================
            # CONTEXT TRACKING
            # ========================================
            
            'context': {
                'current_course': None,
                'current_section': None,
                'section_start_time': None,
                'exercise_id': None,
                'exercise_start_time': None
            },
            
            # For calculating derived metrics
            'last_activity': time.time(),
            'last_keystroke': None
        }

        return self.sessions[session_id]

    # ========================================
    # METRIC 1: TASK SWITCHING RATE
    # ========================================
    
    def track_tab_switch(self, session_id: str, data: Dict):
        """
        Track tab/section switching
        
        Research: Becker et al. (2019) - ADHD students show higher task switching
        Metric: switches_per_minute
        """
        if session_id not in self.sessions:
            self.init_session(session_id)

        session = self.sessions[session_id]
        current_time = time.time()
        
        # Calculate time on previous section
        duration_on_previous = 0
        if session['context']['section_start_time']:
            duration_on_previous = current_time - session['context']['section_start_time']
        
        session['events']['tab_switches'].append({
            'time': current_time,
            'from': data.get('from', ''),
            'to': data.get('to', ''),
            'duration_on_previous_seconds': round(duration_on_previous, 2)
        })
        
        # Update context
        session['context']['current_section'] = data.get('to', '')
        session['context']['section_start_time'] = current_time
        session['last_activity'] = current_time

    # ========================================
    # METRIC 2: ERROR PATTERNS & RECOVERY
    # ========================================
    
    def track_code_execution(self, session_id: str, data: Dict):
        """
        Track code execution attempts
        
        Research: Jadalla & Elnagar (2020) - ADHD students have different error patterns
        Metrics: 
        - error_rate
        - error_recovery_time (time between error and next success)
        - syntax_error_frequency
        """
        if session_id not in self.sessions:
            self.init_session(session_id)

        session = self.sessions[session_id]
        current_time = time.time()
        
        session['events']['code_executions'].append({
            'time': current_time,
            'success': data.get('success', False),
            'error_type': data.get('error_type', ''),  # 'SyntaxError', 'IndentationError', etc.
            'error_message': data.get('error_message', '')[:200],  # Limit length
            'code_length': len(data.get('code', '')),
            'execution_time_ms': data.get('exec_time_ms', 0)
        })
        
        session['last_activity'] = current_time

    # ========================================
    # METRIC 3: TIME ON TASK
    # ========================================
    
    def track_section_time(self, session_id: str, section: str):
        """
        Track time spent on each section
        
        Research: Rapport et al. (2013) - ADHD students have shorter time on task
        Metric: average_time_per_section, section_completion_rate
        """
        if session_id not in self.sessions:
            self.init_session(session_id)

        session = self.sessions[session_id]
        current_time = time.time()
        
        # End previous section
        if session['context']['section_start_time']:
            duration = current_time - session['context']['section_start_time']
            
            session['events']['section_time'].append({
                'time': session['context']['section_start_time'],
                'section': session['context']['current_section'],
                'duration_seconds': round(duration, 2)
            })
        
        # Start new section
        session['context']['current_section'] = section
        session['context']['section_start_time'] = current_time

    # ========================================
    # METRIC 4: KEYSTROKE DYNAMICS
    # ========================================
    
    def track_keystroke(self, session_id: str, data: Dict):
        """
        Track keystroke timing patterns
        
        Research: Monaco et al. (2018) - Keystroke dynamics reveal cognitive state
        Metrics:
        - inter_keystroke_interval (IKI)
        - pause_frequency (IKI > 2 seconds)
        - burst_typing (IKI < 100ms)
        """
        if session_id not in self.sessions:
            self.init_session(session_id)

        session = self.sessions[session_id]
        current_time = time.time()
        
        # Calculate interval from last keystroke
        interval_ms = 0
        if session['last_keystroke']:
            interval_ms = (current_time - session['last_keystroke']) * 1000
        
        # Detect patterns
        is_pause = interval_ms > 2000  # >2 sec = pause (confusion indicator)
        is_burst = interval_ms < 100 and interval_ms > 0  # <100ms = rapid typing
        
        session['events']['keystroke_intervals'].append({
            'time': current_time,
            'interval_ms': round(interval_ms, 2),
            'is_pause': is_pause,
            'is_burst': is_burst
        })
        
        session['last_keystroke'] = current_time
        session['last_activity'] = current_time

    # ========================================
    # METRIC 5: HELP-SEEKING BEHAVIOR
    # ========================================
    
    def track_help_request(self, session_id: str, data: Dict):
        """
        Track help-seeking behavior
        
        Research: Roll et al. (2011) - Help-seeking patterns indicate learning difficulty
        Metrics:
        - help_requests_per_exercise
        - time_before_seeking_help
        - help_type_distribution (hint vs AI chat vs theory)
        """
        if session_id not in self.sessions:
            self.init_session(session_id)

        session = self.sessions[session_id]
        current_time = time.time()
        
        # Calculate time since exercise started
        time_before_help = 0
        if session['context']['exercise_start_time']:
            time_before_help = current_time - session['context']['exercise_start_time']
        
        session['events']['help_requests'].append({
            'time': current_time,
            'type': data.get('type', 'chat'),  # 'hint', 'ai_chat', 'theory_lookup'
            'context': data.get('context', ''),
            'time_before_help_seconds': round(time_before_help, 2)
        })
        
        session['last_activity'] = current_time

    # ========================================
    # METRIC 6: IDLE/PAUSE DETECTION
    # ========================================
    
    def track_pause(self, session_id: str, duration: float, context: str):
        """
        Track idle/pause periods
        
        Metric: pause_frequency, avg_pause_duration
        Indicator: Long pauses may indicate confusion or distraction
        """
        if session_id not in self.sessions:
            self.init_session(session_id)

        session = self.sessions[session_id]
        
        session['events']['pauses'].append({
            'time': time.time(),
            'duration_seconds': round(duration, 2),
            'context': context
        })

    # ========================================
    # RAW INTERACTION TRACKING
    # ========================================
    
    def track_click(self, session_id: str, data: Dict):
        """Track clicks (for exploratory analysis)"""
        if session_id not in self.sessions:
            self.init_session(session_id)
        
        session = self.sessions[session_id]
        session['events']['clicks'].append({
            'time': time.time(),
            'x': data.get('x', 0),
            'y': data.get('y', 0),
            'target': data.get('target', '')
        })
        session['last_activity'] = time.time()
    
    def track_scroll(self, session_id: str, data: Dict):
        """Track scrolling (for exploratory analysis)"""
        if session_id not in self.sessions:
            self.init_session(session_id)
        
        session = self.sessions[session_id]
        session['events']['scrolls'].append({
            'time': time.time(),
            'position': data.get('position', 0)
        })
        session['last_activity'] = time.time()

    # ========================================
    # SELF-REPORTED DATA (GROUND TRUTH)
    # ========================================
    
    def track_self_report(self, session_id: str, data: Dict):
        """
        Track self-reported emotional/cognitive state
        
        This is the GROUND TRUTH for emotional states.
        We do NOT calculate emotion from behavior - students tell us!
        """
        if session_id not in self.sessions:
            self.init_session(session_id)

        session = self.sessions[session_id]
        session['self_reports'].append({
            'time': time.time(),
            'attention_rating': data.get('attention', 5),  # 1-10 scale
            'difficulty_rating': data.get('difficulty', 5),  # 1-10 scale
            'stress_rating': data.get('stress', 5),  # 1-10 scale
            'emotion': data.get('emotion', ''),  # Selected from dropdown
            'feeling_description': data.get('feeling', '')  # Optional text
        })

    # ========================================
    # AGGREGATED METRICS FOR ANALYSIS
    # ========================================
    
    def get_session_metrics(self, session_id: str) -> Dict[str, Any]:
        """
        Calculate aggregated metrics for the session
        
        These are OBJECTIVE, COUNTABLE metrics - not inferred states
        """
        if session_id not in self.sessions:
            return {}

        session = self.sessions[session_id]
        session_duration_minutes = (time.time() - session['start_time']) / 60
        
        # Avoid division by zero
        if session_duration_minutes < 0.1:
            session_duration_minutes = 0.1
        
        # METRIC 1: Task Switching
        tab_switches = session['events']['tab_switches']
        task_switch_rate = len(tab_switches) / session_duration_minutes
        avg_time_per_section = 0
        if tab_switches:
            times = [s['duration_on_previous_seconds'] for s in tab_switches if s['duration_on_previous_seconds'] > 0]
            avg_time_per_section = sum(times) / len(times) if times else 0
        
        # METRIC 2: Error Patterns
        executions = session['events']['code_executions']
        total_attempts = len(executions)
        errors = sum(1 for ex in executions if not ex['success'])
        error_rate = errors / total_attempts if total_attempts > 0 else 0
        
        syntax_errors = sum(1 for ex in executions if 'Syntax' in ex.get('error_type', ''))
        
        # Error recovery time
        error_recovery_times = []
        for i, ex in enumerate(executions):
            if not ex['success']:
                # Find next success
                for next_ex in executions[i+1:]:
                    if next_ex['success']:
                        recovery_time = next_ex['time'] - ex['time']
                        error_recovery_times.append(recovery_time)
                        break
        
        avg_error_recovery_time = sum(error_recovery_times) / len(error_recovery_times) if error_recovery_times else 0
        
        # METRIC 3: Time on Task
        section_times = session['events']['section_time']
        avg_section_duration = 0
        if section_times:
            avg_section_duration = sum(s['duration_seconds'] for s in section_times) / len(section_times)
        
        # METRIC 4: Keystroke Dynamics
        keystrokes = session['events']['keystroke_intervals']
        total_keystrokes = len(keystrokes)
        long_pauses = sum(1 for k in keystrokes if k['is_pause'])
        bursts = sum(1 for k in keystrokes if k['is_burst'])
        
        pause_frequency = long_pauses / total_keystrokes if total_keystrokes > 0 else 0
        burst_frequency = bursts / total_keystrokes if total_keystrokes > 0 else 0
        
        # METRIC 5: Help-Seeking
        help_requests = session['events']['help_requests']
        help_request_rate = len(help_requests) / session_duration_minutes
        
        avg_time_before_help = 0
        if help_requests:
            times = [h['time_before_help_seconds'] for h in help_requests if h['time_before_help_seconds'] > 0]
            avg_time_before_help = sum(times) / len(times) if times else 0
        
        # METRIC 6: Pauses
        pauses = session['events']['pauses']
        total_pause_time = sum(p['duration_seconds'] for p in pauses)
        
        return {
            # Session info
            'session_id': session_id,
            'user_id': session.get('user_id', ''),
            'group': session.get('group', ''),
            'duration_minutes': round(session_duration_minutes, 2),
            
            # OBJECTIVE METRICS
            'task_switch_rate_per_min': round(task_switch_rate, 2),
            'avg_time_per_section_sec': round(avg_time_per_section, 2),
            'total_tab_switches': len(tab_switches),
            
            'total_code_attempts': total_attempts,
            'error_rate': round(error_rate, 2),
            'total_errors': errors,
            'syntax_errors': syntax_errors,
            'avg_error_recovery_time_sec': round(avg_error_recovery_time, 2),
            
            'total_keystrokes': total_keystrokes,
            'pause_frequency': round(pause_frequency, 2),
            'burst_frequency': round(burst_frequency, 2),
            'long_pauses_count': long_pauses,
            
            'help_requests_per_min': round(help_request_rate, 2),
            'total_help_requests': len(help_requests),
            'avg_time_before_help_sec': round(avg_time_before_help, 2),
            
            'total_pause_time_sec': round(total_pause_time, 2),
            'pause_count': len(pauses),
            
            # SELF-REPORTED (separate!)
            'self_reports_count': len(session['self_reports']),
            'avg_attention_rating': round(sum(r['attention_rating'] for r in session['self_reports']) / len(session['self_reports']), 2) if session['self_reports'] else 0,
            'avg_stress_rating': round(sum(r['stress_rating'] for r in session['self_reports']) / len(session['self_reports']), 2) if session['self_reports'] else 0
        }

    # ========================================
    # EXPORT FOR STATISTICAL ANALYSIS
    # ========================================
    
    def export_session_csv(self, session_id: str) -> str:
        """
        Export session data as CSV for R/Python analysis
        
        Format: One row = one session
        Columns: All objective metrics + self-reported averages
        """
        if session_id not in self.sessions:
            return ""

        metrics = self.get_session_metrics(session_id)
        
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=metrics.keys())
        writer.writeheader()
        writer.writerow(metrics)
        
        return output.getvalue()
    
    def export_all_sessions_csv(self) -> str:
        """Export ALL sessions for comparison analysis"""
        if not self.sessions:
            return ""
        
        output = io.StringIO()
        writer = None
        
        for session_id in self.sessions:
            metrics = self.get_session_metrics(session_id)
            
            if writer is None:
                writer = csv.DictWriter(output, fieldnames=metrics.keys())
                writer.writeheader()
            
            writer.writerow(metrics)
        
        return output.getvalue()
    
    def save_session_jsonl(self, session_id: str):
        """Save complete session data as JSONL for detailed analysis"""
        if session_id not in self.sessions:
            return

        session = self.sessions[session_id]
        filepath = os.path.join(self.research_data_dir, f'{session_id}.jsonl')

        with open(filepath, 'w') as f:
            json.dump(session, f, indent=2)

        print(f"📊 Session saved: {filepath}")


# Global instance
metrics_tracker = ObjectiveBehavioralMetrics()


# ========================================
# API ENDPOINTS
# ========================================

async def handle_track_event(request):
    """POST /api/metrics/track - Track behavioral event"""
    session_id = request.cookies.get('session_id', f'session_{int(time.time() * 1000)}')

    try:
        data = await request.json()
        event_type = data.get('type')
        event_data = data.get('data', {})

        if event_type == 'tab_switch':
            metrics_tracker.track_tab_switch(session_id, event_data)
        elif event_type == 'code_execution':
            metrics_tracker.track_code_execution(session_id, event_data)
        elif event_type == 'keystroke':
            metrics_tracker.track_keystroke(session_id, event_data)
        elif event_type == 'help_request':
            metrics_tracker.track_help_request(session_id, event_data)
        elif event_type == 'click':
            metrics_tracker.track_click(session_id, event_data)
        elif event_type == 'scroll':
            metrics_tracker.track_scroll(session_id, event_data)

        return web.json_response({'success': True})

    except Exception as e:
        print(f"❌ Track error: {e}")
        return web.json_response({'error': str(e)}, status=500)


async def handle_self_report(request):
    """POST /api/metrics/self_report - Track self-reported state"""
    session_id = request.cookies.get('session_id', f'session_{int(time.time() * 1000)}')

    try:
        data = await request.json()
        metrics_tracker.track_self_report(session_id, data)

        return web.json_response({'success': True})

    except Exception as e:
        print(f"❌ Self-report error: {e}")
        return web.json_response({'error': str(e)}, status=500)


async def handle_get_metrics(request):
    """GET /api/metrics/session - Get session metrics summary"""
    session_id = request.cookies.get('session_id', 'default')

    try:
        metrics = metrics_tracker.get_session_metrics(session_id)
        return web.json_response(metrics)

    except Exception as e:
        print(f"❌ Get metrics error: {e}")
        return web.json_response({'error': str(e)}, status=500)


async def handle_export_csv(request):
    """GET /api/metrics/export/csv/{session_id} - Export session as CSV"""
    session_id = request.match_info.get('session_id')

    try:
        csv_data = metrics_tracker.export_session_csv(session_id)

        return web.Response(
            text=csv_data,
            content_type='text/csv',
            headers={
                'Content-Disposition': f'attachment; filename="{session_id}.csv"'
            }
        )

    except Exception as e:
        print(f"❌ Export error: {e}")
        return web.json_response({'error': str(e)}, status=500)


async def handle_export_all_csv(request):
    """GET /api/metrics/export/all - Export ALL sessions for analysis"""
    try:
        csv_data = metrics_tracker.export_all_sessions_csv()

        return web.Response(
            text=csv_data,
            content_type='text/csv',
            headers={
                'Content-Disposition': 'attachment; filename="all_sessions.csv"'
            }
        )

    except Exception as e:
        print(f"❌ Export all error: {e}")
        return web.json_response({'error': str(e)}, status=500)


def setup_metrics_routes(app):
    """Register all metrics routes"""
    app.router.add_post("/api/metrics/track", handle_track_event)
    app.router.add_post("/api/metrics/self_report", handle_self_report)
    app.router.add_get("/api/metrics/session", handle_get_metrics)
    app.router.add_get("/api/metrics/export/csv/{session_id}", handle_export_csv)
    app.router.add_get("/api/metrics/export/all", handle_export_all_csv)

    print("✅ Objective behavioral metrics routes registered!")
    print("   📊 Track events: /api/metrics/track")
    print("   🎯 Self-report: /api/metrics/self_report")
    print("   📈 Get metrics: /api/metrics/session")
    print("   💾 Export one: /api/metrics/export/csv/{session_id}")
    print("   💾 Export all: /api/metrics/export/all")


__all__ = ['setup_metrics_routes', 'metrics_tracker', 'ObjectiveBehavioralMetrics']
