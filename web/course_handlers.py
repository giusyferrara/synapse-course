"""
Synapse Course Handlers - COMPLETE PATCHED VERSION
Fixes:
1. Added GET endpoint for progress
2. Fixed structure format for new frontend
3. JAVA CODE RUNNER with sandboxed javac + java execution
4. Enhanced AI system prompt with C security, CERT rules, cross-module knowledge
5. Dual-language: Python stays Pyodide, Java uses real compiler
"""
from aiohttp import web
import json
import os
import subprocess
import tempfile
import shutil
import re as _re
from core.course_content import PythonCourseContent
from database.config import SessionLocal
from database.models import ChatConversation, ChatMessage
from database.models import CourseProgress
from datetime import datetime
from mcp_coordinator import MCPCoordinator
import asyncio
from core.tfl_transport import get_lines
from ai_response import response_text
from .ai_budget import budget, client_ip, Refused
from web.lang import detect_student_language
from web.session import current_user_id
from web import grader, sandbox

def _user_id(request):
    """The signed-in learner's id, or None. Set as a cookie at login."""
    return current_user_id(request)


def _over_budget(request):
    """None if this request may call a model, otherwise the refusal.

    Call it immediately before the model call. Work that fails for some other
    reason must not spend a learner's allowance.
    """
    try:
        budget.check(user_id=_user_id(request), ip=client_ip(request))
        return None
    except Refused as refusal:
        print("AI budget: refused (%s) %s" % (refusal.scope, refusal.message), flush=True)
        return refusal


RATE_LIMITED_MSG = "You've run code a lot in the last minute. Take a breath and try again in %d seconds."
BUSY_MSG = "Lots of people are running code right now. Please try again in a few seconds."


async def _run_learner_code(request, code):
    """The only way the handlers run a learner's code: the per-learner rate
    limit first, then a server-wide sandbox slot, then the container.

    Returns (result, None) or (None, (http_status, message, retry_after)).
    The rate-limit key comes from the signed session, or for a visitor without
    an account from the address nginx writes; nothing in the request body can
    change it.
    """
    uid = _user_id(request)
    key = "u:%s" % uid if uid else "ip:%s" % client_ip(request)
    try:
        sandbox.limiter.check(key)
    except sandbox.RateLimited as r:
        return None, (429, RATE_LIMITED_MSG % r.retry_after, r.retry_after)
    try:
        return await sandbox.run_python(code), None
    except sandbox.Busy:
        return None, (503, BUSY_MSG, 5)


def _record_progress(user_id, course_id, exercise_id, passed):
    """Write one graded attempt into user_progress, the table the dashboard
    reads. Called only by handle_evaluate_code, after the SERVER has graded the
    code: the ids come from the trusted catalogue, and passed is the server's
    own verdict, never something the browser said. completed only ever turns
    true on a pass; attempts count every graded try.

    Best-effort: a database hiccup must never turn a graded answer into an
    error, so this swallows everything and never raises into the grading path.
    """
    if not user_id:
        return
    course = str(course_id)[:100]          # column is varchar(100)
    exercise_id = str(exercise_id)[:100]
    try:
        from sqlalchemy import text
        with SessionLocal() as db:
            db.execute(text("""
                INSERT INTO user_progress
                    (user_id, course_id, topic_id, exercise_id, completed, score,
                     attempts, completed_at, created_at)
                VALUES
                    (:uid, :course, :course, :ex, :done, :score, 1, :now, :now)
                ON CONFLICT (user_id, course_id, topic_id, exercise_id)
                DO UPDATE SET
                    completed = user_progress.completed OR EXCLUDED.completed,
                    score = GREATEST(user_progress.score, EXCLUDED.score),
                    attempts = user_progress.attempts + 1,
                    completed_at = CASE WHEN EXCLUDED.completed
                                        THEN EXCLUDED.completed_at
                                        ELSE user_progress.completed_at END
            """), {
                "uid": user_id, "course": course, "ex": exercise_id,
                "done": bool(passed), "score": 100 if passed else 0,
                "now": datetime.utcnow(),
            })
            db.commit()
    except Exception as e:
        # Once, quietly. A dashboard that misses one row is fine; a 500 on a
        # correct answer is not.
        print("progress not recorded (%s)" % e, flush=True)


# Shared, in-process cache for the double-click dictionary. A word means the
# same thing to everyone, so the first lookup pays and the rest are free.
_define_cache = {}



async def handle_generate_exercise(request):
    """A new practice exercise in the spirit of a lesson's worked example.

    The "Generate a custom exercise" button in course.html called this route
    for months while it did not exist, so the button always failed. One model
    call, small output, counted against the same AI budget as the chat.
    Returns {description, starter_code, hint}.
    """
    try:
        data = await request.json()
    except Exception:
        data = {}
    if not isinstance(data, dict):
        data = {}
    title = str(data.get('example_title') or '')[:120]
    code = str(data.get('example_code') or '')[:2000]
    difficulty = str(data.get('difficulty') or 'easy')[:20]
    challenge = str(data.get('ai_challenge') or '')[:400]
    if not code and not title:
        return web.json_response({'error': 'nothing to base the exercise on'}, status=400)

    refusal = _over_budget(request)
    if refusal:
        return web.json_response({'description': refusal.message, 'limited': True}, status=429)

    tutor = request.app.get("tutor")
    if not tutor or not getattr(tutor, "ai_router", None) or not tutor.ai_router._anthropic:
        return web.json_response({'error': 'tutor not available'}, status=503)

    prompt = (
        "Write ONE small Python practice exercise for a beginner, about 12 years old, "
        "in the spirit of this worked example. Everyday words, short sentences, real "
        "values. Do not include the solution.\n\n"
        f"Example title: {title}\nDifficulty: {difficulty}\n"
        f"Extra idea: {challenge}\n\nExample code:\n{code}\n\n"
        "Reply with JSON only, no markdown fence, exactly these keys: "
        '{"description": "what to do, 2-4 short sentences", '
        '"starter_code": "a few lines of Python with # TODO comments where the student writes", '
        '"hint": "one short clue, not the answer"}'
    )
    try:
        resp = await asyncio.to_thread(tutor.ai_router._anthropic.messages.create,
            model="claude-sonnet-5",
            max_tokens=600,
            messages=[{"role": "user", "content": prompt}],
        )
        raw = (response_text(resp) or "").strip()
        m = _re.search(r"\{.*\}", raw, _re.S)
        out = json.loads(m.group(0)) if m else {}
        result = {
            'description': str(out.get('description') or '')[:800],
            'starter_code': str(out.get('starter_code') or '')[:2000],
            'hint': str(out.get('hint') or '')[:300],
        }
        if not result['description']:
            raise ValueError('empty exercise')
        return web.json_response(result)
    except Exception as e:
        print(f"generate_exercise failed: {e}", flush=True)
        return web.json_response({'error': 'could not make an exercise right now'}, status=502)


