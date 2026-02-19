import requests
import time
import redis
import sys
from datetime import datetime, timezone

import os

# Config
# When running inside Docker (e.g. 'docker-compose exec worker ...'), these should point to service names (redis, elasticsearch).
# When running locally, they default to localhost.
API_URL = os.getenv("API_URL", "http://localhost:8000/api/v1")
ES_URL = os.getenv("ELASTICSEARCH_URL", "http://localhost:9200")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

r = redis.from_url(REDIS_URL, decode_responses=True)

def reset_state():
    print("\n[1] Resetting State...")
    # Flush specific keys to avoid nuking everything if unnecessary, but for test, flushdb is safest
    # Using specific patterns to be safer
    for key in r.keys("rate_limit:*"): r.delete(key)
    for key in r.keys("risk:*"): r.delete(key)
    for key in r.keys("blocked:*"): r.delete(key)
    for key in r.keys("state:*"): r.delete(key)
    print("    Redis keys cleared.")

def send_log(data):
    # Ensure timestamp is current UTC ISO
    data["timestamp"] = datetime.now(timezone.utc).isoformat()
    try:
        requests.post(f"{API_URL}/ingest/logs", json=data)
    except Exception as e:
        print(f"    Error sending log: {e}")

def verify_attack_1_brute_force():
    print("\n[2] Testing Attack: SSH Brute Force (Rule-Based)")
    attacker_ip = "192.168.100.1"
    
    # Send 6 failed logins
    for _ in range(6):
        send_log({
            "source": "ssh",
            "message": f"Failed password for invalid user hacker from {attacker_ip} port 22 ssh2",
            "ip": attacker_ip,
            "event_type": "ssh_login_failed"
        })
        time.sleep(0.05)
    
    print("    Logs sent. Waiting 5s for worker...")
    time.sleep(5)
    
    # Force Refresh
    requests.post(f"{ES_URL}/_refresh")

    # Check ES for Alert
    query = {
        "query": {
            "bool": {
                "must": [
                    {"match": {"source_ip": attacker_ip}}
                ]
            }
        }
    }
    res = requests.get(f"{ES_URL}/alerts-write/_search", json=query).json()
    print(f"    DEBUG: Found {res.get('hits', {}).get('total', {}).get('value', 0)} alerts for {attacker_ip}")
    for hit in res.get('hits', {}).get('hits', []):
        print(f"       -> {hit['_source'].get('rule_name')}")

    # Check for specific rule
    found = False
    for hit in res.get('hits', {}).get('hits', []):
        if "SSH Brute Force" in hit['_source'].get('rule_name', ''):
            found = True
            break
            
    if found:
        print(f"    ✅ PASS: SSH Brute Force Alert detected in ES.")
    else:
        print("    ❌ FAIL: No SSH Brute Force Alert found in ES.")

def verify_attack_2_suspicious_admin_and_block():
    print("\n[3] Testing Attack: Suspicious Admin & Auto-Block (Rule + Response)")
    attacker_ip = "192.168.100.66" # New IP
    
    # Send Successful Login for 'admin'
    send_log({
        "source": "ssh",
        "message": f"Accepted password for admin from {attacker_ip} port 22 ssh2",
        "ip": attacker_ip,
        "user": "admin",
        "event_type": "ssh_login_success"
    })
    
    print("    Log sent. Waiting 5s for worker & response...")
    time.sleep(5)
    
    # Check ES for Alert
    query = {
        "query": {
            "bool": {
                "must": [
                    {"match": {"source_ip": attacker_ip}}
                ]
            }
        }
    }
    res = requests.get(f"{ES_URL}/alerts-write/_search", json=query).json()
    hits = res.get('hits', {}).get('total', {}).get('value', 0)
    print(f"    DEBUG: Found {hits} alerts for {attacker_ip}")
    
    found = False
    for hit in res.get('hits', {}).get('hits', []):
        if "Suspicious Admin Login" in hit['_source'].get('rule_name', ''):
            found = True
            break
            
    if found:
        print(f"    ✅ PASS: Suspicious Admin Alert detected in ES.")
    else:
        print("    ❌ FAIL: No Suspicious Admin Alert found.")
        
    # Check Redis for Block
    if r.exists(f"blocked:{attacker_ip}"):
         print(f"    ✅ PASS: IP {attacker_ip} is BLOCKED in Redis.")
    else:
         print(f"    ❌ FAIL: IP {attacker_ip} is NOT blocked.")

