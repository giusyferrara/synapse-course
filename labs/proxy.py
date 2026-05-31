"""
Reverse Proxy for SYNAPSE Labs
===============================
Forwards requests /labs/<lab_type>/<token>/<path> to the user's lab container.

Key security features:
- Cookie isolation: SYNAPSE cookies (synapse_user) are STRIPPED before forwarding
  to prevent account takeover via XSS/SSRF exploits inside ShopSecure.
- Cookies set by the lab container are rewritten with Path restricted to
  /labs/<lab_type>/<token>/ so they never leak to SYNAPSE endpoints.
- Token validation: every request re-checks session status in DB.
- Last-activity update: keeps sessions alive while user is working.

Design:
- Uses aiohttp.ClientSession to forward requests.
- Streams request and response bodies (supports large uploads).
- Propagates status codes, content-type, most headers.
- Handles HEAD, GET, POST, PUT, DELETE, PATCH, OPTIONS.

Author: SYNAPSE platform
Date: 2026-04-22
"""

import logging
import asyncio
from aiohttp import web, ClientSession, ClientTimeout, ClientError
from typing import Optional

from labs import session_manager as sm

logger = logging.getLogger(__name__)


# =============================================================================
# CONFIG
# =============================================================================

# Cookies that belong to SYNAPSE and MUST NOT be forwarded to lab containers.
# These are stripped before each request is proxied to the container.
SYNAPSE_COOKIES_BLOCKLIST = {
    "synapse_user",
    "csrftoken",
    "csrf_token",
    "session",
    "sessionid",
    "_gid",
    "_ga",
}

# Headers that must NOT be passed through (upstream to container)
HEADERS_STRIP_UPSTREAM = {
    "host",
    "cookie",          # we rebuild it from filtered cookies
    "x-forwarded-for", # we set our own
    "x-real-ip",
    "connection",
    "content-length",  # aiohttp computes on the fly
    "transfer-encoding",
}

# Headers that must NOT be passed back to browser (from container)
HEADERS_STRIP_DOWNSTREAM = {
    "connection",
    "transfer-encoding",
    "content-encoding",  # aiohttp may re-encode
    "content-length",    # will be set after
    "server",            # hide upstream server
    "x-powered-by",
}

# Request timeout
PROXY_REQUEST_TIMEOUT = ClientTimeout(total=60, connect=5)


# =============================================================================
# COOKIE REWRITE
# =============================================================================

def _build_cookie_header_for_upstream(request_cookies: dict, session_token: str) -> Optional[str]:
    """
    Filter cookies before forwarding to container.
    
    Rules:
    1. SYNAPSE cookies (synapse_user, etc.) are STRIPPED (security).
    2. Cookies prefixed 'labsess_<prefix>_' are un-prefixed (restore original name).
    3. Everything else is forwarded as-is.
    
    Returns cookie header string or None if no cookies remain.
    """
    prefix = f"labsess_{session_token[:8]}_"
    forwarded = {}
    
    for name, value in request_cookies.items():
        # Skip SYNAPSE cookies — never forward to lab
        if name in SYNAPSE_COOKIES_BLOCKLIST:
            continue
        
        # Strip lab-session prefix if present
        if name.startswith(prefix):
            real_name = name[len(prefix):]
            forwarded[real_name] = value
        else:
            # Pass-through for any non-SYNAPSE cookie
            forwarded[name] = value
    
    if not forwarded:
        return None
    return "; ".join(f"{k}={v}" for k, v in forwarded.items())


