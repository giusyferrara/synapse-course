"""
Cleanup Worker for SYNAPSE Labs
================================
Background task that periodically scans for expired lab sessions and
terminates the associated containers.

Trigger criteria (any of):
  - expires_at passed
  - last_activity_at older than IDLE_TIMEOUT_MINUTES (15)
  - status='starting' for more than 2 minutes (stuck spawn)

Design:
  - Runs every CLEANUP_INTERVAL_SECONDS (default 60s)
  - Batched: processes multiple expired sessions per tick
  - Safe: errors in one session don't stop the worker
  - Self-healing: reaps orphaned Docker containers (containers managed by
    SYNAPSE but without a live DB row)

Author: SYNAPSE platform
Date: 2026-04-22
"""

import asyncio
import logging
import os
import sys
from datetime import datetime, timedelta

# Ensure parent dir is on sys.path so `from labs import ...` works
# when this module is imported as part of the aiohttp app, AND when run
# directly for standalone testing.
_parent = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _parent not in sys.path:
    sys.path.insert(0, _parent)

from labs import container_manager as cm
from labs import session_manager as sm

logger = logging.getLogger(__name__)


# =============================================================================
# CONFIG
# =============================================================================

CLEANUP_INTERVAL_SECONDS = 60      # run every minute
ORPHAN_REAP_INTERVAL_TICKS = 5     # every 5 ticks (5 min), also check for orphans
MAX_ERRORS_BEFORE_BACKOFF = 3      # after N consecutive errors, back off


# =============================================================================
# MAIN WORKER
# =============================================================================

async def cleanup_worker(app=None):
    """
    Main background task.
    
    Pattern: register via aiohttp's on_startup/on_cleanup hooks.
    Example in app.py:
    
        app.on_startup.append(start_cleanup_worker)
        app.on_cleanup.append(stop_cleanup_worker)
    """
    logger.info("Cleanup worker starting...")
    
    tick = 0
    consecutive_errors = 0
    
    try:
        while True:
            tick += 1
            try:
                await _tick(tick)
                consecutive_errors = 0
            except asyncio.CancelledError:
                raise
            except Exception as e:
                consecutive_errors += 1
                logger.exception(f"Cleanup tick failed (error {consecutive_errors}): {e}")
            
            # Back off if errors pile up (reduce load)
            if consecutive_errors >= MAX_ERRORS_BEFORE_BACKOFF:
                backoff = min(300, CLEANUP_INTERVAL_SECONDS * consecutive_errors)
                logger.warning(f"Too many errors, backing off for {backoff}s")
                await asyncio.sleep(backoff)
            else:
                await asyncio.sleep(CLEANUP_INTERVAL_SECONDS)
    
    except asyncio.CancelledError:
        logger.info("Cleanup worker stopped gracefully.")
        raise


async def _tick(tick_n: int):
    """A single cleanup pass."""
    # 1. Find expired sessions in DB
    expired = sm.find_expired_sessions()
    
    if expired:
        logger.info(f"[tick={tick_n}] Found {len(expired)} expired session(s) to clean up")
    
    for session in expired:
        await _cleanup_one(session)
    
    # 2. Periodically: orphan reaping (Docker containers without DB rows)
    if tick_n % ORPHAN_REAP_INTERVAL_TICKS == 0:
        await _reap_orphans()


async def _cleanup_one(session: dict):
    """Terminate one expired session."""
    session_id = session["id"]
    container_id = session.get("container_id")
    token = session.get("session_token", "?")
    
    # Classify why it expired
    now = datetime.utcnow()
    expires_at = session.get("expires_at")
    last_activity = session.get("last_activity_at")
    created_at = session.get("created_at")
    
    if expires_at and now > expires_at:
        reason = "expired"
    elif last_activity and now - last_activity > timedelta(minutes=sm.IDLE_TIMEOUT_MINUTES):
        reason = "idle"
    elif session["status"] == "starting" and created_at and now - created_at > timedelta(minutes=2):
        reason = "stuck_starting"
    else:
        reason = "unknown"
    
    logger.info(
        f"Cleaning session id={session_id} token={token[:8]} "
        f"reason={reason} container={container_id[:12] if container_id else 'none'}"
    )
    
    # Destroy container (in thread to avoid blocking event loop)
    if container_id:
        loop = asyncio.get_event_loop()
        try:
            destroyed = await loop.run_in_executor(
                None,
                lambda: cm.destroy_container(container_id),
            )
            if not destroyed:
                logger.warning(f"Failed to destroy container {container_id[:12]}")
        except Exception as e:
            logger.exception(f"Error destroying container: {e}")
    
    # Mark session terminated in DB (even if container destroy failed)
    try:
        sm.mark_session_terminated(session_id)
    except Exception as e:
        logger.exception(f"Error marking session terminated: {e}")


async def _reap_orphans():
    """
    Find Docker containers managed by SYNAPSE (label synapse.managed=true) that
    no longer have a matching DB row, and destroy them.
    
    This handles the case where DB rows were deleted manually or migration cleared
    them but the containers remained.
    """
    try:
        active_containers = cm.list_active_lab_containers()
        if not active_containers:
            return
        
        # Get all container IDs that have a live session in DB
        from labs.session_manager import SessionLocal
        from sqlalchemy import text
        
        db = SessionLocal()
        try:
            result = db.execute(
                text("""
                    SELECT container_id FROM lab_sessions
                    WHERE status IN ('starting', 'ready')
                      AND container_id IS NOT NULL
                """)
            )
            active_ids_in_db = {row[0] for row in result.fetchall()}
        finally:
            db.close()
        
        # Find orphans
        orphans = [c for c in active_containers if c.id not in active_ids_in_db]
        
        if orphans:
            logger.info(f"Found {len(orphans)} orphan container(s) to reap")
        
        loop = asyncio.get_event_loop()
        for c in orphans:
            logger.warning(f"Reaping orphan container: name={c.name} id={c.short_id}")
            await loop.run_in_executor(None, lambda cid=c.id: cm.destroy_container(cid))
    
    except Exception as e:
        logger.exception(f"Orphan reaping failed: {e}")


# =============================================================================
# AIOHTTP LIFECYCLE HOOKS
# =============================================================================

_worker_task = None


async def start_cleanup_worker(app):
    """Start the cleanup worker as aiohttp background task."""
    global _worker_task
    _worker_task = asyncio.create_task(cleanup_worker(app))
    logger.info("Cleanup worker task spawned")


async def stop_cleanup_worker(app):
    """Stop the cleanup worker gracefully on app shutdown."""
    global _worker_task
    if _worker_task and not _worker_task.done():
        _worker_task.cancel()
        try:
            await _worker_task
        except asyncio.CancelledError:
            pass
    logger.info("Cleanup worker stopped")


# =============================================================================
# STANDALONE TEST
# =============================================================================

if __name__ == "__main__":
    """Run a single cleanup tick manually (for testing)."""
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    
    print("=" * 60)
    print("Cleanup Worker - Manual Single Tick")
    print("=" * 60)
    
    async def main():
        await _tick(tick_n=1)
        print()
        print("Tick complete. Checking remaining state...")
        
        stats = sm.get_stats()
        print(f"Current session stats: {stats}")
        
        active_containers = cm.list_active_lab_containers()
        print(f"Active managed containers: {len(active_containers)}")
        for c in active_containers:
            print(f"  - {c.name} ({c.short_id})")
    
    asyncio.run(main())
    
    print("=" * 60)
    print("Single tick complete")
    print("=" * 60)
