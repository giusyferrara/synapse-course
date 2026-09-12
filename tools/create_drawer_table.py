#!/usr/bin/env python3
"""Create the drawer's table, once, on a database that already has everything else.

`database/init_db.py` builds a whole empty database; this adds the one new table
to a running one without touching anything already there. It is idempotent —
running it twice is a no-op — and it creates nothing but `saved_views`.

Run it on the server as the user that owns the .env, before restarting:

    sudo -u synapseapp /opt/synapse/python-debug-tutor-mcp/venv/bin/python3 \
        /opt/synapse/python-debug-tutor-mcp/python-debug-tutor-mcp/tools/create_drawer_table.py

It prints the columns it ends up with, so you can see what happened rather than
trust that it worked.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

CODE_ROOT = "/opt/synapse/python-debug-tutor-mcp/python-debug-tutor-mcp"


def load_env():
    """Same lookup the research tool uses: the env var, else the app's own .env."""
    if os.getenv("DATABASE_URL"):
        return True
    here = os.path.dirname(os.path.abspath(__file__))
    for path in (os.path.join(CODE_ROOT, ".env"),
                 os.path.join(here, "..", ".env")):
        if not os.path.exists(path):
            continue
        try:
            with open(path, encoding="utf-8", errors="ignore") as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("DATABASE_URL="):
                        os.environ["DATABASE_URL"] = line.split("=", 1)[1].strip().strip('"').strip("'")
                        return True
        except PermissionError:
            sys.exit("The .env exists but this user cannot read it (%s).\n"
                     "Run it as the user that owns it:\n"
                     "  sudo -u synapseapp %s %s" % (path, sys.executable, os.path.abspath(__file__)))
    return False


if not load_env():
    sys.exit("No DATABASE_URL found. Run this on the server.")

from sqlalchemy import inspect                      # noqa: E402
from database.config import engine                  # noqa: E402
from database.models import SavedView               # noqa: E402

table = SavedView.__table__
existed = inspect(engine).has_table(table.name)

table.create(bind=engine, checkfirst=True)

print("table            %s" % table.name)
print("already present  %s" % ("yes — nothing was changed" if existed else "no — it was created now"))
print("columns:")
for col in inspect(engine).get_columns(table.name):
    print("  %-12s %s%s" % (col["name"], col["type"], "" if col["nullable"] else "  not null"))
for idx in inspect(engine).get_indexes(table.name):
    print("index            %s on %s%s" % (idx["name"], ", ".join(idx["column_names"]),
                                           "  (unique)" if idx.get("unique") else ""))
print()
print("Nothing else in the database was touched. Restart the service to pick up the routes.")
