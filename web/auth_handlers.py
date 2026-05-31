"""
SYNAPSE Auth Handlers
Routes: /login, /register, /dashboard, /logout, /forgot-password, /reset-password
API:    /api/auth/{login,register,logout,forgot-password,reset-password,progress}
Hashing: Argon2id (OWASP ASVS 2.4.1) with legacy SHA-256 migration on login.
"""
import json
import hashlib
import secrets
import os
import re
import time
import logging
from pathlib import Path
from datetime import datetime, timedelta
from collections import defaultdict, deque
from aiohttp import web
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, InvalidHash

from .email_utils import send_email, build_reset_email, APP_BASE_URL

log = logging.getLogger(__name__)

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://USER:PASSWORD@localhost/security_tutor")
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)

TEMPLATES_DIR = Path(__file__).parent.parent / 'templates'

# Argon2id — OWASP ASVS 2.4.1 compliant
ph = PasswordHasher(time_cost=3, memory_cost=65536, parallelism=4, hash_len=32, salt_len=16)

# Rate limiter for password reset
_reset_attempts: dict = defaultdict(lambda: deque(maxlen=10))
RESET_RATE_LIMIT = 3
RESET_RATE_WINDOW = 15 * 60
RESET_TOKEN_TTL = 60 * 60
MIN_PASSWORD_LENGTH = 8


# ─── PASSWORD HASHING ────────────────────────────────────────────────────────

def hash_password(password: str) -> str:
    """Hash a password with Argon2id."""
    return ph.hash(password)


def verify_password(password: str, stored_hash: str) -> tuple[bool, bool]:
    """Verify password. Returns (is_valid, needs_rehash).
    Supports legacy SHA-256 'salt:hex' format with transparent migration."""
    if not stored_hash:
        return False, False
    if ':' in stored_hash and not stored_hash.startswith('$argon2'):
        try:
            salt, expected = stored_hash.split(':', 1)
            actual = hashlib.sha256(f"{salt}{password}".encode()).hexdigest()
            if secrets.compare_digest(actual, expected):
                return True, True
            return False, False
        except Exception:
            return False, False
    try:
        ph.verify(stored_hash, password)
        return True, ph.check_needs_rehash(stored_hash)
    except (VerifyMismatchError, InvalidHash):
        return False, False
    except Exception as e:
        log.error(f"verify_password error: {e}")
        return False, False


_COMMON_PASSWORDS = {
    'password', 'password1', 'password123', '12345678', '123456789',
    'qwerty', 'qwerty123', 'letmein', 'welcome', 'admin123',
    'iloveyou', 'monkey123', 'abc12345', 'synapse123', 'changeme'
}

def _validate_password_strength(password: str):
    if not password or len(password) < MIN_PASSWORD_LENGTH:
        return f'Password must be at least {MIN_PASSWORD_LENGTH} characters.'
    if len(password) > 128:
        return 'Password must be at most 128 characters.'
    if not any(c.isupper() for c in password):
        return 'Password must contain at least one uppercase letter.'
    if not any(c.islower() for c in password):
        return 'Password must contain at least one lowercase letter.'
    if not any(c.isdigit() for c in password):
        return 'Password must contain at least one digit.'
    special = set('!@#$%^&*()_+-=[]{}|;:\'",.<>/?`~')
    if not any(c in special for c in password):
        return 'Password must contain at least one special character (!@#$%^&*...).'
    if password.lower() in _COMMON_PASSWORDS:
        return 'This password is too common. Please choose another.' 
    return None


def _client_ip(request) -> str:
    return request.headers.get('X-Forwarded-For', request.remote or '').split(',')[0].strip()


def _rate_limit_check(key: str) -> bool:
    now = time.time()
    dq = _reset_attempts[key]
    while dq and dq[0] < now - RESET_RATE_WINDOW:
        dq.popleft()
    if len(dq) >= RESET_RATE_LIMIT:
        return False
    dq.append(now)
    return True


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


# ─── PAGE ROUTES ─────────────────────────────────────────────────────────────

