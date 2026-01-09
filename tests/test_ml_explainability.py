from app.services.detection_ml import ml_detector
from app.core.config import settings
import redis

def test_ml_explainability():
    print("\n--- Testing Explainable ML Detection ---")
    
    # Setup Redis for frequency test
    r = redis.Redis.from_url(settings.REDIS_URL, decode_responses=True)
    test_ip = "10.0.0.99"
    r.set(f"rate_limit:{test_ip}", 1000) # Simulate EXTREME frequency (1000 req/min)

    # Case 1: Normal Log
    # Hour 14 (2pm), Short msg, HTTP, Low frequency (default 0 for random IP)
    normal_log = {
        "timestamp": "2023-10-27T14:00:00",
        "message": "GET /index.html HTTP/1.1",
        "source": "nginx",
        "ip": "192.168.1.5" # No redis entry = 0 freq
    }
    
    res_normal = ml_detector.predict(normal_log)
    print(f"Normal Log Score: {res_normal['score']}")
    if res_normal['score'] < 0.6:
        print("   SUCCESS: Normal log correctly classified as normal.")
    else:
        print(f"   FAILED: Normal log flagged as anomaly. {res_normal}")

    # Case 2: Anomalous Log (High Frequency)
    anomaly_log = {
        "timestamp": "2023-10-27T14:00:00", 
        "message": "GET /login HTTP/1.1",
        "source": "nginx",
        "ip": test_ip # We set freq=100 in Redis
    }
    
    res_anomaly = ml_detector.predict(anomaly_log)
    print(f"Anomaly Log Score: {res_anomaly['score']}")
    print(f"Explanation: {res_anomaly['explanation']}")
    
    if res_anomaly['score'] > 0.6:
        print("   SUCCESS: High Freq log flagged as anomaly.")
        if "Frequency" in str(res_anomaly['explanation']):
             print("   SUCCESS: Explanation cites 'Frequency'.")
        else:
             print(f"   WARNING: Explanation might be off: {res_anomaly['explanation']}")
    else:
         print(f"   FAILED: High Freq log NOT flagged. {res_anomaly}")

    # Cleanup
    r.delete(f"rate_limit:{test_ip}")

if __name__ == "__main__":
    test_ml_explainability()
