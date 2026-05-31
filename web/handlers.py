# File: web/handlers.py

from .email_utils import send_email
import os
from aiohttp import web
import json
from database.config import SessionLocal
from database.models import Feedback, Student

# --- Funzione per Configurare tutte le Rotte ---
def setup_routes(app):
    app.router.add_static('/static/', path='static', name='static')
    app.router.add_get("/", handle_mcp_inspector)
    app.router.add_get("/feedback", handle_feedback_form)
    app.router.add_get("/tools", handle_advanced_tools)  # NEW: Advanced tools page
    app.router.add_get("/health", handle_health)

    app.router.add_post("/submit_feedback", handle_submit_feedback)
    app.router.add_post("/analyze", handle_analyze)
    app.router.add_post("/explain", handle_explain)
    app.router.add_post("/suggest_fixes", handle_suggest_fixes)
    app.router.add_post("/run_tests", handle_run_tests)
    app.router.add_post("/generate_tests", handle_generate_tests)
    app.router.add_post("/secure_review", handle_secure_review)
    app.router.add_post("/visual_explanation", handle_visual_explanation)
    app.router.add_post("/chat_followup", handle_chat_followup)
    app.router.add_post("/test_ai", handle_test_ai)
    
    # Advanced Tools API Routes
    app.router.add_post("/api/create_graph", handle_create_graph)
    app.router.add_get("/api/graph_tutorial/{graph_type}", handle_graph_tutorial)
    app.router.add_get("/api/python_docs/{function_name}", handle_python_docs)
    app.router.add_get("/api/encryption_tutorial/{method}", handle_encryption_tutorial)
    app.router.add_post("/api/encrypt_demo", handle_encrypt_demo)
    
    print("✅ Web routes configured.")
    print("✅ Advanced tool routes added!")

# --- Handler per le Pagine HTML ---

async def handle_mcp_inspector(request):
    try:
        with open("templates/index.html", "r", encoding="utf-8") as f:
            return web.Response(text=f.read(), content_type="text/html")
    except FileNotFoundError:
        return web.Response(text="<h1>Error: index.html not found.</h1>", status=500, content_type="text/html")

async def handle_feedback_form(request):
    try:
        with open("templates/feedback.html", "r", encoding="utf-8") as f:
            return web.Response(text=f.read(), content_type="text/html")
    except FileNotFoundError:
        return web.Response(text="<h1>Error: feedback.html not found.</h1>", status=500, content_type="text/html")

async def handle_advanced_tools(request):
    """NEW: Serve advanced learning tools page"""
    if not request.cookies.get('synapse_user'):
        raise web.HTTPFound('/login?next=/tools')
    try:
        with open("templates/advanced_tools.html", "r", encoding="utf-8") as f:
            return web.Response(text=f.read(), content_type="text/html")
    except FileNotFoundError:
        return web.Response(text="<h1>Error: advanced_tools.html not found.</h1>", status=500, content_type="text/html")

# --- Handler per le API (Azioni dei Pulsanti) ---

async def handle_health(request):
    return web.Response(text="Enhanced Security Tutor is running!")

async def handle_submit_feedback(request):
    db = SessionLocal()
    try:
        data = await request.json()
        student_id_str = data.get("student_id", "anonymous_feedback_user")
        student = db.query(Student).filter(Student.student_id == student_id_str).first()

        new_feedback = Feedback(
            student_record_id=student.id if student else None,
            most_helpful=data.get("most_helpful"),
            improvements=data.get("improvements"),
            background=data.get("background")
        )
        db.add(new_feedback)
        db.commit()
        # Send email notification (non-blocking on failure)
        try:
            to_email = os.environ.get("FEEDBACK_TO_EMAIL", "synapse_4AI@outlook.com")
            html_body = f"""<h2>New SYNAPSE Feedback</h2>
<p><strong>Student ID:</strong> {student_id_str}</p>
<p><strong>Most helpful:</strong><br>{data.get("most_helpful") or "—"}</p>
<p><strong>Improvements:</strong><br>{data.get("improvements") or "—"}</p>
<p><strong>Background:</strong><br>{data.get("background") or "—"}</p>"""
            text_body = f"""New SYNAPSE Feedback

Student ID: {student_id_str}
Most helpful: {data.get("most_helpful") or "—"}
Improvements: {data.get("improvements") or "—"}
Background: {data.get("background") or "—"}"""
            send_email(to_email, "New SYNAPSE feedback received", html_body, text_body)
        except Exception as e:
            print(f"[!] Feedback email notification failed: {e}")
        return web.Response(text="Feedback received, thank you!")
    except Exception as e:
        db.rollback()
        return web.Response(text=f"Error: {e}", status=500)
    finally:
        db.close()

