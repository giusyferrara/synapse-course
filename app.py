import asyncio
import os
import sys
import socket
import requests
import json
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
from web.course_handlers import setup_course_routes
from web.advanced_handlers import setup_advanced_routes
from database.config import Base, engine, SessionLocal
from database.models import Student, LearningSession, AIResponse, Feedback, ResearchParticipant
from web.metrics_handlers import setup_metrics_routes
from web.auth_handlers import setup_auth_routes
from web.research_handlers import setup_research_routes as setup_research_api_routes
from web.quiz_handlers import setup_quiz_routes
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

        app = web.Application()
        app["tutor"] = self.tutor
        print("✅ SUCCESS: Tutor instance ready")

        # ====================================================================
        # ICONS HANDLER
        # ====================================================================
        async def serve_icon(request):
            """Serve icon files from /icons/ directory"""
            filename = request.match_info['filename']
            icon_path = Path(__file__).parent / 'icons' / filename

            if not icon_path.exists():
                print(f"❌ ERROR: Icon not found: {filename}")
                return web.Response(status=404, text=f'Icon not found: {filename}')

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
            if not request.cookies.get('synapse_user'):
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
            user_cookie = request.cookies.get('synapse_user')
            participant_code = request.query.get('participant') or request.cookies.get('participant_code')
            admin_key = request.query.get('admin')
            if not user_cookie and not participant_code and admin_key != os.getenv('ADMIN_KEY', ''):
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
            user_cookie = request.cookies.get('synapse_user')
            participant_code = request.query.get('participant') or request.cookies.get('participant_code')
            admin_key = request.query.get('admin')
            if not user_cookie and not participant_code and admin_key != os.getenv('ADMIN_KEY', ''):
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
                        print(f"⚠️  Email TAKEN: '{email}' → {existing.participant_code}")
                        return web.json_response({
                            'available': False,
                            'participant_code': existing.participant_code,
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

                    # Use system_prompt from frontend if provided, otherwise use default
                    frontend_prompt = data.get('system_prompt', '')
                    SHOPSECURE_PROMPT = frontend_prompt if frontend_prompt else (
                        'You are an expert cybersecurity tutor helping a student learn web security through ShopSecure (a practice e-commerce app with 11 vulnerabilities). The student is doing a hands-on research task and you support them with patient, scaffolded guidance that adapts to how much help they need. '
                        ' '
                        'CONCEPTUAL KNOWLEDGE you can explain freely whenever asked: '
                        'Secure Design Principles (Saltzer-Schroeder 1975): least privilege, separation of duties, defence in depth, fail-safe defaults, economy of mechanism, complete mediation, open design (Kerckhoffs), least common mechanism, psychological acceptability, weakest link. '
                        'CWE-754/CWE-209 Exception Handling: auth bypass via loggedIn=true with empty catch on null password; info leakage via stack traces. Fixes: deny-by-default, specific exception types, generic user errors with reference ID. '
                        'CWE-89 SQL Injection: tautology bypass and numeric injection concepts; fix with parameterised queries. '
                        'CWE-78 Command Injection: shell metacharacters; fix with subprocess list-form and whitelist. '
                        'CWE-79 XSS: reflected vs stored; fix with output encoding and Content Security Policy. '
                        'CWE-352 CSRF: the browser automatically attaches the session cookie to cross-site requests, so a request initiated by attacker-controlled content executes with the victim authority. Fix: per-session CSRF token, SameSite cookies. In ShopSecure the realistic scenario chains CSRF with Stored XSS: the attacker plants a hidden iframe in their own profile address field that targets /shop/csrf-demo with to= and amount= query parameters; when an admin or any authenticated user views that profile, the iframe loads and triggers a transfer with their session cookie. '
                        'CWE-614/CWE-384 Session Management: cookie flags HttpOnly/Secure/SameSite; session ID generation; regeneration after login. '
                        'CWE-22 Path Traversal: ../ escape, replace-bypass via ....//; fix with canonical-path verification. '
                        'CWE-502 Insecure Deserialisation: pickle __reduce__ executes on loads(); fix with JSON or restricted unpicklers. '
                        ' '
                        'GRADUATED HELP — track where you are with each student and progress through these levels naturally: '
                        ' '
                        'LEVEL 1 — EXPLORATION (first contact with a vulnerability): '
                        'Ask one diagnostic question that points to the primitive. Examples: "what does the server do with the filename you send?", "where in ShopSecure can a regular user write text that an admin will later view?". Goal: trigger the student is own reasoning. '
                        ' '
                        'LEVEL 2 — CONCEPTUAL HINT (student tried something and got stuck): '
                        'Give the conceptual mechanism in plain language without code. Examples for CSRF: "the browser sends the victim cookie automatically with any request that originates from the victim browser, so if you can make the victim browser issue the request, the server cannot tell it apart from a legitimate one". Name the HTML element or technique that would work without writing it. '
                        ' '
                        'LEVEL 3 — STRUCTURAL HINT (student understands the concept but cannot recall the syntax): '
                        'Give the structure of the solution as a skeleton with placeholders, not as runnable code. Example for CSRF: "you need an iframe with src pointing to the demo endpoint, and the demo endpoint takes two query parameters — one for the recipient username and one for the amount". This is legitimate help: technical syntax is consulted, not memorised, and asking the AI for syntactic structure is exactly how developers use AI assistants in practice. '
                        ' '
                        'LEVEL 4 — WORKED EXAMPLE (student has tried the structural hint and is still blocked, or asks for a complete worked example to learn from): '
                        'Provide a complete working snippet, but always frame it as "here is one way it can be written — read it and tell me which line is doing what" rather than "here is the answer". Then ask the student to explain back at least one element of the snippet so the disclosure becomes a learning moment instead of a shortcut. This level fulfils FR9 of the platform spec, which permits stepwise disclosure when extended scaffolding fails. '
                        ' '
                        'BEHAVIOUR RULES around the levels: '
                        '(A) The student is here to think, not to be tested on memory. Asking for syntax that nobody memorises (iframe attribute order, pickle __reduce__ shape, exact CWE identifier) is a legitimate request and goes straight to Level 3 or Level 4. '
                        '(B) Asking "what is this vulnerability" or "why does this fix work" is conceptual and gets a full clear answer (these questions sit outside the level system). '
                        '(C) When you advance a level, briefly say what you are doing: "you have been thinking about this for a bit, let me show you the structure". This signals to the student that escalation is normal, not failure. '
                        '(D) Never refuse help. Frustration that drives the student to abandon the task is the worst outcome — worse than disclosing a worked example. If a student is clearly running out of patience, advance to Level 4 promptly. '
                        '(E) When the student succeeds, celebrate, help them name the CWE and OWASP category, and ask them what defence would have prevented it — this is where the real learning consolidates. '
                        '(F) Use the student name when you have it. Warm tone, simple analogies (one sentence max), never judge. Always respond in the same language the student writes in. '
                        ' '
                        'STYLE: maximum 4-5 lines per response. One concept or one question or one snippet at a time. Code snippets when given are short and commented. Celebrate small wins.'
                    )

                    # Build messages with chat history for context
                    chat_history = data.get('chat_history', [])
                    extra_context = data.get('extra_context', '')
                    messages = []
                    for msg in chat_history:
                        if msg.get('role') in ('user', 'assistant') and msg.get('content'):
                            messages.append({'role': msg['role'], 'content': msg['content']})
                    # Add current message with findings context
                    current_msg = message
                    if extra_context:
                        current_msg = message + '\n\n' + extra_context
                    messages.append({'role': 'user', 'content': current_msg})
                    response = await router.get_chat_response(SHOPSECURE_PROMPT, messages)
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
                data = await request.json()
                data['server_timestamp'] = datetime.now().isoformat()
                session_id = data.get('session_id', 'unknown')
                filepath = RESEARCH_DATA_DIR / f"{session_id}.jsonl"
                with open(filepath, 'a', encoding='utf-8') as f:
                    f.write(json.dumps(data) + '\n')
                return web.json_response({'status': 'success'})
            except Exception as e:
                print(f"Research logging error: {e}")
                return web.json_response({'status': 'error', 'message': str(e)}, status=500)

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

        async def serve_flashcards(request):
            user_cookie = request.cookies.get('synapse_user')
            participant_code = request.query.get('participant') or request.cookies.get('participant_code')
            admin_key = request.query.get('admin')
            if not user_cookie and not participant_code and admin_key != os.getenv('ADMIN_KEY', ''):
                raise web.HTTPFound('/login?next=/flashcards')
            return web.FileResponse('templates/flashcards.html')

        app.router.add_get('/about', serve_about)
        app.router.add_get('/robots.txt', serve_robots)
        app.router.add_get('/sitemap.xml', serve_sitemap)
        app.router.add_get('/', serve_landing)
        app.router.add_get('/app', serve_app)
        app.router.add_get('/course', serve_course)
        app.router.add_get("/course/java-security", serve_java_security_course)
        app.router.add_get('/flashcards', serve_flashcards)

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
        cors = cors_setup(app, defaults={
            "*": ResourceOptions(
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
