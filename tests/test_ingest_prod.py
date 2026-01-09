import requests
import json
import time

BASE_URL = "http://localhost:8000/api/v1/ingest"

def test_prod_ingestion():
    print("\n--- Testing Production Ingestion (Batch + Raw + Limits) ---")
    
    # 1. Test Batch Ingestion
    print("1. Testing Batch JSON Ingestion...")
    batch_logs = [
        {
            "source": "prod_test",
            "level": "INFO",
            "message": f"Batch Log {i}",
            "metadata": {"batch_id": "batch_001"}
        } for i in range(5)
    ]
    
    headers = {
        "X-Source-Host": "server-01",
        "X-App-Name": "payment-service"
    }
    
    try:
        res = requests.post(f"{BASE_URL}/logs", json=batch_logs, headers=headers)
        if res.status_code == 202:
            print(f"   SUCCESS: Queued {res.json().get('count')} logs.")
        else:
            print(f"   FAILED: {res.status_code} - {res.text}")
    except Exception as e:
        print(f"   ERROR: {e}")

    # 2. Test Raw Ingestion
    print("2. Testing Raw Text Ingestion...")
    raw_text = "Oct 11 22:14:15 server-02 sshd[123]: Failed password for root"
    try:
        res = requests.post(
            f"{BASE_URL}/raw", 
            data=raw_text, 
            headers={"Content-Type": "text/plain", "X-Source-Host": "legacy-syslog"}
        )
        if res.status_code == 202:
            print("   SUCCESS: Raw log accepted.")
        else:
            print(f"   FAILED: {res.status_code} - {res.text}")
    except Exception as e:
        print(f"   ERROR: {e}")

    # 3. Test Rate Limiter (Spamming)
    print("3. Testing Rate Limiter (Spamming 1100 requests)...")
    success_count = 0
    blocked = False
    
    # Note: We need a fresh IP or just spam fast. Since we are localhost, we share the limit.
    # The limit is 1000/min. We pushed ~6 above. Let's push 1000 more.
    for i in range(1005):
        try:
            # Send lightweight request
            res = requests.post(
                f"{BASE_URL}/raw", 
                data=f"spam {i}", 
                headers={"Content-Type": "text/plain"}
            )
            if res.status_code == 202:
                success_count += 1
            elif res.status_code == 429:
                print(f"   SUCCESS: Rate Limit Hit at request #{i}!")
                blocked = True
                break
        except Exception:
            pass
            
    if not blocked:
        print("   WARNING: Rate Limit NOT hit (did you configure > 1000?)")
    else:
        print("   Rate Limiter Functional.")

if __name__ == "__main__":
    test_prod_ingestion()
