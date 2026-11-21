"""
The one place where a learner's Python runs: a throwaway Docker container.
Never in the web process.

Limits (all of them, every run):
  no network; 64 MB memory, no swap; half a CPU; at most 50 processes;
  read-only file system with a 10 MB /tmp; no new privileges; every Linux
  capability dropped; the image's own unprivileged user `sandbox`.
  At most RUN_TIMEOUT seconds, and at most MAX_OUTPUT bytes on stdout and on
  stderr: past either, the container itself is killed by name, not only the
  docker client, so a runaway program cannot keep a CPU busy after the learner
  has been told "timed out".
"""
import asyncio
import contextlib
import os
import tempfile
import time
import uuid
from collections import defaultdict, deque

IMAGE = "synapse-sandbox"
RUN_TIMEOUT = 10          # seconds the program may run
MAX_OUTPUT = 64 * 1024    # bytes kept from stdout and from stderr, each
DOCKER = ["docker"]       # the tests replace this with a stand-in

# How many sandbox containers may run at once on the WHOLE server. Enforced
# with one lock file per slot (flock), so it holds across processes, not only
# inside this one, and a process that dies gives its slot back by itself.
MAX_CONTAINERS = 4
SLOT_WAIT = 5.0           # seconds a request waits for a free slot, then "busy"
SLOT_DIR = os.environ.get("SANDBOX_SLOT_DIR") or os.path.join(tempfile.gettempdir(), "synapse-sandbox-slots")

# Per learner, Run and Check Solution together.
RUNS_PER_MINUTE = 20


class Busy(Exception):
    """Every slot stayed taken for SLOT_WAIT seconds."""


class RateLimited(Exception):
    def __init__(self, retry_after):
        super().__init__("rate limited")
        self.retry_after = max(1, int(retry_after + 0.999))


class RunLimiter:
    """At most `limit` runs per `window` seconds per key. The key is decided
    by the server (the signed session's user id, or the address nginx wrote),
    never by anything in the request body. In memory: Synapse runs as ONE
    process (checked 21 Nov 2026), like the AI budget in web/ai_budget.py."""

    def __init__(self, limit=None, window=60.0, clock=None):
        self.limit = RUNS_PER_MINUTE if limit is None else limit
        self.window = window
        self._clock = clock or time.monotonic
        self._runs = defaultdict(deque)

    def check(self, key):
        """Count one run for key, or raise RateLimited without counting it."""
        now = self._clock()
        q = self._runs[key]
        while q and now - q[0] >= self.window:
            q.popleft()
        if len(q) >= self.limit:
            raise RateLimited(self.window - (now - q[0]))
        q.append(now)
        if len(self._runs) > 10000:          # forget idle keys, bound the memory
            for k in [k for k, v in self._runs.items() if not v or now - v[-1] >= self.window]:
                del self._runs[k]


limiter = RunLimiter()


@contextlib.asynccontextmanager
async def slot(wait=None):
    """Hold one of MAX_CONTAINERS server-wide slots while a container runs."""
    import fcntl
    wait = SLOT_WAIT if wait is None else wait
    os.makedirs(SLOT_DIR, mode=0o700, exist_ok=True)
    deadline = time.monotonic() + wait
    fd = None
    while fd is None:
        for i in range(MAX_CONTAINERS):
            f = os.open(os.path.join(SLOT_DIR, "slot-%d" % i), os.O_RDWR | os.O_CREAT, 0o600)
            try:
                fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
                fd = f
                break
            except BlockingIOError:
                os.close(f)
        if fd is None:
            if time.monotonic() >= deadline:
                raise Busy()
            await asyncio.sleep(0.1)
    try:
        yield
    finally:
        fcntl.flock(fd, fcntl.LOCK_UN)
        os.close(fd)


def docker_args(name):
    return DOCKER + ["run", "--rm", "-i", "--name", name,
                     "--network", "none", "--memory", "64m", "--memory-swap", "64m",
                     "--cpus", "0.5", "--pids-limit", "50",
                     "--read-only", "--tmpfs", "/tmp:size=10m",
                     "--security-opt", "no-new-privileges", "--cap-drop", "ALL",
                     "--user", "sandbox",
                     IMAGE, "python3", "-"]


