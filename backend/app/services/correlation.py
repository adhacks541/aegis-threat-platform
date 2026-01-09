import redis
from app.core.config import settings
from typing import Dict, Any, List

class CorrelationService:
    def __init__(self):
        self.redis = redis.Redis.from_url(settings.REDIS_URL, decode_responses=True)
        self.PHASE_1_TTL = 300 # 5 minutes to succeed after brute force
        self.PHASE_2_TTL = 300 # 5 minutes to escalate privileges after login

    def process_event(self, log_entry: Dict[str, Any]) -> List[str]:
        """
        Process log entry and return list of new Incidents detected.
        """
        incidents = []
        ip = log_entry.get('ip') or log_entry.get('metadata', {}).get('ip')
        if not ip:
            return incidents

        alerts = log_entry.get('alerts', [])
        
        # --- Phase 1: Brute Force Detection ---
        # We rely on RuleBasedDetector to add the specific alert string.
        # Check if ANY alert indicates brute force
        is_brute_force = any("Brute Force" in alert for alert in alerts)
        
        if is_brute_force:
            # Set Phase 1 Indicator
            key = f"risk:phase:1:{ip}"
            self.redis.setex(key, self.PHASE_1_TTL, "true")
            # print(f"DEBUG: Set Phase 1 for {ip}")

        # --- Phase 2: Successful Login after Brute Force ---
        if log_entry.get('event_type') == 'ssh_login_success':
            # Check if Phase 1 exists
            if self.redis.exists(f"risk:phase:1:{ip}"):
                # Set Phase 2 Indicator
                key = f"risk:phase:2:{ip}"
                self.redis.setex(key, self.PHASE_2_TTL, "true")
                incidents.append(f"Suspicious Login after Brute Force ({ip})")
        
        # --- Phase 3: Privilege Escalation (Sudo) after Suspicious Login ---
        # Simple keyword check for sudo usage. In real app, normalization would give us 'command' field.
        # We'll check 'sudo' in message for now.
        msg = log_entry.get('message', '').lower()
        if 'sudo' in msg:
            if self.redis.exists(f"risk:phase:2:{ip}"):
                incidents.append(f"CRITICAL: Privilege Escalation after Brute Force ({ip})")
        
        return incidents

correlation_service = CorrelationService()
