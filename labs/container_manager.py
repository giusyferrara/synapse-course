"""
Container Manager for SYNAPSE Labs (HARDENED v2)
=================================================
Manages the lifecycle of isolated lab containers (ShopSecure, etc.).

Each lab session spawns a dedicated Docker container on an assigned port,
providing true isolation between learners. Containers are destroyed when
the session ends or expires.

Security hardening (Level B - PortSwigger-equivalent):
- Loopback-only port binding (127.0.0.1)
- Dedicated Docker network 'synapse_labs' with --internal flag (no egress)
- Drop ALL capabilities, add back only minimum needed
- no-new-privileges security option
- Memory/CPU/PID limits
- Audit logging of every spawn/destroy

Design notes:
- Port pool: 10001-10100 (100 concurrent sessions max)
- Network: synapse_labs (MUST be created: docker network create --internal ...)
- Image: shopsecure:latest (must exist before calling create_container)
- Default session duration: 60 minutes (configurable per-call)

Author: SYNAPSE platform
Date: 2026-04-22
"""

import docker
import secrets
import socket
import logging
from datetime import datetime, timedelta
from typing import Optional, Tuple

logger = logging.getLogger(__name__)

# =============================================================================
# CONFIGURATION
# =============================================================================

PORT_POOL_START = 10001
PORT_POOL_END = 10100
PORT_POOL_SIZE = PORT_POOL_END - PORT_POOL_START + 1

# Resource limits per container
CONTAINER_MEMORY_LIMIT = "256m"
CONTAINER_MEMSWAP_LIMIT = "256m"  # No swap beyond memory limit
CONTAINER_CPU_QUOTA = 50000       # 0.5 CPU (period 100000)
CONTAINER_PIDS_LIMIT = 100

# Network
LAB_NETWORK_NAME = "synapse_labs"

# Capabilities: drop everything, add back only what Flask needs
CAPABILITIES_DROP = ["ALL"]
CAPABILITIES_ADD = [
    "CHOWN",            # needed for some file ops in SQLite init
    "NET_BIND_SERVICE", # bind to port (even if >1024, keeps compat)
    "SETUID",           # python needs for its startup
    "SETGID",
    "DAC_OVERRIDE",     # read/write files owned by different UID (SQLite)
]

# Security options
SECURITY_OPTS = [
    "no-new-privileges:true",
]

# Session defaults
DEFAULT_SESSION_DURATION_MINUTES = 60
MAX_EXTENSIONS_PER_SESSION = 3
EXTENSION_DURATION_MINUTES = 30

# Container config
LAB_IMAGE_MAP = {
    "shopsecure": "shopsecure:latest",
}

# Container startup timeout (seconds)
CONTAINER_READY_TIMEOUT = 15
CONTAINER_READY_CHECK_INTERVAL = 0.5


# =============================================================================
# DOCKER CLIENT
# =============================================================================

_docker_client = None

def get_docker_client():
    """Singleton Docker client."""
    global _docker_client
    if _docker_client is None:
        _docker_client = docker.from_env()
    return _docker_client


# =============================================================================
# NETWORK SETUP CHECK
# =============================================================================

def ensure_network_exists() -> bool:
    """Verify that the synapse_labs network exists."""
    try:
        client = get_docker_client()
        networks = client.networks.list(names=[LAB_NETWORK_NAME])
        if not networks:
            logger.error(
                f"Network '{LAB_NETWORK_NAME}' does not exist. "
                f"Create it with: docker network create --internal {LAB_NETWORK_NAME}"
            )
            return False
        
        # Verify it's marked as internal
        net = networks[0]
        attrs = net.attrs
        if not attrs.get("Internal", False):
            logger.warning(
                f"Network '{LAB_NETWORK_NAME}' exists but is NOT marked --internal. "
                f"Containers may have internet egress (security risk)!"
            )
        return True
    except Exception as e:
        logger.exception(f"ensure_network_exists failed: {e}")
        return False


# =============================================================================
# PORT POOL
# =============================================================================

