"""E1: deterministic exercise grading. Run:  python -m pytest tests/test_e1_grading.py -q

Needs DATABASE_URL pointing at a THROWAWAY database with database/schema.sql
loaded (the progress tests write and read user_progress there). Never point it
at production.
"""
import asyncio
import json
import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)

from web import grader, sandbox  # noqa: E402

FAKE = [sys.executable, str(ROOT / "tests" / "fake_docker.py")]


# ---------------------------------------------------------------- comparison
@pytest.mark.parametrize("expected,actual", [
    ("Hello, Python Forensics!", "Hello, Python Forensics!\n"),
    ("a\nb", "a  \nb\t\n"),                 # spaces/tabs at line end
    ("a\nb", "a\r\nb\r\n"),                  # Windows line endings
    ("START\n\nEND", "\nSTART\n\nEND\n\n"),  # blank lines only at the edges
])
def test_compare_passes(expected, actual):
    ok, fb = grader.compare(expected, actual)
    assert ok, fb


@pytest.mark.parametrize("expected,actual,phrase", [
    ("5", "15", "Line 1 is different"),                    # no substring passes
    ("Hello World", "hello world", "only capital letters"),  # case matters
    ("a b", "a  b", "Only the spaces inside the line"),
    ("START\n\nEND", "START\nEND", "Line 2 is different"),   # inner blank line matters
    ("a\nb\nc", "a\nb", "missing"),
    ("a", "a\nb", "extra line"),
    ("a", "", "printed nothing"),
    ("Total: 40", "Total: 40 ", None),                       # trailing space is fine -> passes
])
def test_compare_fails_with_a_reason(expected, actual, phrase):
    ok, fb = grader.compare(expected, actual)
    if phrase is None:
        assert ok
    else:
        assert not ok and phrase in fb, fb


def test_compare_is_deterministic():
    assert len({grader.compare("x\ny", "x\nz") for _ in range(50)}) == 1


# ---------------------------------------------------------------- catalogue
def test_catalogue_is_complete():
    cat = grader.load_catalogue()
    assert len(cat) == 49
    assert sum(len(v) for v in cat.values()) == 2523
    # keyed by the file name the course page uses, even where course_id differs
    assert "london_transport_active_ai" in cat and "python_basics_active_ai" in cat


@pytest.mark.parametrize("course,ex", [
    ("../etc", "ex_01"), ("py_syntax_output", "../../x"), ("py_syntax_output", ""),
    (None, "ex_01"), ("py_syntax_output", {"$ne": 1}), ("nope", "ex_01"), ("py_syntax_output", "ex_9999"),
])
def test_find_exercise_refuses_anything_else(course, ex):
    assert grader.find_exercise(course, ex) is None


@pytest.mark.parametrize("ex,reason", [
    ({"expected_output": "x", "starter_code": "public class A {}"}, "java_not_executable"),
    ({"expected_output": "", "starter_code": ""}, "no_expected_output"),
    ({"expected_output": "MD5: d41d8cd...", "starter_code": ""}, "shortened_expected_output"),
    ({"expected_output": "x", "starter_code": "import random\nprint(random.randint(1,6))"}, "variable_output"),
    ({"expected_output": "x", "starter_code": "from datetime import datetime\nprint(datetime.now())"}, "variable_output"),
    ({"expected_output": "x", "starter_code": "import socket"}, "needs_network"),
    ({"expected_output": "x", "starter_code": "import requests"}, "needs_network"),
    ({"expected_output": "x", "starter_code": "from PIL import Image"}, "module_not_in_sandbox"),
])
def test_unchecked_reasons(ex, reason):
    assert reason in grader.unchecked_reasons("py_test", ex)


def test_plain_exercise_is_checkable():
    ex = grader.find_exercise("py_syntax_output", "ex_01")
    assert grader.unchecked_reasons("py_syntax_output", ex) == []
    assert grader.unchecked_reasons("java_loops", {"expected_output": "x", "starter_code": ""}) == ["java_not_executable"]


