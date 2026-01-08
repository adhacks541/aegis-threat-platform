import requests
import redis
import json
import time
import sys

# Requirements: request, redis
# pip install requests redis

BASE_URL = "http://localhost:8000"
REDIS_URL = "redis://localhost:6379/0"

def wait_for_api():
    print("Waiting for API to be ready...")
    for _ in range(30):
        try:
            resp = requests.get(f"{BASE_URL}/")
            if resp.status_code == 200:
                print("API is ready!")
                return True
        except requests.exceptions.ConnectionError:
            pass
        time.sleep(1)
    print("API failed to come up.")
    return False

def test_ingestion():
    log_payload = {
        "source": "test_script",
        "level": "INFO",
        "message": "This is a verification log",
        "metadata": {"user": "admin"}
    }
    
    print(f"Sending log: {log_payload}")
    resp = requests.post(f"{BASE_URL}/api/v1/ingest/logs", json=log_payload)
    
    if resp.status_code != 202:
        print(f"FAILED: Expected 202, got {resp.status_code}")
        print(resp.text)
        sys.exit(1)
        
    print("Log sent successfully (HTTP 202)")
    
    # Verify Redis
    print("Checking Redis Stream...")
    try:
        r = redis.Redis.from_url(REDIS_URL, decode_responses=True)
        # Read items from stream 'logs_stream'
        # xread returns [[stream_name, [(id, data)]]]
        entries = r.xread({"logs_stream": "0-0"}, count=1, block=5000)
        
        if not entries:
            print("FAILED: No entries found in Redis stream 'logs_stream'")
            sys.exit(1)
            
        stream, messages = entries[0]
        msg_id, msg_data = messages[0]
        
        # msg_data['data'] should be our JSON string
        stored_log = json.loads(msg_data['data'])
        
        if stored_log['message'] == "This is a verification log":
            print("SUCCESS: Log found in Redis!")
        else:
            print(f"FAILED: Log content mismatch: {stored_log}")
            sys.exit(1)
            
    except Exception as e:
        print(f"Redis check failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    if not wait_for_api():
        sys.exit(1)
    test_ingestion()
