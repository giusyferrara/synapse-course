"""Stand-in for the `docker` command in the E1 tests. NO isolation: it only
mimics the interface web/sandbox.py uses, so the timeout, output-cap and kill
logic can be tested on a machine without Docker.

  fake_docker.py run ... python3 -      runs stdin as Python, in this process
  fake_docker.py kill <name>            records the kill in $FAKE_DOCKER_LOG
"""
import os
import sys

args = sys.argv[1:]
if args and args[0] == "kill":
    log = os.environ.get("FAKE_DOCKER_LOG")
    if log:
        with open(log, "a") as f:
            f.write("kill %s\n" % args[1])
    sys.exit(0)
if args and args[0] == "run":
    log = os.environ.get("FAKE_DOCKER_LOG")
    if log:
        with open(log, "a") as f:
            f.write("run %s\n" % " ".join(args[1:]))
    import time
    code = sys.stdin.read()
    if log:
        with open(log, "a") as f:
            f.write("start %.6f\n" % time.time())
    try:
        exec(compile(code, "<learner>", "exec"), {"__name__": "__main__"})
    finally:
        if log:
            with open(log, "a") as f:
                f.write("end %.6f\n" % time.time())
    sys.exit(0)
sys.exit(2)