def test_valid_id_helper_does_not_flag_names_containing_id():
    assert grader.unchecked_reasons("py_x", {"expected_output": "x", "starter_code": "def valid(x):\n    return x"}) == []


# ---------------------------------------------------------------- sandbox
def test_sandbox_flags_are_all_there():
    a = sandbox.docker_args("n")
    joined = " ".join(a)
    for flag in ["--network none", "--memory 64m", "--memory-swap 64m", "--cpus 0.5", "--pids-limit 50",
                 "--read-only", "--tmpfs /tmp:size=10m", "--security-opt no-new-privileges",
                 "--cap-drop ALL", "--user sandbox", "--rm", "--name n"]:
        assert flag in joined, flag
    assert a[-3:] == ["synapse-sandbox", "python3", "-"]


@pytest.fixture(autouse=True)
def fresh_limits(tmp_path, monkeypatch):
    """Every test gets its own slot folder and an empty rate limiter."""
    monkeypatch.setattr(sandbox, "SLOT_DIR", str(tmp_path / "slots"))
    monkeypatch.setattr(sandbox, "limiter", sandbox.RunLimiter())


@pytest.fixture
def fake_docker(tmp_path, monkeypatch):
    log = tmp_path / "docker.log"
    monkeypatch.setattr(sandbox, "DOCKER", FAKE)
    monkeypatch.setenv("FAKE_DOCKER_LOG", str(log))
    return log


def run(coro):
    return asyncio.run(coro)


def test_sandbox_normal_run(fake_docker):
    r = run(sandbox.run_python('print("hi")'))
    assert r["ok"] and r["stdout"] == "hi\n" and not r["timed_out"]


def test_sandbox_error_run(fake_docker):
    r = run(sandbox.run_python("1/0"))
    assert not r["ok"] and "ZeroDivisionError" in r["stderr"]


def test_sandbox_timeout_kills_the_container(fake_docker):
    r = run(sandbox.run_python("while True: pass", timeout=1.5))
    assert r["timed_out"] and not r["ok"]
    assert "kill synapse-sbx-" in fake_docker.read_text()


def test_sandbox_output_cap_kills_the_container_at_once(fake_docker):
    import time
    t0 = time.monotonic()
    r = run(sandbox.run_python("while True: print('x' * 1000)", timeout=10, max_output=4096))
    elapsed = time.monotonic() - t0
    assert r["too_much_output"] and not r["ok"] and len(r["stdout"]) <= 4096
    assert "kill synapse-sbx-" in fake_docker.read_text()
    # stopped promptly, and the slot is not held: found on the real server on
    # 21 Nov 2026, where a half-read pipe kept the run going for 20 s
    assert elapsed < 4, elapsed


def test_sandbox_timeout_returns_promptly(fake_docker):
    import time
    t0 = time.monotonic()
    r = run(sandbox.run_python("while True: pass", timeout=1.0))
    assert r["timed_out"] and time.monotonic() - t0 < 4


# ---------------------------------------------------------------- the endpoint
pytest.importorskip("psycopg2")
from aiohttp import web  # noqa: E402
from aiohttp.test_utils import TestClient, TestServer  # noqa: E402
from sqlalchemy import text  # noqa: E402

import web.course_handlers as ch  # noqa: E402
import web.auth_handlers as ah  # noqa: E402

UID = 4242


@pytest.fixture
def db():
    from database.config import SessionLocal
    with SessionLocal() as s:
        s.execute(text("DELETE FROM user_progress WHERE user_id = :u"), {"u": UID})
        s.execute(text("DELETE FROM users WHERE id = :u"), {"u": UID})
        s.execute(text("INSERT INTO users (id, username, email, password_hash) VALUES (:u, 'e1test', 'e1@example.invalid', 'x')"), {"u": UID})
        s.commit()
    yield SessionLocal
    with SessionLocal() as s:
        s.execute(text("DELETE FROM user_progress WHERE user_id = :u"), {"u": UID})
        s.execute(text("DELETE FROM users WHERE id = :u"), {"u": UID})
        s.commit()


