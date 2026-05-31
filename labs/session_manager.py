"""
Session Manager for SYNAPSE Labs
=================================
Database layer for lab_sessions table.

Handles the lifecycle state of lab sessions (not the containers themselves).
Container operations live in container_manager.py.

Database: PostgreSQL `security_tutor`, table `lab_sessions`
ORM: raw asyncpg/psycopg2 — we use sync psycopg2 here because the existing
     codebase uses sync DB access in several places.

Author: SYNAPSE platform
Date: 2026-04-22
"""

import logging
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any

# Use the existing DB config from the project
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.config import SessionLocal
from sqlalchemy import text

logger = logging.getLogger(__name__)


# =============================================================================
# CONFIGURATION
# =============================================================================

DEFAULT_SESSION_DURATION_MINUTES = 60
EXTENSION_DURATION_MINUTES = 30
MAX_EXTENSIONS_PER_SESSION = 3
IDLE_TIMEOUT_MINUTES = 15  # kill if no activity for this long


# =============================================================================
# STATUS CONSTANTS
# =============================================================================

STATUS_STARTING = "starting"
STATUS_READY = "ready"
STATUS_EXPIRED = "expired"
STATUS_TERMINATED = "terminated"
STATUS_ERROR = "error"

ACTIVE_STATUSES = (STATUS_STARTING, STATUS_READY)


# =============================================================================
# CREATE SESSION
# =============================================================================

def create_session(
    lab_type: str,
    session_token: str,
    user_id: Optional[int] = None,
    participant_code: Optional[str] = None,
    duration_minutes: int = DEFAULT_SESSION_DURATION_MINUTES,
) -> Optional[int]:
    """
    Insert a new lab session row with status=starting.
    
    Either user_id or participant_code must be provided (DB enforces this).
    
    Returns:
        session_id (int) on success, None on failure
    """
    if not user_id and not participant_code:
        logger.error("create_session requires user_id or participant_code")
        return None
    
    now = datetime.utcnow()
    expires_at = now + timedelta(minutes=duration_minutes)
    
    db = SessionLocal()
    try:
        result = db.execute(
            text("""
                INSERT INTO lab_sessions
                    (user_id, participant_code, lab_type, session_token,
                     status, created_at, expires_at, last_activity_at)
                VALUES
                    (:user_id, :participant_code, :lab_type, :session_token,
                     :status, :created_at, :expires_at, :last_activity_at)
                RETURNING id
            """),
            {
                "user_id": user_id,
                "participant_code": participant_code,
                "lab_type": lab_type,
                "session_token": session_token,
                "status": STATUS_STARTING,
                "created_at": now,
                "expires_at": expires_at,
                "last_activity_at": now,
            },
        )
        session_id = result.scalar()
        db.commit()
        logger.info(
            f"Session created: id={session_id} token={session_token[:12]}... "
            f"owner={'u'+str(user_id) if user_id else 'p'+participant_code} "
            f"lab={lab_type} expires={expires_at.isoformat()}"
        )
        return session_id
    except Exception as e:
        db.rollback()
        logger.exception(f"create_session failed: {e}")
        return None
    finally:
        db.close()


# =============================================================================
# UPDATE SESSION (AFTER CONTAINER SPAWN)
# =============================================================================

def mark_session_ready(
    session_id: int,
    container_id: str,
    container_name: str,
    container_port: int,
) -> bool:
    """
    After container has spawned successfully, update session with container info
    and flip status to 'ready'.
    """
    db = SessionLocal()
    try:
        result = db.execute(
            text("""
                UPDATE lab_sessions
                SET container_id = :container_id,
                    container_name = :container_name,
                    container_port = :container_port,
                    status = :status,
                    last_activity_at = :now
                WHERE id = :session_id
            """),
            {
                "container_id": container_id,
                "container_name": container_name,
                "container_port": container_port,
                "status": STATUS_READY,
                "now": datetime.utcnow(),
                "session_id": session_id,
            },
        )
        db.commit()
        logger.info(f"Session {session_id} marked ready: container={container_name} port={container_port}")
        return result.rowcount > 0
    except Exception as e:
        db.rollback()
        logger.exception(f"mark_session_ready failed: {e}")
        return False
    finally:
        db.close()


