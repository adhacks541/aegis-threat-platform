import re
from typing import Dict, Any

class NormalizationService:
    def __init__(self):
        # Nginx default log format: '$remote_addr - $remote_user [$time_local] "$request" $status $body_bytes_sent "$http_referer" "$http_user_agent"'
        # Example: 127.0.0.1 - - [08/Jan/2026:17:37:52 +0000] "GET /api/v1/logs HTTP/1.1" 202 31 "-" "python-requests/2.32.5"
        self.nginx_pattern = re.compile(
            r'(?P<ip>[\d\.]+) - (?P<remote_user>[\w-]+) \[(?P<timestamp>.*?)\] "(?P<verb>\w+) (?P<path>.*?) HTTP/[0-9\.]+" (?P<status>\d+) (?P<bytes>\d+) "(?P<referrer>.*?)" "(?P<user_agent>.*?)"'
        )

        # SSH Pattern (Basic examples)
        # Failed password for invalid user admin from 192.168.1.1 port 22 ssh2
        # Accepted password for user root from 192.168.1.1 port 22 ssh2
        self.ssh_failed_pattern = re.compile(
            r'Failed password for (?:invalid user )?(?P<user>[\w\-_]+) from (?P<ip>[\d\.]+) port \d+ ssh2'
        )
        self.ssh_accepted_pattern = re.compile(
            r'Accepted password for (?P<user>[\w\-_]+) from (?P<ip>[\d\.]+) port \d+ ssh2'
        )
        
        # UFW Firewall Pattern
        # [UFW BLOCK] IN=eth0 OUT= MAC=... SRC=1.2.3.4 DST=...
        self.ufw_pattern = re.compile(
            r'\[UFW BLOCK\] .*?SRC=(?P<ip>[\d\.]+) .*?DST=(?P<dst>[\d\.]+) .*?PROTO=(?P<proto>\w+)'
        )

    def parse_log(self, message: str, source_type: str) -> Dict[str, Any]:
        """
        Parse a raw log message based on the source type.
        Returns a dictionary of extracted fields.
        """
        extracted = {}

        if source_type == "nginx":
            match = self.nginx_pattern.match(message)
            if match:
                extracted = match.groupdict()
                # Remove extracted timestamp to avoid format conflicts with ES (use API timestamp instead)
                extracted.pop('timestamp', None)
                # Cast status/bytes to int
                extracted['status'] = int(extracted['status'])
                extracted['bytes'] = int(extracted['bytes'])
        
        elif source_type == "ssh":
            # Check Failed
            fail_match = self.ssh_failed_pattern.search(message)
            if fail_match:
                extracted = fail_match.groupdict()
                extracted['event_type'] = 'ssh_login_failed'
                extracted['action'] = 'block' # simplistic rule
            else:
                # Check Accepted
                success_match = self.ssh_accepted_pattern.search(message)
                if success_match:
                    extracted = success_match.groupdict()
                    extracted['event_type'] = 'ssh_login_success'
        
        elif "UFW BLOCK" in message:
            match = self.ufw_pattern.search(message)
            if match:
                extracted = match.groupdict()
                extracted['event_type'] = 'firewall_block'
                extracted['action'] = 'blocked'
                extracted['source'] = 'firewall'
        
        return extracted

normalization_service = NormalizationService()
