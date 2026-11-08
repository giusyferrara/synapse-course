import asyncio
import os
import sys
import socket
import requests
import json
import re as _re


LESSONS_CHROME = """
<link rel="stylesheet" href="/static/synapse_a11y.css?v=20">
<link rel="stylesheet" href="/static/synapse_a11y_toolbar.css?v=8">
<script src="/static/focus_assistant.js"></script>
<script src="/static/synapse_a11y_toolbar.js?v=7"></script>
<script src="/static/synapse_a11y.js?v=12"></script>
<script>
/* One theme control, not two that disagree.

   The toolbar's moon sets body.dark-mode. The player sets data-theme on the
   root. They are different mechanisms, and the toolbar's own stylesheet says
   so out loud: its dark rules are written html:not([data-theme]), which means
   it stands down on any page that has a theme of its own. So on this page the
   moon would have looked like a button and done nothing.

   Rather than leave a dead control or add a second live one, the moon is
   rewired to drive the player's theme. One button, and it means what it looks
   like. The player's own row is hidden: the navbar already carries a way home,
   and a second theme control is the thing this is here to avoid. */
(function () {
  var KEY = "synapse-theme";
  var root = document.documentElement;
  var bar = document.querySelector(".pagebar");
  if (bar) { bar.hidden = true; }

  function effective() {
    var set = root.getAttribute("data-theme");
    if (set === "dark" || set === "light") { return set; }
    return (window.matchMedia &&
            window.matchMedia("(prefers-color-scheme: dark)").matches) ? "dark" : "light";
  }

  function mark() {
    var b = document.getElementById("darkModeBtn");
    if (b) { b.classList.toggle("active", effective() === "dark"); }
  }

  if (window.synapseToolbar) {
    window.synapseToolbar.toggleDark = function () {
      var next = effective() === "dark" ? "light" : "dark";
      root.setAttribute("data-theme", next);
      try { window.localStorage.setItem(KEY, next); } catch (e) { /* no memory, still works */ }
      mark();
    };
  }
  mark();
})();
</script>
"""
from datetime import datetime
from pathlib import Path
from aiohttp import web
from aiohttp_cors import setup as cors_setup, ResourceOptions
from dotenv import load_dotenv

# MCP imports
try:
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
    from mcp.server.models import InitializationOptions
    from mcp.types import CallToolResult, Tool, TextContent
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False
    print("WARNING: MCP not available. Install: pip install mcp>=1.0.0")

# Core imports
from core.tutor import EnhancedSecurityTutor
from web.handlers import setup_routes
from web.lang import detect_student_language
from web.session import current_user_id, admin_key_ok
from web.course_handlers import setup_course_routes
from web.advanced_handlers import setup_advanced_routes
from database.config import Base, engine, SessionLocal
from database.models import Student, LearningSession, AIResponse, Feedback, ResearchParticipant
from web.metrics_handlers import setup_metrics_routes
from web.auth_handlers import setup_auth_routes
from web.research_handlers import setup_research_routes as setup_research_api_routes
from web.quiz_handlers import setup_quiz_routes
from web.drawer_handlers import setup_drawer_routes
from web.research.research_dashboard_handler import setup_research_routes as setup_research_dashboard_routes

# Advanced MCP Tools Integration
try:
    from mcp_integration import extend_tutor_with_advanced_tools
    ADVANCED_TOOLS_AVAILABLE = True
except ImportError:
    ADVANCED_TOOLS_AVAILABLE = False
    print("WARNING: Advanced tools not found.")

# London Transport Integration
try:
    from london_transport_integration import extend_tutor_with_london_tools
    LONDON_TOOLS_AVAILABLE = True
except ImportError:
    LONDON_TOOLS_AVAILABLE = False
    print("WARNING: London transport tools not found.")

# ============================================================================
# RESEARCH DATA DIRECTORY SETUP
# ============================================================================
RESEARCH_DATA_DIR = Path(__file__).parent / "research_data"
RESEARCH_DATA_DIR.mkdir(exist_ok=True)


def get_external_ip():
    """Get the external IP address of this server."""
    try:
        response = requests.get('https://api.ipify.org', timeout=5)
        response.raise_for_status()
        return response.text.strip()
    except Exception:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
            s.close()
            return local_ip
        except Exception:
            return "unknown"


