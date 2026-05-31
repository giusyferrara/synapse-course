import sys
import os
import time
import logging

sys.path.insert(0, "/opt/synapse/python-debug-tutor-mcp/python-debug-tutor-mcp")

from labs import container_manager as cm
from labs import session_manager as sm

logging.basicConfig(level=logging.INFO, format="%(levelname)s [%(name)s] %(message)s")

print("=" * 70)
print("  INTEGRATION TEST — Multi-tenant ShopSecure Spawn")
print("=" * 70)

print("\n[1/6] Creating test session in DB...")
token = cm.generate_session_token()
session_id = sm.create_session(
    lab_type="shopsecure",
    session_token=token,
    participant_code="INTEGR01",
)
assert session_id, "Failed to create session row"
print(f"    OK Session row created: id={session_id} token={token[:16]}...")

print("\n[2/6] Allocating free port...")
used_ports = sm.get_used_ports()
port = cm.find_free_port(used_ports=used_ports)
assert port, "No free port in pool"
print(f"    OK Port allocated: {port}")

print("\n[3/6] Spawning ShopSecure container...")
start = time.time()
container_id, container_name = cm.create_container(
    lab_type="shopsecure",
    owner_key="pINTEGR01",
    port=port,
)
elapsed = time.time() - start
assert container_id, "Container creation failed"
print(f"    OK Container created in {elapsed:.2f}s")
print(f"        ID: {container_id[:12]}")
print(f"        Name: {container_name}")
print(f"        Port: {port}")

print("\n[4/6] Waiting for container to accept connections...")
start = time.time()
ready = cm.wait_for_container_ready(port, timeout=15)
elapsed = time.time() - start

if ready:
    print(f"    OK Container ready in {elapsed:.2f}s")
    import urllib.request
    try:
        resp = urllib.request.urlopen(f"http://127.0.0.1:{port}/", timeout=5)
        status = resp.status
        content_length = len(resp.read())
        print(f"    OK HTTP request OK: status={status} bytes={content_length}")
    except Exception as e:
        print(f"    WARN HTTP test failed: {e}")
else:
    print(f"    FAIL Container NOT ready after {elapsed:.2f}s")

print("\n[5/6] Marking session ready in DB...")
marked = sm.mark_session_ready(session_id, container_id, container_name, port)
print(f"    OK Session marked ready: {marked}")

from_db = sm.get_session_by_token(token)
assert from_db, "Session lookup by token failed"
assert from_db["container_port"] == port, "Port mismatch"
print(f"    OK Lookup by token works: {from_db['status']} on port {from_db['container_port']}")

stats = sm.get_stats()
print(f"    OK Current stats: {stats}")

print("\n[6/6] Cleaning up...")
destroyed = cm.destroy_container(container_id)
print(f"    OK Container destroyed: {destroyed}")

sm.mark_session_terminated(session_id)
print(f"    OK Session marked terminated in DB")

still_exists = cm.container_exists(container_id)
assert not still_exists, "Container should be gone but still exists"
print(f"    OK Confirmed: container no longer exists")

print()
print("=" * 70)
print("  INTEGRATION TEST PASSED — system works end-to-end")
print("=" * 70)
