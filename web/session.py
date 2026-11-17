"""Who is signed in: one signed session cookie, read in one place.

The cookie used to hold the bare users.id, so anyone could type a number into
their browser and be that user: their drawer, their progress, and, for the
owner account, an AI budget with no ceiling. Now it holds

    <user id>.<expiry, unix seconds>.<signature>

where the signature is an HMAC-SHA256 of the first two parts under a key only
the server knows. A hand-made, edited or expired cookie is simply not a
session. Old bare-number cookies stop working, so existing users sign in once
more.

The key comes from SESSION_SECRET in the environment. Without it, a key is
created once in .session_secret next to the code (mode 600). If even that
cannot be written, a random key lives in memory for this process: sessions
then end at each restart, which is inconvenient but never insecure.
"""
import base64
import hashlib
import hmac
import os
import secrets
import time
from pathlib import Path

COOKIE = "synapse_user"
MAX_AGE = 90 * 24 * 60 * 60  # 90 days, as before

_SECRET_FILE = Path(__file__).resolve().parent.parent / ".session_secret"
_key = None


def _secret():
    global _key
    if _key is not None:
        return _key
    env = os.getenv("SESSION_SECRET", "").strip()
    if env:
        _key = env.encode()
        return _key
    try:
        _key = _SECRET_FILE.read_bytes().strip()
        if _key:
            return _key
    except FileNotFoundError:
        pass
    except OSError as e:
        print(f"session: cannot read {_SECRET_FILE} ({e})", flush=True)
    new = secrets.token_urlsafe(48).encode()
    try:
        fd = os.open(_SECRET_FILE, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, "wb") as f:
            f.write(new)
        _key = new
    except FileExistsError:
        _key = _SECRET_FILE.read_bytes().strip() or new
    except OSError as e:
        print(f"session: no SESSION_SECRET and cannot write {_SECRET_FILE} ({e}); "
              "using a per-process key, sessions end at restart", flush=True)
        _key = new
    return _key


def _sign(payload: str) -> str:
    mac = hmac.new(_secret(), payload.encode(), hashlib.sha256).digest()
    return base64.urlsafe_b64encode(mac).rstrip(b"=").decode()


def make_token(user_id: int, now=None) -> str:
    exp = int(now if now is not None else time.time()) + MAX_AGE
    payload = f"{int(user_id)}.{exp}"
    return f"{payload}.{_sign(payload)}"


def user_id_from_token(token, now=None):
    """The user id a token proves, or None."""
    if not token or token.count(".") != 2:
        return None
    uid, exp, sig = token.split(".")
    if not (uid.isdigit() and exp.isdigit()):
        return None
    if not hmac.compare_digest(sig, _sign(f"{uid}.{exp}")):
        return None
    if int(exp) < int(now if now is not None else time.time()):
        return None
    return int(uid)


def current_user_id(request):
    """The signed-in user's id, or None. The only way to ask who is signed in."""
    return user_id_from_token(request.cookies.get(COOKIE))


def start_session(response, user_id: int):
    response.set_cookie(COOKIE, make_token(user_id), max_age=MAX_AGE,
                        httponly=True, secure=True, samesite="Lax", path="/")
    return response


def end_session(response):
    response.del_cookie(COOKIE, path="/")
    return response


def admin_key_ok(request) -> bool:
    """True only when ADMIN_KEY is set and ?admin= matches it exactly.

    The old check, `admin_key != os.getenv('ADMIN_KEY', '')`, let an empty
    ?admin= through whenever ADMIN_KEY was not configured.
    """
    expected = os.getenv("ADMIN_KEY", "")
    given = request.query.get("admin") or ""
    return bool(expected) and hmac.compare_digest(given, expected)


# ---------------------------------------------------------------- research
# A research participant code used to open /course, /quiz and /spot-the-bug
# with no login at all, whatever the code was: ?participant=x worked. Now a
# code counts only if it exists in research_participants. Answers are cached
# for a few minutes so a page load is not a database round trip.
_PC_CACHE = {}
_PC_TTL = 300
_PC_RE = None


def participant_code(request):
    """The research participant code on this request, if it is a real one."""
    code = request.query.get("participant") or request.cookies.get("participant_code")
    return code if is_real_participant(code) else None


def is_real_participant(code):
    """True only for a code that exists in research_participants."""
    global _PC_RE
    import re
    if _PC_RE is None:
        _PC_RE = re.compile(r"[A-Za-z0-9_-]{3,64}")
    if not code or not isinstance(code, str) or not _PC_RE.fullmatch(code):
        return False
    now = time.time()
    hit = _PC_CACHE.get(code)
    if hit and now - hit[1] < _PC_TTL:
        return hit[0]
    ok = False
    try:
        from sqlalchemy import text
        from database.config import SessionLocal
        with SessionLocal() as db:
            ok = db.execute(
                text("SELECT 1 FROM research_participants WHERE participant_code = :c LIMIT 1"),
                {"c": code},
            ).fetchone() is not None
    except Exception as e:
        # No database, no participant: failing closed is the safe direction.
        print(f"participant check failed ({e})", flush=True)
    if len(_PC_CACHE) > 5000:
        _PC_CACHE.clear()
    _PC_CACHE[code] = (ok, now)
    return ok


# -------------------------------------------------------------------- labs
# A lab URL (/labs/<type>/<token>/) used to open for anybody holding it. The
# labs are deliberately vulnerable and are served from this site's own
# address, so an attacker could send someone a link into the ATTACKER's lab
# with a script in it, and that script would run with the victim's Synapse
# cookies. Now the browser that started the lab gets a key cookie for that
# lab's path only, and the proxy refuses any browser without it.
LAB_KEY_COOKIE = "labkey"


def lab_key(session_token: str) -> str:
    return hmac.new(_secret(), ("lab:" + session_token).encode(),
                    hashlib.sha256).hexdigest()


def lab_key_ok(request, session_token: str) -> bool:
    given = request.cookies.get(LAB_KEY_COOKIE) or ""
    return bool(session_token) and hmac.compare_digest(given, lab_key(session_token))


def set_lab_key(response, lab_type: str, session_token: str):
    response.set_cookie(LAB_KEY_COOKIE, lab_key(session_token),
                        path=f"/labs/{lab_type}/{session_token}/",
                        httponly=True, secure=True, samesite="Strict",
                        max_age=6 * 60 * 60)
    return response
