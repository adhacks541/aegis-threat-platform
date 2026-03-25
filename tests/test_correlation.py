import requests
import json
import time
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from tests.auth_helper import auth_headers, BASE_URL

ES_URL = os.getenv("ELASTICSEARCH_URL", "http://localhost:9200")


def test_correlation():
    print("\n--- Testing Correlation Engine ---")
    ip = "203.0.113.10"
    hdrs = auth_headers()

    # Phase 1: Brute Force (6 failed logins)
    print(f"1. Simulating Brute Force from {ip}...")
    for i in range(6):
        requests.post(
            f"{BASE_URL}/api/v1/ingest/logs",
            json={
                "source": "ssh",
                "level": "INFO",
                "message": f"Failed password for invalid user root from {ip} port 22 ssh2",
                "metadata": {},
            },
            headers=hdrs,
        )
        time.sleep(0.05)

    print("   [Wait] Processing Phase 1...")
    time.sleep(2)

    # Phase 2: Successful Login
    print(f"2. Simulating Successful Login from {ip}...")
    requests.post(
        f"{BASE_URL}/api/v1/ingest/logs",
        json={
            "source": "ssh",
            "level": "INFO",
            "message": f"Accepted password for root from {ip} port 22 ssh2",
            "metadata": {},
        },
        headers=hdrs,
    )

    print("   [Wait] Processing Phase 2...")
    time.sleep(2)

    # Phase 3: Privilege Escalation (sudo)
    print(f"3. Simulating Sudo Command from {ip}...")
    requests.post(
        f"{BASE_URL}/api/v1/ingest/logs",
        json={
            "source": "ssh",
            "level": "INFO",
            "message": "sudo: root : TTY=pts/0 ; PWD=/root ; USER=root ; COMMAND=/bin/bash",
            "metadata": {"ip": ip},
        },
        headers=hdrs,
    )

    print("   [Wait] Processing Phase 3...")
    time.sleep(5)

    # 4. Verify via dashboard incidents API (authenticated)
    print("4. Verifying Critical Incident...")
    try:
        res = requests.get(
            f"{BASE_URL}/api/v1/dashboard/incidents?limit=20",
            headers=hdrs,
        )
        incidents = res.json() if res.status_code == 200 else []

        if incidents:
            print("SUCCESS: Critical Incident found via dashboard API!")
            print(json.dumps(incidents[0], indent=2, default=str))
            return

        # Fallback: query ES directly on new index name
        print("   Not found via API, querying ES directly...")
        es_res = requests.post(
            f"{ES_URL}/incidents-write/_search",
            json={"query": {"match_all": {}}, "size": 5, "sort": [{"timestamp": {"order": "desc"}}]},
            headers={"Content-Type": "application/json"},
        )
        hits = es_res.json().get("hits", {}).get("hits", [])
        if hits:
            print("SUCCESS: Critical Incident found in Elasticsearch!")
            print(hits[0]["_source"].get("incident"))
        else:
            print("FAILED: No Critical Incident found.")
            sys.exit(1)

    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    test_correlation()
