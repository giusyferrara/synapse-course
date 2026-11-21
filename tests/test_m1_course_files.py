"""M1: the course files (expected outputs and solutions) are served only to whoever may open /course.
    python -m pytest tests/test_m1_course_files.py -q
Uses the real guard middleware and aiohttp's real static route, on a temporary folder."""
import asyncio
import os
import sys
from pathlib import Path

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer
from yarl import URL

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from web import guard  # noqa: E402

SECRET = b'{"exercise_id": "ex_01", "expected_output": "secret answer"}'


@pytest.fixture
def site(tmp_path, monkeypatch):
    (tmp_path / "course_content").mkdir()
    (tmp_path / "course_content" / "py_x.json").write_bytes(SECRET)
    (tmp_path / "site.css").write_text("body{}")
    who = {"user": None, "participant": None, "admin": False}
    monkeypatch.setattr(guard, "current_user_id", lambda r: who["user"])
    monkeypatch.setattr(guard, "participant_code", lambda r: who["participant"])
    monkeypatch.setattr(guard, "admin_key_ok", lambda r: who["admin"])

    def get(raw_path, method="GET"):
        async def go():
            app = web.Application(middlewares=[guard.guard])
            app.router.add_static("/static/", path=str(tmp_path), name="static")
            async with TestClient(TestServer(app)) as c:
                r = await c.request(method, URL(raw_path, encoded=True))
                return r.status, await r.read(), r.headers
        return asyncio.run(go())
    get.who = who
    return get


ANON_PATHS = [
    "/static/course_content/py_x.json",
    "/static/./course_content/py_x.json",
    "/static//course_content/py_x.json",
    "/static/%63ourse_content/py_x.json",
    "/static/course_content/%70y_x.json",
    "/static/course_content/py_x.json?v=123",
    "/static/course_content/",
    "/static/course_content",
    "/static/Course_Content/py_x.json",
    "/static/course_content/./py_x.json",
    "/static/course_content/sub/../py_x.json",
]


@pytest.mark.parametrize("path", ANON_PATHS)
def test_no_session_no_course_file(site, path):
    status, body, _ = site(path)
    assert status in (403, 404) and b"secret answer" not in body, (path, status)


def test_head_is_blocked_too(site):
    status, body, _ = site("/static/course_content/py_x.json", method="HEAD")
    assert status == 404


@pytest.mark.parametrize("who", [{"user": 7}, {"participant": "ABC123"}, {"admin": True}])
def test_whoever_may_open_course_gets_the_file_uncacheable(site, who):
    site.who.update(who)
    status, body, headers = site("/static/course_content/py_x.json")
    assert status == 200 and body == SECRET
    assert headers.get("Cache-Control") == "private, no-store"


def test_other_static_files_are_untouched(site):
    status, body, headers = site("/static/site.css")
    assert status == 200 and body == b"body{}" and headers.get("Cache-Control") != "private, no-store"


@pytest.mark.parametrize("path,expected", [
    ("/static/course_content/a.json", True), ("/static/./course_content/a.json", True),
    ("//static//course_content//a.json", True), ("/STATIC/COURSE_CONTENT/a.json", True),
    ("/static/course_content", True), ("/static/course_contents/a.json", False),
    ("/static/lessons/a.html", False), ("/static/x/../course_content/a.json", True),
])
def test_protected_paths(path, expected):
    assert guard._protected(path) is expected


def test_every_page_that_loads_course_files_needs_a_session():
    """The pages that fetch /static/course_content are behind the login (serve_course and the
    Java course), so the rule breaks nothing for a learner who can see them."""
    app_src = (ROOT / "app.py").read_text(encoding="utf-8")
    for tpl in ("course.html", "course_java_security.html"):
        assert "/static/course_content/" in (ROOT / "templates" / tpl).read_text(encoding="utf-8")
    for fn in ("async def serve_course(request):",):
        body = app_src[app_src.index(fn):app_src.index(fn) + 600]
        assert "HTTPFound('/login" in body
