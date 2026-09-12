"""The drawer — where a learner's visualisations are kept, so they can be found
again without scrolling back through a conversation.

Four decisions this file implements, and the reasons, because they are easy to
undo by accident:

  * **The recipe is stored, never the film.** A saved view is a couple of hundred
    bytes — which lesson, or which snippet of the learner's own code — and the
    visualisation is rebuilt from it when they open it. Storing the recording
    would age badly: the engine keeps improving and a stored film would keep
    showing the old one.
  * **Grouped by concept, not by date.** A drawer sorted by date is a
    conversation you have to re-read. Grouped by concept ("loops", "dictionaries")
    it answers the question people actually arrive with.
  * **On the server, not in the browser.** Schools share machines; local storage
    would hand one pupil's drawer to the next one at that desk, and lose it
    whenever the browser is cleaned.
  * **Login required, always.** No participant-code or admin back door: this is
    personal data with a name on it.

Routes (all JSON, all behind the synapse_user cookie):

    GET    /api/drawer          everything this learner has kept, grouped
    POST   /api/drawer          keep one thing
    DELETE /api/drawer/{id}     throw one away (only ever your own)

The learner-facing page is templates/drawer.html, served at /drawer.
"""
import datetime
import json

from aiohttp import web

from database.config import SessionLocal
from database.models import SavedView

# Limits. Not arbitrary: a drawer is a shelf, not a hard drive, and an endpoint
# that accepts anything is an endpoint someone will eventually post a film to.
MAX_ROWS_PER_USER = 200
MAX_CODE_CHARS = 8000
MAX_TITLE_CHARS = 140
MAX_NOTE_CHARS = 500
KINDS = ("library", "mine")
LANGUAGES = ("python", "java", "")


def _user_id(request):
    """The logged-in user, or None. Deliberately no participant-code fallback."""
    raw = request.cookies.get("synapse_user")
    if not raw:
        return None
    try:
        return int(raw)
    except (TypeError, ValueError):
        return None


def _needs_login():
    return web.json_response(
        {"error": "not signed in", "detail": "The drawer keeps your own work, so it needs an account."},
        status=401,
    )


def _row(view):
    return {
        "id": view.id,
        "kind": view.kind,
        "concept": view.concept,
        "title": view.title,
        "prog": view.prog,
        "language": view.language,
        "code": view.code,
        "note": view.note,
        "created_at": view.created_at.isoformat() if view.created_at else None,
        "opened_at": view.opened_at.isoformat() if view.opened_at else None,
    }


def setup_drawer_routes(app):

    async def drawer_list(request):
        uid = _user_id(request)
        if uid is None:
            return _needs_login()

        db = SessionLocal()
        try:
            views = (db.query(SavedView)
                       .filter(SavedView.user_id == uid)
                       .order_by(SavedView.concept.asc(), SavedView.created_at.desc())
                       .all())
        finally:
            db.close()

        # Grouped here rather than in the page, so every client that ever reads
        # this endpoint gets the same shape and the same ordering rule.
        groups, order = {}, []
        for v in views:
            if v.concept not in groups:
                groups[v.concept] = []
                order.append(v.concept)
            groups[v.concept].append(_row(v))

        return web.json_response({
            "count": len(views),
            "limit": MAX_ROWS_PER_USER,
            "concepts": [{"concept": c, "items": groups[c]} for c in order],
        })

    async def drawer_save(request):
        uid = _user_id(request)
        if uid is None:
            return _needs_login()

        try:
            body = await request.json()
        except (json.JSONDecodeError, ValueError):
            return web.json_response({"error": "bad request", "detail": "Expected JSON."}, status=400)

        kind = (body.get("kind") or "library").strip()
        concept = (body.get("concept") or "").strip() or "Unfiled"
        title = (body.get("title") or "").strip()
        prog = (body.get("prog") or "").strip() or None
        language = (body.get("language") or "").strip().lower()
        code = body.get("code") or None
        note = (body.get("note") or "").strip() or None

        if kind not in KINDS:
            return web.json_response({"error": "kind must be 'library' or 'mine'"}, status=400)
        if language not in LANGUAGES:
            return web.json_response({"error": "language must be python or java"}, status=400)
        if kind == "library" and not prog:
            return web.json_response({"error": "a library entry needs the lesson it points at"}, status=400)
        if kind == "mine" and not code:
            return web.json_response({"error": "there is nothing to keep — no code was sent"}, status=400)
        if code and len(code) > MAX_CODE_CHARS:
            return web.json_response(
                {"error": "that snippet is too long to keep",
                 "detail": "Up to %d characters; this was %d." % (MAX_CODE_CHARS, len(code))},
                status=413)

        title = (title or prog or "Untitled")[:MAX_TITLE_CHARS]
        if note:
            note = note[:MAX_NOTE_CHARS]

        db = SessionLocal()
        try:
            held = db.query(SavedView).filter(SavedView.user_id == uid).count()
            if held >= MAX_ROWS_PER_USER:
                return web.json_response(
                    {"error": "your drawer is full",
                     "detail": "It holds %d. Remove one to keep another." % MAX_ROWS_PER_USER},
                    status=409)

            # Keeping the same lesson twice is not an error, it is a no-op.
            if kind == "library":
                already = (db.query(SavedView)
                             .filter(SavedView.user_id == uid,
                                     SavedView.kind == "library",
                                     SavedView.prog == prog)
                             .first())
                if already:
                    already.opened_at = datetime.datetime.utcnow()
                    db.commit()
                    return web.json_response({"saved": _row(already), "already": True})

            view = SavedView(user_id=uid, kind=kind, concept=concept, title=title,
                             prog=prog, language=language or None, code=code, note=note)
            db.add(view)
            db.commit()
            db.refresh(view)
            saved = _row(view)
        finally:
            db.close()

        return web.json_response({"saved": saved, "already": False})

    async def drawer_delete(request):
        uid = _user_id(request)
        if uid is None:
            return _needs_login()

        try:
            view_id = int(request.match_info["view_id"])
        except (KeyError, TypeError, ValueError):
            return web.json_response({"error": "which one?"}, status=400)

        db = SessionLocal()
        try:
            view = (db.query(SavedView)
                      .filter(SavedView.id == view_id, SavedView.user_id == uid)
                      .first())
            if not view:
                # Same answer whether it never existed or belongs to somebody
                # else: no endpoint here confirms other people's rows.
                return web.json_response({"error": "not found"}, status=404)
            db.delete(view)
            db.commit()
        finally:
            db.close()

        return web.json_response({"deleted": view_id})

    app.router.add_get("/api/drawer", drawer_list)
    app.router.add_post("/api/drawer", drawer_save)
    app.router.add_delete("/api/drawer/{view_id}", drawer_delete)
    return app
