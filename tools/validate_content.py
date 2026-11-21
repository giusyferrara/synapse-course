#!/usr/bin/env python3
"""E2 step 2: validate the course content against its reference solutions.

Deterministic, no AI. For every exercise it reports two SEPARATE things:

  output     does the reference program print the expected output?
             (same comparison as the live grader, web/grader.compare)
  teaching   does the reference solution use what the exercise is about?
             (a loop, a condition, a function; or does it just print fixed text?)

A correct output is never taken as proof of teaching quality, and neither of
them is proof that a learner has mastered a skill (that is G0's job).

Programs run ONLY inside bubblewrap (no network, read-only system, private
/tmp, no home folders, unprivileged user, own PID space) under prlimit (memory,
CPU, processes, file size), with a time limit and an output cap. If bwrap is
missing the validator refuses to run anything.

It never changes a course file, a hint or a solution. It writes a report.

    python3 tools/validate_content.py --solutions PATH --report-dir DIR
(run in Linux / WSL, where bwrap is available)
"""
import argparse
import ast
import csv
import json
import os
import re
import shutil
import subprocess
import sys
import time
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve()
REPO = HERE.parent.parent
sys.path.insert(0, str(REPO))
from web import grader  # noqa: E402

TIMEOUT = 5            # seconds per program
MAX_OUTPUT = 64 * 1024  # bytes kept from stdout and stderr each
PYTHON = "/usr/bin/python3"


def isolation_cmd():
    return ["prlimit", "--as=268435456", "--cpu=5", "--nproc=64", "--fsize=1048576", "--nofile=64", "--",
            "bwrap", "--unshare-all", "--die-with-parent", "--new-session", "--cap-drop", "ALL",
            "--uid", "65534", "--gid", "65534",
            "--ro-bind", "/usr", "/usr", "--ro-bind", "/etc/alternatives", "/etc/alternatives",
            "--symlink", "usr/bin", "/bin", "--symlink", "usr/lib", "/lib", "--symlink", "usr/lib64", "/lib64",
            "--proc", "/proc", "--dev", "/dev", "--tmpfs", "/tmp", "--chdir", "/tmp",
            "--clearenv", "--setenv", "PATH", "/usr/bin", "--setenv", "LANG", "C.UTF-8",
            "--setenv", "PYTHONIOENCODING", "utf-8",
            PYTHON, "-I", "-"]


def run_isolated(code):
    """{'ok','stdout','stderr','timed_out','too_much_output'} for one program."""
    p = subprocess.Popen(isolation_cmd(), stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    try:
        out, err = p.communicate(code.encode("utf-8"), timeout=TIMEOUT)
        timed_out = False
    except subprocess.TimeoutExpired:
        p.kill()
        out, err = p.communicate()
        timed_out = True
    too_much = len(out) > MAX_OUTPUT or len(err) > MAX_OUTPUT
    return {"ok": p.returncode == 0 and not timed_out and not too_much,
            "stdout": out[:MAX_OUTPUT].decode("utf-8", "replace"),
            "stderr": err[:MAX_OUTPUT].decode("utf-8", "replace"),
            "timed_out": timed_out, "too_much_output": too_much}


def last_error_line(stderr):
    lines = [ln.strip() for ln in (stderr or "").splitlines() if ln.strip()]
    return lines[-1] if lines else "unknown error"


def first_difference(expected, actual):
    e, g = grader.normalize(expected), grader.normalize(actual)
    for i in range(max(len(e), len(g))):
        a = e[i] if i < len(e) else "(no line)"
        b = g[i] if i < len(g) else "(no line)"
        if a != b:
            return "line %d: expected %r, got %r" % (i + 1, a[:80], b[:80])
    return ""


# ------------------------------------------------------------------ teaching check
# Explicit rules, kept simple on purpose so a person can check them by reading.
NEEDS = {
    # "write/define a function", def, return - NOT "the print() function" or "arguments to print"
    "function": re.compile(r"\bdef\b|\bdefine (?:a |an |the |your own )?\w* ?functions?\b|\bwrite (?:a |an |your own )?\w* ?functions?\b|\bfunctions? (?:that|which|called|named)\b|\bparameters?\b", re.I),
    "loop": re.compile(r"\bloops?\b|\bfor[- ]loop|\bfor each\b|\bwhile\b|\biterat\w*|\brepeat\w*", re.I),
    "condition": re.compile(r"\bif[ -]?(?:statement|/else|-else|else)\b|\belif\b|\bconditions?\b|\bconditional\b", re.I),
}
# the title names the topic most reliably ("Exercise 1: Simple if", "Nested loops")
TITLE_NEEDS = {
    "condition": re.compile(r"\bif\b|\belif\b|\belse\b|\bternary\b|\bcondition", re.I),
    "loop": re.compile(r"\bloops?\b|\bfor\b|\bwhile\b|\biterat|\bbreak\b|\bcontinue\b", re.I),
    "function": re.compile(r"\bdef\b|\bdefin|\breturn\b|\breturning\b|\bparameters?\b|\barguments?\b|\blambda\b|\bown functions?\b", re.I),
}
STARTER_NEEDS = {
    "function": re.compile(r"^\s*def\s", re.M),
    "loop": re.compile(r"^\s*(for|while)\s", re.M),
    "condition": re.compile(r"^\s*(if|elif)\s", re.M),
}
# In these courses a solution that only prints text typed by hand (no variable,
# no expression worked out by Python) cannot be what the exercise teaches.
NO_FIXED_TEXT = {"py_variables_datatypes", "py_conditions_loops", "py_functions_modules"}
# what a whole course is about: a solution must use at least ONE of these
COURSE_TOPIC = {
    "py_conditions_loops": ("condition", "loop"),
    "py_functions_modules": ("function", "module"),
}
VARIABLE_IN_SOLUTION = re.compile(
    r"\brandom\.|\bimport random\b|\bsecrets\.|os\.urandom|\buuid\.|time\.time\(|datetime\.now\(|"
    r"datetime\.utcnow\(|date\.today\(|\binput\s*\(")


def required_constructs(ex):
    title = re.sub(r"^\s*exercise\s+\d+\s*:\s*", "", ex.get("title", ""), flags=re.I)
    desc = ex.get("description", "")
    starter = ex.get("starter_code") or ""
    return sorted(k for k in NEEDS
                  if TITLE_NEEDS[k].search(title) or NEEDS[k].search(desc) or STARTER_NEEDS[k].search(starter))


def constructs_in(code):
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return None
    found = set()
    for n in ast.walk(tree):
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)):
            found.add("function")
        if isinstance(n, (ast.For, ast.While, ast.comprehension)):
            found.add("loop")
        if isinstance(n, (ast.If, ast.IfExp)) or n.__class__.__name__ == "Match":
            found.add("condition")
        if isinstance(n, (ast.Import, ast.ImportFrom)):
            found.add("module")
        if isinstance(n, (ast.Assign, ast.AugAssign, ast.AnnAssign, ast.NamedExpr)):
            found.add("variable")
    return found


