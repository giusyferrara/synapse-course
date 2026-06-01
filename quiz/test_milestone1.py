#!/usr/bin/env python3
"""
Local milestone-1 verification: loader + grading + SM-2 + persistence.

Runs against a throwaway SQLite database so it needs NO PostgreSQL.
DATABASE_URL is set before importing database.config so the same models/engine
machinery works unchanged on SQLite.
"""
import datetime
import os
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

# Point the app's DB layer at a temp SQLite file BEFORE importing it.
_DB_PATH = os.path.join(tempfile.gettempdir(), "quiz_milestone1_test.db")
if os.path.exists(_DB_PATH):
    os.remove(_DB_PATH)
os.environ["DATABASE_URL"] = "sqlite:///" + _DB_PATH.replace("\\", "/")

from database import config  # noqa: E402
from database.models import QuizAttempt, QuizReview  # noqa: E402
from quiz import quiz_engine  # noqa: E402

PASS, FAIL = "PASS", "FAIL"
results = []


def check(name, cond):
    results.append((name, bool(cond)))
    print(f"  [{PASS if cond else FAIL}] {name}")


def main():
    print("== 1. Loader + bank validation ==")
    bank = quiz_engine.load_bank()
    check("bank loads (>=200 questions)", len(bank) >= 200)
    check("every question validates (exactly one correct, unique opts)",
          all(quiz_engine.validate_question(q) is None for q in bank.all()))
    cats = set(bank.by_category().keys())
    check("all 5 categories present",
          cats == {"detect", "understand", "remediate", "severity", "tooling"})

    print("\n== 2. Grading (by option id) ==")
    q = bank.get("detect_cwe352_csrf_0001")
    cid = quiz_engine.correct_option_id(q)
    right = quiz_engine.grade(q, cid)
    wrong_id = next(o["id"] for o in q["options"] if o["id"] != cid)
    wrong = quiz_engine.grade(q, wrong_id)
    check("correct answer graded correct", right["is_correct"] is True)
    check("wrong answer graded incorrect", wrong["is_correct"] is False)
    check("feedback carries explanation + source", bool(right["explanation"]) and bool(right["source_reference"]))
    try:
        quiz_engine.grade(q, "Z")
        check("invalid option rejected", False)
    except ValueError:
        check("invalid option rejected", True)

    print("\n== 3. SM-2 lite transitions ==")
    now = datetime.datetime(2026, 6, 1, 12, 0, 0)
    s1 = quiz_engine.sm2_update({}, True, now)
    check("first correct -> 1 day interval", s1["interval_days"] == 1.0 and s1["consecutive_correct"] == 1)
    s2 = quiz_engine.sm2_update(s1, True, now)
    check("second correct -> 3 day interval", s2["interval_days"] == 3.0 and s2["consecutive_correct"] == 2)
    s3 = quiz_engine.sm2_update(s2, True, now)
    check("third correct -> interval grows by ease", s3["interval_days"] > 3.0)
    sf = quiz_engine.sm2_update(s3, False, now)
    check("wrong -> reset streak, resurface within the hour",
          sf["consecutive_correct"] == 0 and sf["next_due_at"] < now + datetime.timedelta(hours=1))
    check("wrong -> ease decreased but >= floor", quiz_engine.MIN_EASE <= sf["ease"] < s3["ease"])

    print("\n== 4. Persistence (SQLite) ==")
    config.Base.metadata.create_all(config.engine,
                                    tables=[QuizAttempt.__table__, QuizReview.__table__])
    session = config.SessionLocal()
    try:
        r1 = quiz_engine.record_answer(session, bank, "stu1", "detect_cwe352_csrf_0001", cid, time_ms=1500, now=now)
        session.commit()
        check("record_answer returns correct grade", r1["is_correct"] is True)
        check("one QuizAttempt row written", session.query(QuizAttempt).count() == 1)
        rev = session.query(QuizReview).filter_by(student_id="stu1", question_id="detect_cwe352_csrf_0001").one()
        check("QuizReview created with interval 1 day", rev.interval_days == 1.0 and rev.consecutive_correct == 1)

        # answer the SAME question wrong -> review resets, no duplicate review row
        r2 = quiz_engine.record_answer(session, bank, "stu1", "detect_cwe352_csrf_0001", wrong_id,
                                       time_ms=800, now=now + datetime.timedelta(days=1))
        session.commit()
        check("second attempt logged (2 attempts total)", session.query(QuizAttempt).count() == 2)
        check("review upserted, not duplicated (still 1 review row)",
              session.query(QuizReview).filter_by(student_id="stu1").count() == 1)
        rev2 = session.query(QuizReview).filter_by(student_id="stu1", question_id="detect_cwe352_csrf_0001").one()
        check("wrong answer reset the review streak", rev2.consecutive_correct == 0)

        # a different student is isolated
        quiz_engine.record_answer(session, bank, "stu2", "detect_cwe22_pathtraversal_0001",
                                  quiz_engine.correct_option_id(bank.get("detect_cwe22_pathtraversal_0001")), now=now)
        session.commit()
        check("per-student isolation (stu2 has its own review)",
              session.query(QuizReview).filter_by(student_id="stu2").count() == 1)
    finally:
        session.close()

    print("\n" + "=" * 50)
    n_pass = sum(1 for _, ok in results if ok)
    print(f"RESULT: {n_pass}/{len(results)} checks passed")
    if n_pass != len(results):
        print("FAILURES:", [n for n, ok in results if not ok])
        sys.exit(1)
    print("Milestone 1 OK")


if __name__ == "__main__":
    main()
