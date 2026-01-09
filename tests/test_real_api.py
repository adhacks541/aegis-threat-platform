import requests
import json
import time
import sys

BASE_URL = "http://localhost:8000"
ES_URL = "http://localhost:9200"

def test_real_apis():
    print("\n--- Testing Real API Integration (GeoIP + Threat Intel) ---")
    
    # 1. Use a known Bad IP (or just a public one)
    # 45.33.32.156 is a random public IP (Linode).
    ip = "45.33.32.156" 
    
    print(f"1. Sending Login Failure from Public IP: {ip}...")
    log_payload = {
        "source": "ssh",
        "level": "INFO", 
        "message": f"Failed password for root from {ip} port 22 ssh2",
        "metadata": {"ip": ip}
    }
    
    requests.post(f"{BASE_URL}/api/v1/ingest/logs", json=log_payload)
    
    print("   [Wait] Processing Enrichment (API Calls)...")
    time.sleep(10) # 10 seconds for External API + Indexing
    
    # 2. Verify Enrichment in Elasticsearch
    print("2. Verifying Enrichment Data...")
    search_url = f"{ES_URL}/logs/_search"
    query = {
        "query": {
            "match": {
                "ip": ip
            }
        },
        "sort": [{"timestamp": "desc"}],
        "size": 1
    }
    
    try:
        res = requests.post(search_url, json=query, headers={"Content-Type": "application/json"})
        hits = res.json().get('hits', {}).get('hits', [])
        
        if hits:
            source = hits[0]['_source']
            geo = source.get('geo', {})
            threat = source.get('threat_intel', {})
            
            print(f"   Country: {geo.get('country')} (Expected: US or similar)")
            print(f"   ISP: {geo.get('isp')}")
            print(f"   Abuse Score: {threat.get('abuse_score')} (From AbuseIPDB)")
            
            if geo.get('country') != 'Unknown' and 'abuse_score' in threat:
                print("SUCCESS: Log Enriched with Real Data!")
            else:
                print("WARNING: Geo/Threat data might be missing or Mocked.")
                print(f"Full Source: {source}")
        else:
            print("FAILED: Log not found in ES.")
            sys.exit(1)
            
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    test_real_apis()