async def handle_define(request):
    """One short definition for a word the built-in dictionary does not have.

    Kept cheap on purpose: capped output, shared cache, and it counts against
    the same AI budget as the chat so it cannot be run up. Returns plain text
    the tooltip drops straight in.
    """
    try:
        data = await request.json()
    except Exception:
        data = {}
    word = "".join(c for c in str(data.get("word", "")).strip().lower() if c.isalpha())[:40]
    if not word or len(word) < 2:
        return web.json_response({"definition": ""})
    if word in _define_cache:
        return web.json_response({"definition": _define_cache[word], "cached": True})

    refusal = _over_budget(request)
    if refusal:
        return web.json_response({
            "definition": "Word look-ups have hit today's limit. The built-in "
                          "terms still work, and the tutor can explain it in the chat.",
            "limited": True,
        })

    tutor = request.app.get("tutor")
    if not tutor or not getattr(tutor, "ai_router", None) or not tutor.ai_router._anthropic:
        return web.json_response({"definition": ""})
    try:
        resp = await asyncio.to_thread(tutor.ai_router._anthropic.messages.create,
            model="claude-sonnet-5",
            max_tokens=120,
            system=("You define a single programming, computing or cybersecurity "
                    "term for a beginner. Reply with one or two short, plain "
                    "sentences. No markdown, no lists, no preamble, no restating "
                    "the word first. If it is an everyday word, give its ordinary "
                    "meaning briefly."),
            messages=[{"role": "user", "content": "Define: " + word}],
        )
        text = (response_text(resp) or "").strip()
    except Exception as e:
        print("define error: %s" % e, flush=True)
        return web.json_response({"definition": ""})
    if text:
        _define_cache[word] = text
    return web.json_response({"definition": text})


# Initialize course content and MCP
course_content = PythonCourseContent()
mcp_coordinator = None

async def init_mcp_coordinator():
    """Initialize MCP Coordinator (4 AI clients)"""
    global mcp_coordinator
    try:
        mcp_coordinator = MCPCoordinator()
        course_content.set_mcp_coordinator(mcp_coordinator)
        print("✅ MCP Coordinator initialized for course generation!")
        return True
    except Exception as e:
        print(f"⚠️  MCP Coordinator initialization failed: {e}")
        print("    Course will use basic content without AI generation")
        return False


async def handle_course_page(request):
    """Serve the main course page"""
    try:
        with open("templates/course.html", "r", encoding="utf-8") as f:
            return web.Response(text=f.read(), content_type="text/html")
    except FileNotFoundError:
        return web.Response(
            text="<h1>Error: course.html not found</h1>",
            status=500,
            content_type="text/html"
        )


async def handle_get_structure(request):
    """Get complete course structure - FIXED FORMAT"""
    try:
        structure_dict = course_content.get_structure()

        # CONVERT dict format to array format for new frontend
        levels = []

        level_icons = {
            'beginner': '🌱',
            'intermediate': '🚀',
            'advanced': '🔬',
            'expert': '🏆'
        }

        for level_id, level_data in structure_dict.items():
            levels.append({
                'id': level_id,
                'name': level_data.get('title', level_id.title()),
                'description': level_data.get('description', ''),
                'icon': level_icons.get(level_id, '📚'),
                'topics': level_data.get('topics', [])
            })

        # Get user progress
        student_id = request.query.get('student_id', 'web_user')
        progress = await get_user_progress(student_id)

        return web.json_response({
            'success': True,
            'levels': levels,  # Changed to match frontend expectation!
            'progress': progress,
            'ai_enabled': mcp_coordinator is not None
        })

    except Exception as e:
        print(f"❌ Error in get_structure: {e}")
        import traceback
        traceback.print_exc()
        return web.json_response({
            'success': False,
            'error': str(e)
        }, status=500)


async def handle_get_topic(request):
    """Get specific topic content with AI generation"""
    try:
        topic_id = request.match_info['topic_id']
        topic = course_content.get_topic(topic_id)

        if not topic:
            return web.json_response({
                'success': False,
                'error': 'Topic not found'
            }, status=404)

        # Check if we should generate AI content
        if topic.get('requires_ai_generation') and mcp_coordinator:
            student_type = request.query.get('student_type', 'neurotypical')
            student_profile = {'type': student_type}

            print(f"🎯 Generating AI lesson for: {topic['name']}")

            # Generate complete lesson with 4 AIs + workflow!
            ai_content = await course_content.get_ai_generated_content(
                topic_id,
                student_profile
            )

            if ai_content.get('success'):
                # Merge AI content into topic
                topic['ai_content'] = ai_content
                topic['content'] = {
                    'theory': ai_content.get('theory', {}),
                    'slides': ai_content.get('slides', []),
                    'flowcharts': ai_content.get('flowcharts', []),
                    'workflow': ai_content.get('workflow', []),  # NEW!
                    'images': ai_content.get('images', []),
                    'exercises': ai_content.get('exercises', []),
                    'examples': ai_content.get('exercises', [])[:3]
                }
                topic['generation_time'] = ai_content.get('generation_time', 0)
                topic['models_used'] = ai_content.get('metadata', {}).get('models_used', {})

        return web.json_response({
            'success': True,
            'topic': topic
        })

    except Exception as e:
        print(f"❌ Error getting topic: {e}")
        import traceback
        traceback.print_exc()
        return web.json_response({
            'success': False,
            'error': str(e)
        }, status=500)


async def handle_generate_lesson(request):
    """Generate AI lesson on demand"""
    try:
        data = await request.json()
        topic_id = data.get('topic_id')
        student_profile = data.get('student_profile', {'type': 'neurotypical'})

        if not mcp_coordinator:
            return web.json_response({
                'success': False,
                'error': 'AI generation not available'
            }, status=503)

        topic = course_content.get_topic(topic_id)
        if not topic:
            return web.json_response({
                'success': False,
                'error': 'Topic not found'
            }, status=404)

        refusal = _over_budget(request)
        if refusal:
            return web.json_response({
                'success': False,
                'error': refusal.message
            }, status=429)

        print(f"🎨 Generating lesson: {topic['name']} for {student_profile.get('type')}")

        lesson = await course_content.get_ai_generated_content(
            topic_id,
            student_profile
        )

        return web.json_response({
            'success': True,
            'lesson': lesson
        })

    except Exception as e:
        print(f"❌ Lesson generation error: {e}")
        return web.json_response({
            'success': False,
            'error': str(e)
        }, status=500)


# NEW: GET endpoint for progress
async def handle_get_progress(request):
    """Get user progress - NEW GET ENDPOINT"""
    try:
        student_id = request.query.get('student_id', 'web_user')
        progress = await get_user_progress(student_id)

        return web.json_response({
            'success': True,
            'progress': progress
        })

    except Exception as e:
        print(f"❌ Error getting progress: {e}")
        return web.json_response({
            'success': False,
            'progress': {},
            'error': str(e)
        })


async def handle_update_progress(request):
    """Update user progress for a topic"""
    try:
        data = await request.json()
        student_id = data.get('student_id', 'web_user')
        topic_id = data.get('topic_id')
        completed = data.get('completed', False)

        db = SessionLocal()
        try:
            progress = db.query(CourseProgress).filter_by(
                student_id=student_id,
                topic_id=topic_id
            ).first()

            if progress:
                progress.completed = completed
                progress.updated_at = datetime.utcnow()
            else:
                progress = CourseProgress(
                    student_id=student_id,
                    topic_id=topic_id,
                    completed=completed
                )
                db.add(progress)

            db.commit()
            return web.json_response({
                'success': True,
                'message': 'Progress updated'
            })
        finally:
            db.close()

    except Exception as e:
        print(f"❌ Error updating progress: {e}")
        return web.json_response({
            'success': False,
            'error': str(e)
        }, status=500)


# ============================================================
# SECURE DUAL-LANGUAGE CODE RUNNER (Java + Python)
# Security: code scanning, 10s timeout, temp dir, env isolation
# ============================================================