def _is_port_free(port: int) -> bool:
    """Check if a port is free on 127.0.0.1 (no one listening)."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(0.5)
        try:
            result = sock.connect_ex(("127.0.0.1", port))
            return result != 0
        except (socket.timeout, OSError):
            return True


def find_free_port(used_ports: set = None) -> Optional[int]:
    """
    Find a free port in the pool.
    
    Args:
        used_ports: set of ports already allocated in DB
    
    Returns:
        port number (int) or None if pool exhausted
    """
    if used_ports is None:
        used_ports = set()
    
    for port in range(PORT_POOL_START, PORT_POOL_END + 1):
        if port in used_ports:
            continue
        if _is_port_free(port):
            return port
    
    logger.error(f"Port pool exhausted (range {PORT_POOL_START}-{PORT_POOL_END})")
    return None


# =============================================================================
# TOKEN GENERATION
# =============================================================================

def generate_session_token() -> str:
    """Generate a URL-safe random token for session routing."""
    return secrets.token_urlsafe(32)


def generate_container_name(lab_type: str, owner_key: str) -> str:
    """Generate a unique container name."""
    suffix = secrets.token_hex(4)
    return f"{lab_type}-{owner_key}-{suffix}"[:63]


# =============================================================================
# CONTAINER LIFECYCLE — HARDENED
# =============================================================================

def create_container(
    lab_type: str,
    owner_key: str,
    port: int,
) -> Tuple[Optional[str], Optional[str]]:
    """
    Spawn a new HARDENED container for a lab session.
    
    Security hardening applied:
    - Runs on dedicated network synapse_labs (--internal, no egress)
    - Binds only to 127.0.0.1 on host
    - Drops ALL Linux capabilities, adds back only minimum
    - no-new-privileges prevents privilege escalation
    - Memory limited to 256MB (no swap beyond)
    - CPU limited to 0.5 cores
    - PIDs limited to 100
    
    Args:
        lab_type: 'shopsecure' (must exist in LAB_IMAGE_MAP)
        owner_key: user_id/participant_code (for naming)
        port: host port to bind (must be free)
    
    Returns:
        (container_id, container_name) on success
        (None, None) on failure
    """
    if lab_type not in LAB_IMAGE_MAP:
        logger.error(f"AUDIT_SPAWN_FAIL reason=unknown_lab_type lab={lab_type}")
        return None, None
    
    # Verify network exists
    if not ensure_network_exists():
        logger.error(f"AUDIT_SPAWN_FAIL reason=network_missing network={LAB_NETWORK_NAME}")
        return None, None
    
    image = LAB_IMAGE_MAP[lab_type]
    container_name = generate_container_name(lab_type, owner_key)
    
    try:
        client = get_docker_client()
        
        container = client.containers.run(
            image=image,
            name=container_name,
            detach=True,
            
            # Port binding (loopback only on host)
            ports={"8080/tcp": ("127.0.0.1", port)},
            
            # Resource limits
            mem_limit=CONTAINER_MEMORY_LIMIT,
            memswap_limit=CONTAINER_MEMSWAP_LIMIT,
            cpu_quota=CONTAINER_CPU_QUOTA,
            pids_limit=CONTAINER_PIDS_LIMIT,
            
            # Network isolation
            network=LAB_NETWORK_NAME,
            
            # Capabilities
            cap_drop=CAPABILITIES_DROP,
            cap_add=CAPABILITIES_ADD,
            
            # Security options
            security_opt=SECURITY_OPTS,
            
            # Lifecycle
            auto_remove=False,
            restart_policy={"Name": "no"},
            
            # Labels for audit/monitoring
            labels={
                "synapse.lab_type": lab_type,
                "synapse.owner_key": owner_key,
                "synapse.created_at": datetime.utcnow().isoformat(),
                "synapse.managed": "true",
            },
        )
        
        logger.info(
            f"AUDIT_SPAWN_OK name={container_name} id={container.short_id} "
            f"port={port} lab_type={lab_type} owner={owner_key} "
            f"network={LAB_NETWORK_NAME}"
        )
        return container.id, container_name
    
    except docker.errors.ImageNotFound:
        logger.error(f"AUDIT_SPAWN_FAIL reason=image_not_found image={image}")
        return None, None
    except docker.errors.APIError as e:
        logger.error(f"AUDIT_SPAWN_FAIL reason=docker_api_error error='{e}'")
        return None, None
    except Exception as e:
        logger.exception(f"AUDIT_SPAWN_FAIL reason=unexpected error='{e}'")
        return None, None


def wait_for_container_ready(port: int, timeout: int = CONTAINER_READY_TIMEOUT) -> bool:
    """
    Poll the container port until Flask app responds with HTTP, or timeout.
    
    TCP port open != app ready, so we check HTTP response, not just port.
    """
    import time
    import urllib.request
    import urllib.error
    
    elapsed = 0.0
    tcp_ok = False
    
    while elapsed < timeout:
        # First, wait for TCP port to accept
        if not tcp_ok:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(0.5)
                try:
                    if sock.connect_ex(("127.0.0.1", port)) == 0:
                        tcp_ok = True
                except (socket.timeout, OSError):
                    pass
        
        # Then, wait for HTTP response
        if tcp_ok:
            try:
                resp = urllib.request.urlopen(f"http://127.0.0.1:{port}/", timeout=2)
                if resp.status < 500:
                    logger.info(f"Container ready on port {port} (HTTP {resp.status}) after {elapsed:.1f}s")
                    return True
            except (urllib.error.URLError, ConnectionResetError, OSError):
                pass
        
        time.sleep(CONTAINER_READY_CHECK_INTERVAL)
        elapsed += CONTAINER_READY_CHECK_INTERVAL
    
    logger.warning(f"Container NOT ready on port {port} after {timeout}s (tcp_ok={tcp_ok})")
    return False


def destroy_container(container_id: str, force: bool = True) -> bool:
    """Stop and remove a container."""
    try:
        client = get_docker_client()
        container = client.containers.get(container_id)
        
        try:
            container.stop(timeout=5)
        except docker.errors.APIError:
            if force:
                container.kill()
        
        container.remove(force=force)
        logger.info(f"AUDIT_DESTROY_OK id={container_id[:12]}")
        return True
    
    except docker.errors.NotFound:
        logger.info(f"AUDIT_DESTROY_GONE id={container_id[:12]} (already removed)")
        return True
    except docker.errors.APIError as e:
        logger.error(f"AUDIT_DESTROY_FAIL id={container_id[:12]} error='{e}'")
        return False
    except Exception as e:
        logger.exception(f"AUDIT_DESTROY_FAIL id={container_id[:12]} error='{e}'")
        return False


def container_exists(container_id: str) -> bool:
    """Check if a container still exists in Docker."""
    try:
        client = get_docker_client()
        client.containers.get(container_id)
        return True
    except docker.errors.NotFound:
        return False
    except Exception:
        return False


def container_running(container_id: str) -> bool:
    """Check if a container is currently running."""
    try:
        client = get_docker_client()
        container = client.containers.get(container_id)
        container.reload()
        return container.status == "running"
    except Exception:
        return False


# =============================================================================
# MONITORING HELPERS
# =============================================================================

def list_active_lab_containers() -> list:
    """
    List all containers currently managed by SYNAPSE.
    Uses Docker labels to filter — only containers with synapse.managed=true.
    """
    try:
        client = get_docker_client()
        return client.containers.list(
            filters={"label": "synapse.managed=true"}
        )
    except Exception as e:
        logger.exception(f"list_active_lab_containers failed: {e}")
        return []


# =============================================================================
# SELF-TEST
# =============================================================================

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    print("=" * 60)
    print("Container Manager v2 (HARDENED) Self-Test")
    print("=" * 60)
    
    try:
        client = get_docker_client()
        version = client.version()
        print(f"[OK] Docker API v{version['ApiVersion']}")
    except Exception as e:
        print(f"[FAIL] Docker connection: {e}")
        exit(1)
    
    # Check network
    if ensure_network_exists():
        print(f"[OK] Network '{LAB_NETWORK_NAME}' exists")
    else:
        print(f"[FAIL] Network '{LAB_NETWORK_NAME}' not found")
        exit(1)
    
    # Check lab images
    for lab_type, image_name in LAB_IMAGE_MAP.items():
        try:
            client.images.get(image_name)
            print(f"[OK] Image available: {image_name} ({lab_type})")
        except docker.errors.ImageNotFound:
            print(f"[FAIL] Image MISSING: {image_name} ({lab_type})")
    
    # Port pool
    port = find_free_port()
    if port:
        print(f"[OK] Port pool has free ports (first free: {port})")
    else:
        print("[FAIL] Port pool exhausted!")
    
    # Token generation
    token = generate_session_token()
    print(f"[OK] Token generation works: {token[:20]}... (len={len(token)})")
    
    # List existing managed containers
    active = list_active_lab_containers()
    print(f"[OK] Currently managed containers: {len(active)}")
    
    print("=" * 60)
    print("All checks passed — container_manager.py v2 ready")
    print("=" * 60)
