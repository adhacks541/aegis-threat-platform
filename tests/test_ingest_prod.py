import requests
import json
import time
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from tests.auth_helper import auth_headers, BASE_URL

INGEST_URL = f"{BASE_URL}/api/v1/ingest"


def test_prod_ingestion():
    print("\n--- Testing Production Ingestion (Batch + Raw + Rate Limit) ---")
    hdrs = auth_headers()

    # 1. Batch JSON ingestion
    print("1. Testing Batch JSON Ingestion...")
    batch_logs = [
        {
            "source": "prod_test",
            "level": "INFO",
            "message": f"Batch Log {i}",
            "metadata": {"batch_id": "batch_001"},
        }
        for i in range(5)
    ]

    combined_headers = {
        **hdrs,
        "X-Source-Host": "server-01",
        "X-App-Name": "payment-service",
    }

    try:
        res = requests.post(f"{INGEST_URL}/logs", json=batch_logs, headers=combined_headers)
        if res.status_code == 202:
            print(f"   SUCCESS: Queued {res.json().get('count')} logs.")
        else:
            print(f"   FAILED: {res.status_code} - {res.text}")
    except Exception as e:
        print(f"   ERROR: {e}")

    # 2. Raw text ingestion
    print("2. Testing Raw Text Ingestion...")
    raw_text = "Oct 11 22:14:15 server-02 sshd[123]: Failed password for root"
    try:
        res = requests.post(
            f"{INGEST_URL}/raw",
            data=raw_text,
            headers={
                **hdrs,
                "Content-Type": "text/plain",
                "X-Source-Host": "legacy-syslog",
            },
        )
        if res.status_code == 202:
            print("   SUCCESS: Raw log accepted.")
        else:
            print(f"   FAILED: {res.status_code} - {res.text}")
    except Exception as e:
        print(f"   ERROR: {e}")

    # 3. Rate limiter (spam > 1000 requests/min)
    print("3. Testing Rate Limiter (spamming 1005 requests)...")
    blocked = False
    for i in range(1005):
        try:
            res = requests.post(
                f"{INGEST_URL}/raw",
                data=f"spam {i}",
                headers={**hdrs, "Content-Type": "text/plain"},
            )
            if res.status_code == 429:
                print(f"   SUCCESS: Rate Limit hit at request #{i + 1}!")
                blocked = True
                break
        except Exception:
            pass

    if not blocked:
        print("   WARNING: Rate Limit NOT triggered (limit may be > 1000 or counter shared).")
    else:
        print("   Rate Limiter functional.")


if __name__ == "__main__":
    test_prod_ingestion()