async def serve_login(request):
    try:
        path = TEMPLATES_DIR / 'login.html'
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
        return web.Response(text=content, content_type='text/html')
    except FileNotFoundError:
        return web.Response(text="Login page not found", status=404)


async def serve_register(request):
    try:
        path = TEMPLATES_DIR / 'register.html'
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
        return web.Response(text=content, content_type='text/html')
    except FileNotFoundError:
        return web.Response(text="Register page not found", status=404)


async def serve_dashboard(request):
    try:
        path = TEMPLATES_DIR / 'user_dashboard.html'
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
        return web.Response(text=content, content_type='text/html')
    except FileNotFoundError:
        return web.Response(text="Dashboard page not found", status=404)


async def serve_forgot_password(request):
    path = TEMPLATES_DIR / 'forgot_password.html'
    if not path.exists():
        return web.Response(text='Page not found', status=404)
    return web.Response(text=path.read_text(encoding='utf-8'), content_type='text/html')


async def serve_reset_password(request):
    path = TEMPLATES_DIR / 'reset_password.html'
    if not path.exists():
        return web.Response(text='Page not found', status=404)
    return web.Response(text=path.read_text(encoding='utf-8'), content_type='text/html')


# ─── API ROUTES ──────────────────────────────────────────────────────────────

async def api_register(request):
    try:
        data = await request.json()
        display_name = data.get('display_name', '').strip()
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')
        nd_type = data.get('nd_type')
        is_neurodivergent = data.get('is_neurodivergent', False)

        if not display_name or len(display_name) < 2:
            return web.json_response({'success': False, 'message': 'Display name must be at least 2 characters.'})
        if not email or '@' not in email:
            return web.json_response({'success': False, 'message': 'Please enter a valid email address.'})

        pw_error = _validate_password_strength(password)
        if pw_error:
            return web.json_response({'success': False, 'message': pw_error})

        password_hash = hash_password(password)

        with Session() as session:
            existing = session.execute(
                text("SELECT id FROM users WHERE email = :email"),
                {'email': email}
            ).fetchone()

            if existing:
                return web.json_response({'success': False, 'message': 'An account with this email already exists.'})

            result = session.execute(
                text("""
                    INSERT INTO users (display_name, email, password_hash, is_neurodivergent, nd_type, created_at)
                    VALUES (:display_name, :email, :password_hash, :is_neurodivergent, :nd_type, :created_at)
                    RETURNING id, display_name, email, is_neurodivergent, nd_type, subscription_tier, created_at
                """),
                {
                    'display_name': display_name,
                    'email': email,
                    'password_hash': password_hash,
                    'is_neurodivergent': is_neurodivergent,
                    'nd_type': nd_type,
                    'created_at': datetime.now()
                }
            )
            session.commit()
            row = result.fetchone()

            user = {
                'id': row.id,
                'display_name': row.display_name,
                'email': row.email,
                'is_neurodivergent': row.is_neurodivergent,
                'nd_type': row.nd_type,
                'subscription_tier': row.subscription_tier
            }

            log.info(f"✅ New user registered: {email}")
            return web.json_response({'success': True, 'user': user})

    except Exception as e:
        log.error(f"❌ Registration error: {e}")
        return web.json_response({'success': False, 'message': 'Server error. Please try again.'}, status=500)


