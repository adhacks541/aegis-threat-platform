import json
import random
import numpy as np
from datetime import datetime, timedelta
import ipaddress

# Configuration
TOTAL_LOGS = 10000
START_TIME = datetime.now() - timedelta(days=7)
OUTPUT_FILE = "backend/training_data.json"

# Networking Constants
COMMON_PORTS = [80, 443, 22, 53, 3306]
HTTP_METHODS = ["GET", "POST", "PUT", "DELETE"]
STATUS_CODES = [200, 200, 200, 404, 500, 301]

def generate_zipfian_ips(num_ips=100, shape=1.5):
    """
    Generate IPs with a distribution where few IPs are very common (Zipf/Power Law).
    """
    ips = [str(ipaddress.IPv4Address(random.getrandbits(32))) for _ in range(num_ips)]
    # Use Zipf distribution: indices 1..num_ips, probabilities ~ 1/k^a
    weights = 1.0 / np.power(np.arange(1, num_ips + 1), shape)
    weights /= weights.sum() # Normalize
    return ips, weights

def generate_dataset():
    print(f"Generating {TOTAL_LOGS} logs with Zipfian IP distribution...")
    
    ips, weights = generate_zipfian_ips(num_ips=200, shape=1.5)
    
    logs = []
    
    for i in range(TOTAL_LOGS):
        # 1. Realistic Timestamp (Spread over 7 days, more during day)
        dt = START_TIME + timedelta(minutes=random.randint(0, 7*24*60))
        # Add simpler circadian rhythm (more traffic 9am-6pm)
        if 9 <= dt.hour <= 18:
            if random.random() < 0.3: # Turbo boost during day
                dt += timedelta(seconds=random.randint(0, 60))

        # 2. Select IP based on Power Law
        ip = np.random.choice(ips, p=weights)
        
        # 3. Message Type Pattern
        r = random.random()
        if r < 0.8:
            # Normal HTTP Traffic
            method = random.choice(HTTP_METHODS)
            path = random.choice(["/login", "/api/v1/data", "/index.html", "/images/logo.png"])
            status = random.choice(STATUS_CODES)
            msg = f"{method} {path} HTTP/1.1 {status}"
        elif r < 0.95:
            # SSH Traffic
            msg = f"Accepted publickey for ubuntu from {ip} port {random.randint(10000, 60000)}"
        else:
            # Random Noise / Error
            msg = f"Error: Connection timed out to database from {ip}"

        # 4. Feature Extraction (Simulated)
        # In detection_ml.py we extract: hour, msg_len, is_ssh, login_rate (from Redis)
        # We save raw features here to match what the ML model expects for training
        
        # Simulate login rate (Zipfian somewhat correlates with traffic, but we'll randomize for noise)
        # Normal traffic: 0-10 req/min
        login_rate = 0
        if ip in ips[:5]: # Top talkers
            login_rate = random.randint(5, 20)
        else:
            login_rate = random.randint(0, 5)

        log_entry = {
            "timestamp": dt.isoformat(),
            "ip": ip,
            "message": msg,
            "hour": dt.hour,
            "is_ssh": 1 if "ssh" in msg.lower() or "Accepted" in msg else 0,
            "msg_len": len(msg),
            "login_rate": login_rate
        }
        
        logs.append(log_entry)

    # 5. Inject Anomalies (Things we want Isolated Forest to find)
    print("Injecting Attack Patterns (Anomalies)...")
    
    # Anomaly 1: Burst Attack (DDoS) - 500 logs in 1 minute from NEW IP
    burst_ip = "192.168.66.6" 
    burst_time = START_TIME + timedelta(days=3, hours=12)
    for _ in range(500):
        logs.append({
            "timestamp": burst_time.isoformat(),
            "ip": burst_ip,
            "message": f"GET /api/v1/heavy-load HTTP/1.1 200",
            "hour": burst_time.hour,
            "is_ssh": 0,
            "msg_len": 35,
            "login_rate": random.randint(50, 100), # Abnormal Rate
            "is_injected_anomaly": True
        })
        
    # Anomaly 2: Weird Payload (Buffer Overflow attempt)
    # Very long message length
    for _ in range(50):
        logs.append({
            "timestamp": (START_TIME + timedelta(days=2)).isoformat(),
            "ip": "10.0.0.99",
            "message": "GET /" + "A"*500 + " HTTP/1.1 400",
            "hour": 14,
            "is_ssh": 0,
            "msg_len": 520, # HUGE length
            "login_rate": random.randint(1, 5),
            "is_injected_anomaly": True
        })

    # Save
    with open(OUTPUT_FILE, "w") as f:
        json.dump(logs, f, indent=2)
    
    print(f"Dataset generated at {OUTPUT_FILE}. Total records: {len(logs)}")

if __name__ == "__main__":
    generate_dataset()
