"""E2: the solution extractor and the content validator.
Run in Linux/WSL (the isolation tests need bwrap):  python3 -m pytest tests/test_e2_validator.py -q
Needs no database and no network."""
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))

import extract_solutions as xs  # noqa: E402
import validate_content as vc  # noqa: E402


def hint3(text):
    return {"hints": [{"message": "a"}, {"message": "b"}, {"message": text}]}


# ---------------------------------------------------------------- extraction
def test_solution_code():
    e = xs.classify(hint3('Solution: print("Hello")'))
    assert (e["kind"], e["form"], e["code"]) == ("solution", "code", 'print("Hello")')


def test_escape_inside_a_string_is_kept():
    e = xs.classify(hint3('Solution: print("Row A\\nRow B")'))
    assert e["form"] == "code" and e["code"] == 'print("Row A\\nRow B")' and not e["flags"]


def test_literal_backslash_n_used_as_line_break_is_flagged_and_decoded():
    e = xs.classify(hint3("Solution:\\nx = 1\\nprint(x)"))
    assert e["form"] == "code" and e["code"] == "x = 1\nprint(x)" and e["flags"] == ["escaped_newlines"]


def test_two_answers_joined_by_or_are_alternatives_not_one_program():
    e = xs.classify(hint3('Fix: print(r"C:\\a")  or  print("C:\\\\a")'))
    assert e["form"] == "alternatives" and len(e["alternatives"]) == 2


def test_words_are_an_explanation_and_a_header_is_a_fragment():
    assert xs.classify(hint3("Fix: Add count += 1 after the print statement."))["form"] == "explanation"
    assert xs.classify(hint3("Fix: if x == 5:"))["form"] == "fragment"


def test_output_hint_and_missing_hint():
    assert xs.classify(hint3("Output: 15"))["kind"] == "output"
    assert xs.classify({"hints": [{"message": "a"}]})["kind"] == "missing"


def test_extractor_refuses_to_write_inside_the_public_repo():
    r = subprocess.run([sys.executable, str(ROOT / "tools" / "extract_solutions.py"), "--out", str(ROOT / "static" / "x.json")],
                       capture_output=True, text=True)
    assert r.returncode != 0 and "refusing" in r.stderr and not (ROOT / "static" / "x.json").exists()


# ---------------------------------------------------------------- teaching check (separate from output)
def ex(title, desc="", starter=""):
    return {"title": title, "description": desc, "starter_code": starter}


@pytest.mark.parametrize("course,exercise,code,expect", [
    # right output, but the topic of the course is not used
    ("py_conditions_loops", ex("Exercise 3: Even numbers"), 'print("4 is even")', "MISSING"),
    ("py_variables_datatypes", ex("Exercise 2: Your age"), 'print("Age: 25")', "prints fixed text only"),
    # false alarms found on the real content (21 Nov 2026) must stay quiet
    ("py_syntax_output", ex("Exercise 5: Wrong Function Name", "Fix the NameError"), 'print("made up text")', "no construct required"),
    ("py_variables_datatypes", ex("Exercise 2: Guess the Type", "What type does 7 / 2 return?"),
     "q = 7 / 2\nprint(type(q).__name__)", "no construct required"),
    ("py_variables_datatypes", ex("Exercise 3: Sums", "Print the result of 6+1"), 'print(f"6 + 1 = {6 + 1}")', "no construct required"),
    ("py_conditions_loops", ex("Exercise 4: Range Check", "Check if a score is in the valid range"),
     "score = 7\nif 0 <= score <= 10:\n    print('ok')", "uses condition"),
    # the title asks for a construct the solution does not use
    ("py_conditions_loops", ex("Exercise 1: Simple if"), "for i in range(2):\n    print(i)", "MISSING: condition"),
    ("py_functions_modules", ex("Exercise 4: Define a function"), "import math\nprint(math.pi)", "MISSING: function"),
    # used properly
    ("py_conditions_loops", ex("Exercise 1: Simple if"), "x = 4\nif x % 2 == 0:\n    print('even')", "uses condition"),
    ("py_functions_modules", ex("Exercise 5: Return a value"), "def f(a):\n    return a * 2\nprint(f(2))", "uses function"),
    # "the print() function" is not a request to write a function
    ("py_syntax_output", ex("Exercise 9: Multiple items", "Use the print() function with several arguments"), 'print("a", "b")', "no construct required"),
])
def test_teaching_check(course, exercise, code, expect):
    status, _, _ = vc.teaching_check(course, exercise, code)
    assert status.startswith(expect), status


def test_teaching_check_without_a_solution_is_not_assessed():
    assert vc.teaching_check("py_conditions_loops", ex("x"), None)[0].startswith("not assessed")


# ---------------------------------------------------------------- isolation (Linux with bwrap only)
needs_bwrap = pytest.mark.skipif(not shutil.which("bwrap"), reason="bwrap not available")


@needs_bwrap
def test_isolated_run_prints():
    r = vc.run_isolated('print("hi")')
    assert r["ok"] and r["stdout"] == "hi\n"


@needs_bwrap
@pytest.mark.parametrize("probe", [
    "import socket\nsocket.create_connection(('1.1.1.1', 53), timeout=2)",
    "import os\nprint(os.listdir('/home'))",
    "import os\nprint(os.listdir('/mnt'))",
    "open('/usr/x', 'w')",
    "x = bytearray(600 * 1024 * 1024)",
])
def test_isolation_refuses(probe):
    r = vc.run_isolated(probe)
    assert not r["ok"], r


@needs_bwrap
def test_isolated_runs_are_stopped(monkeypatch):
    monkeypatch.setattr(vc, "TIMEOUT", 1)
    assert vc.run_isolated("while True: pass")["timed_out"]
    r = vc.run_isolated("while True: print('x' * 1000)")
    assert (r["too_much_output"] or r["timed_out"]) and not r["ok"]


# ---------------------------------------------------------------- E2 round 1 content (needs bwrap)
@needs_bwrap
def test_ex29_corrected_solution_matches_and_the_old_one_did_not():
    from web import grader
    ex = grader.load_catalogue()["py_functions_modules"]["ex_29"]
    sol = xs.classify(ex)
    assert sol["form"] == "code" and "len(t)" in sol["code"]
    r = vc.run_isolated(sol["code"])
    assert r["ok"] and grader.compare(ex["expected_output"], r["stdout"])[0]
    old = sol["code"].replace("len(t)", 'len(t.replace(" ", ""))')
    r = vc.run_isolated(old)
    assert r["ok"] and not grader.compare(ex["expected_output"], r["stdout"])[0]
