import redis
import time
from app.core.config import settings

class RuleBasedDetector:
    def __init__(self):
        self.redis = redis.Redis.from_url(settings.REDIS_URL, decode_responses=True)
        # Rules configuration
        self.brute_force_window = 60 # seconds
        self.brute_force_threshold = 5

    def check_rules(self, log_entry: dict) -> list:
        """
        Check log against rules. Returns list of triggered alert names.
        """
        alerts = []
        
        # Rule 1: SSH Brute Force Detection
        if log_entry.get('event_type') == 'ssh_login_failed':
            ip = log_entry.get('ip')
            if ip:
                key = f"risk:brute:{ip}"
                # Increment counter
                count = self.redis.incr(key)
                if count == 1:
                    self.redis.expire(key, self.brute_force_window)
                
                if count >= self.brute_force_threshold:
                    alerts.append(f"SSH Brute Force Detected from {ip} ({count} failures)")

        # Rule 2: Suspicious Admin Activity (Example)
        # e.g., 'sudo' usage failures or simple keyword match
        msg = log_entry.get('message', '').lower()
        if 'sudo' in msg and 'incorrect password' in msg:
             alerts.append("Suspicious Sudo Failure")

        return alerts

rule_detector = RuleBasedDetector()