def verify_attack_3_ml_anomaly():
    print("\n[4] Testing Attack: High Frequency Anomaly (ML)")
    attacker_ip = "192.168.100.77"
    
    # Send 30 requests in quick succession (High Frequency)
    # The ML model uses 'login_rate' from Redis. 
    # We rely on Ingest Service to increment this.
    for i in range(30):
        # Use a hardcoded valid Nginx timestamp format to pass ES validation
        # The actual time doesn't matter for the "High Frequency" ML check as long as they are close together
        ts_str = "09/Jan/2026:12:00:00 +0000" 
        send_log({
            "source": "nginx",
            "message": f'192.168.100.77 - - [{ts_str}] "GET /api/v1/sensitive_data_{i} HTTP/1.1" 200 123 "-" "-"',
            "ip": attacker_ip
        })
    
    print("    Logs sent. Waiting 5s for worker...")
    time.sleep(5)
    
    # Check Logs for 'ml_anomaly: true'
    query = {
        "query": {
            "bool": {
                "must": [
                    {"match": {"ip": attacker_ip}}
                ]
            }
        }
    }
    res = requests.get(f"{ES_URL}/logs-write/_search", json=query).json()
    hits = 0
    for hit in res.get('hits', {}).get('hits', []):
        if hit['_source'].get('ml_anomaly') is True:
            hits += 1
            
    if hits > 0:
        print(f"    ✅ PASS: ML Anomaly detected in ES ({hits} logs flagged).")
    else:
        print("    ❌ FAIL: No ML Anomaly flagged.")

def verify_attack_4_correlation():
    print("\n[5] Testing Attack: Correlated Incident (Brute -> PrivEsc)")
    attacker_ip = "192.168.100.88"
    
    # Phase 1: Brute Force
    for _ in range(6):
        send_log({
            "source": "ssh",
            "message": f"Failed password for root from {attacker_ip} port 22 ssh2",
            "ip": attacker_ip,
            "event_type": "ssh_login_failed"
        })
        time.sleep(0.05)
    
    # Phase 2: Success
    time.sleep(1)
    send_log({
        "source": "ssh",
        "message": f"Accepted password for root from {attacker_ip} port 22 ssh2",
        "ip": attacker_ip,
        "event_type": "ssh_login_success"
    })
    
    # Phase 3: Sudo
    time.sleep(1)
    send_log({
        "source": "ssh",
        "message": "sudo cat /etc/shadow",
        "ip": attacker_ip
    })
    
    print("    Attack chain sent. Waiting 5s for worker...")
    time.sleep(5)
    
    # Check Incidents Index
    query = {
        "query": {
            "bool": {
                "must": [
                    {"match": {"log_reference.ip": attacker_ip}}
                ]
            }
        }
    }
    res = requests.get(f"{ES_URL}/incidents-write/_search", json=query).json()
    hits = res.get('hits', {}).get('total', {}).get('value', 0)
    
    if hits > 0:
        print(f"    ✅ PASS: Correlated Incident detected in ES ({hits} incidents).")
    else:
         print("    ❌ FAIL: No Incident found.")

if __name__ == "__main__":
    try:
        reset_state()
        verify_attack_1_brute_force()
        verify_attack_2_suspicious_admin_and_block()
        verify_attack_3_ml_anomaly()
        verify_attack_4_correlation()
        print("\n--- Verification Complete ---")
    except Exception as e:
        print(f"\n❌ FATAL ERROR: {e}")
