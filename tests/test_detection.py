import requests
import json
import time
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from tests.auth_helper import auth_headers, BASE_URL

ES_URL = os.getenv("ELASTICSEARCH_URL", "http://localhost:9200")


def test_rule_detection():
    print("\n--- Testing Rule-Based Detection (SSH Brute Force) ---")
    ip = "192.168.1.100"
    hdrs = auth_headers()

    for i in range(6):
        requests.post(
            f"{BASE_URL}/api/v1/ingest/logs",
            json={
                "source": "ssh",
                "level": "INFO",
                "message": f"Failed password for invalid user hacker from {ip} port 22 ssh2",
                "metadata": {},
            },
            headers=hdrs,
        )
        time.sleep(0.1)

    print("Sent 6 failed logins. Waiting for worker...")
    time.sleep(5)

    # Check via alerts API
    res = requests.get(f"{BASE_URL}/api/v1/dashboard/alerts?limit=50", headers=hdrs)
    alerts = res.json() if res.status_code == 200 else []
    brute_force_alert = any(
        "Brute Force" in str(a.get("rule_name", "")) for a in alerts
    )

    if brute_force_alert:
        print("SUCCESS: Rule Alert found via dashboard API!")
        return

    # Fallback: ES direct
    try:
        res = requests.post(
            f"{ES_URL}/logs-write/_search",
            json={
                "query": {
                    "bool": {
                        "must": [
                            {"match": {"ip": ip}},
                            {"match": {"severity": "HIGH"}},
                        ]
                    }
                }
            },
            headers={"Content-Type": "application/json"},
        )
        hits = res.json().get("hits", {}).get("hits", [])
        if hits:
            print("SUCCESS: Rule Alert Found in Elasticsearch!")
            print(hits[0]["_source"].get("alerts"))
        else:
            print("FAILED: No Rule Alert found.")
            sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


def test_ml_detection():
    print("\n--- Testing ML Detection (Anomaly) ---")
    hdrs = auth_headers()

    weird_msg = "X" * 200
    requests.post(
        f"{BASE_URL}/api/v1/ingest/logs",
        json={
            "source": "unknown_alien_process",
            "level": "CRITICAL",
            "message": weird_msg,
            "metadata": {},
        },
        headers=hdrs,
    )
    print("Sent anomalous log. Waiting for worker...")
    time.sleep(5)

    # Check via ES (ml_anomaly is a bool field not exposed via dashboard API filter)
    try:
        res = requests.post(
            f"{ES_URL}/logs-write/_search",
            json={"query": {"term": {"ml_anomaly": True}}, "size": 10},
            headers={"Content-Type": "application/json"},
        )
        hits = res.json().get("hits", {}).get("hits", [])
        if hits:
            for h in hits:
                if h["_source"].get("source") == "unknown_alien_process":
                    print("SUCCESS: ML Anomaly Detected!")
                    print(f"  Score: {h['_source'].get('anomaly_score')}")
                    print(f"  Explanation: {h['_source'].get('anomaly_explanation')}")
                    return
            print("FAILED: ML Anomaly not found for our specific log.")
            sys.exit(1)
        else:
            print("FAILED: No ML Anomalies found in index.")
            sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    test_rule_detection()
    test_ml_detection()