def rows(SessionLocal):
    with SessionLocal() as s:
        return [dict(r._mapping) for r in s.execute(text(
            "SELECT course_id, topic_id, exercise_id, completed, score, attempts FROM user_progress WHERE user_id = :u"), {"u": UID})]


class _NoAI:
    def __getattr__(self, name):
        raise AssertionError("grading must never call the AI (%s)" % name)


@pytest.fixture
def client(fake_docker, monkeypatch, db):
    signed_in = {"uid": UID}
    monkeypatch.setattr(ch, "_user_id", lambda request: signed_in["uid"])
    monkeypatch.setattr(ch, "mcp_coordinator", _NoAI())       # any AI use would fail the test

    async def make():
        app = web.Application()
        app.router.add_post("/api/course/evaluate_code", ch.handle_evaluate_code)
        c = TestClient(TestServer(app))
        await c.start_server()
        return c
    loop = asyncio.new_event_loop()
    c = loop.run_until_complete(make())

    def post(body, raw=None):
        async def go():
            r = await c.post("/api/course/evaluate_code", data=raw) if raw is not None else \
                await c.post("/api/course/evaluate_code", json=body)
            return r.status, await r.json()
        return loop.run_until_complete(go())
    post.signed_in = signed_in
    yield post
    loop.run_until_complete(c.close())
    loop.close()


def solution_for(course, ex_id):
    exp = grader.find_exercise(course, ex_id)["expected_output"]
    return "print(%s)" % json.dumps(exp)


def test_correct_solution_passes_and_saves_the_real_exercise_id(client, db):
    status, body = client({"course_id": "py_syntax_output", "exercise_id": "ex_02",
                           "code": solution_for("py_syntax_output", "ex_02")})
    assert status == 200 and body["status"] == "passed" and body["passed"] is True
    assert rows(db) == [{"course_id": "py_syntax_output", "topic_id": "py_syntax_output",
                         "exercise_id": "ex_02", "completed": True, "score": 100, "attempts": 1}]


def test_wrong_solution_fails_and_is_not_completed(client, db):
    status, body = client({"course_id": "py_syntax_output", "exercise_id": "ex_02", "code": 'print("Laptop")'})
    assert body["status"] == "failed" and body["passed"] is False and "missing" in body["feedback"]
    r = rows(db)
    assert len(r) == 1 and r[0]["completed"] is False and r[0]["attempts"] == 1


def test_pass_after_fail_counts_attempts_and_a_later_fail_never_undoes_it(client, db):
    client({"course_id": "py_syntax_output", "exercise_id": "ex_01", "code": 'print("hello, python forensics!")'})
    client({"course_id": "py_syntax_output", "exercise_id": "ex_01", "code": solution_for("py_syntax_output", "ex_01")})
    client({"course_id": "py_syntax_output", "exercise_id": "ex_01", "code": 'print("no")'})
    r = rows(db)[0]
    assert r["completed"] is True and r["attempts"] == 3 and r["score"] == 100


def test_the_browser_cannot_declare_a_pass(client, db):
    status, body = client({"course_id": "py_syntax_output", "exercise_id": "ex_01", "code": 'print("wrong")',
                           "user_output": "Hello, Python Forensics!", "passed": True, "correct": True,
                           "exercise": {"expected_output": "wrong"}, "expected_output": "wrong", "user_id": 1})
    assert body["status"] == "failed"
    assert rows(db)[0]["completed"] is False


def test_signed_out_is_refused_and_nothing_runs(client, db, fake_docker):
    client.signed_in["uid"] = None
    status, body = client({"course_id": "py_syntax_output", "exercise_id": "ex_01", "code": "print(1)"})
    assert status == 401 and body["status"] == "sign_in"
    assert not fake_docker.exists() and rows(db) == []


