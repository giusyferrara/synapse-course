"""
Deterministic exercise grading (E1). No AI anywhere in here.

The browser says only WHICH exercise and sends the code. Everything else comes
from the trusted catalogue on the server (static/course_content/*.json): the
expected output, the course, whether the exercise can be checked at all. The
code runs in the sandbox (web/sandbox.py), never in this process, and the
server compares the output itself.

Comparison rule, deliberately narrow:
  - line endings (CRLF / CR) do not matter;
  - spaces and tabs at the END of a line do not matter;
  - blank lines at the very start or end of the output do not matter;
  - everything else matters: capital letters, spaces inside a line, blank
    lines between other lines, every character.
There is no wildcard. An expected output that is shortened with "..." cannot be
compared exactly, so that exercise is reported as "not checkable yet" and left
for the content validator (E2) instead of being guessed at.
"""
import json
import os
import re
import sys
from pathlib import Path

CATALOGUE_DIR = Path(__file__).resolve().parent.parent / "static" / "course_content"
_ID = re.compile(r"^[A-Za-z0-9_\-]{1,100}$")

# Modules the sandbox image has besides the standard library (see its Dockerfile:
# `pip install matplotlib numpy`).
SANDBOX_EXTRA_MODULES = {"numpy", "matplotlib"}
_NETWORK_MODULES = {"socket", "ssl", "urllib", "http", "ftplib", "smtplib", "poplib",
                    "imaplib", "telnetlib", "requests", "httpx", "aiohttp", "scapy",
                    "dns", "whois", "nmap", "paramiko"}
_VARIABLE_CALLS = re.compile(
    r"\brandom\.|\bimport random\b|\bfrom random\b|\bsecrets\.|\bimport secrets\b|"
    r"os\.urandom|\buuid\.|\bimport uuid\b|time\.time\(|time\.perf_counter\(|"
    r"time\.monotonic\(|datetime\.now\(|datetime\.utcnow\(|date\.today\(|"
    r"getpass\.|os\.getpid\(|(?<![\w.])id\(")
_JAVA_MARKERS = ("public class", "public static void main", "System.out.")
# The same course prefixes handle_run_code uses to decide a topic is Java.
JAVA_COURSE_PREFIXES = ("java_", "owasp_", "security_", "memory_safety", "exceptions_",
                        "csrf_", "auth_", "authentication_", "sql_", "xss_",
                        "path_traversal", "static_analysis", "webapp_", "cw1_")

# Why an exercise cannot be checked automatically yet. Stable codes: the E2
# report and the tests use them.
REASONS = {
    "java_not_executable": "Java code cannot run on Synapse at the moment",
    "no_expected_output": "the exercise has no expected output",
    "shortened_expected_output": "the expected output is shortened with '...'",
    "variable_output": "the output changes from run to run (random values, time, ids)",
    "needs_network": "the exercise needs the internet, and the sandbox has none",
    "module_not_in_sandbox": "the exercise needs a library the sandbox does not have",
}


def valid_id(s):
    return isinstance(s, str) and bool(_ID.match(s))


def _walk_exercises(node):
    if isinstance(node, dict):
        if "exercise_id" in node and "expected_output" in node:
            yield node
        for v in node.values():
            yield from _walk_exercises(v)
    elif isinstance(node, list):
        for v in node:
            yield from _walk_exercises(v)


def load_catalogue(directory=CATALOGUE_DIR):
    """{course_id: {exercise_id: exercise}} from the course files on disk.

    Read-only; a broken file is skipped with a message, never half-loaded.
    """
    catalogue = {}
    for path in sorted(Path(directory).glob("*.json")):
        try:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
        except (OSError, ValueError) as e:
            print("grader: skipped %s (%s)" % (path.name, e), flush=True)
            continue
        # The key is the FILE name, because that is the id the course page uses
        # (/static/course_content/<id>.json); five files carry a different
        # course_id inside (e.g. london_transport_active_ai -> london_transport_api).
        course_id = path.stem
        if not valid_id(course_id) or not isinstance(data, dict):
            continue
        exercises = {}
        for ex in _walk_exercises(data):
            ex_id = ex.get("exercise_id")
            if valid_id(ex_id) and ex_id not in exercises:
                exercises[ex_id] = ex
        catalogue[course_id] = exercises
    return catalogue


_catalogue = None


