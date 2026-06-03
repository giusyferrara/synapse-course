"""Initialise the SYNAPSE database: create all tables.

Run once after creating an empty PostgreSQL database and setting DATABASE_URL in .env:
    python -m database.init_db
"""
from pathlib import Path
from sqlalchemy import text
from database.config import engine, Base
import database.models  # noqa: F401 - registers all ORM models on Base.metadata


def main():
    Base.metadata.create_all(engine)
    print("Created all ORM tables.")
    # Apply extra SQL schema (lesson-content tables) if present.
    schema = Path(__file__).with_name("lesson_content_schema.sql")
    if schema.exists():
        try:
            with engine.begin() as conn:
                conn.execute(text(schema.read_text()))
            print("Applied lesson_content_schema.sql.")
        except Exception as e:
            print(f"Note: could not auto-apply lesson_content_schema.sql ({e}).")
            print("Run it manually if needed: psql $DATABASE_URL -f database/lesson_content_schema.sql")
    print("Database initialised.")


if __name__ == "__main__":
    main()