@pytest.mark.parametrize("payload", [
    {"course_id": "../static", "exercise_id": "ex_01", "code": "print(1)"},
    {"course_id": "py_syntax_output", "exercise_id": "nope", "code": "print(1)"},
    {"course_id": "py_syntax_output", "exercise_id": "ex_01", "code": ""},
    {"course_id": "py_syntax_output", "exercise_id": "ex_01", "code": "x" * 60000},
    {"course_id": "py_syntax_output", "exercise_id": "ex_01"},
])
def test_bad_requests_run_nothing_and_save_nothing(client, db, fake_docker, payload):
    status, body = client(payload)
    assert status in (400, 404) and body["passed"] is False
    assert not fake_docker.exists() and rows(db) == []


def test_not_json_is_refused(client, db):
    status, body = client(None, raw="not json")
    assert status == 400 and rows(db) == []


def test_java_is_declared_not_checkable_and_nothing_runs(client, db, fake_docker):
    course = "java_loops"
    ex_id = next(iter(grader.catalogue()[course]))
    status, body = client({"course_id": course, "exercise_id": ex_id, "code": "public class A {}"})
    assert body["status"] == "not_checkable" and "java_not_executable" in body["reasons"]
    assert not fake_docker.exists() and rows(db) == []


def test_shortened_expected_output_is_not_judged(client, db, fake_docker):
    course, ex_id = next((c, e) for c, exs in grader.catalogue().items() for e, x in exs.items()
                         if "..." in str(x.get("expected_output")) and not grader.is_java(c, x))
    status, body = client({"course_id": course, "exercise_id": ex_id, "code": "print(1)"})
    assert body["status"] == "not_checkable" and "shortened_expected_output" in body["reasons"]
    assert not fake_docker.exists() and rows(db) == []


def test_errors_and_timeouts_are_failures_with_a_reason(client, db, monkeypatch):
    status, body = client({"course_id": "py_syntax_output", "exercise_id": "ex_01", "code": "print(undefined_name)"})
    assert body["status"] == "failed" and "NameError" in body["feedback"]
    monkeypatch.setattr(sandbox, "RUN_TIMEOUT", 1.5)
    status, body = client({"course_id": "py_syntax_output", "exercise_id": "ex_01", "code": "while True: pass"})
    assert body["status"] == "failed" and "still running" in body["feedback"]


def test_sandbox_down_is_503_and_saves_nothing(client, db, monkeypatch):
    async def broken(code, **kw):
        raise FileNotFoundError("docker")
    monkeypatch.setattr(sandbox, "run_python", broken)
    status, body = client({"course_id": "py_syntax_output", "exercise_id": "ex_01", "code": "print(1)"})
    assert status == 503 and body["status"] == "unavailable" and rows(db) == []


# ---------------------------------------------------------------- regressions
def test_progress_can_no_longer_be_written_from_the_browser():
    app = web.Application()
    ah.setup_auth_routes(app)
    routes = {(r.method, r.resource.canonical) for r in app.router.routes()}
    assert ("GET", "/api/auth/progress") in routes          # the dashboard still reads it
    assert ("POST", "/api/auth/progress") not in routes


def test_pages_send_only_ids_and_code():
    course = (ROOT / "templates" / "course.html").read_text(encoding="utf-8")
    fn = course[course.index("async function checkSolution()"):]
    fn = fn[:fn.index("\n    }\n")]
    assert "course_id: currentGraded.course_id" in fn and "exercise_id: currentGraded.exercise_id" in fn
    assert "expected_output" not in fn and "user_output" not in fn
    java = (ROOT / "templates" / "course_java_security.html").read_text(encoding="utf-8")
    jfn = java[java.index("async function checkSolution()"):]
    jfn = jfn[:jfn.index("\n    }\n")]
    assert "evaluate_code" not in jfn and "🎉" not in jfn and "can't run on Synapse" in jfn


def test_run_code_uses_the_hardened_sandbox(fake_docker, monkeypatch):
    async def go():
        app = web.Application()
        app["tutor"] = object()
        app.router.add_post("/api/course/run_code", ch.handle_run_code)
        async with TestClient(TestServer(app)) as c:
            r = await c.post("/api/course/run_code", json={"code": "print(2+2)", "topic_id": "py_syntax_output"})
            return await r.json()
    body = asyncio.run(go())
    assert body["success"] and body["output"] == "4\n"
    assert "--cap-drop ALL" in fake_docker.read_text()


