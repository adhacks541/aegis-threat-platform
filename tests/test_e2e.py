import requests
import json
import time
import sys

# Requirements: request
# pip install requests

BASE_URL = "http://localhost:8000"
ES_URL = "http://localhost:9200"

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
        except:
            pass
        
        if api_ready and es_ready:
            return True
        time.sleep(1)
    return False

def test_e2e():
    # 1. Send Log
    test_msg = f"E2E Test {int(time.time())}"
    log_payload = {
        "source": "e2e_tester",
        "level": "WARN",
        "message": test_msg,
        "metadata": {"test_id": "123"}
    }
    
    print(f"Sending log: {test_msg}")
    resp = requests.post(f"{BASE_URL}/api/v1/ingest/logs", json=log_payload)
    if resp.status_code != 202:
        print("Failed to send log")
        sys.exit(1)
        
    print("Log queued. Waiting for worker to index...")
    time.sleep(5) 
    
    # 2. Check Elasticsearch
    # ES is eventually consistent, refresh interval is usually 1s
    search_url = f"{ES_URL}/logs/_search"
    query = {
        "query": {
            "match": {
                "message": test_msg
            }
        }
    }
    
    try:
        res = requests.post(search_url, json=query, headers={"Content-Type": "application/json"})
        data = res.json()
        
        hits = data.get('hits', {}).get('hits', [])
        if hits:
            print("SUCCESS: Log found in Elasticsearch!")
            print(hits[0]['_source'])
        else:
            print("FAILED: Log not found in ES.")
            print(data)
            sys.exit(1)
    except Exception as e:
        print(f"Error querying ES: {e}")
        sys.exit(1)

if __name__ == "__main__":
    if wait_for_services():
        test_e2e()
    else:
        print("Services failed to start.")
