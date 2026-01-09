from app.services.storage import storage_service
from elasticsearch import Elasticsearch
from app.core.config import settings
import time

def test_ilm_storage():
    print("\n--- Testing ILM Storage Routing ---")
    
    es = Elasticsearch(settings.ELASTICSEARCH_URL)
    
    # Dummy Log with Alert
    test_log = {
        "timestamp": "2023-10-27T12:00:00",
        "ip": "1.2.3.4",
        "message": "Test ILM Log",
        "severity": "HIGH",
        "alerts": ["Test Alert Rule 1"],
        "incidents": ["Test Incident A"]
    }
    
    print("1. Indexing Log via StorageService...")
    storage_service.index_log(test_log)
    
    print("   Waiting for ES refresh...")
    time.sleep(2)
    
    # 2. Check LOGS Alias
    res_logs = es.search(index="logs-write", query={"match": {"ip": "1.2.3.4"}})
    if res_logs['hits']['total']['value'] > 0:
        print("   SUCCESS: Log found in 'logs-write'.")
    else:
        print("   FAILED: Log not found in 'logs-write'.")

    # 3. Check ALERTS Alias
    res_alerts = es.search(index="alerts-write", query={"match": {"rule_name": "Test Alert Rule 1"}})
    if res_alerts['hits']['total']['value'] > 0:
        print("   SUCCESS: Alert found in 'alerts-write'.")
    else:
        print("   FAILED: Alert not found in 'alerts-write'.")
        
    # 4. Check INCIDENTS Alias
    res_incident = es.search(index="incidents-write", query={"match": {"incident": "Test Incident A"}})
    if res_incident['hits']['total']['value'] > 0:
        print("   SUCCESS: Incident found in 'incidents-write'.")
    else:
        print("   FAILED: Incident not found in 'incidents-write'.")

if __name__ == "__main__":
    test_ilm_storage()
