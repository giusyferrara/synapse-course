#!/usr/bin/env python3
"""E2 step 1: pull the reference solutions out of the third hint of each exercise.

Reads the course files (never changes them), executes NOTHING, and writes one
private JSON file OUTSIDE this public repository, at a path you must give.
It refuses to write anywhere inside this repo.

    python tools/extract_solutions.py --out PATH_OUTSIDE_THIS_REPO [course_id ...]

Every exercise gets exactly one `kind`, read from the label of its third hint:
    solution   "Solution: <code>"       the reference program (or a fragment of it)
    fix        "Fix: <code>"            a find-and-fix exercise: the corrected code
    output     "Output: <text>"         a predict-the-output exercise: no solution code;
                                        the starter program itself is the reference
    other      a third hint with no recognised label
    missing    no third hint
and, for solution/fix, a `form` decided WITHOUT running anything:
    code          parses as Python
    alternatives  "A  or  B": several answers; each is kept, the first is tried first
    explanation   words, not code
    broken        looks like code but does not parse
Defects of the text itself are listed in `flags` (e.g. escaped_newlines: the hint
shows a literal "\\n" to the learner instead of a new line).
"""
import argparse
import ast
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve()
REPO = HERE.parent.parent
sys.path.insert(0, str(REPO))
from web import grader  # noqa: E402

FIRST_STRETCH = ["py_syntax_output", "py_variables_datatypes", "py_conditions_loops", "py_functions_modules"]
LABEL = re.compile(r"^\s*(solution|fix|output)\s*:\s*", re.I)


def parses(src):
    try:
        ast.parse(src)
        return True
    except SyntaxError:
        return False


INSTRUCTION = re.compile(r"^\s*(add|change|move|remove|indent|put|use|replace|delete|insert)\b", re.I)


def complete_program(src):
    """Parses, and is not just a block header such as 'if x == 5:' or 'def f(a):'."""
    if not parses(src):
        return False
    tree = ast.parse(src)
    return bool(tree.body)


def decoded(body):
    """Undo a literal "\\n" used as a LINE BREAK in the hint text. Only tried when
    the text does not parse as it is, because inside a Python string "\\n" is
    a real escape that must stay (print("Line 1\\nLine 2"))."""
    return body.replace("\\n", "\n").replace("\\t", "\t").strip("\n")


def classify(ex):
    hints = ex.get("hints") or []
    if len(hints) < 3:
        return {"kind": "missing", "form": None, "code": None, "alternatives": [], "flags": [], "raw": None}
    h = hints[2]
    raw = h.get("message") if isinstance(h, dict) else str(h)
    raw = raw or ""
    flags = []
    m = LABEL.match(raw)
    kind = m.group(1).lower() if m else "other"
    body = (raw[m.end():] if m else raw).strip("\n")
    entry = {"kind": kind, "raw": raw, "flags": flags, "code": None, "alternatives": [], "form": None}
    if kind == "output":
        if "\\n" in body:
            flags.append("escaped_newlines")
            body = decoded(body)
        entry["shown_output"] = body.strip("\n")
        return entry
    if kind not in ("solution", "fix"):
        return entry

    def settle(text):
        """(form, code, alternatives) for one candidate text, or None.
        "print(A) or print(B)" parses as ONE Python expression that prints twice,
        but in a hint it means two acceptable answers: alternatives are checked first."""
        alts = [a.strip() for a in re.split(r"\s+(?:or|OR)\s+(?=print\s*\(|[A-Za-z_]\w*\s*=[^=])", text) if a.strip()]
        if len(alts) > 1:
            good = [a for a in alts if complete_program(a)]
            if good:
                return ("alternatives", good[0], good)
        if complete_program(text):
            return ("code", text, [])
        return None

    if INSTRUCTION.match(body):
        entry["form"] = "explanation"          # words telling what to change, not a program
        return entry
    got = settle(body)
    if got is None and "\\n" in body:
        got = settle(decoded(body))
        if got is not None:
            flags.append("escaped_newlines")   # the learner sees a literal \n in this hint
    if got is not None:
        entry["form"], entry["code"], entry["alternatives"] = got
    elif any(re.match(r"^\s*(if|elif|else|for|while|def)\b[^\n]*:\s*(\n|$)", t) for t in (body, decoded(body))):
        entry.update(form="fragment", code=decoded(body) if "\\n" in body else body)  # a piece to put into the starter code
        if "\\n" in body:
            flags.append("escaped_newlines")
    else:
        entry.update(form="broken", code=body)
    return entry


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True, help="a path OUTSIDE this repository")
    ap.add_argument("courses", nargs="*", default=FIRST_STRETCH)
    a = ap.parse_args()
    out = Path(a.out).resolve()
    if out == REPO or REPO in out.parents:
        sys.exit("refusing to write solutions inside the public repository: %s" % out)

    cat = grader.load_catalogue()
    data = {"source": "third hint of each exercise in static/course_content (unchanged)",
            "courses": {}}
    for course in a.courses:
        exercises = cat.get(course)
        if exercises is None:
            sys.exit("unknown course: %s" % course)
        data["courses"][course] = {ex_id: dict(classify(ex), title=ex.get("title", ""))
                                   for ex_id, ex in exercises.items()}
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", encoding="utf-8", newline="\n") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    n = sum(len(v) for v in data["courses"].values())
    print("wrote %d exercises from %d courses to %s" % (n, len(a.courses), out))


if __name__ == "__main__":
    main()