async def _read_capped(stream, limit):
    """Up to limit bytes. Returns (data, overflowed); stops reading at the limit."""
    buf = bytearray()
    while True:
        chunk = await stream.read(8192)
        if not chunk:
            return bytes(buf), False
        if len(buf) + len(chunk) > limit:
            buf += chunk[:limit - len(buf)]
            return bytes(buf), True
        buf += chunk


async def _drain(stream):
    while await stream.read(65536):
        pass


async def _kill(name):
    try:
        p = await asyncio.create_subprocess_exec(
            *DOCKER, "kill", name,
            stdout=asyncio.subprocess.DEVNULL, stderr=asyncio.subprocess.DEVNULL)
        await asyncio.wait_for(p.wait(), timeout=10)
    except Exception:
        pass


async def run_python(code, timeout=None, max_output=None):
    """Run code in the sandbox, inside one of the server-wide slots.
    Returns a dict: ok, stdout, stderr, timed_out, too_much_output, exit_code
    (ok means: exit code 0 and no limit was hit). Raises Busy if no slot frees
    up within SLOT_WAIT seconds."""
    async with slot():
        return await _run_in_container(code, timeout, max_output)


async def _run_in_container(code, timeout=None, max_output=None):
    timeout = RUN_TIMEOUT if timeout is None else timeout
    max_output = MAX_OUTPUT if max_output is None else max_output
    name = "synapse-sbx-" + uuid.uuid4().hex[:16]
    loop = asyncio.get_running_loop()
    deadline = loop.time() + timeout
    proc = await asyncio.create_subprocess_exec(
        *docker_args(name),
        stdin=asyncio.subprocess.PIPE, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
    out_task = asyncio.ensure_future(_read_capped(proc.stdout, max_output))
    err_task = asyncio.ensure_future(_read_capped(proc.stderr, max_output))
    timed_out = too_much = False
    try:
        try:
            proc.stdin.write((code or "").encode("utf-8", "replace"))
            await proc.stdin.drain()
        except (BrokenPipeError, ConnectionResetError):
            pass
        finally:
            proc.stdin.close()

        pending = {out_task, err_task}
        while pending:
            done, pending = await asyncio.wait(
                pending, timeout=max(0.0, deadline - loop.time()), return_when=asyncio.FIRST_COMPLETED)
            if not done:
                timed_out = True
                break
            if any(t.result()[1] for t in done):
                too_much = True
                break
        if not (timed_out or too_much):
            try:
                await asyncio.wait_for(proc.wait(), timeout=max(0.1, deadline - loop.time()))
            except asyncio.TimeoutError:
                timed_out = True
    finally:
        stop = timed_out or too_much
        # The ORDER matters (seen on the real server, 21 Nov 2026):
        # 1. kill the docker CLIENT first, so nothing is left attached to the
        #    container's output. While a client sits on a full, unread pipe the
        #    daemon waits for that output to be read before it reports the
        #    container stopped, and `docker kill` hung until its own timeout
        #    (10 s after an output overflow).
        if stop:
            try:
                proc.kill()
            except ProcessLookupError:
                pass
        for t in (out_task, err_task):
            if not t.done():
                t.cancel()
        # 2. read both pipes to their end. A pipe left half-read stays open
        #    (asyncio pauses it when its buffer is full) and the process is
        #    never reported finished. The client is dead or done: the end comes at once.
        await asyncio.gather(*[asyncio.wait_for(_drain(s), timeout=5) for s in (proc.stdout, proc.stderr)],
                             return_exceptions=True)
        # 3. then the container itself, by name: without its client it would
        #    keep running (docker run -i does not stop it), and --rm removes it.
        if stop:
            await _kill(name)
        try:
            await asyncio.wait_for(proc.wait(), timeout=5)
        except Exception:
            pass

    def _text(task):
        if task.done() and not task.cancelled() and task.exception() is None:
            return task.result()[0].decode("utf-8", "replace")
        return ""
    return {
        "ok": proc.returncode == 0 and not (timed_out or too_much),
        "stdout": _text(out_task),
        "stderr": _text(err_task),
        "timed_out": timed_out,
        "too_much_output": too_much,
        "exit_code": proc.returncode,
    }
