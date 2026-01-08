import requests
import json
import time
import sys

# Requirements: request
# pip install requests

BASE_URL = "http://localhost:8000"
ES_URL = "http://localhost:9200"

def wait_for_services():
    # Reuse valid wait logic or assume running if recently checked
    time.sleep(2) 
    return True

def test_enrichment():
    # 1. Send SSH Log
    ssh_msg = "Failed password for invalid user admin from 45.1.2.3 port 22 ssh2"
    log_payload = {
        "source": "ssh",
        "level": "INFO",
        "message": ssh_msg,
        "metadata": {}
    }
    
    print(f"Sending SSH log: {ssh_msg}")
    resp = requests.post(f"{BASE_URL}/api/v1/ingest/logs", json=log_payload)
    if resp.status_code != 202:
        print("Failed to send log")
        sys.exit(1)
        
    print("Log queued. Waiting for worker...")
    time.sleep(5) 
    
    # Check ES
    search_url = f"{ES_URL}/logs/_search"
    query = {
        "query": {
            "match": {
                "message": ssh_msg
            }
        }
    }
    
    try:
        res = requests.post(search_url, json=query, headers={"Content-Type": "application/json"})
        data = res.json()
        
        hits = data.get('hits', {}).get('hits', [])
        if hits:
            doc = hits[0]['_source']
            print("Found Log!")
            # Verify Fields
            print(f"Extracted IP: {doc.get('ip')}")
            print(f"Extracted User: {doc.get('user')}")
            print(f"Geo Country: {doc.get('geo', {}).get('country')}")
            
            if doc.get('ip') == "45.1.2.3" and doc.get('geo', {}).get('country') == "RU":
                 print("SUCCESS: Log parsed and enriched correctly!")
            else:
                 print("FAILED: Data mismatch")
                 sys.exit(1)
        else:
            print("FAILED: Log not found.")
            sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    test_enrichment()
