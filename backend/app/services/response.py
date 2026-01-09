import redis
import yaml
import os
import logging
import ipaddress
from typing import Dict, Any, List
from app.core.config import settings

logger = logging.getLogger(__name__)

CONFIG_PATH = "backend/app/response/response_config.yaml"

class ResponseService:
    def __init__(self):
        self.redis = redis.Redis.from_url(settings.REDIS_URL, decode_responses=True)
        self.config = self.load_config()
        self.whitelist = [ipaddress.ip_network(cidr) for cidr in self.config.get("whitelist", {}).get("cidrs", [])]
        self.policy = self.config.get("policy", {})

    def load_config(self):
        try:
            if os.path.exists(CONFIG_PATH):
                with open(CONFIG_PATH, "r") as f:
                    return yaml.safe_load(f)
            return {}
        except Exception as e:
            logger.error(f"Failed to load response config: {e}")
            return {}

    def is_whitelisted(self, ip: str) -> bool:
        try:
            ip_obj = ipaddress.ip_address(ip)
            for net in self.whitelist:
                if ip_obj in net:
                    return True
        except ValueError:
            pass # Invalid IP
        return False

    def calculate_risk_score(self, log_entry: Dict[str, Any]) -> int:
        """
        Calculate simple risk score based on severity and ML score.
        """
        score = 0
        severity = log_entry.get("severity", "INFO")
        
        # Base Severity Score
        if severity == "CRITICAL":
            score = 100
        elif severity == "HIGH":
            score = 70
        elif severity == "MEDIUM":
            score = 40
        else:
            score = 10

        # ML Modifier (Boost score if ML is confident)
        ml_result = log_entry.get("anomaly_score") # Assuming anomalies merged into log
        # Or checking specific ML output if stored differently.
        # For now, let's look at incidents list size as a multiplier
        if len(log_entry.get("incidents", [])) > 0:
            score += 10 # Boost for confirmed incidents

        # Cap at 100 for normalization, but we can go higher for extreme threats
        return score

    def evaluate(self, log_entry: Dict[str, Any]):
        """
        Decide and execute response.
        """
        ip = log_entry.get("ip") or log_entry.get("metadata", {}).get("ip")
        if not ip:
            return

        if self.is_whitelisted(ip):
            logger.info(f"Response: IP {ip} is whitelisted. Ignoring.")
            return

        risk_score = self.calculate_risk_score(log_entry)
        threshold = self.policy.get("block_threshold", 80)
        
        if risk_score >= threshold:
            self.execute_block(ip, risk_score)
            return {"action": "block", "score": risk_score, "reason": f"Risk Score {risk_score} > Threshold {threshold}"}
        
        return {"action": "monitor", "score": risk_score}

    def execute_block(self, ip: str, score: int):
        """
        Simulate Block: Add to Redis 'blocked:{ip}'
        """
        duration = self.policy.get("block_duration_seconds", 300)
        key = f"blocked:{ip}"
        
        # Only block if not already blocked (or refresh TTL)
        self.redis.setex(key, duration, f"Risk Score: {score}")
        logger.warning(f"Response: BLOCKED IP {ip} for {duration}s. Reason: Risk Score {score}")
        
        # In a real system, here we would call:
        # subprocess.run(["ufw", "deny", "from", ip]) 
        # But we are using the Ingest Service to enforce it.

response_service = ResponseService()
