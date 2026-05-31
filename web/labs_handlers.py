"""
HTTP Handlers for SYNAPSE Labs API
===================================
Exposes REST endpoints for users to start/stop/extend their lab sessions.

Endpoints:
    POST /api/labs/start       - Spawn a new lab container
    GET  /api/labs/status      - Current session state + countdown
    POST /api/labs/end         - Terminate current session
    POST /api/labs/extend      - Extend session by +30 min (max 3x)

All endpoints use aiohttp and return JSON.
Authentication: either session cookie (logged-in user) or participant_code param.

Author: SYNAPSE platform
Date: 2026-04-22
"""

import logging
import asyncio
from datetime import datetime, timedelta
from aiohttp import web

from labs import container_manager as cm
from labs import session_manager as sm

logger = logging.getLogger(__name__)


# =============================================================================
# AUTH HELPER
# =============================================================================

async def _get_requester(request: web.Request):
    """
    Identify who is calling: logged-in user OR research participant.
    
    SYNAPSE auth pattern: cookie 'synapse_user' contains user_id as integer.
    Research participants pass participant_code in query string or body.
    
    Returns:
        ('user', user_id) for logged-in users
        ('participant', participant_code) for research participants
        (None, None) if neither is present
    """
    # Try logged-in user via synapse_user cookie
    try:
        cv = request.cookies.get("synapse_user")
        if cv and cv.isdigit():
            return ("user", int(cv))
    except Exception:
        pass
    
    # Try participant_code from query string first
    participant_code = request.query.get("participant_code")
    
    # Then from JSON body (POST requests)
    if not participant_code and request.method in ("POST", "PUT"):
        try:
            data = await request.json()
            if isinstance(data, dict):
                participant_code = data.get("participant_code")
        except Exception:
            pass
    
    if participant_code:
        return ("participant", participant_code)
    
    return (None, None)


def _owner_key(owner_type: str, owner_value) -> str:
    """Build the owner_key string for container naming."""
    prefix = "u" if owner_type == "user" else "p"
    return f"{prefix}{owner_value}"


# =============================================================================
# POST /api/labs/start
# =============================================================================

async def start_lab(request: web.Request) -> web.Response:
    """
    Start (or reuse) a lab session for the current user.
    
    Body: {"lab_type": "shopsecure"}
    
    Returns JSON:
        {
            "session_token": "...",
            "lab_url": "/labs/shopsecure/<token>/",
            "expires_at": "ISO datetime",
            "expires_in_seconds": 3600,
            "status": "ready"
        }
    """
    owner_type, owner_value = await _get_requester(request)
    if not owner_type:
        return web.json_response(
            {"error": "authentication required"},
            status=401,
        )
    
    # Parse body
    try:
        data = await request.json()
    except Exception:
        data = {}
    lab_type = data.get("lab_type", "shopsecure")
    
    if lab_type not in cm.LAB_IMAGE_MAP:
        return web.json_response(
            {"error": f"unknown lab_type: {lab_type}"},
            status=400,
        )
    
    # Check if user already has an active session (reuse it)
    if owner_type == "user":
        existing = sm.get_active_session_for_user(owner_value, lab_type)
    else:
        existing = sm.get_active_session_for_participant(owner_value, lab_type)
    
    if existing and existing["status"] == "ready":
        logger.info(f"Reusing existing session {existing['id']} for {owner_type}={owner_value}")
        expires_at = existing["expires_at"]
        expires_in = max(0, int((expires_at - datetime.utcnow()).total_seconds()))
        return web.json_response({
            "session_token": existing["session_token"],
            "lab_url": f"/labs/{lab_type}/{existing['session_token']}/",
            "expires_at": expires_at.isoformat() + "Z",
            "expires_in_seconds": expires_in,
            "status": "ready",
            "reused": True,
        })
    
    # 1. Create session row (status=starting)
    token = cm.generate_session_token()
    create_kwargs = {"lab_type": lab_type, "session_token": token}
    if owner_type == "user":
        create_kwargs["user_id"] = owner_value
    else:
        create_kwargs["participant_code"] = owner_value
    
    session_id = sm.create_session(**create_kwargs)
    if not session_id:
        return web.json_response({"error": "failed to create session"}, status=500)
    
    # 2. Allocate port
    used_ports = sm.get_used_ports()
    port = cm.find_free_port(used_ports=used_ports)
    if not port:
        sm.mark_session_error(session_id, "port pool exhausted")
        return web.json_response(
            {"error": "server is full - try again in a few minutes"},
            status=503,
        )
    
    # 3. Spawn container (blocking — ~1s)
    owner_key = _owner_key(owner_type, owner_value)
    container_id, container_name = cm.create_container(
        lab_type=lab_type,
        owner_key=owner_key,
        port=port,
    )
    if not container_id:
        sm.mark_session_error(session_id, "container spawn failed")
        return web.json_response(
            {"error": "could not start lab - please retry"},
            status=500,
        )
    
    # 4. Wait for ready (blocking — ~1-3s)
    # Run in thread so we don't block the event loop
    loop = asyncio.get_event_loop()
    ready = await loop.run_in_executor(
        None,
        lambda: cm.wait_for_container_ready(port, timeout=15),
    )
    
    if not ready:
        cm.destroy_container(container_id)
        sm.mark_session_error(session_id, "container did not become ready")
        return web.json_response(
            {"error": "lab failed to start - please retry"},
            status=500,
        )
    
    # 5. Mark session ready
    sm.mark_session_ready(session_id, container_id, container_name, port)
    
    # 6. Return success
    expires_at = datetime.utcnow() + timedelta(minutes=sm.DEFAULT_SESSION_DURATION_MINUTES)
    logger.info(f"Lab started: session_id={session_id} owner={owner_key} port={port}")
    
    return web.json_response({
        "session_token": token,
        "lab_url": f"/labs/{lab_type}/{token}/",
        "expires_at": expires_at.isoformat() + "Z",
        "expires_in_seconds": sm.DEFAULT_SESSION_DURATION_MINUTES * 60,
        "status": "ready",
        "reused": False,
    })


