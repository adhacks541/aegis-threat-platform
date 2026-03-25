import requests
import json
import time
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from tests.auth_helper import auth_headers, BASE_URL

ES_URL = os.getenv("ELASTICSEARCH_URL", "http://localhost:9200")


def test_real_apis():
    print("\n--- Testing Real API Integration (GeoIP + Threat Intel) ---")

    ip = "45.33.32.156"  # Known public IP (Linode)

    print(f"1. Sending Login Failure from Public IP: {ip}...")
    log_payload = {
        "source": "ssh",
        "level": "INFO",
        "message": f"Failed password for root from {ip} port 22 ssh2",
        "metadata": {"ip": ip},
    }

    requests.post(
        f"{BASE_URL}/api/v1/ingest/logs",
        json=log_payload,
        headers=auth_headers(),
    )

    print("   [Wait] Processing Enrichment (API Calls)...")
    time.sleep(10)

    # 2. Verify enrichment via authenticated dashboard API first
    print("2. Verifying Enrichment Data...")
    try:
        res = requests.get(
            f"{BASE_URL}/api/v1/dashboard/logs?query=ip:{ip}",
            headers=auth_headers(),
        )
        hits = res.json() if res.status_code == 200 else []

        if not hits:
            # Fallback: query ES directly
            es_res = requests.post(
                f"{ES_URL}/logs-write/_search",
                json={
                    "query": {"match": {"ip": ip}},
                    "sort": [{"timestamp": {"order": "desc"}}],
                    "size": 1,
                },
                headers={"Content-Type": "application/json"},
            )
            hits_raw = es_res.json().get("hits", {}).get("hits", [])
            hits = [h["_source"] for h in hits_raw]

        if hits:
            source = hits[0]
            geo = source.get("geo", {})
            threat = source.get("threat_intel", {})

            print(f"   Country:     {geo.get('country', 'Unknown')}")
            print(f"   ISP:         {geo.get('isp', 'Unknown')}")
            print(f"   Abuse Score: {threat.get('abuse_score', 'N/A')} (AbuseIPDB)")

            if geo.get("country") not in (None, "Unknown") or "abuse_score" in threat:
                print("SUCCESS: Log enriched with real data!")
            else:
                print("WARNING: Geo/Threat data missing or mocked.")
                print(f"Full source: {json.dumps(source, indent=2, default=str)}")
        else:
            print("FAILED: Log not found in ES.")
            sys.exit(1)

    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    test_real_apis()