async def api_login(request):
    try:
        data = await request.json()
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')

        if not email or not password:
            return web.json_response({'success': False, 'message': 'Email and password are required.'})

        with Session() as session:
            row = session.execute(
                text("""
                    SELECT id, display_name, email, password_hash,
                           is_neurodivergent, nd_type, subscription_tier, is_active
                    FROM users WHERE email = :email
                """),
                {'email': email}
            ).fetchone()

            if not row:
                return web.json_response({'success': False, 'message': 'Invalid email or password.'})

            if not row.is_active:
                return web.json_response({'success': False, 'message': 'This account has been deactivated.'})

            is_valid, needs_rehash = verify_password(password, row.password_hash)
            if not is_valid:
                return web.json_response({'success': False, 'message': 'Invalid email or password.'})

            if needs_rehash:
                new_hash = hash_password(password)
                session.execute(
                    text("UPDATE users SET password_hash = :h WHERE id = :id"),
                    {'h': new_hash, 'id': row.id}
                )
                log.info(f"🔐 Migrated legacy hash → Argon2id for user {row.email}")

            session.execute(
                text("UPDATE users SET last_login = :now WHERE id = :id"),
                {'now': datetime.now(), 'id': row.id}
            )
            session.commit()

            user = {
                'id': row.id,
                'display_name': row.display_name,
                'email': row.email,
                'is_neurodivergent': row.is_neurodivergent,
                'nd_type': row.nd_type,
                'subscription_tier': row.subscription_tier
            }

            log.info(f"✅ User logged in: {email}")
            response = web.json_response({'success': True, 'user': user})
            response.set_cookie('synapse_user', str(row.id), max_age=90*24*60*60, httponly=True, samesite='Lax')
            return response

    except Exception as e:
        log.error(f"❌ Login error: {e}")
        return web.json_response({'success': False, 'message': 'Server error. Please try again.'}, status=500)


async def api_logout(request):
    return web.json_response({'success': True, 'message': 'Logged out.'})


async def api_forgot_password(request):
    """Always returns generic success — prevents user enumeration (CWE-204)."""
    generic = web.json_response({
        'success': True,
        'message': 'If an account with that email exists, a reset link has been sent.'
    })
    try:
        data = await request.json()
        email = (data.get('email') or '').strip().lower()
        if not email or '@' not in email:
            return generic

        ip = _client_ip(request)
        if not _rate_limit_check(f"email:{email}") or not _rate_limit_check(f"ip:{ip}"):
            log.warning(f"Rate limit hit: email={email} ip={ip}")
            return generic

        with Session() as session:
            row = session.execute(
                text("SELECT id, display_name FROM users WHERE email = :e AND is_active = true"),
                {'e': email}
            ).fetchone()
            if not row:
                return generic

            raw_token = secrets.token_urlsafe(32)
            token_hash = _hash_token(raw_token)
            expires_at = datetime.utcnow() + timedelta(seconds=RESET_TOKEN_TTL)

            session.execute(
                text("UPDATE password_reset_tokens SET used_at = NOW() WHERE user_id = :u AND used_at IS NULL"),
                {'u': row.id}
            )
            session.execute(
                text("INSERT INTO password_reset_tokens (user_id, token_hash, expires_at, ip_address) "
                     "VALUES (:u, :t, :e, :ip)"),
                {'u': row.id, 't': token_hash, 'e': expires_at, 'ip': ip}
            )
            session.commit()

        reset_url = f"{APP_BASE_URL}/reset-password?token={raw_token}"
        html_body, text_body = build_reset_email(row.display_name, reset_url)
        send_email(email, "Reset your SYNAPSE password", html_body, text_body)
        log.info(f"📧 Reset token issued for {email}")
        return generic

    except Exception as e:
        log.error(f"forgot-password error: {e}")
        return generic


async def api_reset_password(request):
    try:
        data = await request.json()
        raw_token = (data.get('token') or '').strip()
        new_password = data.get('password') or ''

        if not raw_token:
            return web.json_response({'success': False, 'message': 'Missing or invalid reset link.'})

        pw_error = _validate_password_strength(new_password)
        if pw_error:
            return web.json_response({'success': False, 'message': pw_error})

        token_hash = _hash_token(raw_token)
        now = datetime.utcnow()

        with Session() as session:
            row = session.execute(
                text("SELECT id AS tid, user_id, expires_at, used_at "
                     "FROM password_reset_tokens WHERE token_hash = :t"),
                {'t': token_hash}
            ).fetchone()

            if not row or row.used_at is not None or row.expires_at < now:
                return web.json_response({'success': False, 'message': 'This reset link is invalid or has expired. Please request a new one.'})

            new_hash = hash_password(new_password)
            session.execute(text("UPDATE users SET password_hash = :h WHERE id = :u"),
                            {'h': new_hash, 'u': row.user_id})
            session.execute(text("UPDATE password_reset_tokens SET used_at = :n WHERE id = :id"),
                            {'n': now, 'id': row.tid})
            session.commit()

        log.info(f"🔐 Password reset completed for user_id={row.user_id}")
        return web.json_response({'success': True, 'message': 'Password updated. You can now sign in.'})
    except Exception as e:
        log.error(f"reset-password error: {e}")
        return web.json_response({'success': False, 'message': 'Something went wrong. Please try again.'})


