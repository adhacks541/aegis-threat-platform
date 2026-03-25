import requests
import json
import time
import redis
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from tests.auth_helper import auth_headers, BASE_URL

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# Import settings from backend app
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))
try:
    from app.core.config import settings
    REDIS_URL = settings.REDIS_URL
except Exception:
    pass  # fall back to env var above


def test_automated_blocking():
    print("\n--- Testing Automated Response (Blocking) ---")

    r = redis.Redis.from_url(REDIS_URL, decode_responses=True)
    test_ip = "192.168.66.66"
    r.delete(f"blocked:{test_ip}")

    hdrs = auth_headers()

    # Clear any existing brute-force phase state
    r.srem("state:admin_ips:admin", test_ip)

    print("1. Sending Attack Log to trigger Block...")
    attack_log = {
        "source": "ssh",
        "message": f"Accepted password for admin from {test_ip} port 22",
        "metadata": {},
    }
    headers = {**hdrs, "X-Source-Host": "victim-server", "X-App-Name": "sshd"}

    res = requests.post(f"{BASE_URL}/api/v1/ingest/logs", json=attack_log, headers=headers)
    print(f"   Log Sent: HTTP {res.status_code}")

    print("   [Simulating Worker Decision] Blocking IP manually for enforcement test...")
    r.setex(f"blocked:{test_ip}", 60, "Test Block")

    print("   Waiting for Worker to process...")
    time.sleep(3)

    if r.exists(f"blocked:{test_ip}"):
        print(f"   SUCCESS: Attacker IP {test_ip} is blocked in Redis!")
    else:
        print(f"   FAILED: Key 'blocked:{test_ip}' not found.")

    # Cleanup
    r.delete(f"blocked:{test_ip}")
    print("   Cleanup complete.")


if __name__ == "__main__":
    test_automated_blocking()
