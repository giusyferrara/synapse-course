#!/usr/bin/env python3
"""
Research study: is anybody still using it, and archive it before it is removed.

READ ONLY. Every statement it can run is a SELECT; it never writes to the
database. It answers with evidence and writes a CSV archive, because people who
gave consent are owed their data even after the study pages come down.

Signing up is not the same as taking part, so this asks the better question:
when did anybody last DO anything - start the task, submit it, get scored.

Run it on the server as the user that owns the .env:

    sudo -u synapseapp /opt/synapse/python-debug-tutor-mcp/venv/bin/python3 \
        /tmp/research_usage.py [--csv /tmp/research_archive.csv] [--days 90]

Nothing is deleted here. Removing the study is a separate, deliberate step,
and it should happen after reading what this prints.
"""
import argparse
import csv
import os
import sys
from datetime import datetime, timedelta, timezone

try:
    from sqlalchemy import create_engine, text
except ImportError:
    sys.exit("sqlalchemy is not installed in this environment")

CODE_ROOT = "/opt/synapse/python-debug-tutor-mcp/python-debug-tutor-mcp"

# The timestamps are stored naive, in UTC (models.py uses datetime.utcnow as the
# default), so compare against a naive UTC "now" rather than a local one.
NOW = datetime.now(timezone.utc).replace(tzinfo=None)


def database_url():
    """The env var if set, otherwise the .env the app itself reads."""
    if os.getenv("DATABASE_URL"):
        return os.getenv("DATABASE_URL"), "the environment"

    here = os.path.dirname(os.path.abspath(__file__))
    for path in (os.path.join(CODE_ROOT, ".env"),
                 os.path.join(here, "..", ".env"),
                 os.path.join(here, ".env")):
        if not os.path.exists(path):
            continue
        try:
            with open(path, encoding="utf-8", errors="ignore") as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("DATABASE_URL="):
                        return line.split("=", 1)[1].strip().strip('"').strip("'"), path
        except PermissionError:
            return None, "locked:" + path
    return None, None


def ago(when):
    if not when:
        return "never"
    days = (NOW - when).days
    return "%s  (%d days ago)" % (when.strftime("%Y-%m-%d"), days)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", metavar="FILE", help="also write an archive of the table")
    ap.add_argument("--days", type=int, default=90, help="window for the 'recent' counts")
    args = ap.parse_args()

    url, where = database_url()
    if not url:
        if where and where.startswith("locked:"):
            sys.exit("The .env exists but this user cannot read it (%s).\n"
                     "Run it as the user that owns it:\n"
                     "  sudo -u synapseapp %s %s"
                     % (where[7:], sys.executable, os.path.abspath(__file__)))
        sys.exit("No DATABASE_URL found. Run this on the server.")

    engine = create_engine(url)
    with engine.connect() as c:
        if not c.execute(text(
                "SELECT to_regclass('public.research_participants') IS NOT NULL")).scalar():
            print("There is no research_participants table. Nothing to decide.")
            return

        # One question, one query. GREATEST ignores NULLs in Postgres, so this is
        # "the last time this person did anything at all".
        r = c.execute(text("""
            SELECT count(*)                                          AS people,
                   min(created_at)                                   AS first_signup,
                   max(created_at)                                   AS last_signup,
                   count(task_start_time)                            AS started,
                   count(task_submission_time)                       AS submitted,
                   count(*) FILTER (WHERE consent_given IS TRUE)     AS consented,
                   max(GREATEST(created_at, task_start_time, task_end_time,
                                task_submission_time, vuln_scored_at,
                                updated_at))                         AS last_touch
            FROM research_participants
        """)).mappings().one()

        cut = NOW - timedelta(days=args.days)
        active = c.execute(text("""
            SELECT count(*) FROM research_participants
            WHERE GREATEST(created_at, task_start_time, task_end_time,
                           task_submission_time, vuln_scored_at, updated_at) > :cut
        """), {"cut": cut}).scalar()

        print("research_participants")
        print("  people                 %d" % r["people"])
        print("  gave consent           %d" % r["consented"])
        print("  started the task       %d" % r["started"])
        print("  submitted it           %d" % r["submitted"])
        print("  first signed up        %s" % ago(r["first_signup"]))
        print("  last signed up         %s" % ago(r["last_signup"]))
        print("  LAST ACTIVITY of any kind  %s" % ago(r["last_touch"]))
        print("  anyone active in %d days   %d" % (args.days, active))

        quiet = (NOW - r["last_touch"]).days if r["last_touch"] else None
        print()
        if quiet is None:
            print("VERDICT: nothing has ever happened in this table.")
        elif quiet >= 60:
            print("VERDICT: dormant. Nobody has touched it for %d days." % quiet)
            print("Retiring the study pages costs no live participant anything.")
            print("Archive the %d consented rows first: add --csv /tmp/research_archive.csv"
                  % r["consented"])
        elif quiet >= 21:
            print("VERDICT: quiet for %d days, but not cold. Your call." % quiet)
        else:
            print("VERDICT: someone was here %d days ago. Do not remove the pages yet." % quiet)

        if args.csv:
            rows = c.execute(text(
                "SELECT * FROM research_participants ORDER BY id")).mappings().all()
            if rows:
                with open(args.csv, "w", newline="", encoding="utf-8") as f:
                    w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
                    w.writeheader()
                    for row in rows:
                        w.writerow(dict(row))
                print()
                print("archived %d rows to %s" % (len(rows), args.csv))
                print("Keep it somewhere that is not the web server.")


if __name__ == "__main__":
    main()
