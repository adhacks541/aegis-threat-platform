from user_agents import parse
import random

class EnrichmentService:
    def __init__(self):
        pass

    def _get_geoip(self, ip: str) -> dict:
        """
        Mock GeoIP service.
        In a real app, this would use a MaxMind DB or API.
        """
        # Deterministic mock based on IP octets for verification stability
        if ip in ["127.0.0.1", "::1"]:
            return {"country": "Localhost", "city": "Localhost", "lat": 0.0, "lon": 0.0}
        
        parts = ip.split('.')
        if len(parts) == 4:
            if parts[0] == "192":
                return {"country": "Private", "city": "LAN", "lat": 0.0, "lon": 0.0}
            if parts[0] == "10":
                return {"country": "US", "city": "New York", "lat": 40.7128, "lon": -74.0060}
            if parts[0] == "45":
                return {"country": "RU", "city": "Moscow", "lat": 55.7558, "lon": 37.6173}
            if parts[0] == "203":
                return {"country": "CN", "city": "Beijing", "lat": 39.9042, "lon": 116.4074}
        
        return {"country": "Unknown", "city": "Unknown", "lat": 0.0, "lon": 0.0}

    def _parse_user_agent(self, ua_string: str) -> dict:
        if not ua_string or ua_string == "-":
            return {}
        
        user_agent = parse(ua_string)
        return {
            "browser": user_agent.browser.family,
            "os": user_agent.os.family,
            "device": user_agent.device.family,
            "is_mobile": user_agent.is_mobile,
            "is_bot": user_agent.is_bot
        }

    def enrich_log(self, log_entry: dict) -> dict:
        """
        Enrich a log entry with additional data.
        Modifies the dict in place or returns a new one.
        """
        # 1. Normalize first (extract IP, UA) if not already done?
        # Assuming log_entry now contains 'parsed' fields from Normalization Service
        # If not, we check metadata or root fields.
        
        # Let's say normalization puts extracted fields into 'metadata' or top level?
        # We'll expect 'ip' and 'user_agent' to be present if normalization succeeded.
        
        # Try to find IP
        ip = log_entry.get("ip") or log_entry.get("metadata", {}).get("ip")
        if ip:
            geo = self._get_geoip(ip)
            log_entry["geo"] = geo
        
        # Try to find UA
        ua = log_entry.get("user_agent") or log_entry.get("metadata", {}).get("user_agent")
        if ua:
            ua_data = self._parse_user_agent(ua)
            log_entry["ua_details"] = ua_data

        return log_entry

enrichment_service = EnrichmentService()
