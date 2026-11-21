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
import uuid

IMAGE = "synapse-sandbox"
RUN_TIMEOUT = 10          # seconds the program may run
MAX_OUTPUT = 64 * 1024    # bytes kept from stdout and from stderr, each
DOCKER = ["docker"]       # the tests replace this with a stand-in


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


async def _kill(name):
    try:
        p = await asyncio.create_subprocess_exec(
            *DOCKER, "kill", name,
            stdout=asyncio.subprocess.DEVNULL, stderr=asyncio.subprocess.DEVNULL)
        await asyncio.wait_for(p.wait(), timeout=10)
    except Exception:
        pass


async def run_python(code, timeout=None, max_output=None):
    """Run code in the sandbox. Returns a dict:
       ok, stdout, stderr, timed_out, too_much_output, exit_code
    ok means: exit code 0 and no limit was hit."""
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
        if timed_out or too_much:
            await _kill(name)
            try:
                proc.kill()
            except ProcessLookupError:
                pass
        for t in (out_task, err_task):
            if not t.done():
                t.cancel()
        try:
            await asyncio.wait_for(proc.wait(), timeout=10)
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