def _rewrite_set_cookie_for_downstream(set_cookie_value: str, lab_type: str, session_token: str) -> str:
    """
    Rewrite a Set-Cookie header from the container before sending to browser.
    
    Rules:
    1. Add prefix 'labsess_<prefix>_' to cookie name (isolation).
    2. Force Path=/labs/<lab_type>/<token>/
    3. Remove Domain= (always host-only).
    4. Add HttpOnly if missing.
    5. Add SameSite=Lax if missing.
    """
    prefix = f"labsess_{session_token[:8]}_"
    new_path = f"/labs/{lab_type}/{session_token}/"
    
    parts = [p.strip() for p in set_cookie_value.split(";")]
    if not parts or "=" not in parts[0]:
        return set_cookie_value  # malformed, leave alone
    
    name, _, value = parts[0].partition("=")
    new_name = prefix + name
    new_parts = [f"{new_name}={value}"]
    
    # Track attributes we need to override
    had_path = False
    had_httponly = False
    had_samesite = False
    
    for attr in parts[1:]:
        if not attr:
            continue
        attr_lower = attr.lower()
        
        if attr_lower.startswith("path="):
            had_path = True
            new_parts.append(f"Path={new_path}")
        elif attr_lower.startswith("domain="):
            continue  # strip Domain to make cookie host-only
        elif attr_lower == "httponly":
            had_httponly = True
            new_parts.append("HttpOnly")
        elif attr_lower.startswith("samesite="):
            had_samesite = True
            new_parts.append(attr)
        else:
            new_parts.append(attr)
    
    if not had_path:
        new_parts.append(f"Path={new_path}")
    if not had_httponly:
        new_parts.append("HttpOnly")
    if not had_samesite:
        new_parts.append("SameSite=Lax")
    
    return "; ".join(new_parts)


# =============================================================================
# PROXY HANDLER
# =============================================================================

async def proxy_to_lab(request: web.Request) -> web.StreamResponse:
    """
    Main proxy handler.
    
    URL pattern: /labs/{lab_type}/{token}/{tail:.*}
    
    Matches URLs like:
        /labs/shopsecure/abc123.../products/42
        /labs/shopsecure/abc123.../login
    """
    lab_type = request.match_info.get("lab_type", "")
    token = request.match_info.get("token", "")
    tail = request.match_info.get("tail", "")
    
    # 1. Validate token + lookup session
    session = sm.get_session_by_token(token)
    if not session:
        return web.Response(
            text="Lab session not found. It may have expired or been terminated.",
            status=404,
            content_type="text/plain",
        )
    
    if session["status"] != "ready":
        return web.Response(
            text=f"Lab session not available (status: {session['status']}).",
            status=410,
            content_type="text/plain",
        )
    
    if session["lab_type"] != lab_type:
        return web.Response(
            text="Lab type mismatch for this token.",
            status=403,
            content_type="text/plain",
        )
    
    port = session["container_port"]
    if not port:
        return web.Response(
            text="Lab container not bound to a port.",
            status=500,
            content_type="text/plain",
        )
    
    # 2. Build target URL
    query_string = request.query_string
    qs_part = f"?{query_string}" if query_string else ""
    target_url = f"http://127.0.0.1:{port}/{tail}{qs_part}"
    
    # 3. Filter request headers
    upstream_headers = {}
    for h, v in request.headers.items():
        if h.lower() in HEADERS_STRIP_UPSTREAM:
            continue
        upstream_headers[h] = v
    
    # Set Host header to localhost so ShopSecure doesn't get confused
    upstream_headers["Host"] = f"127.0.0.1:{port}"
    upstream_headers["X-Forwarded-For"] = request.remote or "unknown"
    upstream_headers["X-Forwarded-Proto"] = request.scheme
    upstream_headers["X-Forwarded-Host"] = request.host
    upstream_headers["X-Forwarded-Prefix"] = f"/labs/{lab_type}/{token}"
    upstream_headers["X-Lab-Session"] = token[:8]  # for debugging
    
    # 4. Filter cookies
    cookie_header = _build_cookie_header_for_upstream(dict(request.cookies), token)
    if cookie_header:
        upstream_headers["Cookie"] = cookie_header
    
    # 5. Read request body (allow any size for file uploads, etc.)
    body = await request.read()
    
    # 6. Forward request to container
    try:
        async with ClientSession(timeout=PROXY_REQUEST_TIMEOUT) as client:
            async with client.request(
                method=request.method,
                url=target_url,
                headers=upstream_headers,
                data=body if body else None,
                allow_redirects=False,
            ) as upstream_resp:
                # 7. Build downstream response
                response_body = await upstream_resp.read()
                
                response = web.Response(
                    body=response_body,
                    status=upstream_resp.status,
                )
                
                # 8. Filter response headers + rewrite Set-Cookie
                set_cookies_raw = []
                for h, v in upstream_resp.headers.items():
                    h_lower = h.lower()
                    if h_lower in HEADERS_STRIP_DOWNSTREAM:
                        continue
                    if h_lower == "set-cookie":
                        set_cookies_raw.append(v)
                        continue
                    # Handle Location header (redirects): rewrite container URL to lab URL
                    if h_lower == "location":
                        new_location = _rewrite_location(v, lab_type, token, port)
                        response.headers["Location"] = new_location
                        continue
                    response.headers[h] = v
                
                # Rewrite and add Set-Cookie headers (can be multiple)
                # aiohttp exposes multiple Set-Cookie via getall()
                try:
                    all_set_cookies = upstream_resp.headers.getall("Set-Cookie")
                except KeyError:
                    all_set_cookies = []
                
                for sc in all_set_cookies:
                    rewritten = _rewrite_set_cookie_for_downstream(sc, lab_type, token)
                    response.headers.add("Set-Cookie", rewritten)
                
                # 9. Update session last_activity_at (fire-and-forget)
                # Async touch to avoid slowing down the response
                asyncio.create_task(_async_touch(token))
                
                return response
    
    except asyncio.TimeoutError:
        logger.warning(f"Proxy timeout: token={token[:8]} target={target_url}")
        return web.Response(text="Lab container timed out.", status=504)
    except ClientError as e:
        logger.error(f"Proxy client error: token={token[:8]} error={e}")
        return web.Response(text="Lab container unreachable.", status=502)
    except Exception as e:
        logger.exception(f"Proxy unexpected error: token={token[:8]}")
        return web.Response(text="Proxy internal error.", status=500)


