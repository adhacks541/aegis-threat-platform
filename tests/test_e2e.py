import requests
import json
import time
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from tests.auth_helper import auth_headers, BASE_URL

ES_URL = os.getenv("ELASTICSEARCH_URL", "http://localhost:9200")


def wait_for_services():
    print("Waiting for API and ES...")
    api_ready = False
    es_ready = False
    for _ in range(60):
        try:
            if not api_ready and requests.get(f"{BASE_URL}/").status_code == 200:
                api_ready = True
                print("API is ready.")
            if not es_ready and requests.get(f"{ES_URL}/").status_code == 200:
                es_ready = True
                print("ES is ready.")
        except Exception:
            pass

        if api_ready and es_ready:
            return True
        time.sleep(1)
    return False


def test_e2e():
    # 1. Send Log (authenticated)
    test_msg = f"E2E Test {int(time.time())}"
    log_payload = {
        "source": "e2e_tester",
        "level": "WARN",
        "message": test_msg,
        "metadata": {"test_id": "123"},
    }

    print(f"Sending log: {test_msg}")
    resp = requests.post(
        f"{BASE_URL}/api/v1/ingest/logs",
        json=log_payload,
        headers=auth_headers(),
    )
    if resp.status_code != 202:
        print(f"Failed to send log: {resp.status_code} {resp.text}")
        sys.exit(1)

    print("Log queued. Waiting for worker to index...")
    time.sleep(5)

    # 2. Check Elasticsearch via the dashboard API (authenticated)
    print("Checking via dashboard API...")
    try:
        res = requests.get(
            f"{BASE_URL}/api/v1/dashboard/logs?query={test_msg}",
            headers=auth_headers(),
        )
        data = res.json()

        if isinstance(data, list) and data:
            print("SUCCESS: Log found via dashboard API!")
            print(json.dumps(data[0], indent=2, default=str))
        else:
            # Fallback: query ES directly
            print("Not found via API, trying ES directly...")
            es_res = requests.post(
                f"{ES_URL}/logs-write/_search",
                json={"query": {"match": {"message": test_msg}}},
                headers={"Content-Type": "application/json"},
            )
            hits = es_res.json().get("hits", {}).get("hits", [])
            if hits:
                print("SUCCESS: Log found in Elasticsearch!")
                print(hits[0]["_source"])
            else:
                print("FAILED: Log not found in ES.")
                print(es_res.json())
                sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    if wait_for_services():
        test_e2e()
    else:
        print("Services failed to start.")
        sys.exit(1)