def catalogue():
    global _catalogue
    if _catalogue is None:
        _catalogue = load_catalogue()
    return _catalogue


def find_exercise(course_id, exercise_id, cat=None):
    if not (valid_id(course_id) and valid_id(exercise_id)):
        return None
    return (cat if cat is not None else catalogue()).get(course_id, {}).get(exercise_id)


def _imports(code):
    mods = set()
    for m in re.finditer(r"^\s*(?:from\s+([A-Za-z_][\w.]*)\s+import|import\s+([A-Za-z_][\w., ]*))", code or "", re.M):
        if m.group(1):
            mods.add(m.group(1).split(".")[0])
        else:
            for part in m.group(2).split(","):
                part = part.strip().split(" ")[0]
                if part:
                    mods.add(part.split(".")[0])
    return mods


def is_java(course_id, exercise):
    starter = str(exercise.get("starter_code") or "")
    return str(course_id).startswith(JAVA_COURSE_PREFIXES) or any(m in starter for m in _JAVA_MARKERS)


def unchecked_reasons(course_id, exercise):
    """[] if the exercise can be graded exactly, else the reason codes (see REASONS).

    Explicit rules, each checkable by reading the exercise; nothing is guessed
    from the learner's code.
    """
    reasons = []
    if is_java(course_id, exercise):
        return ["java_not_executable"]
    expected = str(exercise.get("expected_output") or "")
    starter = str(exercise.get("starter_code") or "")
    if not expected.strip():
        reasons.append("no_expected_output")
    if "..." in expected or "…" in expected:
        reasons.append("shortened_expected_output")
    if _VARIABLE_CALLS.search(starter):
        reasons.append("variable_output")
    mods = _imports(starter)
    if mods & _NETWORK_MODULES:
        reasons.append("needs_network")
    stdlib = set(getattr(sys, "stdlib_module_names", ()))
    missing = {m for m in mods - _NETWORK_MODULES if stdlib and m not in stdlib and m not in SANDBOX_EXTRA_MODULES}
    if missing:
        reasons.append("module_not_in_sandbox")
    return reasons


def normalize(text):
    """The comparison rule above, as code. Returns a list of lines."""
    text = (text or "").replace("\r\n", "\n").replace("\r", "\n")
    lines = [ln.rstrip(" \t") for ln in text.split("\n")]
    while lines and lines[0] == "":
        lines.pop(0)
    while lines and lines[-1] == "":
        lines.pop()
    return lines


def _show(s, limit=120):
    s = s if len(s) <= limit else s[:limit] + " [cut]"
    return s if s else "(an empty line)"


def compare(expected, actual):
    """(passed, feedback). Deterministic: same inputs, same answer, every time."""
    exp, got = normalize(expected), normalize(actual)
    if exp == got:
        return True, "Correct! Your output matches the expected output exactly."
    if not got:
        return False, "Your program printed nothing. The exercise expects:\n" + "\n".join(_show(x) for x in exp[:5])
    if [e.lower() for e in exp] == [g.lower() for g in got]:
        for i, (e, g) in enumerate(zip(exp, got), 1):
            if e != g:
                return False, ("Very close: only capital letters differ. Line %d should be:\n%s\n"
                               "Yours is:\n%s" % (i, _show(e), _show(g)))
    for i, (e, g) in enumerate(zip(exp, got), 1):
        if e != g:
            hint = ""
            if " ".join(e.split()) == " ".join(g.split()):
                hint = "\n(Only the spaces inside the line differ.)"
            return False, "Line %d is different.\nExpected: %s\nYours:    %s%s" % (i, _show(e), _show(g), hint)
    if len(got) < len(exp):
        return False, ("Your first %d line(s) are right, but %d line(s) are missing. Next expected line:\n%s"
                       % (len(got), len(exp) - len(got), _show(exp[len(got)])))
    return False, ("All %d expected line(s) are there, but your program prints %d extra line(s), starting with:\n%s"
                   % (len(exp), len(got) - len(exp), _show(got[len(exp)])))


def error_feedback(stderr):
    """The last line of a traceback, which is the one that names the error."""
    lines = [ln for ln in (stderr or "").strip().splitlines() if ln.strip()]
    last = lines[-1].strip() if lines else "an unknown error"
    return "Your code stopped with an error before finishing:\n%s" % _show(last, 200)