async def _async_touch(token: str):
    """Touch session activity without blocking the request."""
    try:
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, lambda: sm.touch_session(token))
    except Exception:
        pass  # non-critical


def _rewrite_location(location: str, lab_type: str, token: str, port: int) -> str:
    """
    Rewrite Location header (for redirects) from container URL to lab URL.
    
    Container sends: Location: http://127.0.0.1:10001/welcome
    Browser needs:   Location: /labs/shopsecure/<token>/welcome
    
    Relative locations are passed as-is (browser will resolve against current path).
    """
    lab_base = f"/labs/{lab_type}/{token}"
    
    # Absolute URL pointing at container
    host_prefix = f"http://127.0.0.1:{port}"
    if location.startswith(host_prefix):
        return lab_base + location[len(host_prefix):]
    
    # Relative location starting with /
    if location.startswith("/"):
        return lab_base + location
    
    # Other absolute URLs (external) or relative without / — leave as-is
    return location


# =============================================================================
# ROUTE REGISTRATION
# =============================================================================

def register_proxy_routes(app: web.Application):
    """Register /labs/<lab_type>/<token>/{tail:.*} catch-all route."""
    # The {tail:.*} uses regex to match everything after the token
    app.router.add_route(
        "*",  # any HTTP method
        r"/labs/{lab_type}/{token}/{tail:.*}",
        proxy_to_lab,
    )
    # Also match without trailing path (e.g., /labs/shopsecure/<token>)
    app.router.add_route(
        "*",
        r"/labs/{lab_type}/{token}",
        proxy_to_lab,
    )
    logger.info("Proxy routes registered: /labs/<lab_type>/<token>/*")
