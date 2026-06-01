"""
web/quiz_handlers.py — Adaptive Vulnerability Assessment Quiz (Milestone 4).

Routes (all behind the existing session/participant auth gating):
  GET  /quiz                 -> the quiz page (redirects to /login if not authed)
  GET  /api/quiz/next        -> adaptively selected questions (answer key stripped)
  POST /api/quiz/answer      -> grade, persist attempt + review, return static feedback
  POST /api/quiz/explain     -> on-demand AI "explain why" (executor; rate-limited; cached)
  POST /api/quiz/hint        -> on-demand AI hint (executor; rate-limited; cached)
  GET  /api/quiz/progress    -> per-skill accuracy for the logged-in student

Design:
  * Identity = the normal app login: 'synapse_user' cookie, else 'participant_code'.
    Progress (QuizAttempt/QuizReview) is keyed by that, as ordinary app telemetry.
  * The bank is loaded once at startup into app['quiz_bank'].
  * /next NEVER sends the correct flag / explanation to the client — grading is
    server-side from the authoritative bank.
  * AI explain/hint reuse mcp_coordinator (lazy, built on first use) and run in an
    executor so the aiohttp event loop is never blocked. Rate-limit -> HTTP 429.
"""
import asyncio
import os

from aiohttp import web

from database.config import SessionLocal
from quiz import quiz_engine
from quiz.quiz_ai import RateLimitError


# --------------------------------------------------------------------------
# Identity / gating
# --------------------------------------------------------------------------
def _student_id(request):
    """Return a stable student id for the logged-in user, or None."""
    uid = request.cookies.get("synapse_user")
    if uid:
        return f"user:{uid}"
    pc = request.query.get("participant") or request.cookies.get("participant_code")
    if pc:
        return f"participant:{pc}"
    return None


def _require_student(request):
    sid = _student_id(request)
    if sid is None:
        raise web.HTTPUnauthorized(
            text='{"error": "Please log in to use the quiz."}',
            content_type="application/json",
        )
    return sid


# --------------------------------------------------------------------------
# Serialisation — strip the answer key before sending to the browser
# --------------------------------------------------------------------------
def _client_question(q):
    return {
        "id": q["id"],
        "category": q["category"],
        "skill_tag": q["skill_tag"],
        "owasp": q.get("owasp"),
        "severity": q.get("severity"),
        "difficulty": q["difficulty"],
        "prompt": q["prompt"],
        "code_snippet": q.get("code_snippet"),
        # options WITHOUT the 'correct' flag:
        "options": [{"id": o["id"], "text": o["text"]} for o in q["options"]],
    }


# --------------------------------------------------------------------------
# Lazy AI service (reuses mcp_coordinator; built only on first explain/hint)
# --------------------------------------------------------------------------
def _get_quiz_ai(app):
    svc = app.get("quiz_ai")
    if svc is None:
        from mcp_coordinator import MCPCoordinator
        coord = app.get("mcp")
        if coord is None:
            coord = MCPCoordinator()
            app["mcp"] = coord
        svc = coord.get_quiz_ai()
        app["quiz_ai"] = svc
    return svc


# --------------------------------------------------------------------------
# Route setup
# --------------------------------------------------------------------------
def setup_quiz_routes(app):
    app["quiz_bank"] = quiz_engine.load_bank()

    async def serve_quiz_page(request):
        admin_key = request.query.get("admin", "")
        if _student_id(request) is None and admin_key != os.getenv("ADMIN_KEY", ""):
            raise web.HTTPFound("/login?next=/quiz")
        return web.FileResponse("templates/quiz.html")

    async def quiz_next(request):
        sid = _require_student(request)
        try:
            n = int(request.query.get("n", "10"))
        except ValueError:
            n = 10
        n = max(1, min(n, 20))
        bank = request.app["quiz_bank"]
        db = SessionLocal()
        try:
            questions = quiz_engine.select_quiz(db, bank, sid, n=n)
        finally:
            db.close()
        return web.json_response({"questions": [_client_question(q) for q in questions]})

    async def quiz_answer(request):
        sid = _require_student(request)
        data = await request.json()
        qid = data.get("question_id")
        chosen = data.get("chosen_option")
        time_ms = data.get("time_ms")
        bank = request.app["quiz_bank"]
        if bank.get(qid) is None:
            return web.json_response({"error": "unknown question"}, status=400)
        db = SessionLocal()
        try:
            result = quiz_engine.record_answer(db, bank, sid, qid, chosen, time_ms=time_ms)
            db.commit()
        except ValueError as e:
            db.rollback()
            return web.json_response({"error": str(e)}, status=400)
        finally:
            db.close()
        return web.json_response(result)

    async def quiz_explain(request):
        sid = _require_student(request)
        data = await request.json()
        qid = data.get("question_id")
        chosen = data.get("chosen_option")
        question = request.app["quiz_bank"].get(qid)
        if question is None:
            return web.json_response({"error": "unknown question"}, status=400)
        try:
            svc = _get_quiz_ai(request.app)
        except Exception as e:
            return web.json_response({"error": f"AI unavailable: {e}"}, status=503)
        loop = asyncio.get_event_loop()
        try:
            result = await loop.run_in_executor(None, svc.explain, sid, question, chosen)
        except RateLimitError as e:
            return web.json_response({"error": str(e), "rate_limited": True}, status=429)
        except Exception as e:
            return web.json_response({"error": f"AI error: {e}"}, status=502)
        return web.json_response(result)

    async def quiz_hint(request):
        sid = _require_student(request)
        data = await request.json()
        qid = data.get("question_id")
        question = request.app["quiz_bank"].get(qid)
        if question is None:
            return web.json_response({"error": "unknown question"}, status=400)
        try:
            svc = _get_quiz_ai(request.app)
        except Exception as e:
            return web.json_response({"error": f"AI unavailable: {e}"}, status=503)
        loop = asyncio.get_event_loop()
        try:
            result = await loop.run_in_executor(None, svc.hint, sid, question)
        except RateLimitError as e:
            return web.json_response({"error": str(e), "rate_limited": True}, status=429)
        except Exception as e:
            return web.json_response({"error": f"AI error: {e}"}, status=502)
        return web.json_response(result)

    async def quiz_progress(request):
        sid = _require_student(request)
        bank = request.app["quiz_bank"]
        db = SessionLocal()
        try:
            seen, skill_acc, recent_acc, total = quiz_engine._history(db, sid)
        finally:
            db.close()
        bank_skills = {s: len(qs) for s, qs in bank.by_skill().items()}
        skills = []
        for skill, n_total in sorted(bank_skills.items()):
            acc = skill_acc.get(skill)
            skills.append({
                "skill_tag": skill,
                "accuracy": None if acc is None else round(acc, 2),
                "questions_available": n_total,
                "attempted": skill in skill_acc,
            })
        return web.json_response({
            "total_attempts": total,
            "recent_accuracy": None if recent_acc is None else round(recent_acc, 2),
            "questions_seen": len(seen),
            "allowed_difficulties": sorted(quiz_engine.allowed_difficulties(total, recent_acc)),
            "skills": skills,
        })

    app.router.add_get("/quiz", serve_quiz_page)
    app.router.add_get("/api/quiz/next", quiz_next)
    app.router.add_post("/api/quiz/answer", quiz_answer)
    app.router.add_post("/api/quiz/explain", quiz_explain)
    app.router.add_post("/api/quiz/hint", quiz_hint)
    app.router.add_get("/api/quiz/progress", quiz_progress)
    return app
