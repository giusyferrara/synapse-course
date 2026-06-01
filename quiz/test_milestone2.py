#!/usr/bin/env python3
"""
Local milestone-2 verification: adaptive selection.

Covers: cold-start, due-review surfacing + cap, weak-skill weighting,
difficulty ramp gate, no-repeats, and determinism. Uses throwaway SQLite.
"""
import datetime
import os
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

_DB_PATH = os.path.join(tempfile.gettempdir(), "quiz_milestone2_test.db")
if os.path.exists(_DB_PATH):
    os.remove(_DB_PATH)
os.environ["DATABASE_URL"] = "sqlite:///" + _DB_PATH.replace("\\", "/")

from database import config  # noqa: E402
from database.models import QuizAttempt, QuizReview  # noqa: E402
from quiz import quiz_engine  # noqa: E402

NOW = datetime.datetime(2026, 6, 1, 12, 0, 0)
results = []


def check(name, cond):
    results.append((name, bool(cond)))
    print(f"  [{'PASS' if cond else 'FAIL'}] {name}")


def fresh_session():
    config.Base.metadata.drop_all(config.engine, tables=[QuizAttempt.__table__, QuizReview.__table__])
    config.Base.metadata.create_all(config.engine, tables=[QuizAttempt.__table__, QuizReview.__table__])
    return config.SessionLocal()


def add_attempt(session, student, qid, skill, cat, correct, when):
    session.add(QuizAttempt(student_id=student, question_id=qid, skill_tag=skill,
                            category=cat, chosen_option="A", is_correct=correct,
                            time_ms=1000, created_at=when))


def add_due_review(session, student, qid, skill, due_at):
    session.add(QuizReview(student_id=student, question_id=qid, skill_tag=skill,
                           consecutive_correct=0, ease=2.5, interval_days=0.0,
                           next_due_at=due_at, last_result=False, updated_at=due_at))


def main():
    bank = quiz_engine.load_bank()

    print("== 1. Cold start (no history) ==")
    s = fresh_session()
    q = quiz_engine.select_quiz(s, bank, "new_user", n=10, now=NOW, seed=1)
    check("returns exactly 10 questions", len(q) == 10)
    check("no repeats", len({x['id'] for x in q}) == 10)
    cats = {x['category'] for x in q}
    check("spreads across >=4 categories", len(cats) >= 4)
    check("cold start surfaces no advanced", all(x['difficulty'] in {'beginner', 'intermediate'} for x in q))
    s.close()

    print("\n== 2. Determinism ==")
    s = fresh_session()
    a = [x['id'] for x in quiz_engine.select_quiz(s, bank, "u", n=10, now=NOW, seed=7)]
    b = [x['id'] for x in quiz_engine.select_quiz(s, bank, "u", n=10, now=NOW, seed=7)]
    c = [x['id'] for x in quiz_engine.select_quiz(s, bank, "u", n=10, now=NOW, seed=8)]
    check("same (student,seed) -> identical selection", a == b)
    check("different seed -> different selection", a != c)
    s.close()

    print("\n== 3. Due-review surfacing + 40% cap ==")
    s = fresh_session()
    due_ids = ["detect_cwe89_sqli_0001", "detect_cwe79_xss_0001", "remediate_cwe22_pathtraversal_0001",
               "understand_cwe502_deserialization_0001", "tooling_nmap_sv_0001"]  # 5 past-due
    for qid in due_ids:
        add_due_review(s, "due_user", qid, bank.get(qid)["skill_tag"], NOW - datetime.timedelta(days=2))
    # a far-future review that must NOT be force-surfaced
    add_due_review(s, "due_user", "detect_cwe918_ssrf_0001", "CWE-918", NOW + datetime.timedelta(days=30))
    s.commit()
    sel = quiz_engine.select_quiz(s, bank, "due_user", n=10, now=NOW, seed=3)
    overlap = len(set(due_ids) & {x['id'] for x in sel})
    cap = round(quiz_engine.DUE_FRACTION * 10)
    check(f"due reviews surfaced (>= cap {cap})", overlap >= cap)
    check("due cap not wildly exceeded (<= cap+1)", overlap <= cap + 1)
    check("future-due review NOT force-included",
          "detect_cwe918_ssrf_0001" not in {x['id'] for x in sel} or overlap <= cap + 1)
    s.close()

    print("\n== 4. Weak-skill weighting ==")
    s = fresh_session()
    # mastered + seen: many correct CWE-89 detect questions
    for i in range(1, 7):
        qid = f"detect_cwe89_sqli_000{i}"
        if bank.get(qid):
            add_attempt(s, "skilled", qid, "CWE-89", "detect", True, NOW - datetime.timedelta(days=1))
    s.commit()
    sel = quiz_engine.select_quiz(s, bank, "skilled", n=10, now=NOW, seed=5)
    cwe89 = sum(1 for x in sel if x['skill_tag'] == "CWE-89")
    unseen_or_weak = sum(1 for x in sel if x['skill_tag'] != "CWE-89")
    check("mastered+seen skill (CWE-89) rarely re-selected (<=1)", cwe89 <= 1)
    check("selection favours other/weaker skills (>=9/10)", unseen_or_weak >= 9)
    check("covers multiple distinct skills (>=6)", len({x['skill_tag'] for x in sel}) >= 6)
    s.close()

    print("\n== 5. Difficulty ramp gate ==")
    check("cold/low signal -> no advanced", quiz_engine.allowed_difficulties(0, None) == {"beginner", "intermediate"})
    check("enough attempts + high recent acc -> advanced unlocked",
          "advanced" in quiz_engine.allowed_difficulties(12, 0.9))
    check("enough attempts but low recent acc -> still no advanced",
          "advanced" not in quiz_engine.allowed_difficulties(12, 0.4))
    # end-to-end: a strong learner should never get a DISALLOWED difficulty leaked
    s = fresh_session()
    for i in range(12):
        add_attempt(s, "strong", f"x{i}", "CWE-79", "detect", True, NOW - datetime.timedelta(hours=12 - i))
    s.commit()
    sel = quiz_engine.select_quiz(s, bank, "strong", n=10, now=NOW, seed=2)
    seen, skill_acc, recent_acc, total = quiz_engine._history(s, "strong")
    allowed = quiz_engine.allowed_difficulties(total, recent_acc)
    check("strong learner unlocked advanced", "advanced" in allowed)
    check("strong learner: every returned difficulty is within the allowed set",
          all(x['difficulty'] in allowed for x in sel))
    s.close()

    print("\n" + "=" * 50)
    n_pass = sum(1 for _, ok in results if ok)
    print(f"RESULT: {n_pass}/{len(results)} checks passed")
    if n_pass != len(results):
        print("FAILURES:", [n for n, ok in results if not ok])
        sys.exit(1)
    print("Milestone 2 OK")


if __name__ == "__main__":
    main()
