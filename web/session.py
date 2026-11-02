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