def prints_fixed_text_only(code):
    """True if the program only print()s text typed by hand: no variable, and no
    expression Python has to work out (10 + 3, 2 ** 8, ord('A') are worked out)."""
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return False
    if not tree.body:
        return False
    for st in tree.body:
        if not (isinstance(st, ast.Expr) and isinstance(st.value, ast.Call)
                and isinstance(st.value.func, ast.Name) and st.value.func.id == "print"):
            return False
        for arg in list(st.value.args) + [k.value for k in st.value.keywords]:
            for node in ast.walk(arg):
                if not isinstance(node, (ast.Constant, ast.JoinedStr, ast.expr_context)):
                    return False
    return True


def teaching_check(course, ex, code):
    """(status, needs, uses). Separate from the output check on purpose."""
    need = required_constructs(ex)
    if code is None:
        return "not assessed (no runnable solution)", need, []
    have = constructs_in(code) or set()
    missing = [k for k in need if k not in have]
    if missing:
        return "MISSING: " + ", ".join(missing), need, sorted(have)
    topic = COURSE_TOPIC.get(course)
    if topic and not (have & set(topic)):
        return "MISSING course topic: uses none of " + "/".join(topic), need, sorted(have)
    if (need or topic or course in NO_FIXED_TEXT) and prints_fixed_text_only(code):
        return "prints fixed text only (computes nothing)", need, sorted(have)
    if not need and not topic:
        return "no construct required (by the rules)", need, sorted(have)
    return "uses " + ", ".join(sorted(set(need) | (have & set(topic or ())))), need, sorted(have)


