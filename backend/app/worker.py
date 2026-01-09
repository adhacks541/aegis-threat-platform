import redis
import json
import time
from app.core.config import settings
from app.services.storage import storage_service
from app.services.normalization import normalization_service
from app.services.enrichment import enrichment_service
from app.services.detection_rules import rule_detector
from app.services.detection_ml import ml_detector
from app.services.correlation import correlation_service
from app.services.response import response_service

# Reuse connection logic or create new
r = redis.Redis.from_url(settings.REDIS_URL, decode_responses=True)
STREAM_KEY = "logs_stream"
GROUP_NAME = "ingest_group"
CONSUMER_NAME = "worker_1"

def create_consumer_group():
    try:
        r.xgroup_create(STREAM_KEY, GROUP_NAME, id="0", mkstream=True)
    except redis.exceptions.ResponseError as e:
        if "BUSYGROUP" in str(e):
            pass # Group already exists
        else:
            raise e

def process_messages():
    print(f"Worker {CONSUMER_NAME} started listening on {STREAM_KEY}...")
    create_consumer_group()
    
    while True:
        try:
            # Read new messages manually via consumer group
            # '>' means messages never delivered to other consumers in this group
            entries = r.xreadgroup(GROUP_NAME, CONSUMER_NAME, {STREAM_KEY: ">"}, count=10, block=2000)
            
            if entries:
                for stream, messages in entries:
                    for message_id, message_data in messages:
                        # message_data is {'data': '{"json": ...}'}
                        raw_json = message_data.get('data')
                        if raw_json:
                            log_entry = json.loads(raw_json)
                            
                            # 1. Normalize
                            source_type = log_entry.get('source', '')
                            message_text = log_entry.get('message', '')
                            # 1. Normalization
                            extracted = normalization_service.parse_log(message_text, source_type)
                            if extracted:
                                # Merge extracted fields into main log or metadata
                                # Let's put them at the top level for cleaner ES querying, 
                                # but be careful not to overwrite protected fields.
                                log_entry.update(extracted)
                            print(f"DEBUG WORKER: Normalized Log: {log_entry}")
                            
                            # 2. Enrich
                            enrichment_service.enrich_log(log_entry)

                            # 3. Detection
                            # Rule-based
                            alerts, rule_severity = rule_detector.check_rules(log_entry)
                            if alerts:
                                log_entry['alerts'] = alerts
                                log_entry['severity'] = rule_severity
                                print(f"ALERT: {alerts} (Severity: {rule_severity})")
                            
                            # ML-based
                            anomaly_result = ml_detector.predict(log_entry)
                            log_entry['anomaly_score'] = anomaly_result['score']
                            log_entry['anomaly_explanation'] = anomaly_result['explanation']
                            
                            if anomaly_result['score'] > 0.7:
                                log_entry['ml_anomaly'] = True
                                if 'alerts' not in log_entry: 
                                    log_entry['alerts'] = []
                                log_entry['alerts'].append(f"ML Detection: {anomaly_result['explanation']}")
                                print(f"ML ANOMALY detected: {anomaly_result['explanation']}")

                            # 4. Correlation (The Flex)
                            incidents = correlation_service.process_event(log_entry)
                            if incidents:
                                if 'incidents' not in log_entry:
                                    log_entry['incidents'] = []
                                log_entry['incidents'].extend(incidents)
                                log_entry['severity'] = 'CRITICAL'
                                print(f"INCIDENT DETECTED: {incidents}")

                            # 5. Automated Response
                            resp_result = response_service.evaluate(log_entry)
                            if resp_result:
                                log_entry['response_action'] = resp_result

                            # 6. Index to ES
                            storage_service.index_log(log_entry)
                            print(f"Indexed log: {log_entry.get('timestamp')} - {log_entry.get('message')}")
                        
                        # Acknowledge
                        r.xack(STREAM_KEY, GROUP_NAME, message_id)
            
            # Optional: Handling of pending messages that crashed could go here (xpending/xclaim)
            
        except Exception as e:
            print(f"Worker error: {e}")
            time.sleep(1)

if __name__ == "__main__":
    # Wait for ES to accept connections?
    # StorageService init connects immediately but real connection check happens on calls mostly
    # But let's give services a moment to warm up if we are starting together
    time.sleep(5)
    process_messages()
