import requests
import json
import time
import sys

BASE_URL = "http://localhost:8000"
ES_URL = "http://localhost:9200"

def test_correlation():
    print("\n--- Testing Correlation Engine (The Flex) ---")
    ip = "203.0.113.10" # Public IP example (will map to CN based on Mock, but fine)
    
    # 1. Phase 1: Brute Force (5 failed logins)
    print(f"1. Simulating Brute Force from {ip}...")
    for i in range(6):
        log_payload = {
            "source": "ssh",
            "level": "INFO", 
            "message": f"Failed password for invalid user root from {ip} port 22 ssh2",
            "metadata": {}
        }
        requests.post(f"{BASE_URL}/api/v1/ingest/logs", json=log_payload)
        time.sleep(0.05)
    
    print("   [Wait] Processing Phase 1...")
    time.sleep(2)
    
    # 2. Phase 2: Successful Login
    print(f"2. Simulating Successful Login from {ip}...")
    log_payload = {
        "source": "ssh",
        "level": "INFO", 
        "message": f"Accepted password for root from {ip} port 22 ssh2",
        "metadata": {}
    }
    requests.post(f"{BASE_URL}/api/v1/ingest/logs", json=log_payload)
    
    print("   [Wait] Processing Phase 2...")
    time.sleep(2)
    
    # 3. Phase 3: Privilege Escalation (Sudo)
    print(f"3. Simulating Sudo Command from {ip}...")
    log_payload = {
        "source": "ssh",
        "level": "INFO", 
        "message": f"sudo: root : TTY=pts/0 ; PWD=/root ; USER=root ; COMMAND=/bin/bash",
        "metadata": {},
        "ip": ip # Explicitly setting IP in metadata or relying on extraction. 
                 # Our parser puts it in top level log_entry. 
                 # But our Nginx/SSH regex parser extracts it from MESSAGE.
                 # The 'sudo' log format in parser isn't defined!
                 # NormalizationService only has nginx/ssh patterns.
                 # If I send a generic log, it won't extract 'ip'.
                 # So I must ensure 'ip' is present in the log_entry passed to Enrichment/Correlation.
                 # I'll pass it in metadata and hope Enrichment checks metadata or I'll just pass 'ip' top level if API allows.
                 # API model LogEntry has metadata. Enrichment checks metadata['ip'].
                 # Correlation checks log_entry['ip'].
                 # So I need to put it where Correlation looks. 
                 # Enrichemnt might populate log_entry['ip'] from metadata['ip'] if I modify it?
                 # Let's check EnrichmentService.enrich_log:
                 # ip = log_entry.get("ip") or log_entry.get("metadata", {}).get("ip")
                 # But it just sets log_entry["geo"]. It doesn't back-fill log_entry["ip"] if missing.
                 # CorrelationService checks log_entry.get('ip').
                 # So I should pass 'ip' in the top-level JSON manually IF the parser doesn't extract it.
                 # BUT LogEntry model (Pydantic) doesn't have 'ip' field at root, only 'source', 'level', 'message', 'metadata'.
                 # Wait, 'LogEntry' in `models/log.py` defines schema.
                 # If I send `ip` in JSON to API, Pydantic might strip it if checking `extra='ignore'`. 
                 # Default is usually ignore.
                 # So I should put it in metadata, and update CorrelationService to check metadata as fallback.
    }
    # Fix: Put IP in metadata for safety, AND verify CorrelationService reads it.
    # Actually, let's update CorrelationService locally to check metadata['ip'] too?
    # Or rely on parser? 'sudo' log isn't parsed by my regex parser.
    # So I will update `test_correlation.py` to stick IP in metadata, AND I will quickly patch CorrelationService to look there too.
    
    # Update script to include metadata ip
    log_payload['metadata']['ip'] = ip
    requests.post(f"{BASE_URL}/api/v1/ingest/logs", json=log_payload)
    
    print("   [Wait] Processing Phase 3...")
    time.sleep(5)
    
    # 4. Verify Critical Incident
    search_url = f"{ES_URL}/logs/_search"
    query = {
        "query": {
            "match": {
                "incidents": "CRITICAL"
            }
        }
    }
    
    try:
        res = requests.post(search_url, json=query, headers={"Content-Type": "application/json"})
        hits = res.json().get('hits', {}).get('hits', [])
        
        if hits:
            print("SUCCESS: Critical Incident Detected!")
            print(hits[0]['_source'].get('incidents'))
        else:
            print("FAILED: No Critical Incident found.")
            # Debug
            sys.exit(1)
            
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    test_correlation()