JAVA_BLOCKED_PATTERNS = [
    # System/OS access
    'Runtime.getRuntime', 'ProcessBuilder', 'System.exit',
    # File system
    'java.io.File', 'java.nio.file', 'FileInputStream', 'FileOutputStream',
    'FileReader', 'FileWriter', 'RandomAccessFile', 'new File(',
    'Files.read', 'Files.write', 'Files.delete', 'Files.list', 'Files.walk',
    # Network
    'java.net.', 'Socket', 'ServerSocket',
    'HttpURLConnection', 'URLConnection', 'DatagramSocket',
    # Reflection / classloading
    'Class.forName', 'ClassLoader', 'setAccessible', 'java.lang.reflect',
    # Native / unsafe
    'System.load', 'System.loadLibrary', 'sun.misc.Unsafe',
    # Deserialization
    'ObjectInputStream', 'readObject',
    # Process / shell
    'Runtime.exec', '/bin/', '/usr/', '/etc/', 'cmd.exe', 'powershell',
]

JAVA_BLOCKED_IMPORTS = [
    'java.io.File', 'java.nio.file', 'java.net',
    'java.lang.reflect', 'java.lang.Runtime', 'java.lang.ProcessBuilder',
    'javax.script', 'sun.misc', 'java.rmi', 'javax.naming',
]