# ---------------------------------------------------------------- limits (concurrency, rate)
SLOW = "import time\ntime.sleep(0.6)\nprint('done')"


def max_overlap(log):
    """From the fake docker's start/end lines, the most containers alive at once."""
    ev = []
    for line in log.read_text().splitlines():
        if line.startswith(("start ", "end ")):
            kind, t = line.split()[:2]
            ev.append((float(t), 1 if kind == "start" else -1))
    alive = peak = 0
    for _, d in sorted(ev, key=lambda e: (e[0], e[1])):
        alive += d
        peak = max(peak, alive)
    return peak


def test_never_more_than_four_containers_at_once(fake_docker):
    """Ten simultaneous runs: at most 4 containers alive at any moment, all ten finish."""
    async def go():
        return await asyncio.gather(*[sandbox.run_python(SLOW) for _ in range(10)])
    results = run(go())
    assert all(r["ok"] and r["stdout"] == "done\n" for r in results)
    assert sum(l.startswith("run ") for l in fake_docker.read_text().splitlines()) == 10
    peak = max_overlap(fake_docker)
    assert peak == 4, peak          # the cap is what limits them, not chance


def test_busy_after_a_short_wait_when_all_slots_are_taken(fake_docker, monkeypatch):
    monkeypatch.setattr(sandbox, "SLOT_WAIT", 0.5)

    async def go():
        held = [sandbox.slot() for _ in range(4)]
        for h in held:
            await h.__aenter__()
        t0 = asyncio.get_running_loop().time()
        with pytest.raises(sandbox.Busy):
            await sandbox.run_python("print(1)")
        waited = asyncio.get_running_loop().time() - t0
        for h in held:
            await h.__aexit__(None, None, None)
        r = await sandbox.run_python("print(1)")          # free again
        return waited, r
    waited, r = run(go())
    assert 0.4 <= waited < 2 and r["ok"]
    assert sum(l.startswith("run ") for l in fake_docker.read_text().splitlines()) == 1


def test_slots_are_global_across_processes(fake_docker, monkeypatch):
    """Another PROCESS holding all 4 slots makes this one wait, then busy."""
    import subprocess
    monkeypatch.setattr(sandbox, "SLOT_WAIT", 0.5)
    holder = subprocess.Popen([sys.executable, "-c", (
        "import fcntl,os,sys,time\n"
        "d=sys.argv[1]; os.makedirs(d, exist_ok=True); fs=[]\n"
        "for i in range(4):\n"
        "    f=os.open(os.path.join(d,'slot-%d'%i), os.O_RDWR|os.O_CREAT, 0o600); fcntl.flock(f, fcntl.LOCK_EX); fs.append(f)\n"
        "print('held', flush=True); time.sleep(30)\n"), sandbox.SLOT_DIR], stdout=subprocess.PIPE, text=True)
    try:
        assert holder.stdout.readline().strip() == "held"
        with pytest.raises(sandbox.Busy):
            run(sandbox.run_python("print(1)"))
    finally:
        holder.kill()
        holder.wait()
    assert run(sandbox.run_python("print(1)"))["ok"]     # the dead process gave its slots back


def test_slots_are_released_after_errors_and_timeouts(fake_docker, monkeypatch):
    async def go():
        await asyncio.gather(*[sandbox.run_python("1/0") for _ in range(4)])
        await asyncio.gather(*[sandbox.run_python("while True: pass", timeout=0.8) for _ in range(4)])
        held = [sandbox.slot(wait=0.3) for _ in range(4)]   # all four must be free now
        for h in held:
            await h.__aenter__()
        for h in held:
            await h.__aexit__(None, None, None)
    run(go())


