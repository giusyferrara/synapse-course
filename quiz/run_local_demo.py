#!/usr/bin/env python3
"""
Local demo harness for Milestone 4 — runs the REAL quiz routes against a
throwaway SQLite DB with a FAKE AI service injected (no API keys, no cost).

    python quiz/run_local_demo.py           # serve on http://127.0.0.1:8099
"""
import os
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
os.chdir(ROOT)  # so FileResponse('templates/quiz.html') resolves

_DB = os.path.join(tempfile.gettempdir(), "quiz_demo.db")
if os.path.exists(_DB):
    os.remove(_DB)
os.environ["DATABASE_URL"] = "sqlite:///" + _DB.replace("\\", "/")
os.environ.setdefault("ADMIN_KEY", "demo-admin")

from aiohttp import web  # noqa: E402
from database import config  # noqa: E402
from database.models import QuizAttempt, QuizReview  # noqa: E402
from web.quiz_handlers import setup_quiz_routes  # noqa: E402
from quiz.quiz_ai import QuizAIService  # noqa: E402

config.Base.metadata.create_all(config.engine, tables=[QuizAttempt.__table__, QuizReview.__table__])

app = web.Application()
setup_quiz_routes(app)
# the real app serves /static via its own route; the minimal demo needs it too
app.router.add_static("/static/", path=os.path.join(ROOT, "static"))

# Inject a fake AI service so explain/hint work offline (tight limits to show 429).
_FAKE = "Demo elaboration: the untrusted input flows into the sink, which is why the marked answer is correct. (This text is a stand-in for the real Claude output.)"
app["quiz_ai"] = QuizAIService(lambda prompt: _FAKE, per_minute=4, per_day=30)

if __name__ == "__main__":
    print("Serving quiz demo on http://127.0.0.1:8099  (DB:", _DB, ")")
    web.run_app(app, host="127.0.0.1", port=8099, print=None)
