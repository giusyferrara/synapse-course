#!/usr/bin/env python3
"""
Create the quiz telemetry tables (quiz_attempts, quiz_reviews) in the
configured database. Safe to run repeatedly: create_all only creates what is
missing and never drops or alters existing tables.

Run on the server (where DATABASE_URL points at PostgreSQL):
    python quiz/setup_quiz_tables.py
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.config import engine, Base  # noqa: E402
from database.models import QuizAttempt, QuizReview  # noqa: E402


def main():
    Base.metadata.create_all(engine, tables=[QuizAttempt.__table__, QuizReview.__table__])
    print("Ensured tables exist:", QuizAttempt.__tablename__, "+", QuizReview.__tablename__)


if __name__ == "__main__":
    main()