async def api_get_progress(request):
    try:
        user_id = request.rel_url.query.get('user_id')
        if not user_id:
            return web.json_response({'success': False, 'message': 'user_id required'})

        with Session() as session:
            rows = session.execute(
                text("""
                    SELECT course_id, topic_id, exercise_id, completed, score, attempts, completed_at
                    FROM user_progress
                    WHERE user_id = :user_id
                    ORDER BY completed_at DESC
                """),
                {'user_id': user_id}
            ).fetchall()

            progress = [
                {
                    'course_id': r.course_id,
                    'topic_id': r.topic_id,
                    'exercise_id': r.exercise_id,
                    'completed': r.completed,
                    'score': r.score,
                    'attempts': r.attempts,
                    'completed_at': str(r.completed_at) if r.completed_at else None
                }
                for r in rows
            ]

            return web.json_response({'success': True, 'progress': progress})

    except Exception as e:
        log.error(f"❌ Progress fetch error: {e}")
        return web.json_response({'success': False, 'message': 'Server error.'}, status=500)


async def api_save_progress(request):
    try:
        data = await request.json()
        user_id = data.get('user_id')
        course_id = data.get('course_id', '')
        topic_id = data.get('topic_id', '')
        exercise_id = data.get('exercise_id', '')
        completed = data.get('completed', False)
        score = data.get('score', 0)

        if not user_id:
            return web.json_response({'success': False, 'message': 'user_id required'})

        with Session() as session:
            session.execute(
                text("""
                    INSERT INTO user_progress (user_id, course_id, topic_id, exercise_id, completed, score, attempts, completed_at, created_at)
                    VALUES (:user_id, :course_id, :topic_id, :exercise_id, :completed, :score, 1, :now, :now)
                    ON CONFLICT (user_id, course_id, topic_id, exercise_id)
                    DO UPDATE SET
                        completed = EXCLUDED.completed,
                        score = EXCLUDED.score,
                        attempts = user_progress.attempts + 1,
                        completed_at = CASE WHEN EXCLUDED.completed THEN EXCLUDED.completed_at ELSE user_progress.completed_at END
                """),
                {
                    'user_id': user_id,
                    'course_id': course_id,
                    'topic_id': topic_id,
                    'exercise_id': exercise_id,
                    'completed': completed,
                    'score': score,
                    'now': datetime.now()
                }
            )
            session.commit()

        return web.json_response({'success': True})

    except Exception as e:
        log.error(f"❌ Progress save error: {e}")
        return web.json_response({'success': False, 'message': 'Server error.'}, status=500)


# ─── ROUTE SETUP ─────────────────────────────────────────────────────────────

def setup_auth_routes(app):
    """Register all auth routes."""
    # Pages
    app.router.add_get('/login', serve_login)
    app.router.add_get('/register', serve_register)
    app.router.add_get('/dashboard', serve_dashboard)
    app.router.add_get('/forgot-password', serve_forgot_password)
    app.router.add_get('/reset-password', serve_reset_password)

    # API
    app.router.add_post('/api/auth/login', api_login)
    app.router.add_post('/api/auth/register', api_register)
    app.router.add_post('/api/auth/logout', api_logout)
    app.router.add_post('/api/auth/forgot-password', api_forgot_password)
    app.router.add_post('/api/auth/reset-password', api_reset_password)
    app.router.add_get('/api/auth/progress', api_get_progress)
    app.router.add_post('/api/auth/progress', api_save_progress)

    print("✅ Auth routes registered (incl. forgot/reset password)")
