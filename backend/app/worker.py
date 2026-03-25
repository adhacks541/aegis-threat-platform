"""
Background worker: reads from the Redis Stream, runs the full pipeline,
publishes results to the Redis pub/sub channel, and enforces iptables blocks.
"""
import redis
import json
import time
import subprocess
import logging
import os
from app.core.config import settings
from app.services.storage import storage_service
from app.services.normalization import normalization_service
from app.services.enrichment import enrichment_service
from app.services.detection_rules import rule_detector
from app.services.detection_ml import ml_detector
from app.services.correlation import correlation_service
from app.services.response import response_service

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("aegis.worker")

r = redis.Redis.from_url(settings.REDIS_URL, decode_responses=True)
STREAM_KEY = "logs_stream"
GROUP_NAME = "ingest_group"
CONSUMER_NAME = "worker_1"
PUBSUB_CHANNEL = "aegis:feed"

# Whether the host supports iptables (set NET_ADMIN cap in Docker)
IPTABLES_ENABLED = os.getenv("IPTABLES_ENABLED", "false").lower() == "true"


# ---------------------------------------------------------------------------
# iptables helpers (Phase 4)
# ---------------------------------------------------------------------------

def iptables_block(ip: str):
    """Add a DROP rule for the given IP (idempotent via -C check)."""
    try:
        check = subprocess.run(
            ["iptables", "-C", "INPUT", "-s", ip, "-j", "DROP"],
            capture_output=True,
        )
        if check.returncode != 0:
            subprocess.run(
                ["iptables", "-I", "INPUT", "-s", ip, "-j", "DROP"],
                check=True,
            )
            logger.warning(f"iptables: blocked {ip}")
    except Exception as e:
        logger.error(f"iptables block failed for {ip}: {e}")


def iptables_unblock(ip: str):
    """Remove the DROP rule for the given IP."""
    try:
        subprocess.run(
            ["iptables", "-D", "INPUT", "-s", ip, "-j", "DROP"],
            capture_output=True,
        )
        logger.info(f"iptables: unblocked {ip}")
    except Exception as e:
        logger.error(f"iptables unblock failed for {ip}: {e}")


def sync_iptables_blocks():
    """
    Called periodically: scan Redis for blocked:{ip} keys.
    Any key that has disappeared means the TTL expired → remove iptables rule.
    We track active rules in a Redis set 'iptables:blocked'.
    """
    if not IPTABLES_ENABLED:
        return
    try:
        tracked = r.smembers("iptables:blocked")
        for ip in tracked:
            if not r.exists(f"blocked:{ip}"):
                iptables_unblock(ip)
                r.srem("iptables:blocked", ip)

        # Also ensure any new blocks are enforced
        blocked_keys = r.keys("blocked:*")
        for key in blocked_keys:
            ip = key.split(":", 1)[1]
            if ip not in tracked:
                iptables_block(ip)
                r.sadd("iptables:blocked", ip)
    except Exception as e:
        logger.error(f"sync_iptables_blocks error: {e}")


# ---------------------------------------------------------------------------
# Consumer group setup
# ---------------------------------------------------------------------------

def create_consumer_group():
    try:
        r.xgroup_create(STREAM_KEY, GROUP_NAME, id="0", mkstream=True)
    except redis.exceptions.ResponseError as e:
        if "BUSYGROUP" not in str(e):
            raise


# ---------------------------------------------------------------------------
# Main processing loop
# ---------------------------------------------------------------------------

def process_messages():
    logger.info(f"Worker {CONSUMER_NAME} started on stream '{STREAM_KEY}'…")
    create_consumer_group()

    last_iptables_sync = time.time()
    IPTABLES_SYNC_INTERVAL = 30  # seconds

    while True:
        try:
            # Periodic iptables sync (Phase 4)
            if IPTABLES_ENABLED and time.time() - last_iptables_sync > IPTABLES_SYNC_INTERVAL:
                sync_iptables_blocks()
                last_iptables_sync = time.time()

            entries = r.xreadgroup(
                GROUP_NAME, CONSUMER_NAME, {STREAM_KEY: ">"}, count=10, block=2000
            )

            if not entries:
                continue

            for _stream, messages in entries:
                for message_id, message_data in messages:
                    raw_json = message_data.get("data")
                    if not raw_json:
                        r.xack(STREAM_KEY, GROUP_NAME, message_id)
                        continue

                    log_entry = json.loads(raw_json)

                    try:
                        _process_single(log_entry)
                    except Exception as e:
                        logger.error(f"Processing error for {message_id}: {e}")

                    r.xack(STREAM_KEY, GROUP_NAME, message_id)

        except Exception as e:
            logger.error(f"Worker loop error: {e}")
            time.sleep(1)


def _process_single(log_entry: dict):
    # 1. Normalize
    extracted = normalization_service.parse_log(
        log_entry.get("message", ""), log_entry.get("source", "")
    )
    if extracted:
        log_entry.update(extracted)

    # 2. Enrich
    enrichment_service.enrich_log(log_entry)

    # 3. Rule-based detection
    alerts, rule_severity = rule_detector.check_rules(log_entry)
    if alerts:
        log_entry["alerts"] = alerts
        log_entry["severity"] = rule_severity
        logger.info(f"ALERT: {alerts} (Severity: {rule_severity})")

    # 4. ML detection
    anomaly_result = ml_detector.predict(log_entry)
    log_entry["anomaly_score"] = anomaly_result["score"]
    log_entry["anomaly_explanation"] = anomaly_result["explanation"]

    if anomaly_result["score"] > 0.7:
        log_entry["ml_anomaly"] = True
        log_entry.setdefault("alerts", []).append(
            f"ML Detection: {anomaly_result['explanation']}"
        )
        logger.info(f"ML ANOMALY: {anomaly_result['explanation']}")

    # 5. Correlation
    incidents = correlation_service.process_event(log_entry) or []
    if incidents:
        log_entry.setdefault("incidents", []).extend(incidents)
        log_entry["severity"] = "CRITICAL"
        logger.warning(f"INCIDENT: {incidents}")

    # 6. Automated response (Redis block + optional iptables)
    resp_result = response_service.evaluate(log_entry)
    if resp_result:
        log_entry["response_action"] = resp_result
        if resp_result.get("action") == "block" and IPTABLES_ENABLED:
            ip = log_entry.get("ip") or log_entry.get("metadata", {}).get("ip")
            if ip:
                iptables_block(ip)
                r.sadd("iptables:blocked", ip)

    # 7. Index to ES
    storage_service.index_log(log_entry)
    logger.debug(
        f"Indexed: {log_entry.get('timestamp')} — {log_entry.get('message', '')[:80]}"
    )

    # 8. Publish to WebSocket pub/sub (Phase 3)
    r.publish(PUBSUB_CHANNEL, json.dumps(log_entry, default=str))


if __name__ == "__main__":
    time.sleep(5)  # Let ES/Redis warm up
    process_messages()