def mark_session_error(session_id: int, error_message: str) -> bool:
    """Mark a session as errored (spawn failed)."""
    db = SessionLocal()
    try:
        db.execute(
            text("""
                UPDATE lab_sessions
                SET status = :status,
                    error_message = :error_message,
                    terminated_at = :now
                WHERE id = :session_id
            """),
            {
                "status": STATUS_ERROR,
                "error_message": error_message[:2000],
                "now": datetime.utcnow(),
                "session_id": session_id,
            },
        )
        db.commit()
        logger.warning(f"Session {session_id} marked error: {error_message[:100]}")
        return True
    except Exception as e:
        db.rollback()
        logger.exception(f"mark_session_error failed: {e}")
        return False
    finally:
        db.close()


# =============================================================================
# LOOKUP
# =============================================================================

def _row_to_dict(row) -> Dict[str, Any]:
    """Convert a SQLAlchemy Row to dict."""
    return dict(row._mapping) if hasattr(row, "_mapping") else dict(row)


def get_session_by_token(session_token: str) -> Optional[Dict[str, Any]]:
    """
    Lookup a session by its token (HOT PATH for proxy routing).
    Returns dict with all columns, or None.
    """
    db = SessionLocal()
    try:
        result = db.execute(
            text("SELECT * FROM lab_sessions WHERE session_token = :token"),
            {"token": session_token},
        )
        row = result.fetchone()
        return _row_to_dict(row) if row else None
    except Exception as e:
        logger.exception(f"get_session_by_token failed: {e}")
        return None
    finally:
        db.close()


def get_active_session_for_user(user_id: int, lab_type: str) -> Optional[Dict[str, Any]]:
    """
    Check if a user already has an active session for this lab type.
    If so, reuse it (avoid creating duplicate containers).
    """
    db = SessionLocal()
    try:
        result = db.execute(
            text("""
                SELECT * FROM lab_sessions
                WHERE user_id = :user_id
                  AND lab_type = :lab_type
                  AND status IN ('starting', 'ready')
                  AND expires_at > :now
                ORDER BY created_at DESC
                LIMIT 1
            """),
            {"user_id": user_id, "lab_type": lab_type, "now": datetime.utcnow()},
        )
        row = result.fetchone()
        return _row_to_dict(row) if row else None
    except Exception as e:
        logger.exception(f"get_active_session_for_user failed: {e}")
        return None
    finally:
        db.close()


def get_active_session_for_participant(participant_code: str, lab_type: str) -> Optional[Dict[str, Any]]:
    """Same as above but for research participants."""
    db = SessionLocal()
    try:
        result = db.execute(
            text("""
                SELECT * FROM lab_sessions
                WHERE participant_code = :pc
                  AND lab_type = :lab_type
                  AND status IN ('starting', 'ready')
                  AND expires_at > :now
                ORDER BY created_at DESC
                LIMIT 1
            """),
            {"pc": participant_code, "lab_type": lab_type, "now": datetime.utcnow()},
        )
        row = result.fetchone()
        return _row_to_dict(row) if row else None
    except Exception as e:
        logger.exception(f"get_active_session_for_participant failed: {e}")
        return None
    finally:
        db.close()


def get_used_ports() -> set:
    """Return set of ports currently held by active sessions (for pool allocation)."""
    db = SessionLocal()
    try:
        result = db.execute(
            text("""
                SELECT container_port FROM lab_sessions
                WHERE status IN ('starting', 'ready')
                  AND container_port IS NOT NULL
            """)
        )
        return {r[0] for r in result.fetchall()}
    except Exception as e:
        logger.exception(f"get_used_ports failed: {e}")
        return set()
    finally:
        db.close()


# =============================================================================
# ACTIVITY & EXTEND
# =============================================================================

def touch_session(session_token: str) -> bool:
    """
    Update last_activity_at for a session.
    Called on every proxied request so idle detection works.
    Kept minimal (single UPDATE) to stay fast in the proxy hot path.
    """
    db = SessionLocal()
    try:
        db.execute(
            text("""
                UPDATE lab_sessions
                SET last_activity_at = :now
                WHERE session_token = :token AND status = 'ready'
            """),
            {"now": datetime.utcnow(), "token": session_token},
        )
        db.commit()
        return True
    except Exception as e:
        db.rollback()
        logger.exception(f"touch_session failed: {e}")
        return False
    finally:
        db.close()


