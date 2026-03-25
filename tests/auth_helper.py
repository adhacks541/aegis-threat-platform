"""
Shared authentication helper for all Aegis test scripts.

Usage:
    from tests.auth_helper import get_token, auth_headers

    headers = auth_headers()          # {"Authorization": "Bearer <token>"}
    token   = get_token()             # raw JWT string

Credentials are read from env vars (same as .env):
    AEGIS_TEST_USER      default: admin
    AEGIS_TEST_PASSWORD  default: aegis-admin
    AEGIS_BASE_URL       default: http://localhost:8000
"""
import os
import sys
import requests

BASE_URL  = os.getenv("AEGIS_BASE_URL", "http://localhost:8000")
_TEST_USER = os.getenv("AEGIS_TEST_USER", "admin")
_TEST_PASS = os.getenv("AEGIS_TEST_PASSWORD", "aegis-admin")

_cached_token: str | None = None


def get_token() -> str:
    """Obtain (and cache) a JWT from the auth endpoint."""
    global _cached_token
    if _cached_token:
        return _cached_token

    resp = requests.post(
        f"{BASE_URL}/api/v1/auth/token",
        data={"username": _TEST_USER, "password": _TEST_PASS},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        timeout=10,
    )

    if resp.status_code != 200:
        print(f"[auth_helper] Login failed: {resp.status_code} {resp.text}", file=sys.stderr)
        sys.exit(1)

    _cached_token = resp.json()["access_token"]
    return _cached_token


def auth_headers() -> dict:
    """Return headers dict with Bearer token for use in requests.* calls."""
    return {"Authorization": f"Bearer {get_token()}"}