async def handle_run_code(request):
    """Execute user code safely — routes Java or Python based on course"""
    try:
        data = await request.json()
        code = data.get('code', '')
        topic_id = data.get('topic_id', '') or ''

        # Detect language from topic_id
        # All Java Security course topics run as Java
        java_topics = [
            'java_', 'owasp_', 'security_', 'memory_safety',
            'exceptions_', 'csrf_', 'auth_', 'authentication_',
            'sql_', 'xss_', 'path_traversal', 'static_analysis',
            'webapp_', 'cw1_'
        ]
        is_java = any(topic_id.startswith(p) for p in java_topics)
        # If no topic_id but code looks like Java, run as Java
        if not is_java and not topic_id:
            java_patterns = ['public class', 'public static void main', 'System.out.print', 'String[]']
            is_java = any(p in code for p in java_patterns)

        if is_java:
            # Off since 8 November 2026. javac/java ran on the server itself,
            # held back only by a list of forbidden words, and Java's \uXXXX
            # escapes walk straight past any word list. It comes back when it
            # runs inside a Docker sandbox like Python does.
            return web.json_response({
                'success': False,
                'error': True,
                'output': ('Running Java is switched off for a little while, '
                           'while we move it somewhere safer. You can still '
                           'read the lesson and ask the tutor about your code.'),
            })
        else:
            # Python — use existing tutor (Pyodide-based)
            tutor = request.app.get('tutor')
            if not tutor:
                return web.json_response({
                    'success': False,
                    'error': 'Tutor not available'
                }, status=503)

            # In the Docker sandbox (web/sandbox.py), with the output capped and
            # the container itself killed on a timeout.
            r, refused = await _run_learner_code(request, code)
            if refused:
                status, msg, retry = refused
                return web.json_response({"success": False, "error": True, "output": msg},
                                         status=status, headers={"Retry-After": str(retry)})
            if r["timed_out"]:
                return web.json_response({"success": False, "output": "Timed out after %ds." % sandbox.RUN_TIMEOUT, "error": True})
            if r["too_much_output"]:
                return web.json_response({"success": False, "output": (r["stdout"][-2000:] + "\n\nStopped: your program printed too much (more than %d KB)." % (sandbox.MAX_OUTPUT // 1024)), "error": True})
            if r["ok"]:
                return web.json_response({"success": True, "output": r["stdout"] or "(No output)"})
            return web.json_response({"success": False, "output": r["stderr"] or r["stdout"] or "Error", "error": True})

    except Exception as e:
        return web.json_response({
            'success': False,
            'error': str(e)
        }, status=500)


async def _run_java_sandboxed(code, topic_id):
    """Compile and run Java code in a sandboxed environment"""

    # ─── LAYER 1: Code Scanning ───
    for pattern in JAVA_BLOCKED_PATTERNS:
        if pattern.lower() in code.lower():
            return web.json_response({
                'success': False,
                'output': (
                    f'SECURITY BLOCK\n\n'
                    f'Blocked pattern: {pattern}\n\n'
                    f'For security, the sandbox blocks:\n'
                    f'  - File system access (File, Files, FileReader)\n'
                    f'  - Network access (Socket, URL, HttpURLConnection)\n'
                    f'  - System commands (Runtime.exec, ProcessBuilder)\n'
                    f'  - Reflection (Class.forName, setAccessible)\n\n'
                    f'Allowed: java.util.*, java.lang.*, java.text.*, java.math.*, java.time.*\n\n'
                    f'Click "Get AI Hint" to learn about this security concept!'
                ),
                'result': f'SECURITY BLOCK: {pattern}'
            })

    for blocked in JAVA_BLOCKED_IMPORTS:
        if blocked.lower() in code.lower():
            return web.json_response({
                'success': False,
                'output': (
                    f'SECURITY BLOCK\n\n'
                    f'Import not allowed: {blocked}\n\n'
                    f'Allowed: java.util.*, java.lang.*, java.text.*, java.math.*, java.time.*\n\n'
                    f'Use the AI Tutor chat to learn about this import safely!'
                ),
                'result': f'SECURITY BLOCK: {blocked}'
            })

    # ─── Extract class name from code ───
    class_match = _re.search(r'public\s+class\s+(\w+)', code)
    if not class_match:
        return web.json_response({
            'success': False,
            'output': (
                'COMPILATION ERROR\n\n'
                'Could not find a public class declaration.\n\n'
                'Every Java program needs:\n'
                '  public class ClassName {\n'
                '      public static void main(String[] args) {\n'
                '          // your code here\n'
                '      }\n'
                '  }\n\n'
                'The class name must match the filename.'
            ),
            'result': 'No public class found'
        })

    class_name = class_match.group(1)

    # ─── LAYER 3: Temp Directory (isolated) ───
    temp_dir = tempfile.mkdtemp(prefix='synapse_java_')

    try:
        # Write the Java source file
        java_file = os.path.join(temp_dir, f'{class_name}.java')
        with open(java_file, 'w', encoding='utf-8') as f:
            f.write(code)

        # ─── COMPILE (10s timeout) ───
        try:
            compile_result = subprocess.run(
                ['javac', java_file],
                capture_output=True,
                text=True,
                timeout=10,
                cwd=temp_dir,
            )
        except subprocess.TimeoutExpired:
            return web.json_response({
                'success': False,
                'output': (
                    'COMPILATION TIMEOUT (10 seconds)\n\n'
                    'Compilation took too long.\n'
                    'Check for: missing semicolons, unmatched braces,\n'
                    'or incorrect class/method names.'
                ),
                'result': 'Compilation timeout'
            })

        if compile_result.returncode != 0:
            # Make error paths friendlier (hide temp dir path)
            errors = compile_result.stderr.replace(java_file, f'{class_name}.java')
            errors = errors.replace(temp_dir + '/', '')
            return web.json_response({
                'success': False,
                'output': (
                    f'COMPILATION ERROR\n\n'
                    f'{errors}\n\n'
                    f'Common fixes:\n'
                    f'  Missing semicolon -> add ; at end of statement\n'
                    f'  Cannot find symbol -> check spelling and imports\n'
                    f'  Incompatible types -> check variable types match\n\n'
                    f'Click "Get AI Hint" for a detailed explanation!'
                ),
                'result': f'Compilation error:\n{errors}'
            })

        # ─── RUN (10s timeout, 64MB memory, restricted env) ───
        try:
            run_result = subprocess.run(
                ['java', '-Xmx64m', '-Xss512k', class_name],
                capture_output=True,
                text=True,
                timeout=10,
                cwd=temp_dir,
                env={
                    'PATH': '/usr/bin:/usr/lib/jvm/java-21-openjdk-amd64/bin',
                    'HOME': temp_dir,
                    'JAVA_HOME': '/usr/lib/jvm/java-21-openjdk-amd64',
                },
            )
        except subprocess.TimeoutExpired:
            return web.json_response({
                'success': False,
                'output': (
                    'EXECUTION TIMEOUT (10 seconds)\n\n'
                    'Your program took too long. Common causes:\n'
                    '  - Infinite loop (while/for that never ends)\n'
                    '  - Waiting for input (Scanner not supported in sandbox)\n'
                    '  - Very large computation\n\n'
                    'Check your loop conditions!'
                ),
                'result': 'Execution timeout'
            })

        # ─── Build output ───
        output_parts = []

        if run_result.stdout:
            stdout = run_result.stdout
            # Truncate long output (10KB max)
            if len(stdout) > 10000:
                stdout = stdout[:10000] + '\n\n... Output truncated (10KB limit)'
            output_parts.append(stdout)

        if run_result.stderr:
            stderr = run_result.stderr[:5000]
            if len(run_result.stderr) > 5000:
                stderr += '\n\n... Error output truncated'
            output_parts.append(f'RUNTIME ERROR:\n{stderr}')

        if run_result.returncode != 0 and not run_result.stderr:
            output_parts.append(f'Program exited with code {run_result.returncode}')

        if not output_parts:
            output_parts.append(
                'Program compiled and ran successfully!\n'
                '(No output produced — add System.out.println() to see results)'
            )

        final_output = '\n\n'.join(output_parts)

        return web.json_response({
            'success': run_result.returncode == 0,
            'output': final_output,
            'result': final_output
        })

    finally:
        # ─── CLEANUP: Always remove temp directory ───
        try:
            shutil.rmtree(temp_dir, ignore_errors=True)
        except Exception:
            pass


async def handle_get_hint(request):
    """Get AI hint for current exercise using Claude"""
    try:
        data = await request.json()
        topic_id = data.get('topic_id')
        code = data.get('code', '')
        exercise_description = data.get('exercise_description', '')

        if not mcp_coordinator:
            return web.json_response({
                'success': True,
                'hint': 'Try breaking the problem into smaller steps. You can do it!'
            })

        refusal = _over_budget(request)
        if refusal:
            # The hint slot is the only place a learner would see this, so the
            # refusal goes where the hint would have gone.
            return web.json_response({'success': True, 'hint': refusal.message})

        # Pick the language from the topic (Java for the Java-security topics, else Python)
        java_prefixes = ('java_', 'owasp_', 'security_', 'memory_safety')
        language = 'Java' if str(topic_id or '').startswith(java_prefixes) else 'Python'

        hint = await mcp_coordinator.claude.generate_hint(
            exercise_description=exercise_description,
            student_code=code,
            hint_level=data.get('hint_level', 1),
            language=language
        )

        return web.json_response({
            'success': True,
            'hint': hint
        })

    except Exception as e:
        return web.json_response({
            'success': True,
            'hint': 'Keep practicing! You\'re on the right track.'
        })


MAX_CODE = 50_000   # characters; a real exercise solution is a few hundred


def _verdict(status, feedback, **extra):
    """One response shape for every outcome. status is one of:
    passed, failed, not_checkable, sign_in, bad_request, unavailable,
    rate_limited, busy."""
    body = {'success': status in ('passed', 'failed', 'not_checkable'),
            'status': status, 'passed': status == 'passed',
            'correct': status == 'passed', 'feedback': feedback}
    body.update(extra)
    return body


async def handle_evaluate_code(request):
    """Grade an exercise, deterministically, on the server (E1).

    The browser sends only {course_id, exercise_id, code}. The exercise, its
    expected output and whether it can be checked at all come from the trusted
    catalogue (web/grader.py); the code runs in the sandbox (web/sandbox.py);
    the server compares. No AI is called here, so grading works the same with
    every model switched off. Anything else in the request (an "expected
    output", a "user output", a verdict) is ignored.
    """
    user_id = _user_id(request)
    if not user_id:
        return web.json_response(_verdict('sign_in', 'Sign in to have your solution checked and your progress saved.'), status=401)
    try:
        data = await request.json()
        if not isinstance(data, dict):
            raise ValueError
    except Exception:
        return web.json_response(_verdict('bad_request', 'Bad request.'), status=400)

    course_id = data.get('course_id')
    exercise_id = data.get('exercise_id')
    code = data.get('code')
    if not isinstance(code, str) or not code.strip():
        return web.json_response(_verdict('bad_request', 'Write some code first, then check it.'), status=400)
    if len(code) > MAX_CODE:
        return web.json_response(_verdict('bad_request', 'That code is too long to check.'), status=400)

    exercise = grader.find_exercise(course_id, exercise_id)
    if exercise is None:
        return web.json_response(_verdict(
            'bad_request', 'Choose an exercise from the course list first: only those have a fixed answer to check against.'), status=404)

    reasons = grader.unchecked_reasons(course_id, exercise)
    if reasons == ['not_auto']:
        # Nothing runs, nothing is marked as done: the exercise itself says why.
        why = grader.not_auto_why(exercise) or grader.REASONS['not_auto']
        return web.json_response(_verdict(
            'not_checkable',
            "This exercise isn't checked automatically: it needs a different kind of assessment. %s "
            "Run your code and look at the result yourself, or ask the tutor what to improve. "
            "It won't be marked as done automatically." % why,
            reasons=reasons))
    if reasons:
        why = '; '.join(grader.REASONS[r] for r in reasons)
        return web.json_response(_verdict(
            'not_checkable',
            "This exercise can't be checked automatically yet (%s). Compare your output with the expected one yourself, or ask the tutor." % why,
            reasons=reasons))

    try:
        r, refused = await _run_learner_code(request, code)
    except Exception as e:
        print("evaluate: sandbox unavailable (%s)" % e, flush=True)
        return web.json_response(_verdict('unavailable', 'Checking is not available right now. Please try again in a minute.'), status=503)
    if refused:
        status, msg, retry = refused
        return web.json_response(_verdict('rate_limited' if status == 429 else 'busy', msg),
                                 status=status, headers={"Retry-After": str(retry)})

    if r['timed_out']:
        passed, feedback = False, "Your program was still running after %d seconds, so it was stopped. Look for a loop that never ends." % sandbox.RUN_TIMEOUT
    elif r['too_much_output']:
        passed, feedback = False, "Your program printed far more than the exercise expects, so it was stopped."
    elif not r['ok']:
        passed, feedback = False, grader.error_feedback(r['stderr'] or r['stdout'])
    else:
        passed, feedback = grader.compare(exercise.get('expected_output', ''), r['stdout'])

    _record_progress(user_id, course_id, exercise_id, passed)
    return web.json_response(_verdict('passed' if passed else 'failed', feedback))


async def get_user_progress(student_id):
    """Helper: Get user progress from database"""
    try:
        db = SessionLocal()
        try:
            records = db.query(CourseProgress).filter_by(
                student_id=student_id
            ).all()

            progress = {}
            for record in records:
                progress[record.topic_id] = {
                    'completed': record.completed,
                    'updated_at': record.updated_at.isoformat() if record.updated_at else None
                }
            return progress
        finally:
            db.close()
    except Exception as e:
        print(f"Error getting progress: {e}")
        return {}

# ============================================================
# NEW SECTION — TfL (London Transport) integration
# ============================================================

async def handle_tfl_lines(request):
    """Get all London Underground lines"""
    try:
        lines = get_lines()
        return web.json_response({"success": True, "lines": lines})
    except Exception as e:
        return web.json_response({"success": False, "error": str(e)}, status=500)


async def handle_user_profile(request):
    """Return user profile from participant code"""
    code = request.query.get("code", "")
    if code:
        try:
            from database.models import SessionLocal, ResearchParticipant
            db = SessionLocal()
            p = db.query(ResearchParticipant).filter_by(participant_code=code).first()
            if p and p.nickname:
                db.close()
                return web.json_response({"name": p.nickname, "username": p.nickname, "first_name": p.nickname})
            db.close()
        except Exception as e:
            print(f"Profile lookup error: {e}")
    return web.json_response({"name": "", "username": "", "first_name": ""})



async def clear_chat(request):
    """End this learner's conversation, so clearing it actually clears it.

    The button used to empty the page and nothing else: the history was still
    in the browser and still went out with the next message, and the whole
    conversation came back on reload. So the tutor told the student the truth,
    that it still remembered, which reads as a threat rather than a feature.

    Nothing is deleted here. The conversation is marked closed, the next
    message starts a new one, and the old one stays in the database for the
    student's own history and for the research consent already given.
    """
    try:
        data = await request.json()
    except Exception:
        data = {}
    course_id = data.get('course_id') or 'general'
    user_id = _user_id(request)

    db = SessionLocal()
    try:
        rows = db.query(ChatConversation).filter_by(
            topic=course_id, is_active=True, user_id=user_id
        ).all()
        for conv in rows:
            conv.is_active = False
        db.commit()
        return web.json_response({'success': True, 'closed': len(rows)})
    except Exception as e:
        print(f"Clear chat error: {e}")
        return web.json_response({'success': False}, status=500)
    finally:
        try:
            db.close()
        except Exception:
            pass


async def get_chat_history(request):
    """Load chat history for a user/course"""
    try:
        course_id = request.rel_url.query.get('course_id', 'general')
        user_id = current_user_id(request)
        # Without a session there is nobody to load a history for. This used
        # to drop the user filter instead, and return the newest conversation
        # of anybody at all on that course.
        if not user_id:
            return web.json_response({'messages': []})
        db = SessionLocal()
        try:
            conv = db.query(ChatConversation).filter_by(
                topic=course_id, is_active=True, user_id=user_id
            ).order_by(ChatConversation.id.desc()).first()
            if not conv:
                return web.json_response({'messages': []})
            msgs = db.query(ChatMessage).filter_by(
                conversation_id=conv.id
            ).order_by(ChatMessage.timestamp.asc()).all()
            history = [{'role': m.role, 'content': m.message, 'timestamp': str(m.timestamp)} for m in msgs[-20:]]
            return web.json_response({'messages': history})
        finally:
            db.close()
    except Exception as e:
        print(f'Chat history error: {e}')
        return web.json_response({'messages': []})

def setup_course_routes(app):
    """Setup all course routes + initialize MCP"""

    # Initialize MCP Coordinator
    asyncio.create_task(init_mcp_coordinator())

    # Route registration
    app.router.add_get("/course", handle_course_page)
    app.router.add_get("/java-security", handle_java_security_page)
    # 19 Nov 2026 (Phase 0, package 0.1): /api/course/structure, /content/{id} and
    # /topic/{id} are no longer registered. No page used them, and content/topic
    # could make the AI generate a lesson for anyone, outside the spending cap.
    # handle_get_structure and handle_get_topic are kept: one line each re-enables them.
    app.router.add_get("/api/tfl/lines", handle_tfl_lines)


    # FIXED: Added GET for progress!
    app.router.add_get("/api/course/progress", handle_get_progress)  # ← NEW!
    app.router.add_post("/api/course/progress", handle_update_progress)

    app.router.add_post("/api/course/run_code", handle_run_code)
    app.router.add_post("/api/course/get_hint", handle_get_hint)
    app.router.add_post("/api/course/chat", handle_course_chat)
    app.router.add_get("/api/course/chat/history", get_chat_history)
    app.router.add_post("/api/course/chat/clear", clear_chat)
    app.router.add_post("/api/course/generate_lesson", handle_generate_lesson)
    app.router.add_post("/api/course/evaluate_code", handle_evaluate_code)
    app.router.add_post("/api/course/generate_exercise", handle_generate_exercise)
    app.router.add_get("/api/user/profile", handle_user_profile)
    app.router.add_post("/api/define", handle_define)

    print("✅ Synapse Course routes registered!")
    print("   🤖 AI content generation: ENABLED")
    print("   ☕ Java compiler: ENABLED (sandboxed)")
    print("   🐍 Python executor: ENABLED (Pyodide)")
    print("   🚇 London Transport project: READY")
    print("   ♿ Neurodivergent support: ACTIVE")
    print("   🔧 Progress GET endpoint: FIXED")


# ============================================================
# COURSE-AWARE AI CHAT — Enhanced with C Security + Cross-Module
# ============================================================
from pathlib import Path

async def handle_course_chat(request):
    """AI chat that actually knows the course content + cross-module security knowledge"""
    try:
        data = await request.json()
        # Lengths are capped here because the tutor is open to anybody on /try,
        # and both the message and the history arrive from the browser: an
        # uncapped history is a way to make every question cost a whole book.
        # 4,000 characters is several screens of a real question with code.
        message = str(data.get('message', '') or '')[:4000]
        course_id = str(data.get('course_id', '') or '')
        if not _re.fullmatch(r'[a-z0-9_]{1,64}', course_id):
            course_id = ''   # it becomes part of a file path below
        code_context = data.get('code_context', '')
        history = data.get('history', [])
        if not isinstance(history, list):
            history = []
        history = [
            {"role": m.get("role"), "content": str(m.get("content", ""))[:4000]}
            for m in history[-18:]
            if isinstance(m, dict) and m.get("role") in ("user", "assistant")
        ]
        user_id = current_user_id(request)
        output_context = data.get('output_context', '')
        user_state = data.get('user_state', {})

        if not message:
            return web.json_response({'response': 'Please type a message.'})

        # Load the course JSON for context
        course_json_path = Path(__file__).parent.parent / 'static' / 'course_content' / f'{course_id}.json'
        course_context = ""
        if course_json_path.exists():
            try:
                with open(course_json_path, 'r', encoding='utf-8') as f:
                    course_data = json.load(f)

                # Extract key teaching content (keep it focused to fit in context)
                title = course_data.get('title', course_id)
                description = course_data.get('description', '')
                lessons = course_data.get('lessons', [])

                # Build a teaching summary from the JSON
                lesson_summaries = []
                for lesson in lessons:
                    lesson_title = lesson.get('title', '')
                    objectives = lesson.get('learning_objectives_explicit', [])
                    theory = lesson.get('theory', {})
                    concepts = theory.get('key_concepts', [])
                    examples = lesson.get('complete_examples', [])
                    exercises = lesson.get('practice_exercises', [])

                    concept_texts = []
                    for c in concepts:
                        concept_texts.append(f"- {c.get('concept', '')}: {c.get('one_sentence_summary', '')}")

                    example_texts = []
                    for ex in examples:
                        example_texts.append(f"- {ex.get('title', '')}: {ex.get('description', '')}")
                        if ex.get('code'):
                            example_texts.append(f"  Code:\n{ex['code'][:500]}")
                        if ex.get('ai_explanation'):
                            example_texts.append(f"  Explanation: {ex['ai_explanation'][:300]}")

                    exercise_texts = []
                    for ex in exercises:
                        exercise_texts.append(f"- {ex.get('title', '')} ({ex.get('difficulty', '')}): {ex.get('description', '')}")
                        if ex.get('starter_code'):
                            exercise_texts.append(f"  Starter code:\n{ex['starter_code'][:400]}")
                        if ex.get('solution'):
                            exercise_texts.append(f"  Solution:\n{ex['solution'][:400]}")
                        hints = ex.get('hints', [])
                        for h in hints:
                            exercise_texts.append(f"  Hint {h.get('level', '')}: {h.get('message', '')[:200]}")

                    lesson_summaries.append(f"""
LESSON: {lesson_title}
Objectives: {'; '.join(objectives)}
Concepts:
{chr(10).join(concept_texts)}
Examples:
{chr(10).join(example_texts)}
Exercises:
{chr(10).join(exercise_texts)}
""")

                # ND config
                nd_config = course_data.get('neurodivergent_design_principles', {})
                ai_tutor = course_data.get('ai_tutor_config', {})
                nd_rules = ai_tutor.get('neurodivergent_mode', {}).get('communication_rules', [])
                ref_cards = ai_tutor.get('reference_cards', {}).get('cards', [])

                ref_card_text = ""
                for card in ref_cards:
                    ref_card_text += f"\n{card.get('title', '')}:\n{card.get('content', '')}\n"

                course_context = f"""
COURSE: {title}
{description}

NEURODIVERGENT COMMUNICATION RULES:
{chr(10).join(f'- {r}' for r in nd_rules)}

REFERENCE CARDS (share these when relevant):
{ref_card_text}

{''.join(lesson_summaries)}
"""
            except Exception as e:
                print(f"⚠️ Could not load course JSON: {e}")
                course_context = f"Course: {course_id} (content could not be loaded)"
        else:
            course_context = f"Course: {course_id} (no JSON file found)"

        # Build the system prompt with course context
        system_prompt = f"""You are the Synapse AI Tutor — a friendly, knowledgeable expert in programming, cybersecurity, and computer science. You help neurodivergent learners (ADHD, dyslexia) succeed.

YOUR PERSONALITY:
- You are warm, patient, and encouraging — like a brilliant friend who loves teaching.
- You answer ANY question about programming, security, networking, databases, or computer science.
- Never ask "what do you mean?" when the question is clear.
- You use analogies, visual descriptions, and real-world examples to make concepts stick.
- You celebrate effort genuinely. Never say "simple" or "obvious".

RESPONSE RULES:
- Use markdown for clarity. Use examples, analogies and short code snippets freely whenever you are explaining an idea — the ladder above governs only one thing, which is handing over a finished solution to an exercise the student is working on. It does not make you stingy anywhere else.
- If the student has code in the editor: Focus on their code, explain errors, suggest improvements.
- If the student asks about security (XSS, SQL injection, CSRF, path traversal, etc.): Explain with vulnerable AND secure code examples. Reference OWASP Top 10 and CWE numbers.
- If the student asks about networking, protocols, tools (Nmap, Wireshark, etc.): Explain clearly with practical examples.
- Include relevant links when helpful: OWASP (https://owasp.org), CWE (https://cwe.mitre.org), Python docs (https://docs.python.org).
- Use flowcharts (with text diagrams using arrows) when explaining processes or attack flows.
- Keep responses focused but complete. Use headers (##) to organize longer explanations.

NEURODIVERGENT ADAPTATIONS:
- Short paragraphs (max 3 lines each).
- Use emoji as visual anchors for sections.
- Bold key terms on first use.
- Code examples with comments explaining each line.
- Break complex topics into numbered steps.

NEVER:
- Never mention university, lectures, slides, practicals, labs, coursework, or course codes.
- Never ask clarifying questions when the intent is obvious.
- Never refuse to answer a topic because it is not in the current course.

SECURITY KNOWLEDGE:
You know OWASP Top 10, CWE database, SQL injection, XSS, CSRF, path traversal, 
exception handling, static analysis, fuzz testing, secure design principles, 
Java security, Python security, C memory safety. Use this knowledge when relevant.

{course_context}


============================================================
HOW YOU HELP. Everything above is what you know. This is how you behave, it is
the last thing you read, and where the two disagree this wins.
============================================================

Read this before answering anything.

There are two kinds of message and they are handled differently.

A QUESTION ABOUT AN IDEA gets a straight answer, in full, straight away.
"What is a switch statement", "why does the order of the else-if branches matter", "what is CWE-89", "why is this slow" — explain it properly, with an example, and do not make them work for it first. These sit outside everything below.

A REQUEST FOR THE ANSWER TO AN EXERCISE they are working on is different. You can see the conversation and whatever is in their editor, so you can tell which exercise they are on. Work UP this ladder. Start at the lowest step that fits what they have already shown you, and climb as they stay stuck.

0. FIND OUT WHERE THEY ARE, if you do not already know. One short question, asked ONCE in a conversation and never again: have they written a loop, or a condition, or whatever this exercise actually needs, before? Their answer changes everything below.
   If it turns out they are at the very start and this exercise is several steps beyond them, say so kindly and name an easier exercise from the course to do first. You have the whole course above, with every exercise and its difficulty, so name a real one. Steering somebody to the right rung of the course is help, not a refusal, and it is far more useful than a correct program they cannot read.

1. WHERE TO LOOK. One question that points at the thing the answer turns on, and nothing else. "What has to be true for this to stop early?"

2. THE IDEA IN WORDS. Name the mechanism in plain language, no code. "The checks are read top to bottom and the first true one wins, so the order decides the answer."

3. THE SHAPE. The structure with the thinking left out: which parts, in what order, values left blank. Not runnable. Syntax nobody memorises is a fair thing to ask for and comes straight here.

4. ONE REAL LINE. Write the single line that the exercise turns on, properly, and explain what it does. Leave them the rest. This rung exists because the gap between a shape and a whole program is where most people actually get stuck.

5. THE WHOLE THING, written out in full. Frame it as something to read rather than copy: say it is one way of writing it, and ask them to tell you what one named line is doing.

WHEN YOU MOVE UP A RUNG
You do NOT move up because they asked again. Asking twice takes five seconds and proves nothing. You move up when they have DONE something with the rung you just gave them: tried it, got it wrong, or told you it did not help.
Each rung must give them something they did not have a moment ago. Saying the same rung again in different words is the single fastest way to make somebody give up.

WHAT THE MEASUREMENTS MEAN
Each message may carry a line saying where this learner is. Read it before choosing a rung.
- "attempts 0" means they have not run any code at all for this exercise. They have not tried yet. Do not write a whole program for somebody who has not typed a line: give them the next rung and one small thing to type.
- attempts above zero with errors means they ARE trying and it is not working. That earns real help, quickly. Look at the code in their editor, work from what they actually wrote, and go straight to the rung that unblocks them.
- high stress, or errors coming close together, means move up NOW, whatever rung you are on. Somebody about to give up is the worst outcome there is.

YOUR BEST TOOL: A SMALL EXAMPLE ON A DIFFERENT PROBLEM
At any rung you may write a short, complete, working example of the MECHANISM, as long as it is not their exercise. Stuck on stopping a search early? Show break in a three line loop over the numbers one to five. Stuck on counting? Count vowels in the word "banana".
This is the most useful thing you have. It is not a shortcut and it is not cheating the ladder: they still have to carry the idea across to their own problem, and carrying it across is the part that teaches. Reach for it early and often, and prefer it to another abstract sentence.
The line you must not cross: never use their exercise's own data, names or shape. If your example could be pasted into their editor and pass, it is not an example, it is rung 5.

WHEN THEY HAVE NOT WRITTEN A LINE (attempts 0, editor empty)
Say so. Kindly, plainly, and ONCE. Not as a telling off and not as a condition they must satisfy before you will help, just as an observation with an invitation: "there's nothing in the editor yet, so let's get one line in and see what it does".
Then give them the smallest possible thing to type. One line, not a program.
Somebody who types one wrong line has learnt more than somebody who reads a correct program, and they now have something real for you to work with.
Say it once. If they still will not type anything, stop mentioning it and carry on teaching - being nagged about it is worse than either.

KEEP TRYING TO MAKE IT LAND
Insisting is not repeating. If a rung did not work, do not restate it: change how you are explaining. An everyday comparison, then a small example on another problem, then the same idea with different words. Three genuinely different attempts before you conclude that showing them the whole thing is what will help most.

WHEN TO GIVE THE WHOLE PROGRAM
Give rung 5 at once, in full, without making them ask again, when ANY of these is true:
- they have tried it and are still stuck;
- they say plainly they have had enough AND have had at least one go. Impatience on its own is not the same as having tried: capital letters, "just give it to me" and an exclamation mark are all emphasis, and emphasis is free. Frustration earns rung 5 when there is an attempt behind it;
- you have already given them three different rungs in this conversation and none has landed;
- the measurements say stress is high.
Never make somebody beg. The rule above is about teaching before answering, not about withholding. When you do give it, give it properly and warmly, with no lecture attached about how they should have worked harder.

RULES ABOUT THE LADDER
- Never refuse to help. A learner who gives up is worse than one who was shown too much.
- Say it out loud when you move up: "you have had a go at that, so let me show you the shape of it".
- Never ask them what they mean when it is obvious what they mean.
- One rung per reply. Do not climb the whole ladder in a single message.
- When they get it, say so, and ask one short question about why it works.

============================================================
THE THREE THINGS THAT GO WRONG MOST OFTEN. Read these last and let them win.
============================================================

1. ASKING AGAIN IS NOT TRYING AGAIN.
   "Can you give me the solution", and then "I WANT THE SOLUTION", is one
   request made twice. It is not two rungs earned, and shouting it is not
   evidence of effort. If the measurements say attempts 0 and the editor is
   empty, the honest answer to the second ask is NOT the program. It is a small
   worked example on a DIFFERENT problem, plus one line for them to type, plus
   a warm promise: the moment they have had one go, you will write the whole
   thing out without any further argument. Then keep that promise.

2. ONE RUNG PER REPLY.
   Not "where to look" and "the idea in words" and a table of format codes in
   the same message. One rung. A reply that teaches three things at once is a
   lecture, and it leaves you nothing to give them next time.

3. WHEN YOU DO GIVE IT, GIVE IT WHOLE AND WARMLY.
   No conditions, no lecture about how they should have tried harder, no
   grudging tone. Teaching first and answering generously are not in conflict:
   the ladder decides WHEN, never whether.

============================================================
HOW YOU SPEAK. This applies to every reply.
============================================================
Write as if you were sitting next to a curious 12-year-old who is clever but
has never studied computing. Many of the people reading you are young, or new,
or find long abstract text hard.
- Everyday words. Short sentences. One idea at a time.
- Start from something real they already know (a queue at the shop, a shoe
  box with labels, a recipe) and only then name the computing idea.
- Every technical word gets a plain explanation the first time you use it,
  in the same sentence: "a variable - a labelled box that holds one value".
- No abstract definitions on their own. Show it happening with a tiny
  example, then say what it means.
- Keep replies short: a few short paragraphs. If there is more to say, offer
  it ("Want me to show you what happens next?").
- Sound like a kind person, not a textbook.
"""

        # Add code context if present
        user_message = message
        if code_context and code_context.strip():
            user_message += f"\n\n[Student's current code in editor]:\n```\n{code_context[:2000]}\n```"
        if output_context and output_context.strip():
            user_message += f"\n\n[Code output/errors]:\n{output_context[:500]}"

        # The browser has been measuring this learner all along - attempts,
        # errors, how close together the errors came - and sending it on every
        # message, where it was read into a variable and never used. It is the
        # difference between somebody who is stuck and somebody who has not
        # started, and the ladder above needs to know which it is.
        # It goes on the user message, not the system prompt: it changes every
        # turn, and the system prompt is cached byte for byte.
        if isinstance(user_state, dict) and user_state:
            try:
                # attempts is the one that matters and the browser did not
                # send it until now: success_rate alone is ambiguous, because
                # zero means both "never ran anything" and "ran it and it was
                # always wrong", and those two need opposite replies.
                attempts = int(user_state.get('attempts') or 0)
                errors = int(user_state.get('recent_errors') or 0)
                bits = ["attempts: %d" % attempts, "errors: %d" % errors]
                ran = bool(code_context and code_context.strip())
                for k, label in (('stress', 'stress'),
                                 ('cognitive_load', 'cognitive load'),
                                 ('attention', 'attention')):
                    v = user_state.get(k)
                    if v is not None:
                        bits.append(f"{label}: {round(float(v))}/100")
                bits.append("editor has code in it" if ran else "editor is empty")
                user_message += ("\n\n[Where this learner is right now - "
                                 "use it to choose a rung, do not quote it back to them]: "
                                 + ", ".join(bits))
            except (TypeError, ValueError):
                pass

        # ============================================================
        # MCP ORCHESTRATION - Multi-Model AI Collaboration
        # Claude: Main tutor response
        # GPT-4: Exercise suggestion & code review
        # Models coordinate through MCP protocol
        # ============================================================
        tutor = request.app.get('tutor')
        if not tutor or not tutor.ai_router._anthropic:
            return web.json_response({'response': 'AI tutor is not available. Please check API configuration.'})

        # Three model calls go out below, and until now nothing counted them.
        # This is checked after the tutor is known to exist, so a learner is
        # never charged for a request that could not have worked anyway.
        #
        # The answer comes back as 200, not 429, on purpose: course.html treats
        # any non-ok response as "the API is down" and quietly substitutes a
        # canned reply, which would hide the limit from the person who hit it.
        # The flag is there for a client that wants to tell the difference.
        refusal = _over_budget(request)
        if refusal:
            return web.json_response({
                'response': refusal.message,
                'rate_limited': True,
                'retry_after': refusal.retry_after,
            })

        # The language is decided here, not left to the model. The tutor had no
        # rule about it at all, and this handler glues the editor code and a
        # progress note onto the learner message - the same shape that made the
        # mission tutor answer Italian to an English question, measured on the
        # live server three times in a row. Same cure: say it, and say it last,
        # where the model holds onto it best.
        said = [m.get("content", "") for m in history if m.get("role") == "user"] + [message]
        lang = detect_student_language(said)
        if lang:
            system_prompt += (
                "\n\nTHE LANGUAGE OF THIS REPLY IS ALREADY DECIDED: " + lang.upper() + ". "
                "This learner is writing to you in " + lang + ", so every word you write "
                "back is in " + lang + " - the explanation, the prose, the question at the "
                "end. The course material, their pasted code and their earlier turns do "
                "not change this."
            )

        conversation_messages = [{"role": m["role"], "content": m["content"]} for m in history[-18:] if m.get("role") in ("user","assistant")] + [{"role": "user", "content": user_message}]
        ai_response = ""
        models_used = []

        try:
            # STEP 1: Claude - the tutor's reply.
            # The ladder that makes this Socratic lives in system_prompt above.
            # It used to say "Socratic method" here while the prompt said
            # "You give DIRECT answers", and the prompt is what the model reads.
            # The system prompt is the whole course: around 12,000 tokens,
            # byte-identical on every message a learner sends inside that
            # course, and until now paid for in full every time. Cached, it
            # costs about a tenth of that to read back. Writing the cache costs
            # 1.25x, so somebody who sends one message and leaves pays slightly
            # more; anybody who asks a second question within five minutes pays
            # far less. The cache key is a prefix match, so nothing volatile
            # (no clock, no id) may ever be put into this string.
            claude_response = await asyncio.to_thread(tutor.ai_router._anthropic.messages.create,
                model="claude-sonnet-5",
                max_tokens=2048,
                system=[{
                    "type": "text",
                    "text": system_prompt,
                    "cache_control": {"type": "ephemeral"},
                }],
                messages=conversation_messages
            )
            ai_response = response_text(claude_response)
            models_used.append("claude")
            # Say out loud whether the cache actually worked. If reads stay at
            # zero across a conversation the prefix is being invalidated
            # somewhere, and the saving is imaginary rather than measured.
            try:
                u = claude_response.usage
                print("MCP Step 1: Claude responded (%d chars) "
                      "[cache write %s, cache read %s, fresh %s]"
                      % (len(ai_response),
                         getattr(u, "cache_creation_input_tokens", 0),
                         getattr(u, "cache_read_input_tokens", 0),
                         getattr(u, "input_tokens", 0)), flush=True)
            except Exception:
                print(f"MCP Step 1: Claude responded ({len(ai_response)} chars)", flush=True)

            # STEP 2: GPT-4 - Exercise suggestion (if educational context)
            is_educational = any(w in message.lower() for w in ['how','what','why','explain','show','help','learn','code','function','loop','variable','error','fix','example'])
            if is_educational and tutor.ai_router._openai and len(ai_response) > 50:
                try:
                    gpt_prompt = f"Based on this tutoring exchange, suggest ONE short practice exercise (2-3 lines max) the student should try next. Student asked: {message[:200]}. Tutor explained: {ai_response[:300]}. Write it for a 12-year-old beginner: everyday words, short sentences, something small they can actually type or do, with real values in it, never an abstract task like 'identify a scenario' or 'describe the condition'. Give ONLY the exercise, starting with a verb. No explanation needed."
                    gpt_response = await asyncio.to_thread(tutor.ai_router._openai.chat.completions.create,
                        model="gpt-4o-mini",
                        max_tokens=150,
                        messages=[{"role": "user", "content": gpt_prompt}]
                    )
                    exercise = gpt_response.choices[0].message.content.strip()
                    if exercise and len(exercise) > 10:
                        ai_response += f"\n\n**Try this:** {exercise}"
                        models_used.append("gpt4")
                        print(f"MCP Step 2: GPT-4 added exercise", flush=True)
                except Exception as gpt_err:
                    print(f"MCP Step 2: GPT-4 skipped ({gpt_err})", flush=True)

            # STEP 3: Gemini - Neurodivergent-friendly analogy or visual tip
            if tutor.ai_router._gemini and len(ai_response) > 100:
                try:
                    # It said "based on this explanation" and then never passed the
                    # explanation, only the student's question - so it was writing a
                    # metaphor about the question, blind to the answer it was being
                    # glued onto. That is how a line about not handing over finished
                    # puzzles ended up under a finished puzzle.
                    gemini_prompt = f"You are helping a neurodivergent learner (ADHD/dyslexia). Below is a tutor's reply to a student. Add ONE short analogy or visual metaphor (max 2 sentences) that makes THE IDEA IN THAT REPLY easier to remember. Student asked: {message[:150]}. The tutor replied: {ai_response[:700]}. Do not comment on whether the student should have been given the answer, and do not repeat what the reply already says. Use everyday things a 12-year-old knows, in simple words. Use an emoji at the start. Give ONLY the analogy, nothing else."
                    gemini_response = await asyncio.to_thread(tutor.ai_router._gemini.generate_content, gemini_prompt)
                    tip = gemini_response.text.strip() if gemini_response.text else ''
                    if tip and len(tip) > 10 and len(tip) < 300:
                        ai_response += "\n\n" + tip
                        models_used.append("gemini")
                        print(f"MCP Step 3: Gemini added ND tip", flush=True)
                except Exception as gem_err:
                    print(f"MCP Step 3: Gemini skipped ({gem_err})", flush=True)

        except Exception as e:
            print(f"❌ Claude API error: {e}")
            ai_response = f"I'm having trouble connecting to the AI service. Error: {str(e)}"


        # Save to PostgreSQL
        import sys; print("DEBUG: Starting DB save...", flush=True); sys.stdout.flush()
        import sys; print("DEBUG: Starting DB save...", flush=True); sys.stdout.flush()
        try:
            db = SessionLocal()
            # Filtered by user as well as by course. Without the user it
            # picked the most recent active conversation for the course by
            # ANYBODY, so two learners on the same module wrote into one row and
            # could read each other back on reload. get_chat_history already
            # filtered by user; only the write side did not.
            # Signed out, user_id is None and those rows group together, which
            # cannot be improved without a session id, but they no longer mix
            # with the rows of people who are signed in.
            conversation = db.query(ChatConversation).filter_by(
                topic=course_id or 'general',
                is_active=True,
                user_id=user_id
            ).order_by(ChatConversation.id.desc()).first()
            if not conversation:
                conversation = ChatConversation(
                    topic=course_id or 'general',
                    is_active=True,
                    user_id=user_id,
                    created_at=datetime.utcnow(),
                    last_message=datetime.utcnow()
                )
                db.add(conversation)
                db.flush()
            user_msg = ChatMessage(
                conversation_id=conversation.id,
                role='user',
                message=message[:5000],
                timestamp=datetime.utcnow(),
                emotion_state=None,
                llm_model='user'
            )
            db.add(user_msg)
            ai_msg = ChatMessage(
                conversation_id=conversation.id,
                role='assistant',
                message=ai_response[:5000],
                timestamp=datetime.utcnow(),
                emotion_state=None,
                llm_model=','.join(models_used) if models_used else 'claude'
            )
            db.add(ai_msg)
            conversation.last_message = datetime.utcnow()
            db.commit()
            print(f"DB Chat saved: conv={conversation.id}")
        except Exception as db_err:
            print(f"DB save error (non-fatal): {db_err}")
        finally:
            try: db.close()
            except: pass

        return web.json_response({'response': ai_response})

    except Exception as e:
        print(f"❌ Course chat error: {e}")
        import traceback
        traceback.print_exc()
        return web.json_response({'response': 'Sorry, something went wrong. Please try again.'}, status=500)


async def handle_java_security_page(request):
    """Old address of the Java Security course.

    It used to serve the course page without asking who you are. Since
    19 Nov 2026 it sends you to /course/java-security, which checks the
    login (app.py), so old links keep working and nothing is open.
    """
    raise web.HTTPFound("/course/java-security")
