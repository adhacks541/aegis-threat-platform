import requests
import time
import random
from datetime import datetime

BASE_URL = "http://localhost:8000/api/v1/ingest"

def simulate_traffic():
    print("--- Simulating SOC Traffic ---")
    
    now_iso = datetime.utcnow().isoformat()
    
    # 1. Normal Traffic (50 logs)
    print("1. Sending Normal Traffic...")
    batch = []
    for i in range(50):
        batch.append({
            "source": "nginx",
            "message": f"GET /image_{i}.png HTTP/1.1 200",
            "timestamp": now_iso
        })
    requests.post(f"{BASE_URL}/logs", json=batch)

    # 2. Alerts (SSH Brute Force)
    print("2. Sending SSH Brute Force (High Severity)...")
    ip = "192.168.99.99"
    for i in range(6):
        requests.post(f"{BASE_URL}/logs", json={
            "source": "ssh",
            "ip": ip,
            "message": f"Failed password for root from {ip} port 22 ssh2",
            "event_type": "ssh_login_failed",
            "timestamp": datetime.utcnow().isoformat()
        })
        time.sleep(0.1)

    # 3. Incident (Correlated: Brute -> Success -> Sudo)
    print("3. Sending Complex Attack (Critical Incident)...")
    attacker = "10.10.10.10"
    # Brute
    for _ in range(6):
        requests.post(f"{BASE_URL}/logs", json={"source": "ssh", "ip": attacker, "event_type": "ssh_login_failed", "message": "fail", "timestamp": datetime.utcnow().isoformat()})
    time.sleep(1)
    # Success
    requests.post(f"{BASE_URL}/logs", json={"source": "ssh", "ip": attacker, "event_type": "ssh_login_success", "message": "success", "timestamp": datetime.utcnow().isoformat()})
    time.sleep(1)
    # Sudo
    requests.post(f"{BASE_URL}/logs", json={"source": "ssh", "ip": attacker, "message": "sudo cat /etc/shadow", "timestamp": datetime.utcnow().isoformat()})
    
    print("Done. Dashboard should be lit up.")

if __name__ == "__main__":
    simulate_traffic()