class HybridEducationalServer:
    """Hybrid server supporting both web interface and MCP protocol"""

    def __init__(self):
        """Initialize server with tutor instance"""
        self.tutor = EnhancedSecurityTutor()
        self._advanced_tools_initialized = False

        if MCP_AVAILABLE:
            self.mcp_server = Server("educational-tutor")
            self._setup_mcp_tools()

    async def _init_advanced_tools_once(self):
        """Initialize advanced tools ONCE - fixes duplicate bug"""
        if not self._advanced_tools_initialized:
            try:
                if ADVANCED_TOOLS_AVAILABLE:
                    await extend_tutor_with_advanced_tools(self.tutor)
                if LONDON_TOOLS_AVAILABLE:
                    await extend_tutor_with_london_tools(self.tutor)
                self._advanced_tools_initialized = True
            except Exception as e:
                print(f"WARNING: Could not initialize tools: {e}")

    def _setup_mcp_tools(self):
        """Setup MCP tools using existing tutor functionality"""

        if not MCP_AVAILABLE:
            return

        @self.mcp_server.list_tools()
        async def list_tools():
            return [
                Tool(
                    name="analyze_code_comprehensive",
                    description="Comprehensive code analysis with security review, emotional state awareness, and neurodivergent adaptations",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "code": {"type": "string", "description": "Source code to analyze (Python or Java)"},
                            "user_message": {"type": "string", "default": ""},
                            "student_id": {"type": "string", "default": "mcp_student"}
                        },
                        "required": ["code"]
                    }
                ),
                Tool(
                    name="generate_visual_explanation",
                    description="Create visual explanations with interactive diagrams",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "code": {"type": "string", "description": "Code to visualize"},
                            "user_message": {"type": "string", "default": ""},
                            "accessibility_level": {
                                "type": "string",
                                "enum": ["basic", "intermediate", "advanced"],
                                "default": "intermediate"
                            }
                        },
                        "required": ["code"]
                    }
                ),
                Tool(
                    name="review_code_security",
                    description="Analyze code for security vulnerabilities",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "code": {"type": "string", "description": "Code to review"}
                        },
                        "required": ["code"]
                    }
                ),
                Tool(
                    name="explain_code_concepts",
                    description="Explain programming concepts with AI",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "code": {"type": "string", "description": "Code to explain"},
                            "learning_style": {
                                "type": "string",
                                "enum": ["visual", "auditory", "kinesthetic", "reading"],
                                "default": "visual"
                            }
                        },
                        "required": ["code"]
                    }
                ),
                Tool(
                    name="suggest_code_improvements",
                    description="Suggest code improvements and best practices",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "code": {"type": "string", "description": "Code to improve"}
                        },
                        "required": ["code"]
                    }
                ),
                Tool(
                    name="generate_practice_exercises",
                    description="Generate personalized coding exercises",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "code": {"type": "string", "description": "Base code"},
                            "difficulty": {
                                "type": "string",
                                "enum": ["beginner", "intermediate", "advanced"],
                                "default": "intermediate"
                            }
                        },
                        "required": ["code"]
                    }
                ),
                Tool(
                    name="run_code_tests",
                    description="Execute code safely with tests",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "code": {"type": "string", "description": "Code to test"}
                        },
                        "required": ["code"]
                    }
                ),
                Tool(
                    name="diagnose_ai_systems",
                    description="Test AI services connectivity",
                    inputSchema={
                        "type": "object",
                        "properties": {},
                        "additionalProperties": False
                    }
                ),
                Tool(
                    name="analyze_emotional_state",
                    description="Analyze student emotional state for adaptations",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "message": {"type": "string", "description": "Student message"},
                            "context": {"type": "object", "default": {}}
                        },
                        "required": ["message"]
                    }
                )
            ]

        @self.mcp_server.call_tool()
        async def call_tool(name: str, arguments: dict):
            """Execute educational tools"""
            try:
                if name == "analyze_code_comprehensive":
                    result = await self.tutor.tool_execute_python_debug(arguments)
                elif name == "generate_visual_explanation":
                    result = await self.tutor.tool_visual_guide(arguments)
                elif name == "review_code_security":
                    result = await self.tutor.tool_secure_review(arguments)
                elif name == "explain_code_concepts":
                    result = await self.tutor.tool_explain_code(arguments)
                elif name == "suggest_code_improvements":
                    result = await self.tutor.tool_suggest_fixes(arguments)
                elif name == "generate_practice_exercises":
                    result = await self.tutor.tool_generate_tests(arguments)
                elif name == "run_code_tests":
                    result = await self.tutor.tool_run_tests(arguments)
                elif name == "diagnose_ai_systems":
                    result = await self.tutor.tool_test_ai(arguments)
                elif name == "analyze_emotional_state":
                    emotion_state = self.tutor.emotion_analyzer.analyze_comprehensive_state(
                        message=arguments["message"],
                        user_id="mcp_user",
                        context=arguments.get("context", {})
                    )
                    result = json.dumps(emotion_state, indent=2)
                else:
                    result = f"Unknown tool: {name}"

                return CallToolResult(content=[TextContent(type="text", text=result)])

            except Exception as e:
                error_msg = f"Error executing {name}: {str(e)}"
                print(f"ERROR: MCP Tool Error: {error_msg}")
                return CallToolResult(
                    content=[TextContent(type="text", text=error_msg)],
                    isError=True
                )

    async def run_web_server(self):
        """Run the web interface server"""
        load_dotenv()

        # Create database tables (PostgreSQL)
        Base.metadata.create_all(bind=engine)
        print("✅ SUCCESS: Database tables created (PostgreSQL)")

        # Initialize advanced tools ONCE
        await self._init_advanced_tools_once()

        # web/guard.py: one gate in front of every request (8 Nov 2026 audit).
        from web.guard import guard
        app = web.Application(middlewares=[guard])
        app["tutor"] = self.tutor
        print("✅ SUCCESS: Tutor instance ready")

        # ====================================================================
        # ICONS HANDLER
        # ====================================================================
        async def serve_icon(request):
            """Serve icon files from /icons/ directory"""
            filename = request.match_info['filename']
            # A plain file name only. '..%2Fapp.py' used to reach here as
            # '../app.py' and serve any file next to this one.
            icons_dir = (Path(__file__).parent / 'icons').resolve()
            icon_path = (icons_dir / filename).resolve()
            if ('/' in filename or '\\' in filename or '..' in filename
                    or icon_path.parent != icons_dir or not icon_path.is_file()):
                return web.Response(status=404, text='Icon not found')

            content_type = 'image/png'
            if filename.endswith('.svg'):
                content_type = 'image/svg+xml'
            elif filename.endswith('.jpg') or filename.endswith('.jpeg'):
                content_type = 'image/jpeg'
            elif filename.endswith('.gif'):
                content_type = 'image/gif'
            elif filename.endswith('.webp'):
                content_type = 'image/webp'

            print(f"✅ Serving icon: {filename} ({content_type})")
            return web.FileResponse(icon_path, headers={'Content-Type': content_type})

        app.router.add_get('/icons/{filename}', serve_icon)
        print("✅ SUCCESS: Icons handler registered")

        # ====================================================================
        # LANDING PAGE AND COURSE ROUTES
        # ====================================================================
        async def serve_app(request):
            """Python AI Tool"""
            if not current_user_id(request):
                raise web.HTTPFound('/login?next=/app')
            index_path = Path(__file__).parent / 'templates' / 'index.html'
            try:
                with open(index_path, 'r', encoding='utf-8', errors='ignore') as f:
                    return web.Response(text=f.read(), content_type='text/html')
            except FileNotFoundError:
                return web.Response(text="<h1>Not found</h1>", status=404)

        
        
        
        async def serve_favicon(request):
            fav_path = Path(__file__).parent / 'icons' / 'favicon.ico'
            if fav_path.exists():
                return web.FileResponse(fav_path)
            return web.Response(status=404)
        async def serve_google_verify(request):
            return web.Response(text='google-site-verification: googleb2bf07109a72196e.html', content_type='text/html')
        async def serve_sitemap(request):
            sitemap_path = Path(__file__).parent / 'static' / 'sitemap.xml'
            try:
                with open(sitemap_path, 'r') as f:
                    return web.Response(text=f.read(), content_type='application/xml')
            except:
                return web.Response(text='Not found', status=404)

        async def serve_landing(request):
            """Home routing - always serve landing page"""
            landing_path = Path(__file__).parent / 'templates' / 'landing.html'
            try:
                with open(landing_path, 'r', encoding='utf-8', errors='ignore') as f:
                    return web.Response(text=f.read(), content_type='text/html')
            except FileNotFoundError:
                return web.Response(text="<h1>Landing not found</h1>", status=404)

        async def serve_java_security_course(request):
            """Java Security course page - requires auth"""
            user_cookie = current_user_id(request)
            participant_code = request.query.get('participant') or request.cookies.get('participant_code')
            if not user_cookie and not participant_code and not admin_key_ok(request):
                raise web.HTTPFound('/login?next=/course/java-security')
            from sqlalchemy import text as sql_text
            from database.config import SessionLocal
            display_name = ''
            if user_cookie:
                db = SessionLocal()
                try:
                    result = db.execute(sql_text("SELECT display_name FROM users WHERE id = :uid"), {'uid': int(user_cookie)}).fetchone()
                    if result and result.display_name:
                        display_name = result.display_name
                except Exception:
                    pass
                finally:
                    db.close()
            course_path = Path(__file__).parent / 'templates' / 'course_java_security.html'
            try:
                with open(course_path, 'r', encoding='utf-8', errors='ignore') as f:
                    html_content = f.read()
                safe_name = display_name.replace('"', '').replace('<', '').replace('>', '')
                if safe_name:
                    injection = f'<script>window.SYNAPSE_USER_NAME = "{safe_name}";</script>\n'
                    html_content = html_content.replace('</head>', injection + '</head>', 1)
                response = web.Response(text=html_content, content_type='text/html')
                if participant_code:
                    response.set_cookie('participant_code', participant_code, max_age=90*24*60*60)
                    print(f"✅ Java Security Participant: {participant_code}")
                return response
            except FileNotFoundError:
                return web.Response(text="<h1>Java Security course not found</h1>", status=404)

        async def serve_course(request):
            """Course page - requires auth"""
            user_cookie = current_user_id(request)
            participant_code = request.query.get('participant') or request.cookies.get('participant_code')
            if not user_cookie and not participant_code and not admin_key_ok(request):
                raise web.HTTPFound('/login?next=/course')
            course_path = Path(__file__).parent / 'templates' / 'course.html'
            try:
                with open(course_path, 'r', encoding='utf-8', errors='ignore') as f:
                    response = web.Response(text=f.read(), content_type='text/html')
                if participant_code:
                    response.set_cookie('participant_code', participant_code, max_age=90*24*60*60)
                    print(f"✅ Participant: {participant_code}")
                return response
            except FileNotFoundError:
                return web.Response(text="<h1>Course not found</h1>", status=404)

        # ====================================================================
        # RESEARCH PARTICIPANT VALIDATION - PostgreSQL
        # ====================================================================
        async def validate_participant_code(request):
            """Validate participant code - PostgreSQL version"""
            try:
                data = await request.json()
                code = data.get('code', '').strip().upper()

                if not code or len(code) != 8:
                    return web.json_response({'valid': False})

                db = SessionLocal()
                try:
                    participant = db.query(ResearchParticipant).filter_by(
                        participant_code=code
                    ).first()

                    if participant:
                        print(f"✅ Valid login: {code}")
                        return web.json_response({'valid': True})
                    else:
                        print(f"⚠️  Invalid code: {code}")
                        return web.json_response({'valid': False})
                finally:
                    db.close()

            except Exception as e:
                print(f"❌ Validation error: {e}")
                return web.json_response({'valid': False})

        async def get_participant_info(request):
            """GET /api/research/participant?code=X"""
            try:
                code = request.query.get("code", "").strip().upper()
                if not code:
                    return web.json_response({"error": "No code provided"})
                db = SessionLocal()
                try:
                    p = db.query(ResearchParticipant).filter_by(participant_code=code).first()
                    if p:
                        return web.json_response({"nickname": p.nickname, "group": "A", "code": p.participant_code})
                    else:
                        return web.json_response({"error": "Code not found"})
                finally:
                    db.close()
            except Exception as e:
                return web.json_response({"error": str(e)})

        # ====================================================================
        # NICKNAME CHECK - PostgreSQL (CRITICAL!)
        # ====================================================================
        async def check_nickname_availability(request):
            """Check nickname availability - PostgreSQL version"""
            try:
                data = await request.json()
                nickname = data.get('nickname', '').strip().lower()

                if not nickname or len(nickname) < 3:
                    return web.json_response({
                        'available': False,
                        'error': 'Nickname must be at least 3 characters'
                    })

                db = SessionLocal()
                try:
                    existing = db.query(ResearchParticipant).filter(
                        ResearchParticipant.nickname.ilike(nickname)
                    ).first()

                    if existing:
                        print(f"⚠️  Nickname TAKEN: '{nickname}'")
                        return web.json_response({
                            'available': False,
                            'message': 'This nickname is already taken'
                        })
                    else:
                        print(f"✅ Nickname AVAILABLE: '{nickname}'")
                        return web.json_response({
                            'available': True,
                            'message': 'Nickname is available!'
                        })
                finally:
                    db.close()

            except Exception as e:
                print(f"❌ Nickname check error: {e}")
                import traceback
                traceback.print_exc()
                return web.json_response({
                    'available': False,
                    'error': str(e)
                }, status=500)

        # ====================================================================
        # EMAIL CHECK - PostgreSQL
        # ====================================================================
        async def check_email_availability(request):
            """Check email availability - PostgreSQL version"""
            try:
                data = await request.json()
                email = data.get('email', '').strip().lower()

                if not email or '@' not in email:
                    return web.json_response({
                        'available': False,
                        'error': 'Invalid email format'
                    })

                db = SessionLocal()
                try:
                    existing = db.query(ResearchParticipant).filter_by(
                        email=email
                    ).first()

                    if existing:
                        # Never the code: it is the participant's key, and
                        # this answer goes to whoever typed the email.
                        return web.json_response({
                            'available': False,
                            'message': 'This email is already registered'
                        })
                    else:
                        print(f"✅ Email AVAILABLE: '{email}'")
                        return web.json_response({'available': True})
                finally:
                    db.close()

            except Exception as e:
                print(f"❌ Email check error: {e}")
                return web.json_response({
                    'available': False,
                    'error': str(e)
                }, status=500)

        # ====================================================================
        # CODE RECOVERY - PostgreSQL
        # ====================================================================
        async def recover_code_by_nickname(request):
            """Recover code by nickname - PostgreSQL version"""
            try:
                data = await request.json()
                nickname = data.get('nickname', '').strip().lower()

                if not nickname:
                    return web.json_response({
                        'found': False,
                        'error': 'Nickname required'
                    })

                db = SessionLocal()
                try:
                    participant = db.query(ResearchParticipant).filter(
                        ResearchParticipant.nickname.ilike(nickname)
                    ).first()

                    if participant:
                        print(f"✅ Code recovered: {nickname} → {participant.participant_code}")
                        return web.json_response({
                            'found': True,
                            'code': participant.participant_code,
                            'nickname': participant.nickname
                        })
                    else:
                        return web.json_response({'found': False})
                finally:
                    db.close()

            except Exception as e:
                print(f"❌ Recovery error: {e}")
                return web.json_response({'found': False, 'error': str(e)})

        async def recover_code_by_email(request):
            """Recover code by email - PostgreSQL version"""
            try:
                data = await request.json()
                email = data.get('email', '').strip().lower()

                if not email:
                    return web.json_response({
                        'found': False,
                        'error': 'Email required'
                    })

                db = SessionLocal()
                try:
                    participant = db.query(ResearchParticipant).filter_by(
                        email=email
                    ).first()

                    if participant:
                        print(f"✅ Code recovered: {email} → {participant.participant_code}")
                        return web.json_response({
                            'found': True,
                            'code': participant.participant_code
                        })
                    else:
                        return web.json_response({'found': False})
                finally:
                    db.close()

            except Exception as e:
                print(f"❌ Recovery error: {e}")
                return web.json_response({'found': False, 'error': str(e)})

        # ====================================================================
        # AI CHAT
        # ====================================================================
        async def chat_ai(request):
            """Handle AI chat - routes to ShopSecure tutor or default tutor"""
            try:
                data = await request.json()
                message = data.get('message', '')
                context = data.get('context', '')
                participant_code = data.get('student_id', data.get('participant_code', 'UNKNOWN'))

                # ShopSecure vulnerability assessment context
                if context == 'shopsecure_vuln_assessment':
                    tutor = request.app.get('tutor'); router = tutor.ai_router if tutor else None
                    if not router:
                        return web.json_response({'response': 'AI system not available'}, status=500)

                    # The prompt is built HERE, on the server. The browser used to
                    # send its own system_prompt and this code preferred it, which
                    # both overrode this safe version and let anyone edit the
                    # tutor's rules from devtools. Its system_prompt is now ignored;
                    # only a sanitised display name is taken from the client.
                    raw_name = (data.get('nickname') or '').strip()
                    safe_name = ''.join(c for c in raw_name if c.isalnum() or c in " -'")[:40]
                    student = safe_name or 'the student'

                    SHOPSECURE_PROMPT = (
                        "You are SYNAPSE, a warm, adaptive security tutor. You are helping "
                        + student + " reproduce three vulnerabilities in ShopSecure, a "
                        "deliberately vulnerable practice shop, as a hands-on exercise. "
                        "This is an authorised lab: the app exists to be attacked, and "
                        "teaching how these flaws work is the whole point. "
                        " "
                        "HOW YOU TEACH, IN ONE SENTENCE. You lead them to understand what is "
                        "happening behind the scenes, and you do NOT give the answer straight "
                        "away. The finished payload is the LAST thing you offer, not the first. "
                        "Understanding the mechanism is the point; the working string is just "
                        "the proof they understood. "
                        " "
                        "CREDENTIALS, so you never invent any: admin / adminShop2026, and "
                        "user1 / user1Pass! through user5 / user5Pass!. There are no other "
                        "accounts. "
                        " "
                        "CONCEPTS you may explain in full whenever asked - what a weakness is "
                        "and why a fix works sit OUTSIDE the ladder and get a clear answer: "
                        "CWE-502 Insecure Deserialisation - pickle runs code while loading, so "
                        "untrusted data becomes execution; fix with JSON or a restricted "
                        "unpickler. "
                        "CWE-22 Path Traversal - a filename that climbs out of the intended "
                        "folder reaches files it should not, and naive filters that strip one "
                        "level can still be walked around; fix by resolving the path and "
                        "checking it stays inside the allowed directory. "
                        "CWE-352 CSRF - the browser attaches the victim's session cookie to any "
                        "request their browser makes, so attacker-controlled content can act "
                        "with the victim's authority; fix with a per-session token and SameSite "
                        "cookies. "
                        " "
                        "THE THREE MISSIONS (keep them secret; guide, do not announce): "
                        "1. CWE-502 on the /shop/preferences page, which imports preferences "
                        "with pickle. "
                        "2. CWE-22 on the /shop/invoice page, which opens a file named by the "
                        "user. "
                        "3. CWE-352 on the /shop/csrf-challenge page, which has no token on its "
                        "transfer form. "
                        " "
                        "THE LADDER. One rung per reply, and you climb only when they have "
                        "DONE something with the last rung - tried an input, or reasoned a "
                        "step. Asking again, even in capitals, is not a rung and does not move "
                        "you up. "
                        "1 WHAT HAPPENS BEHIND THE SCENES - explain this well, it is the whole "
                        "point. A disk is a tree of folders inside folders, with one root at "
                        "the top. Every file lives at a path down from that root, and a program "
                        "always runs while standing in one folder. To open a file the server "
                        "joins the base folder it stands in to the name you send: base plus "
                        "name. HOW YOU MOVE BETWEEN FILES: a plain name moves DOWN or sideways "
                        "inside the current folder, and the special step that means "
                        "up-one-level moves you UP, back towards the root. Chain enough "
                        "up-one-level steps and you climb above the base folder entirely, and "
                        "from the root every other folder on the machine is reachable by naming "
                        "the way down to it. DRAW IT, do not only describe it: a picture lands "
                        "faster than a paragraph. Put a tiny tree in a fenced code block - three "
                        "backticks, one folder per line, each level indented under its parent - "
                        "so it keeps its shape, mark where the program is standing and the file "
                        "to reach, and show the climb as a short run of up-one-level steps beside "
                        "it. Use a MADE-UP tree, never the real target's real path - "
                        "for example standing in a folder two levels below the root, count out "
                        "loud how many up-one-level steps reach the root, then walk back down "
                        "into a different folder and name a file there. That illustration on an "
                        "invented tree is a teaching aid and is encouraged; it is NOT the live "
                        "answer, because it does not name the real target. Make sure they can "
                        "picture the folder being climbed out of before you move on. "
                        "2 WHERE TO LOOK - one question pointing at the primitive: \"what does "
                        "the server do with the filename you send it, and where does it look "
                        "for that file?\". "
                        "3 THE SHAPE - the structure with the decisive part left blank: \"a "
                        "path made of repeated up-one-level steps, enough to reach the root, "
                        "then the name of a file you know exists on a Linux box\". Described, "
                        "not written out. Invite them to type their version. "
                        "4 REACT TO THEIR ATTEMPTS - work from what they typed: which part is "
                        "right, which is not, why it did or did not reach the file. Nudge, do "
                        "not correct it FOR them. Stay here across several tries. "
                        "5 THE PAYLOAD, ONLY AS A LAST RESORT. If they have genuinely tried at "
                        "least FOUR times - four real inputs or reasoning steps, not four asks "
                        "- and still cannot reach it, then give the complete working string, "
                        "framed as \"here is one that works - read it against what you tried "
                        "and tell me which step was missing\". Never before the fourth "
                        "genuine attempt. "
                        " "
                        "WHEN THEY HAVE NOT TRIED. If they ask for the answer with no attempt "
                        "behind them, say so kindly, once, explain a piece of the mechanism, "
                        "and give the smallest next thing to type - never the finished input. "
                        "Counting: capital letters, please, and \"just give it to me\" are "
                        "emphasis, not attempts. An attempt is something they actually tried. "
                        " "
                        "BEHAVIOUR. Never refuse to help. If before the fourth attempt they are "
                        "clearly about to give up, do NOT dump the payload - drop to the "
                        "simplest possible next micro-step and one more piece of the mechanism, "
                        "and keep them moving. Say it out loud when you move up a rung. Answer "
                        "\"what is this\" and \"why does the fix work\" in full, outside the "
                        "ladder. Celebrate small wins. "
                        " "
                        "LANGUAGE - THIS ONE IS ABSOLUTE. Look at the student's most "
                        "recent message, and only at that, and reply in the language it "
                        "is written in. If it is English, you answer in English, every "
                        "time, even when everything else you can see is in another "
                        "language. Their notes below, their earlier turns and the name "
                        "of the lab are stored data: they never decide the language. If "
                        "they switch language mid-conversation, you switch with them, "
                        "starting from that message. "
                        " "
                        "THE ARC, AND ITS ORDER. Every vulnerability runs Detect, then "
                        "Understand, then Remediate, always in that order. DETECT: they find "
                        "that the flaw is there. UNDERSTAND: they can say WHY it works - the "
                        "mechanism, which is rungs 1 to 5 above and matters more than the "
                        "payload itself. REMEDIATE: they can say why the FIX holds - not just "
                        "its name, but why it closes the hole the exploit went through. A "
                        "mission is not finished when the payload works; it is finished when "
                        "they can explain the repair. So when an exploit lands, celebrate, then "
                        "carry them to the fix: ask what would have stopped their own input, "
                        "and for traversal make the link plain - resolving the path and "
                        "checking it stays inside the allowed folder defeats the very climb "
                        "they just did. "
                        "STYLE: at most 3-4 lines per reply, one step at a time."
                    )

                    # Build messages with chat history for context
                    chat_history = data.get('chat_history', [])
                    extra_context = data.get('extra_context', '')
                    messages = []
                    for msg in chat_history:
                        if msg.get('role') in ('user', 'assistant') and msg.get('content'):
                            messages.append({'role': msg['role'], 'content': msg['content']})
                    # The saved findings used to be glued onto the end of the
                    # student's own message. That is what answered in Italian to
                    # a question typed in English: the notes carry whatever
                    # language the student writes notes in, and once they sit
                    # inside the student's turn they outweigh the question
                    # itself. Measured on the live server: English question plus
                    # Italian notes came back in Italian, every time. They belong
                    # in the briefing, as stored data, so the student's turn is
                    # only the words the student actually typed.
                    messages.append({'role': 'user', 'content': message})
                    briefing = SHOPSECURE_PROMPT
                    if extra_context:
                        briefing += (
                            " "
                            "WHAT THEY HAVE WRITTEN DOWN SO FAR. The notes this student saved in "
                            "the report form, in whatever language they take notes in. Use the "
                            "facts - what they have found, what is still missing - and ignore the "
                            "language they are written in: " + extra_context
                        )

                    # The language is decided here, not left to the model. It goes
                    # last because that is the instruction it holds onto best.
                    said = [m.get('content', '') for m in chat_history
                            if m.get('role') == 'user'] + [message]
                    lang = detect_student_language(said)
                    if lang:
                        briefing += (
                            " "
                            "THE LANGUAGE OF THIS REPLY IS ALREADY DECIDED: " + lang.upper() + ". "
                            "This student is writing to you in " + lang + ", so every word you "
                            "write back is in " + lang + " - the greeting, the explanation, the "
                            "question at the end. Nothing else you can see changes this."
                        )

                    response = await router.get_chat_response(briefing, messages)
                    print(f'ShopSecure chat [{participant_code}]: {message[:60]}')
                    return web.json_response({'response': response})

                # Default: use original tutor
                tutor = request.app.get('tutor')
                if not tutor:
                    return web.json_response({'response': 'AI system not available'}, status=500)
                model = data.get('model', 'claude')
                if model == 'claude':
                    response = await tutor.ask_claude(message, participant_code)
                elif model == 'gpt4':
                    response = await tutor.ask_gpt4(message, participant_code)
                elif model == 'gemini':
                    response = await tutor.ask_gemini(message, participant_code)
                else:
                    response = 'Invalid model selected'
                return web.json_response({'response': response})
            except Exception as e:
                print(f'Chat error: {e}')
                import traceback
                traceback.print_exc()
                return web.json_response({'response': 'Error processing request'}, status=500)

        # ====================================================================
        # CODE EXECUTION - SANDBOXED
        # ====================================================================
        def _check_code_safety(code):
            """
            Check if submitted code is safe to execute.
            Returns (is_safe, error_message) tuple.
            Blocks dangerous imports, system commands, and file access.
            """
            # Normalize code for checking - collapse whitespace for bypass prevention
            import re
            code_normalized = re.sub(r'\s+', ' ', code).lower()
            code_lower = code.lower()

            # === Block dangerous imports ===
            BLOCKED_IMPORTS = [
                'os', 'subprocess', 'sys', 'shutil', 'socket',
                'http', 'urllib', 'requests', 'pathlib',
                'ctypes', 'signal', 'threading', 'multiprocessing',
                'importlib', 'code', 'codeop',
                'pickle', 'shelve', 'marshal',
                'webbrowser', 'antigravity', 'turtle',
                'tkinter', 'sqlite3', 'ftplib', 'smtplib',
                'telnetlib', 'xmlrpc', 'pdb', 'profile',
                'crypt', 'getpass', 'resource', 'platform',
                'glob', 'tempfile', 'logging', 'configparser',
                'io', 'struct', 'mmap', 'select', 'asyncio',
                'concurrent', 'pty', 'fcntl', 'termios',
            ]

            for blocked in BLOCKED_IMPORTS:
                # Check various import patterns including spaced-out bypass attempts
                patterns = [
                    f'import {blocked}',
                    f'import  {blocked}',
                    f'from {blocked}',
                    f'from  {blocked}',
                    f"__import__('{blocked}'",
                    f'__import__("{blocked}"',
                    f"__import__ ('{blocked}'",
                    f'__import__ ("{blocked}"',
                ]
                for pattern in patterns:
                    if pattern in code_lower:
                        return False, f'\U0001f512 Security: import "{blocked}" is not allowed. This platform supports matplotlib, numpy, math, and random for learning Python.'

            # Also check normalized version (collapsed spaces)
            for blocked in BLOCKED_IMPORTS:
                if f'import {blocked}' in code_normalized or f'from {blocked}' in code_normalized:
                    return False, f'\U0001f512 Security: import "{blocked}" is not allowed. This platform supports matplotlib, numpy, math, and random for learning Python.'

            # === Block dangerous patterns ===
            BLOCKED_PATTERNS = [
                # Built-in abuse
                ('__import__', '__import__'),
                ('__builtins__', '__builtins__'),
                ('__subclasses__', '__subclasses__'),
                ('__class__', '__class__'),
                ('__bases__', '__bases__'),
                ('__mro__', '__mro__'),
                ('__globals__', '__globals__'),
                ('__code__', '__code__'),
                # Function abuse
                ('globals(', 'globals()'),
                ('locals(', 'locals()'),
                ('vars(', 'vars()'),
                ('getattr(', 'getattr()'),
                ('setattr(', 'setattr()'),
                ('delattr(', 'delattr()'),
                ('exec(', 'exec()'),
                ('eval(', 'eval()'),
                ('compile(', 'compile()'),
                ('breakpoint(', 'breakpoint()'),
                ('exit(', 'exit()'),
                ('quit(', 'quit()'),
                # File & system access
                ('open(', 'open()'),
                ('.read(', '.read()'),
                ('.write(', '.write()'),
                ('.system(', 'os.system()'),
                ('.popen(', 'os.popen()'),
                ('.listdir(', 'os.listdir()'),
                ('.environ', 'os.environ'),
                ('.getcwd(', 'os.getcwd()'),
                ('.chdir(', 'os.chdir()'),
                ('.mkdir(', 'os.mkdir()'),
                ('.rmdir(', 'os.rmdir()'),
                ('.remove(', 'os.remove()'),
                ('.rename(', 'os.rename()'),
                ('.unlink(', 'os.unlink()'),
                # Path access
                ('/opt/', 'file paths'),
                ('/root/', 'file paths'),
                ('/etc/', 'file paths'),
                ('/home/', 'file paths'),
                ('/tmp/', 'file paths'),
                ('/var/', 'file paths'),
                ('/usr/', 'file paths'),
                ('/bin/', 'file paths'),
                ('/sbin/', 'file paths'),
                ('/proc/', 'file paths'),
                ('/dev/', 'file paths'),
                # Sensitive files & commands
                ('.env', '.env files'),
                ('environ', 'environment variables'),
                ('useradd', 'system commands'),
                ('usermod', 'system commands'),
                ('userdel', 'system commands'),
                ('passwd', 'system commands'),
                ('chmod', 'system commands'),
                ('chown', 'system commands'),
                ('chgrp', 'system commands'),
                ('sudoers', 'system files'),
                ('authorized_keys', 'SSH files'),
                ('crontab', 'system commands'),
                ('rm -rf', 'destructive commands'),
                ('rm -r', 'destructive commands'),
                ('mkfifo', 'system commands'),
                ('mknod', 'system commands'),
                # Network
                ('socket(', 'network access'),
                ('connect(', 'network access'),
                ('bind(', 'network access'),
                ('listen(', 'network access'),
                ('urlopen', 'network access'),
                ('http.client', 'network access'),
            ]

            for pattern, description in BLOCKED_PATTERNS:
                if pattern.lower() in code_lower:
                    return False, f'\U0001f512 Security: "{description}" is not allowed in this learning environment.'

            # === Block string encoding tricks ===
            # Catches things like: eval(chr(111)+chr(115)) to spell "os"
            if 'chr(' in code_lower and ('eval' in code_lower or 'exec' in code_lower):
                return False, '\U0001f512 Security: Character encoding tricks are not allowed.'

            # Block base64/hex decode tricks
            if any(trick in code_lower for trick in ['b64decode', 'bytes.fromhex', 'bytearray.fromhex', 'decode(']):
                return False, '\U0001f512 Security: Encoding/decoding tricks are not allowed.'

            return True, None

        async def execute_code(request):
            """Execute Python code with matplotlib support - SANDBOXED"""
            try:
                data = await request.json()
                code = data.get('code', '')
                student_id = data.get('student_id', 'UNKNOWN')

                if not code:
                    return web.json_response({
                        'success': False,
                        'error': 'No code provided'
                    })

                # === SECURITY CHECK ===
                is_safe, error_msg = _check_code_safety(code)
                if not is_safe:
                    print(f"\U0001f6a8 BLOCKED dangerous code from {student_id}: {error_msg}")
                    return web.json_response({
                        'success': False,
                        'error': error_msg
                    })

                import matplotlib
                matplotlib.use('Agg')
                import matplotlib.pyplot as plt
                import io
                import base64
                import sys
                from io import StringIO
                import math
                import random

                old_stdout = sys.stdout
                sys.stdout = StringIO()
                plt.clf()
                plt.close('all')

                # === SECURITY: Restricted builtins only ===
                SAFE_BUILTINS = {
                    'print': print, 'len': len, 'range': range,
                    'int': int, 'float': float, 'str': str, 'bool': bool,
                    'list': list, 'dict': dict, 'tuple': tuple, 'set': set,
                    'abs': abs, 'round': round, 'min': min, 'max': max,
                    'sum': sum, 'sorted': sorted, 'reversed': reversed,
                    'enumerate': enumerate, 'zip': zip, 'map': map, 'filter': filter,
                    'isinstance': isinstance, 'type': type,
                    'input': lambda *a: '',
                    'True': True, 'False': False, 'None': None,
                    'Exception': Exception, 'ValueError': ValueError,
                    'TypeError': TypeError, 'KeyError': KeyError,
                    'IndexError': IndexError, 'ZeroDivisionError': ZeroDivisionError,
                    'RuntimeError': RuntimeError, 'StopIteration': StopIteration,
                    'any': any, 'all': all, 'chr': chr, 'ord': ord,
                    'hex': hex, 'oct': oct, 'bin': bin,
                    'format': format, 'repr': repr, 'hash': hash,
                    'id': id, 'callable': callable, 'iter': iter, 'next': next,
                    'pow': pow, 'divmod': divmod, 'complex': complex,
                    'frozenset': frozenset, 'bytes': bytes, 'bytearray': bytearray,
                    'slice': slice, 'property': property,
                    'staticmethod': staticmethod, 'classmethod': classmethod,
                    'super': super, 'object': object,
                }

                # Safely add __build_class__ for class definitions
                try:
                    if isinstance(__builtins__, dict):
                        if '__build_class__' in __builtins__:
                            SAFE_BUILTINS['__build_class__'] = __builtins__['__build_class__']
                    elif hasattr(__builtins__, '__build_class__'):
                        SAFE_BUILTINS['__build_class__'] = __builtins__.__build_class__
                except Exception:
                    pass
                # Allow importing ONLY safe modules
                ALLOWED_MODULES = {'matplotlib', 'matplotlib.pyplot', 'numpy', 'math', 'random', 'string', 'collections', 'itertools', 'functools', 'datetime', 'decimal', 'fractions', 'statistics', 'json', 'csv', 're', 'copy', 'operator', 'textwrap', 'unicodedata'}
                import builtins as _builtins_module
                _real_import = _builtins_module.__import__
                def _safe_import(name, *args, **kwargs):
                    if name.split('.')[0] not in ALLOWED_MODULES:
                        raise ImportError(f'\U0001f512 Security: import "{name}" is not allowed. Only matplotlib, numpy, math, and random are supported.')
                    return _real_import(name, *args, **kwargs)
                SAFE_BUILTINS['__import__'] = _safe_import
                namespace = {
                    '__builtins__': SAFE_BUILTINS,
                    'plt': plt,
                    'matplotlib': matplotlib,
                    'math': math,
                    'random': random,
                }

                try:
                    import numpy as np
                    namespace['np'] = np
                except ImportError:
                    pass

                output_text = ""
                error_text = None
                image_base64 = None

                try:
                    exec(code, namespace)
                    output_text = sys.stdout.getvalue()

                    if plt.get_fignums():
                        buf = io.BytesIO()
                        plt.savefig(buf, format='png', bbox_inches='tight', dpi=100)
                        buf.seek(0)
                        image_base64 = base64.b64encode(buf.read()).decode('utf-8')
                        buf.close()
                        print(f"✅ Graph captured for {student_id}")

                except Exception as e:
                    error_text = str(e)

                finally:
                    sys.stdout = old_stdout
                    plt.close('all')

                if error_text:
                    return web.json_response({
                        'success': False,
                        'error': error_text,
                        'output': output_text
                    })
                else:
                    return web.json_response({
                        'success': True,
                        'output': output_text,
                        'image': image_base64
                    })

            except Exception as e:
                print(f"❌ Execute error: {e}")
                import traceback
                traceback.print_exc()
                return web.json_response({
                    'success': False,
                    'error': str(e)
                })

        # ====================================================================
        # RESEARCH DATA COLLECTION
        # ====================================================================
        async def log_research_data(request):
            """Collect research behavioral data"""
            try:
                # Capped: one event is small, and this endpoint needs no login.
                if (request.content_length or 0) > 20000:
                    return web.json_response({'status': 'error', 'message': 'too large'}, status=413)
                data = await request.json()
                if not isinstance(data, dict):
                    return web.json_response({'status': 'error', 'message': 'bad request'}, status=400)
                data['server_timestamp'] = datetime.now().isoformat()
                # The id becomes a file name, so letters, digits, - and _ only.
                # '../' in it used to append to any .jsonl file on the server.
                session_id = str(data.get('session_id') or 'unknown')
                if not _re.fullmatch(r'[A-Za-z0-9_-]{1,64}', session_id):
                    return web.json_response({'status': 'error', 'message': 'bad session id'}, status=400)
                filepath = RESEARCH_DATA_DIR / f"{session_id}.jsonl"
                if filepath.exists() and filepath.stat().st_size > 5_000_000:
                    return web.json_response({'status': 'error', 'message': 'session log full'}, status=413)
                line = json.dumps(data)
                if len(line) > 20000:
                    return web.json_response({'status': 'error', 'message': 'too large'}, status=413)
                with open(filepath, 'a', encoding='utf-8') as f:
                    f.write(line + '\n')
                return web.json_response({'status': 'success'})
            except Exception as e:
                print(f"Research logging error: {e}")
                return web.json_response({'status': 'error', 'message': 'server error'}, status=500)

        async def research_stats(request):
            """Get research statistics"""
            stats = {
                'total_sessions': 0,
                'total_interactions': 0,
                'total_code_executions': 0,
                'total_chat_messages': 0,
                'accessibility_features_used': {},
                'courses_accessed': {}
            }
            try:
                for filepath in RESEARCH_DATA_DIR.glob('*.jsonl'):
                    with open(filepath, 'r', encoding='utf-8') as f:
                        for line in f:
                            try:
                                data = json.loads(line.strip())
                                stats['total_sessions'] += 1
                                interactions = data.get('interactions', [])
                                stats['total_interactions'] += len(interactions)
                                for interaction in interactions:
                                    event_type = interaction.get('event_type', '')
                                    if 'code_executed' in str(interaction.get('data', {})):
                                        stats['total_code_executions'] += 1
                                    elif event_type == 'chat_message_sent':
                                        stats['total_chat_messages'] += 1
                                    elif event_type == 'accessibility_feature':
                                        feature = interaction.get('data', {}).get('feature', 'unknown')
                                        stats['accessibility_features_used'][feature] = \
                                            stats['accessibility_features_used'].get(feature, 0) + 1
                                    course = interaction.get('current_course')
                                    if course:
                                        stats['courses_accessed'][course] = \
                                            stats['courses_accessed'].get(course, 0) + 1
                            except Exception:
                                continue
                return web.json_response(stats)
            except Exception as e:
                print(f"Stats error: {e}")
                return web.json_response(stats)

        async def export_research_data(request):
            """Export all research data"""
            try:
                all_data = []
                for filepath in RESEARCH_DATA_DIR.glob('*.jsonl'):
                    with open(filepath, 'r', encoding='utf-8') as f:
                        for line in f:
                            try:
                                data = json.loads(line.strip())
                                all_data.append(data)
                            except:
                                continue
                return web.json_response({'total_sessions': len(all_data), 'data': all_data})
            except Exception as e:
                print(f"Export error: {e}")
                return web.json_response({'status': 'error', 'message': str(e)}, status=500)

        # ====================================================================
        # REGISTER ALL ROUTES
        # ====================================================================
        app.router.add_get('/googleb2bf07109a72196e.html', serve_google_verify)
        app.router.add_get('/favicon.ico', serve_favicon)
        async def serve_robots(request):
            robots_path = Path(__file__).parent / 'static' / 'robots.txt'
            try:
                with open(robots_path, 'r') as f:
                    return web.Response(text=f.read(), content_type='text/plain')
            except FileNotFoundError:
                return web.Response(text="User-agent: *\nAllow: /", content_type='text/plain')

        async def serve_about(request):
            about_path = Path(__file__).parent / 'templates' / 'about.html'
            try:
                with open(about_path, 'r', encoding='utf-8') as f:
                    return web.Response(text=f.read(), content_type='text/html')
            except FileNotFoundError:
                return web.Response(text="About page not found.", status=404)

        async def serve_try(request):
            """One complete lesson, open to anyone: the demo the site is sold on.

            Deliberately NOT behind the login. Everything else stays gated; a
            visual product needs one thing a stranger can see before deciding
            whether to make an account. It costs nothing to serve because the
            lesson makes no calls of its own.

            Somebody who is already signed in sees the same lesson and a
            different set of doors. Selling an account to a person who has
            one reads as a page that does not know who it is talking to, and
            it also hid the only route to the other sixteen lessons. The page
            carries both sets, marked GUEST and MEMBER, and whichever does
            not apply is taken out here rather than hidden with CSS: it never
            reaches the browser, so there is nothing to flash and nothing to
            read in the source.
            """
            try_path = Path(__file__).parent / 'templates' / 'try.html'
            try:
                with open(try_path, 'r', encoding='utf-8') as f:
                    html = f.read()
            except FileNotFoundError:
                return web.Response(text="Demo page not found.", status=404)

            drop = 'MEMBER' if not current_user_id(request) else 'GUEST'
            html = _re.sub(r'<!--' + drop + r'-->.*?<!--/' + drop + r'-->',
                           '', html, flags=_re.S)
            # and the markers of the half that stayed, so the page does not
            # explain its own machinery to anyone reading the source
            html = _re.sub(r'\s*<!--/?(?:GUEST|MEMBER)-->', '', html)

            # Signed in, the seventeen rows stop being a menu you cannot
            # order from. They are one list in the template, carrying the
            # program each one opens; here they become links to it. For a
            # visitor they stay plain text on purpose - only the first
            # lesson is theirs, and a row that looks clickable and is not
            # is worse than a row that never claimed to be.
            if drop == 'GUEST':
                html = _re.sub(
                    r'<div data-prog="([^"]+)" class="lesson([^"]*)">(.*?)</div>',
                    lambda m: '<a class="lesson%s" href="/lessons?prog=%s">%s</a>'
                             % (m.group(2), m.group(1), m.group(3)),
                    html, flags=_re.S)
            return web.Response(text=html, content_type='text/html')

        async def serve_accessibility(request):
            """The accessibility controls, described in one place.

            Public on purpose: somebody deciding whether this platform is
            usable for them should not have to make an account to find out.
            """
            path = Path(__file__).parent / 'templates' / 'accessibility.html'
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    return web.Response(text=f.read(), content_type='text/html')
            except FileNotFoundError:
                return web.Response(text="Accessibility page not found.", status=404)

        async def serve_schools(request):
            """For educators who want to try SYNAPSE with a group: how to get
            in touch, and what can be looked at without an account. Deliberately
            short: a public page made of unfinished legal placeholders would
            reassure nobody, least of all a school."""
            path = Path(__file__).parent / 'templates' / 'schools.html'
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    return web.Response(text=f.read(), content_type='text/html')
            except FileNotFoundError:
                return web.Response(text="Schools page not found.", status=404)

        async def serve_mcp(request):
            mcp_path = Path(__file__).parent / 'templates' / 'mcp.html'
            try:
                with open(mcp_path, 'r', encoding='utf-8') as f:
                    return web.Response(text=f.read(), content_type='text/html')
            except FileNotFoundError:
                return web.Response(text="MCP page not found.", status=404)

        async def serve_privacy(request):
            privacy_path = Path(__file__).parent / 'templates' / 'privacy.html'
            try:
                with open(privacy_path, 'r', encoding='utf-8') as f:
                    return web.Response(text=f.read(), content_type='text/html')
            except FileNotFoundError:
                return web.Response(text="Privacy page not found.", status=404)

        async def serve_terms(request):
            terms_path = Path(__file__).parent / 'templates' / 'terms.html'
            try:
                with open(terms_path, 'r', encoding='utf-8') as f:
                    return web.Response(text=f.read(), content_type='text/html')
            except FileNotFoundError:
                return web.Response(text="Terms page not found.", status=404)

        async def serve_cookies(request):
            cookies_path = Path(__file__).parent / 'templates' / 'cookies.html'
            try:
                with open(cookies_path, 'r', encoding='utf-8') as f:
                    return web.Response(text=f.read(), content_type='text/html')
            except FileNotFoundError:
                return web.Response(text="Cookie page not found.", status=404)

        async def serve_flashcards(request):
            user_cookie = current_user_id(request)
            participant_code = request.query.get('participant') or request.cookies.get('participant_code')
            if not user_cookie and not participant_code and not admin_key_ok(request):
                raise web.HTTPFound('/login?next=/flashcards')
            return web.FileResponse('templates/flashcards.html')

        async def serve_lessons(request):
            """Every lesson, not the one the demo shows.

            The player was reachable only as a file under /static, which
            meant that from inside the product there was no way to it at
            all: the one button that pointed at lessons pointed at /try,
            and /try runs the player with ?only=walk:each. Sixteen lessons
            and the comparison view were built, shipped, and unreachable.
            """
            if not current_user_id(request):
                raise web.HTTPFound('/login?next=/lessons')
            page = Path(__file__).parent / 'static' / 'lessons' / 'algorithm-player.html'
            try:
                with open(page, 'r', encoding='utf-8') as f:
                    page_html = f.read()
                # Added here and not in the file: the same file is what /try
                # shows inside its frame, where this chrome would be a second
                # navbar inside a public demo.
                page_html = page_html.replace('</body>', LESSONS_CHROME + '</body>', 1)
                return web.Response(text=page_html, content_type='text/html')
            except FileNotFoundError:
                return web.Response(text="Lessons not found.", status=404)

        async def serve_drawer(request):
            """The drawer: where a learner's own visualisations live.

            Login only - deliberately without the participant_code / admin_key
            doors the older tool pages carry, since this is personal work rather
            than an anonymous exercise.
            """
            if not current_user_id(request):
                raise web.HTTPFound('/login?next=/drawer')
            drawer_path = Path(__file__).parent / 'templates' / 'drawer.html'
            try:
                with open(drawer_path, 'r', encoding='utf-8') as f:
                    return web.Response(text=f.read(), content_type='text/html')
            except FileNotFoundError:
                return web.Response(text="Drawer page not found.", status=404)

        async def serve_spot_the_bug(request):
            user_cookie = current_user_id(request)
            participant_code = request.query.get('participant') or request.cookies.get('participant_code')
            if not user_cookie and not participant_code and not admin_key_ok(request):
                raise web.HTTPFound('/login?next=/spot-the-bug')
            return web.FileResponse('templates/spot_the_bug.html')

        app.router.add_get('/about', serve_about)
        app.router.add_get('/try', serve_try)
        app.router.add_get('/accessibility', serve_accessibility)
        app.router.add_get('/schools', serve_schools)
        app.router.add_get('/mcp', serve_mcp)
        app.router.add_get('/privacy', serve_privacy)
        app.router.add_get('/terms', serve_terms)
        app.router.add_get('/cookies', serve_cookies)
        app.router.add_get('/robots.txt', serve_robots)
        app.router.add_get('/sitemap.xml', serve_sitemap)
        app.router.add_get('/', serve_landing)
        app.router.add_get('/app', serve_app)
        app.router.add_get('/course', serve_course)
        app.router.add_get("/course/java-security", serve_java_security_course)
        app.router.add_get('/flashcards', serve_flashcards)
        app.router.add_get('/spot-the-bug', serve_spot_the_bug)
        app.router.add_get('/lessons', serve_lessons)
        app.router.add_get('/drawer', serve_drawer)

        # API endpoints
        app.router.add_post('/api/chat', chat_ai)
        app.router.add_post('/api/execute', execute_code)

        # Research validation & checks (CRITICAL!)
        app.router.add_post('/api/research/validate_code', validate_participant_code)
        app.router.add_get("/api/research/participant", get_participant_info)
        app.router.add_post('/api/research/check_nickname', check_nickname_availability)
        app.router.add_post('/api/research/check_email', check_email_availability)
        app.router.add_post('/api/research/recover_code_nickname', recover_code_by_nickname)
        app.router.add_post('/api/research/recover_code', recover_code_by_email)
 
        # Research data collection
        app.router.add_post('/api/research/log', log_research_data)
        app.router.add_get('/api/research/stats', research_stats)
        app.router.add_get('/api/research/export', export_research_data)

        print("✅ SUCCESS: Core routes registered")
        print("   -> /api/research/check_nickname - Real-time nickname check")
        print("   -> /api/research/check_email - Real-time email check")
        print("   -> /api/research/validate_code - Participant login")
        print("   -> /api/research/recover_code - Code recovery")

        # Setup other routes
        setup_routes(app)
        setup_course_routes(app)
        setup_advanced_routes(app)
        setup_research_api_routes(app)
        setup_auth_routes(app)
        setup_research_dashboard_routes(app)
        setup_metrics_routes(app)
        setup_quiz_routes(app)
        setup_drawer_routes(app)

        # ====================================================================
        # SYNAPSE LABS - Multi-tenant isolated container system
        # ====================================================================
        try:
            from web.labs_handlers import register_lab_routes
            from labs.proxy import register_proxy_routes
            from labs.cleanup_worker import start_cleanup_worker, stop_cleanup_worker

            register_lab_routes(app)
            register_proxy_routes(app)
            app.on_startup.append(start_cleanup_worker)
            app.on_cleanup.append(stop_cleanup_worker)
            print("✅ SUCCESS: SYNAPSE Labs registered (isolated ShopSecure containers)")
            print("   -> POST /api/labs/start, GET /api/labs/status, POST /api/labs/end, POST /api/labs/extend")
            print("   -> Proxy: /labs/{lab_type}/{token}/*")
            print("   -> Cleanup worker: active (60s interval)")
        except Exception as e:
            import traceback
            print(f"❌ ERROR: Failed to register SYNAPSE Labs: {e}")
            traceback.print_exc()

        # CORS setup
        # Only our own site may read answers with the visitor's cookies.
        # This used to be "*", which aiohttp_cors answers by echoing back any
        # Origin with Allow-Credentials, so any website could read them.
        cors = cors_setup(app, defaults={
            "https://synapse-course.com": ResourceOptions(
                allow_credentials=True,
                expose_headers="*",
                allow_headers="*",
                allow_methods="*"
            )
        })
        for route in list(app.router.routes()):
            # Skip lab proxy routes (they use '*' method which CORS can't wrap)
            try:
                resource_path = str(getattr(route.resource, 'canonical', ''))
            except Exception:
                resource_path = ''
            if resource_path.startswith('/labs/'):
                continue
            try:
                cors.add(route)
            except ValueError:
                # Route already has handler for all methods (e.g. '*' catch-all)
                pass

        # Start server
        runner = web.AppRunner(app)
        await runner.setup()
        http_port = 6281
        site = web.TCPSite(runner, "127.0.0.1", http_port)
        await site.start()
        external_ip = get_external_ip()

        print("=" * 70)
        print("\U0001f98b SYNAPSE EDUCATIONAL PLATFORM - READY")
        print("=" * 70)
        print(f"Local:    http://127.0.0.1:{http_port}/")
        if external_ip != "unknown":
            print(f"External: http://{external_ip}:{http_port}/")
        print("=" * 70)
        print("\u2728 EDUCATIONAL FEATURES:")
        print("   - Multi-LLM orchestration (Claude, GPT-4, Gemini)")
        print("   - Neurodivergent learning adaptations")
        print("   - Real-time nickname/email validation")
        print("   - Matplotlib task with auto-scoring")
        print("   - Research data collection")
        print("   - \U0001f512 SANDBOXED code execution")
        print("=" * 70)

        await asyncio.Event().wait()

    async def run_mcp_server(self):
        """Run the MCP protocol server"""
        if not MCP_AVAILABLE:
            print("ERROR: MCP not available. Install: pip install mcp>=1.0.0")
            return
        load_dotenv()
        Base.metadata.create_all(bind=engine)
        await self._init_advanced_tools_once()

        print("=" * 70)
        print("\U0001f98b SYNAPSE - MCP MODE")
        print("=" * 70)

        async with stdio_server() as (read_stream, write_stream):
            await self.mcp_server.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name="synapse-educational-tutor",
                    server_version="2.0.0",
                    capabilities={"tools": {}}
                )
            )


async def main():
    """Main entry point"""
    if len(sys.argv) > 1 and sys.argv[1] == "--mcp":
        server = HybridEducationalServer()
        await server.run_mcp_server()
    else:
        server = HybridEducationalServer()
        await server.run_web_server()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\U0001f98b Shutting down Synapse...")
    except Exception as e:
        print(f"❌ Server error: {e}")
        sys.exit(1)