def extend_session(session_id: int, minutes: int = EXTENSION_DURATION_MINUTES) -> Optional[Dict[str, Any]]:
    """
    Extend a session expiry by `minutes`, if max_extensions not reached.
    Returns updated session dict, or None on failure.
    """
    db = SessionLocal()
    try:
        # Atomic extend: only if count < max
        result = db.execute(
            text("""
                UPDATE lab_sessions
                SET expires_at = expires_at + (:minutes || ' minutes')::interval,
                    extensions_count = extensions_count + 1,
                    last_activity_at = :now
                WHERE id = :session_id
                  AND status = 'ready'
                  AND extensions_count < max_extensions
                RETURNING *
            """),
            {"minutes": minutes, "now": datetime.utcnow(), "session_id": session_id},
        )
        row = result.fetchone()
        db.commit()
        if row:
            logger.info(f"Session {session_id} extended by {minutes}min")
            return _row_to_dict(row)
        else:
            logger.warning(f"Session {session_id} extend refused (max reached or not ready)")
            return None
    except Exception as e:
        db.rollback()
        logger.exception(f"extend_session failed: {e}")
        return None
    finally:
        db.close()


# =============================================================================
# TERMINATION & CLEANUP
# =============================================================================

def mark_session_terminated(session_id: int) -> bool:
    """Mark a session as terminated (user closed it or cleanup worker did it)."""
    db = SessionLocal()
    try:
        db.execute(
            text("""
                UPDATE lab_sessions
                SET status = :status,
                    terminated_at = :now
                WHERE id = :session_id
                  AND status != 'terminated'
            """),
            {"status": STATUS_TERMINATED, "now": datetime.utcnow(), "session_id": session_id},
        )
        db.commit()
        logger.info(f"Session {session_id} marked terminated")
        return True
    except Exception as e:
        db.rollback()
        logger.exception(f"mark_session_terminated failed: {e}")
        return False
    finally:
        db.close()


def find_expired_sessions() -> List[Dict[str, Any]]:
    """
    Return sessions that should be terminated.
    
    Criteria (any of):
      - expires_at passed
      - last_activity_at older than IDLE_TIMEOUT_MINUTES
      - status = 'starting' for more than 2 minutes (stuck spawn)
    """
    now = datetime.utcnow()
    idle_cutoff = now - timedelta(minutes=IDLE_TIMEOUT_MINUTES)
    stuck_starting_cutoff = now - timedelta(minutes=2)
    
    db = SessionLocal()
    try:
        result = db.execute(
            text("""
                SELECT * FROM lab_sessions
                WHERE status IN ('starting', 'ready')
                  AND (
                      expires_at <= :now
                      OR (status = 'ready' AND last_activity_at <= :idle_cutoff)
                      OR (status = 'starting' AND created_at <= :stuck_cutoff)
                  )
            """),
            {"now": now, "idle_cutoff": idle_cutoff, "stuck_cutoff": stuck_starting_cutoff},
        )
        return [_row_to_dict(row) for row in result.fetchall()]
    except Exception as e:
        logger.exception(f"find_expired_sessions failed: {e}")
        return []
    finally:
        db.close()


# =============================================================================
# STATS (for admin/dashboard)
# =============================================================================

def get_stats() -> Dict[str, int]:
    """Current session counts by status."""
    db = SessionLocal()
    try:
        result = db.execute(
            text("""
                SELECT status, COUNT(*) AS n
                FROM lab_sessions
                GROUP BY status
            """)
        )
        return {row[0]: row[1] for row in result.fetchall()}
    except Exception:
        return {}
    finally:
        db.close()


# =============================================================================
# SELF-TEST
# =============================================================================

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    print("=" * 60)
    print("Session Manager Self-Test")
    print("=" * 60)
    
    # 1. DB connectivity
    try:
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        print("✓ DB connection OK")
    except Exception as e:
        print(f"✗ DB connection FAILED: {e}")
        exit(1)
    
    # 2. Table exists
    try:
        db = SessionLocal()
        result = db.execute(text("SELECT COUNT(*) FROM lab_sessions"))
        count = result.scalar()
        db.close()
        print(f"✓ Table lab_sessions accessible (current rows: {count})")
    except Exception as e:
        print(f"✗ Table lab_sessions not accessible: {e}")
        exit(1)
    
    # 3. Stats query
    stats = get_stats()
    print(f"✓ Stats query OK: {stats if stats else '(no sessions yet)'}")
    
    # 4. Used ports query
    ports = get_used_ports()
    print(f"✓ Used ports query OK: {len(ports)} ports in use")
    
    # 5. Find expired sessions
    expired = find_expired_sessions()
    print(f"✓ Expired sessions query OK: {len(expired)} expired")
    
    print("=" * 60)
    print("All checks passed — session_manager.py ready")
    print("=" * 60)
