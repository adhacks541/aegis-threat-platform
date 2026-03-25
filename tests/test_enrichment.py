import requests
import json
import time
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from tests.auth_helper import auth_headers, BASE_URL

ES_URL = os.getenv("ELASTICSEARCH_URL", "http://localhost:9200")


def test_enrichment():
    hdrs = auth_headers()
    ssh_msg = "Failed password for invalid user admin from 45.1.2.3 port 22 ssh2"
    log_payload = {
        "source": "ssh",
        "level": "INFO",
        "message": ssh_msg,
        "metadata": {},
    }

    print(f"Sending SSH log: {ssh_msg}")
    resp = requests.post(
        f"{BASE_URL}/api/v1/ingest/logs", json=log_payload, headers=hdrs
    )
    if resp.status_code != 202:
        print(f"Failed to send log: {resp.status_code} {resp.text}")
        sys.exit(1)

    print("Log queued. Waiting for worker...")
    time.sleep(5)

    # Verify via dashboard API (authenticated)
    try:
        res = requests.get(
            f"{BASE_URL}/api/v1/dashboard/logs?query=ip:45.1.2.3",
            headers=hdrs,
        )
        hits = res.json() if res.status_code == 200 else []

        if not hits:
            # Fallback: direct ES query
            es_res = requests.post(
                f"{ES_URL}/logs-write/_search",
                json={"query": {"match": {"message": ssh_msg}}, "size": 1},
                headers={"Content-Type": "application/json"},
            )
            hits = [h["_source"] for h in es_res.json().get("hits", {}).get("hits", [])]

        if hits:
            doc = hits[0]
            print(f"Extracted IP:  {doc.get('ip')}")
            print(f"Extracted User:{doc.get('user')}")
            print(f"Geo Country:   {doc.get('geo', {}).get('country')}")

            if doc.get("ip") == "45.1.2.3":
                print("SUCCESS: Log parsed and enriched correctly!")
            else:
                print(f"FAILED: IP mismatch. Got: {doc.get('ip')}")
                sys.exit(1)
        else:
            print("FAILED: Log not found.")
            sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    test_enrichment()