async def handle_analyze(request):
    data = await request.json()
    tutor = request.app["tutor"]
    result = await tutor.tool_execute_python_debug(data)
    return web.json_response({"response": result})

async def handle_explain(request):
    data = await request.json()
    tutor = request.app["tutor"]
    result = await tutor.tool_explain_code(data)
    return web.json_response({"response": result})

async def handle_suggest_fixes(request):
    data = await request.json()
    tutor = request.app["tutor"]
    result = await tutor.tool_suggest_fixes(data)
    return web.json_response({"response": result})

async def handle_run_tests(request):
    data = await request.json()
    tutor = request.app["tutor"]
    result = await tutor.tool_run_tests(data)
    return web.json_response({"response": result})

async def handle_generate_tests(request):
    data = await request.json()
    tutor = request.app["tutor"]
    result = await tutor.tool_generate_tests(data)
    return web.json_response({"response": result})

async def handle_visual_explanation(request):
    data = await request.json()
    tutor = request.app["tutor"]
    result = await tutor.tool_visual_guide(data)
    return web.json_response({"response": result})

async def handle_secure_review(request):
    data = await request.json()
    tutor = request.app["tutor"]
    result = await tutor.tool_secure_review(data)
    return web.json_response({"response": result})

async def handle_chat_followup(request):
    try:
        data = await request.json()
        tutor = request.app["tutor"]
        result = await tutor.tool_chat_followup(data)
        return web.json_response({"response": result})
    except Exception as e:
        return web.json_response({"response": f"Chat error: {e}"}, status=500)

async def handle_test_ai(request):
    data = await request.json()
    tutor = request.app["tutor"]
    result = await tutor.tool_test_ai(data)
    return web.json_response({"response": result})

# --- Advanced Tools Handlers ---

async def handle_create_graph(request):
    """Create educational graph"""
    try:
        data = await request.json()
        tutor = request.app['tutor']
        result = await tutor.tool_create_graph(data)
        return web.json_response({"result": result})
    except Exception as e:
        return web.json_response({"error": str(e)}, status=500)

async def handle_graph_tutorial(request):
    """Get graph tutorial"""
    try:
        graph_type = request.match_info['graph_type']
        tutor = request.app['tutor']
        result = await tutor.tool_graph_tutorial({'graph_type': graph_type})
        return web.json_response({"result": result})
    except Exception as e:
        return web.json_response({"error": str(e)}, status=500)

async def handle_python_docs(request):
    """Get Python function documentation"""
    try:
        function_name = request.match_info['function_name']
        tutor = request.app['tutor']
        result = await tutor.tool_python_docs({'function_name': function_name})
        return web.json_response({"result": result})
    except Exception as e:
        return web.json_response({"error": str(e)}, status=500)

async def handle_encryption_tutorial(request):
    """Get encryption tutorial"""
    try:
        method = request.match_info['method']
        tutor = request.app['tutor']
        result = await tutor.tool_encryption_tutorial({'method': method})
        return web.json_response({"result": result})
    except Exception as e:
        return web.json_response({"error": str(e)}, status=500)

async def handle_encrypt_demo(request):
    """Demonstrate encryption"""
    try:
        data = await request.json()
        tutor = request.app['tutor']
        result = await tutor.tool_encrypt_demo(data)
        return web.json_response({"result": result})
    except Exception as e:
        return web.json_response({"error": str(e)}, status=500)
