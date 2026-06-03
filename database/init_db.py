"""Initialise the SYNAPSE database from database/schema.sql (single source of truth).

Run once against an EMPTY PostgreSQL database after setting DATABASE_URL in .env:
    python -m database.init_db
"""
import os
from pathlib import Path

from dotenv import load_dotenv
import psycopg2


def main():
    load_dotenv()
    url = os.getenv("DATABASE_URL")
    if not url:
        raise SystemExit(
            "DATABASE_URL is not set. Copy .env.example to .env and fill in your "
            "database credentials (see README -> Running locally)."
        )

    schema_path = Path(__file__).with_name("schema.sql")
    sql = schema_path.read_text(encoding="utf-8")

    # Strip psql client meta-commands (lines beginning with a backslash, e.g. the
    # \restrict / \unrestrict guards recent pg_dump versions emit). They are not SQL
    # and psycopg2 sends the script straight to the server, which would reject them.
    sql = "\n".join(
        line for line in sql.splitlines() if not line.lstrip().startswith("\\")
    )

    # Apply the full schema dump in one shot via a raw psycopg2 connection.
    # (SQLAlchemy's text() cannot run multi-statement scripts; psycopg2 sends the
    # whole dump to the server, which executes every statement.)
    conn = psycopg2.connect(url)
    try:
        conn.autocommit = True
        with conn.cursor() as cur:
            cur.execute(sql)
        print(f"Database initialised from {schema_path.name} "
              f"({sql.count('CREATE TABLE')} tables created).")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