def test_rate_limiter_window():
    now = [0.0]
    lim = sandbox.RunLimiter(limit=3, window=60, clock=lambda: now[0])
    for _ in range(3):
        lim.check("u:1")
    with pytest.raises(sandbox.RateLimited) as e:
        lim.check("u:1")
    assert 1 <= e.value.retry_after <= 60
    lim.check("u:2")                      # another learner is not affected
    now[0] = 60.0
    lim.check("u:1")                      # the window moved on


def test_rate_limit_answers_429_and_the_refused_try_is_not_an_attempt(client, db, fake_docker, monkeypatch):
    monkeypatch.setattr(sandbox, "limiter", sandbox.RunLimiter(limit=3))
    body = {"course_id": "py_syntax_output", "exercise_id": "ex_01", "code": "print(1)"}
    for _ in range(3):
        status, b = client(body)
        assert status == 200
    status, b = client(body)
    assert status == 429 and b["status"] == "rate_limited" and b["passed"] is False and "try again" in b["feedback"]
    assert sum(l.startswith("run ") for l in fake_docker.read_text().splitlines()) == 3
    assert rows(db)[0]["attempts"] == 3


def test_rate_limit_cannot_be_dodged_by_changing_the_request(client, db, fake_docker, monkeypatch):
    monkeypatch.setattr(sandbox, "limiter", sandbox.RunLimiter(limit=2))
    extras = [{}, {"user_id": 999, "student_id": "x"}, {"exercise_id": "ex_02"}]
    for i, extra in enumerate(extras):
        body = {"course_id": "py_syntax_output", "exercise_id": "ex_01", "code": "print(1)"}
        body.update(extra)
        status, b = client(body)
        assert status == (200 if i < 2 else 429), (i, b)


def test_not_checkable_exercises_do_not_spend_the_limit(client, db, fake_docker, monkeypatch):
    monkeypatch.setattr(sandbox, "limiter", sandbox.RunLimiter(limit=1))
    java = next(iter(grader.catalogue()["java_loops"]))
    for _ in range(3):
        status, b = client({"course_id": "java_loops", "exercise_id": java, "code": "x"})
        assert b["status"] == "not_checkable"
    status, b = client({"course_id": "py_syntax_output", "exercise_id": "ex_01", "code": "print(1)"})
    assert status == 200


def test_busy_answers_503_and_saves_nothing(client, db, fake_docker, monkeypatch):
    async def busy(code, **kw):
        raise sandbox.Busy()
    monkeypatch.setattr(sandbox, "run_python", busy)
    status, b = client({"course_id": "py_syntax_output", "exercise_id": "ex_01", "code": "print(1)"})
    assert status == 503 and b["status"] == "busy" and rows(db) == []


def test_run_and_check_share_one_limit_and_run_answers_429(fake_docker, monkeypatch):
    monkeypatch.setattr(sandbox, "limiter", sandbox.RunLimiter(limit=2))
    monkeypatch.setattr(ch, "_user_id", lambda request: 77)
    monkeypatch.setattr(ch, "_record_progress", lambda *a: None)

    async def go():
        app = web.Application()
        app["tutor"] = object()
        app.router.add_post("/api/course/run_code", ch.handle_run_code)
        app.router.add_post("/api/course/evaluate_code", ch.handle_evaluate_code)
        out = []
        async with TestClient(TestServer(app)) as c:
            r = await c.post("/api/course/run_code", json={"code": "print(1)", "topic_id": "py_syntax_output"})
            out.append((r.status, None, await r.json()))
            r = await c.post("/api/course/evaluate_code", json={"course_id": "py_syntax_output", "exercise_id": "ex_01", "code": "print(1)"})
            out.append((r.status, None, await r.json()))
            r = await c.post("/api/course/run_code", json={"code": "print(1)", "topic_id": "py_syntax_output"})
            out.append((r.status, r.headers.get("Retry-After"), await r.json()))
        return out
    out = run(go())
    assert [s for s, _, _ in out] == [200, 200, 429]
    assert out[2][1] and "try again" in out[2][2]["output"]
