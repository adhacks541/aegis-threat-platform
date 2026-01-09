import redis
import yaml
import os
import logging
from typing import List, Dict, Any
from app.core.config import settings

logger = logging.getLogger(__name__)

CONFIG_PATH = "app/rules/detection_config.yaml"

class RuleBasedDetector:
    def __init__(self):
        self.redis = redis.Redis.from_url(settings.REDIS_URL, decode_responses=True)
        self.config = self.load_config()
        
    def load_config(self):
        try:
            if os.path.exists(CONFIG_PATH):
                with open(CONFIG_PATH, "r") as f:
                    return yaml.safe_load(f).get("rules", {})
            else:
                logger.warning(f"Detection Config not found at {CONFIG_PATH}. Using defaults.")
                return {}
        except Exception as e:
            logger.error(f"Failed to load detection config: {e}")
            return {}

    def check_rules(self, log_entry: dict) -> tuple[List[str], str]:
        """
        Check log against rules. Returns (alerts_list, max_severity).
        """
        alerts = []
        max_severity = "INFO"
        
        # Severity Map for comparison
        sev_map = {"CRITICAL": 50, "HIGH": 40, "MEDIUM": 30, "LOW": 20, "INFO": 10}
        
        def update_severity(new_sev):
            nonlocal max_severity
            if sev_map.get(new_sev, 0) > sev_map.get(max_severity, 0):
                max_severity = new_sev

        ip = log_entry.get('ip') or log_entry.get('metadata', {}).get('ip')
        user = log_entry.get('user') or log_entry.get('metadata', {}).get('user')
        
        # 1. SSH Brute Force
        rule_cfg = self.config.get("ssh_brute_force", {})
        if rule_cfg.get("enabled"):
            if log_entry.get('event_type') == 'ssh_login_failed' and ip:
                key = f"risk:brute:{ip}"
                count = self.redis.incr(key)
                if count == 1:
                    self.redis.expire(key, rule_cfg.get("window_seconds", 60))
                
                if count >= rule_cfg.get("threshold", 5):
                     alerts.append(f"SSH Brute Force Detected from {ip} ({count} failures)")
                     update_severity(rule_cfg.get("severity", "HIGH"))

        # 2. Sudo Usage
        rule_cfg = self.config.get("sudo_usage", {})
        if rule_cfg.get("enabled"):
            msg = log_entry.get('message', '').lower()
            if "sudo" in msg and "command not found" not in msg:
                 alerts.append("Suspicious Sudo Command Detection")
                 update_severity(rule_cfg.get("severity", "MEDIUM"))
        
        # 3. Suspicious Admin Login (New IP)
        rule_cfg = self.config.get("suspicious_admin", {})
        if rule_cfg.get("enabled") and user and ip:
             admin_users = rule_cfg.get("admin_users", ["root", "admin", "ubuntu"])
             if user in admin_users:
                 known_key = f"state:admin_ips:{user}"
                 
                 is_known = self.redis.sismember(known_key, ip)
                 if not is_known:
                     alerts.append(f"Suspicious Admin Login (New IP): User {user} from {ip}")
                     update_severity(rule_cfg.get("severity", "CRITICAL"))
                     self.redis.sadd(known_key, ip)
                 
        return alerts, max_severity

rule_detector = RuleBasedDetector()