# =============================================================================
# GET /api/labs/status
# =============================================================================

async def lab_status(request: web.Request) -> web.Response:
    """
    Return current lab session state for the user.
    
    Query param: ?lab_type=shopsecure (optional, default shopsecure)
    
    Returns JSON:
        {
            "has_session": true/false,
            "status": "ready|starting|error|none",
            "session_token": "...",
            "lab_url": "/labs/shopsecure/<token>/",
            "expires_in_seconds": 3421,
            "extensions_remaining": 3,
            "max_extensions": 3
        }
    """
    owner_type, owner_value = await _get_requester(request)
    if not owner_type:
        return web.json_response({"error": "authentication required"}, status=401)
    
    lab_type = request.query.get("lab_type", "shopsecure")
    
    if owner_type == "user":
        session = sm.get_active_session_for_user(owner_value, lab_type)
    else:
        session = sm.get_active_session_for_participant(owner_value, lab_type)
    
    if not session:
        return web.json_response({
            "has_session": False,
            "status": "none",
        })
    
    expires_at = session["expires_at"]
    expires_in = max(0, int((expires_at - datetime.utcnow()).total_seconds()))
    extensions_remaining = session["max_extensions"] - session["extensions_count"]
    
    return web.json_response({
        "has_session": True,
        "status": session["status"],
        "session_token": session["session_token"],
        "lab_url": f"/labs/{lab_type}/{session['session_token']}/",
        "expires_at": expires_at.isoformat() + "Z",
        "expires_in_seconds": expires_in,
        "extensions_remaining": extensions_remaining,
        "max_extensions": session["max_extensions"],
    })


# =============================================================================
# POST /api/labs/end
# =============================================================================

async def end_lab(request: web.Request) -> web.Response:
    """Terminate the current lab session (user clicked 'End session')."""
    owner_type, owner_value = await _get_requester(request)
    if not owner_type:
        return web.json_response({"error": "authentication required"}, status=401)
    
    try:
        data = await request.json()
    except Exception:
        data = {}
    lab_type = data.get("lab_type", "shopsecure")
    
    if owner_type == "user":
        session = sm.get_active_session_for_user(owner_value, lab_type)
    else:
        session = sm.get_active_session_for_participant(owner_value, lab_type)
    
    if not session:
        return web.json_response({"message": "no active session"}, status=200)
    
    # Destroy container (in thread to avoid blocking)
    if session["container_id"]:
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None,
            lambda: cm.destroy_container(session["container_id"]),
        )
    
    sm.mark_session_terminated(session["id"])
    
    logger.info(f"Lab ended by user: session_id={session['id']}")
    return web.json_response({"message": "session terminated"}, status=200)


# =============================================================================
# POST /api/labs/extend
# =============================================================================

async def extend_lab(request: web.Request) -> web.Response:
    """Extend current session by +30 min (max 3 times)."""
    owner_type, owner_value = await _get_requester(request)
    if not owner_type:
        return web.json_response({"error": "authentication required"}, status=401)
    
    try:
        data = await request.json()
    except Exception:
        data = {}
    lab_type = data.get("lab_type", "shopsecure")
    
    if owner_type == "user":
        session = sm.get_active_session_for_user(owner_value, lab_type)
    else:
        session = sm.get_active_session_for_participant(owner_value, lab_type)
    
    if not session:
        return web.json_response({"error": "no active session"}, status=404)
    
    extended = sm.extend_session(session["id"])
    if not extended:
        return web.json_response(
            {"error": "extension refused (max reached or session not ready)"},
            status=400,
        )
    
    expires_at = extended["expires_at"]
    expires_in = max(0, int((expires_at - datetime.utcnow()).total_seconds()))
    extensions_remaining = extended["max_extensions"] - extended["extensions_count"]
    
    logger.info(f"Lab extended: session_id={session['id']} now expires {expires_at.isoformat()}")
    
    return web.json_response({
        "expires_at": expires_at.isoformat() + "Z",
        "expires_in_seconds": expires_in,
        "extensions_remaining": extensions_remaining,
        "extensions_count": extended["extensions_count"],
    })


# =============================================================================
# ROUTE REGISTRATION
# =============================================================================

def register_lab_routes(app: web.Application):
    """Call this from app.py to register /api/labs/* routes."""
    app.router.add_post("/api/labs/start", start_lab)
    app.router.add_get("/api/labs/status", lab_status)
    app.router.add_post("/api/labs/end", end_lab)
    app.router.add_post("/api/labs/extend", extend_lab)
    logger.info("Lab routes registered: /api/labs/{start,status,end,extend}")
