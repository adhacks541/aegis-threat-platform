import requests
import json
import time
import sys

# Requirements: request
# pip install requests

BASE_URL = "http://localhost:8000"
ES_URL = "http://localhost:9200"

def test_rule_detection():
    print("\n--- Testing Rule-Based Detection (SSH Brute Force) ---")
    ip = "192.168.1.100"
    
    # Send 6 failed login attempts
    for i in range(6):
        log_payload = {
            "source": "ssh",
            "level": "INFO", 
            "message": f"Failed password for invalid user hacker from {ip} port 22 ssh2",
            "metadata": {}
        }
        requests.post(f"{BASE_URL}/api/v1/ingest/logs", json=log_payload)
        time.sleep(0.1)
    
    print("Sent 6 failed logins. Waiting for worker...")
    time.sleep(5)
    
    # Check for Alert in ES
    # We look for the last log, it should have severity HIGH and alerts field
    search_url = f"{ES_URL}/logs/_search"
    query = {
        "query": {
            "bool": {
                "must": [
                    {"match": {"ip": ip}},
                    {"match": {"severity": "HIGH"}}
                ]
            }
        }
    }
    
    try:
        res = requests.post(search_url, json=query, headers={"Content-Type": "application/json"})
        data = res.json()
        hits = data.get('hits', {}).get('hits', [])
        
        if hits:
            print("SUCCESS: Rule Alert Found!")
            print(hits[0]['_source'].get('alerts'))
        else:
            print("FAILED: No Rule Alert found.")
            # Debug: print what IS there
            debug_res = requests.post(f"{ES_URL}/logs/_search", json={"query": {"match_all": {}}}, headers={"Content-Type": "application/json"})
            print("DEBUG: All logs in ES:", json.dumps(debug_res.json(), indent=2))
            sys.exit(1)
            
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

def test_ml_detection():
    print("\n--- Testing ML Detection (Anomaly) ---")
    # Send a weird log: Weird source, long message, error level (mapped to high val), off-hours (we can't control time easily in payload unless we override ts parsing, but let's try weird content)
    # Our simple feature extractor uses: [hour, lvl, msg_len, src_hash]
    # Normal was: hour=9-17, lvl=INFO(1), len=50, src=nginx
    
    # Anomalous: 
    # Hour: we can't easily spoof without changing vectorizer to use provided timestamp. 
    # But we can change Level to CRITICAL (4), Length to very long (e.g. 1000), Source to 'unknown_alien'
    
    weird_msg = "X" * 200
    log_payload = {
        "source": "unknown_alien_process",
        "level": "CRITICAL",
        "message": weird_msg,
        "metadata": {}
    }
    
    requests.post(f"{BASE_URL}/api/v1/ingest/logs", json=log_payload)
    print("Sent anomalous log. Waiting for worker...")
    time.sleep(5)
    
    # Check for ML Anomaly
    search_url = f"{ES_URL}/logs/_search"
    query = {
        "query": {
             "term": {"ml_anomaly": True}
        }
    }
    
    try:
        res = requests.post(search_url, json=query, headers={"Content-Type": "application/json"})
        data = res.json()
        hits = data.get('hits', {}).get('hits', [])
        
        if hits:
            # Check if one of them is our weird log
            for h in hits:
                if h['_source'].get('source') == 'unknown_alien_process':
                    print("SUCCESS: ML Anomaly Detected!")
                    return
            print("FAILED: ML Anomaly not found for our log.")
            sys.exit(1)
        else:
            print("FAILED: No ML Anomalies found.")
            sys.exit(1)
            
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    test_rule_detection()
    test_ml_detection()