# ------------------------------------------------------------------ one exercise
def validate(course, ex_id, ex, sol):
    row = {"course": course, "exercise_id": ex_id, "title": ex.get("title", "")[:80],
           "kind": sol["kind"], "form": sol.get("form") or "", "flags": ";".join(sol.get("flags", [])),
           "checkable": "", "output": "", "detail": "", "reference": "", "teaching": "",
           "needs": "", "uses": ""}
    reasons = grader.unchecked_reasons(course, ex)
    row["checkable"] = "yes" if not reasons else "no: " + ";".join(reasons)
    expected = ex.get("expected_output", "")
    starter = ex.get("starter_code") or ""

    def try_programs(programs):
        """First program whose output matches; else the most informative failure."""
        best = None
        for label, prog in programs:
            r = run_isolated(prog)
            if r["timed_out"]:
                res = ("TIMEOUT", "still running after %ds" % TIMEOUT, label, prog)
            elif r["too_much_output"]:
                res = ("TOO MUCH OUTPUT", "more than %d bytes" % MAX_OUTPUT, label, prog)
            elif not r["ok"]:
                res = ("ERROR", last_error_line(r["stderr"]), label, prog)
            else:
                ok, _ = grader.compare(expected, r["stdout"])
                res = ("MATCH", "", label, prog) if ok else ("MISMATCH", first_difference(expected, r["stdout"]), label, prog)
            if res[0] == "MATCH":
                return res
            if best is None or (best[0] == "ERROR" and res[0] == "MISMATCH"):
                best = res
        return best

    code_for_teaching = None
    if reasons:
        row["output"] = "NOT CHECKABLE"
        row["detail"] = "; ".join(grader.REASONS[r] for r in reasons)
    elif sol["kind"] in ("solution", "fix") and sol.get("form") in ("code", "alternatives"):
        alts = sol.get("alternatives") or [sol["code"]]
        progs = [("solution" + (" (alternative %d)" % (i + 1) if len(alts) > 1 else ""), a) for i, a in enumerate(alts)]
        progs += [("starter code + solution" + (" (alternative %d)" % (i + 1) if len(alts) > 1 else ""), starter + "\n" + a)
                  for i, a in enumerate(alts) if starter.strip()]
        status, detail, label, prog = try_programs(progs)
        row.update(output=status, detail=detail, reference=label)
        notes = []
        if re.search(r"\bvar(y|ies)\b|\bmust include\b|\be\.g\.|\bexample\b|\bsomething like\b", expected, re.I):
            notes.append("expected_output looks like a DESCRIPTION, not an output: a learner can never match it")
        if any(VARIABLE_IN_SOLUTION.search(x) for x in alts):
            notes.append("the solution uses time, random values or input(): the output cannot be fixed")
        if notes:
            row["detail"] = "; ".join([row["detail"]] + notes if row["detail"] else notes)
        code_for_teaching = prog if status == "MATCH" else alts[0]
        if sol["kind"] == "fix" and starter.strip():
            # a find-and-fix exercise must start broken
            r = run_isolated(starter)
            if r["ok"] and grader.compare(expected, r["stdout"])[0]:
                row["detail"] = (row["detail"] + "; " if row["detail"] else "") + "the starter code ALREADY prints the expected output: nothing to fix"
    elif sol["kind"] == "output":
        status, detail, label, prog = try_programs([("starter code (predict-the-output)", starter)])
        row.update(output=status, detail=detail, reference=label)
        shown = sol.get("shown_output", "")
        if shown and grader.normalize(shown) != grader.normalize(expected):
            row["detail"] = (row["detail"] + "; " if row["detail"] else "") + "the hint shows a different output than expected_output"
        code_for_teaching = None   # predicting output: the learner writes no code
    else:
        row["output"] = "NO RUNNABLE SOLUTION"
        row["detail"] = {"fragment": "the third hint is a piece to place in the starter code",
                         "explanation": "the third hint explains in words, there is no code",
                         "broken": "the third hint looks like code but does not parse"}.get(
            sol.get("form") or "", "no labelled solution in the third hint" if sol["kind"] == "other" else "no third hint")

    if sol["kind"] == "output":
        row["teaching"] = "not applicable (predict-the-output exercise)"
    else:
        row["teaching"], need, have = teaching_check(course, ex, code_for_teaching)
        row["needs"], row["uses"] = ",".join(need), ",".join(have)
    return row


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--solutions", required=True)
    ap.add_argument("--report-dir", required=True)
    a = ap.parse_args()
    for tool in ("bwrap", "prlimit"):
        if not shutil.which(tool):
            sys.exit("STOPPED: %s is not available, so programs cannot be run in isolation. Nothing was run." % tool)
    rep = Path(a.report_dir).resolve()
    if rep == REPO or REPO in rep.parents:
        sys.exit("refusing to write the report inside the public repository")
    probe = run_isolated("import socket\ntry:\n    socket.create_connection(('1.1.1.1', 53), timeout=2)\n    print('NET')\nexcept OSError:\n    print('nonet')\n")
    if probe["stdout"].strip() != "nonet":
        sys.exit("STOPPED: the isolation check failed (network reachable or sandbox broken): %r" % probe)

    sols = json.load(open(a.solutions, encoding="utf-8"))["courses"]
    cat = grader.load_catalogue()
    rows, t0 = [], time.time()
    for course, exs in sols.items():
        for ex_id, sol in exs.items():
            rows.append(validate(course, ex_id, cat[course][ex_id], sol))
    rep.mkdir(parents=True, exist_ok=True)
    with open(rep / "validation-first-stretch.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    out = Counter(r["output"] for r in rows)
    teach = Counter(r["teaching"].split(":")[0] for r in rows)
    print("validated %d exercises in %.0fs" % (len(rows), time.time() - t0))
    print("output:  ", dict(out))
    print("teaching:", dict(teach))
    print("report:  ", rep / "validation-first-stretch.csv")


if __name__ == "__main__":
    main()
