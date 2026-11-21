"""
One gate in front of every request.

Written on 8 November 2026 after an audit found doors that had been left open
for months: a path trick that read any file next to app.py, a Python runner
that executed visitors' code inside the web server, the research data
downloadable by anybody, and AI endpoints with no limit on what they could
cost. Each of those is also fixed where it lives, or is being fixed; this file
is the second lock, so that one forgotten handler cannot open the house again.

What it does, in order:
1. Refuses any path that tries to climb out of its folder (`..`, or a slash
   or backslash smuggled in as %2F / %5C).
1b. Refuses any path that names a backup copy (see _BACKUP_NAME).
2. Answers 404 for endpoints that are retired. They are listed, not deleted,
   so it is obvious what was switched off and why.
3. Lets the research and admin endpoints through only for the admin.
4. Puts the AI budget (web/ai_budget.py) in front of every endpoint that
   calls a paid model and does not already check the budget itself.
5. Adds the security headers to every response.
"""
import posixpath
import re

from aiohttp import web

from .ai_budget import budget, client_ip, Refused, UNLIMITED
from .session import current_user_id, admin_key_ok, participant_code

# Retired. Nothing on the site uses them any more, or what used them was the
# danger. 404, as if they had never existed.
RETIRED = {
    "/api/execute",            # ran visitors' Python inside the web server
    "/analyze", "/suggest_fixes", "/test_ai",
    "/api/get-hint", "/api/ai/explain_code", "/api/ai/generate_exercises",
    "/api/generate-next-exercise", "/api/next-exercise-ai",
    "/api/generate-flowchart", "/api/run-exercise",
    "/api/course/progress",    # keyed by a student_id the caller chose
    "/api/research/recover_code", "/api/research/recover_code_nickname",
}
RETIRED_PREFIXES = ("/api/metrics/export",)

# The admin only: research data, exports, statistics.
ADMIN_ONLY = {
    "/research/dashboard", "/dashboard/research",
    "/api/research/dashboard_data", "/api/research/export",
    "/api/research/export/csv", "/api/research/stats",
}
ADMIN_PREFIXES = ("/api/research/export",)

# Endpoints that call a paid model without checking the budget themselves.
# /api/course/chat, /api/course/get_hint, /api/define and generate_lesson do
# their own check and are deliberately not listed, or they would count twice.
AI_PATHS = {
    "/api/chat", "/explain", "/chat_followup", "/api/check-exercise",
    "/api/quiz/explain", "/api/quiz/hint", "/api/quiz/chat",
}

_CLIMB = re.compile(r"\.\.|%2e%2e|%2f|%5c|\\", re.I)

# The course files hold every exercise's expected output and, in the third
# hint, its solution. Until E3 stops sending those to the browser at all, they
# are served only to whoever may open /course (same rule as serve_course in
# app.py): a signed-in user, a valid research participant, or the admin key.
# Found 22 Nov 2026: anyone could download them without an account.
# Checked on the DECODED and NORMALISED path, so /static/./course_content,
# /static/%63ourse_content, /static//course_content and the like are caught.
PROTECTED_DIRS = ("/static/course_content",)


def _normalised(path):
    p = posixpath.normpath(re.sub(r"/{2,}", "/", path or "/"))
    return p.lower()


def _protected(path):
    p = _normalised(path)
    return any(p == d or p.startswith(d + "/") for d in PROTECTED_DIRS)


def _may_open_courses(request):
    return bool(current_user_id(request)) or bool(participant_code(request)) or admin_key_ok(request)

# Copies left behind by edits and deploys: name.bak, name.bak_20261119_113924,
# name.BAK, name.orig, name.backup3, name.save.1, name~ and the like. They are
# old versions of pages and code, and some still hold what was deliberately
# taken off the site. On 19 Nov 2026, 249 of them could be downloaded under
# /static/ and /icons/. Checked on the DECODED path, so %2Ebak is caught too,
# and on every segment, so a backup folder is caught as well as a file.
# Nothing the site really serves has such a name (checked against git and
# every registered route), so this costs nothing.
_BACKUP_NAME = re.compile(
    r"\.(bak|bk|orig|backup|old|save|swp|swo|rej)(?![a-z])|~(/|$)", re.I)

# nginx already adds X-Frame-Options, nosniff and Referrer-Policy; sending
# them twice makes some browsers read "nosniff, nosniff" and ignore it.
HEADERS = {
    "Content-Security-Policy": "frame-ancestors 'self'; object-src 'none'; base-uri 'self'",
    "Permissions-Policy": "camera=(), geolocation=(), microphone=(self)",
}


def _is_admin(request):
    if admin_key_ok(request):
        return True
    uid = current_user_id(request)
    return bool(uid) and budget.tier_for(uid) in UNLIMITED


def _not_found():
    return web.json_response({"error": "not found"}, status=404)


@web.middleware
async def guard(request, handler):
    raw_path = request.raw_path.split("?", 1)[0]
    path = request.path.rstrip("/") or "/"

    if _CLIMB.search(raw_path):
        return _not_found()

    if _BACKUP_NAME.search(request.path):
        return _not_found()

    if path in RETIRED or path.startswith(RETIRED_PREFIXES):
        return _not_found()

    course_file = _protected(request.path)
    if course_file and not _may_open_courses(request):
        return _not_found()

    if (path in ADMIN_ONLY or path.startswith(ADMIN_PREFIXES)) and not _is_admin(request):
        return _not_found()

    if path in AI_PATHS and request.method == "POST":
        try:
            budget.check(user_id=current_user_id(request), ip=client_ip(request))
        except Refused as r:
            headers = {"Retry-After": str(r.retry_after)} if r.retry_after else None
            return web.json_response(
                {"error": "rate_limited", "response": r.message, "message": r.message},
                status=429, headers=headers)

    response = await handler(request)
    try:
        if course_file:
            # never kept by a shared cache (Cloudflare, a proxy) for the next visitor
            response.headers["Cache-Control"] = "private, no-store"
        for k, v in HEADERS.items():
            response.headers.setdefault(k, v)
    except Exception:
        pass   # an already-started stream; its headers are gone
    return response
