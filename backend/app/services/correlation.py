import redis
from app.core.config import settings
from typing import Dict, Any, List

class CorrelationService:
    def __init__(self):
        self.redis = redis.Redis.from_url(settings.REDIS_URL, decode_responses=True)
        self.PHASE_1_TTL = 300 # 5 minutes to succeed after brute force
        self.PHASE_2_TTL = 300 # 5 minutes to escalate privileges after login


    def process_event(self, log_entry: dict):
        """
        Correlate events to detect multi-stage attacks.
        
        Mitre ATT&CK mapping:
        - T1110: Brute Force (Phase 1)
        - T1078: Valid Accounts (Phase 2 - successful login after brute force)
        - T1098: Account Manipulation / T1078: Valid Accounts (Phase 3 - sudo/privilege escalation)
        """
        ip = log_entry.get("ip") or log_entry.get("metadata", {}).get("ip")
        if not ip:
            return

        # 1. State: Brute Force Attempt (Phase 1)
        # This is set by the RuleBasedDetector (T1110)
        # We check if this IP is already flagged as a risk.
        if log_entry.get('alerts'):
            for alert in log_entry['alerts']:
                if "SSH Brute Force" in alert:
                    # Set short-term state: "Risk Level 1"
                    self.redis.setex(f"risk:phase:1:{ip}", 300, "active") # TTL 5 mins

        # 2. State: Successful Login after Brute Force (Phase 2)
        # Technique: T1078 - Valid Accounts
        if log_entry.get('event_type') == 'ssh_login_success':
            if self.redis.exists(f"risk:phase:1:{ip}"):
                # Escalating risk to Phase 2
                self.redis.setex(f"risk:phase:2:{ip}", 300, "active")
                
                # Create Incident
                incident_msg = f"Suspicious Login after Brute Force from {ip}"
                log_entry['incidents'] = log_entry.get('incidents', [])
                log_entry['incidents'].append(incident_msg)
                log_entry['severity'] = 'CRITICAL'
                log_entry['alerts'].append(incident_msg)

        # 3. State: Privilege Escalation (Phase 3)
        # Technique: T1548.003 - Sudo Caching / Sudo Usage
        msg = log_entry.get("message", "").lower()
        if "sudo" in msg and "command not found" not in msg:
            if self.redis.exists(f"risk:phase:2:{ip}"):
                 # Highest Risk: Attacker Brute Forced -> Logged In -> Is now Root
                incident_msg = f"CRITICAL: Privilege Escalation after Brute Force from {ip}"
                log_entry['incidents'] = log_entry.get('incidents', [])
                log_entry['incidents'].append(incident_msg)
                log_entry['severity'] = 'CRITICAL'
                log_entry['alerts'].append(incident_msg)

correlation_service = CorrelationService()
