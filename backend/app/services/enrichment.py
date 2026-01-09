from user_agents import parse
from app.core.config import settings
import requests
import logging
from functools import lru_cache

logger = logging.getLogger(__name__)

# Cache GeoIP results to save API quotas (LRU Cache size 1000)
@lru_cache(maxsize=1000)
def get_geo_data(ip: str, token: str):
    try:
        resp = requests.get(f"https://ipinfo.io/{ip}?token={token}", timeout=2)
        if resp.status_code == 200:
            return resp.json()
    except Exception as e:
        logger.error(f"GeoIP Lookup Failed for {ip}: {e}")
    return None

class EnrichmentService:
    def __init__(self):
        # Production: No local DB init required as we use External APIs
        pass

    def enrich_log(self, log_entry: dict):
        """
        Add 'geo', 'ua_details', and 'threat_intel' to log_entry.
        Production Mode: No Mocks. If API fails, fields are omitted.
        """
        ip = log_entry.get("ip") or log_entry.get("metadata", {}).get("ip")
        
        # 1. GeoIP Enrichment (Production: ipinfo.io)
        if ip and settings.IPINFO_TOKEN:
            data = get_geo_data(ip, settings.IPINFO_TOKEN)
            if data:
                loc = data.get('loc', '0,0').split(',')
                log_entry["geo"] = {
                    "country": data.get("country", "Unknown"),
                    "city": data.get("city", "Unknown"),
                    "lat": float(loc[0]) if len(loc) == 2 else 0.0,
                    "lon": float(loc[1]) if len(loc) == 2 else 0.0,
                    "isp": data.get("org", "Unknown")
                }

        # 2. Threat Intel (Production: AbuseIPDB)
        # Note: We don't cache locally here for simplicity, but in real Prod we would use Redis to cache IP scores for 24h.
        if ip and settings.ABUSEIPDB_API_KEY:
            try:
                headers = {
                    'Key': settings.ABUSEIPDB_API_KEY,
                    'Accept': 'application/json'
                }
                params = {'ipAddress': ip, 'maxAgeInDays': 90}
                resp = requests.get("https://api.abuseipdb.com/api/v2/check", headers=headers, params=params, timeout=2)
                if resp.status_code == 200:
                    data = resp.json().get('data', {})
                    score = data.get('abuseConfidenceScore', 0)
                    log_entry["threat_intel"] = {
                        "abuse_score": score,
                        "is_tor": data.get('isTor', False),
                        "usage_type": data.get('usageType', 'Unknown')
                    }
                    
                    # ALERT LOGIC: High Reputation Score = High Severity
                    if score > 80:
                        log_entry['alerts'] = log_entry.get('alerts', [])
                        log_entry['alerts'].append(f"High-Risk IP Detected (AbuseIPDB Score: {score})")
                        log_entry['severity'] = 'HIGH'
            except Exception as e:
                logger.error(f"Threat Intel failed for {ip}: {e}")

        # 3. User-Agent Enrichment (Local Lib, safe to run)
        ua_string = log_entry.get("user_agent")
        if ua_string:
            try:
                ua = parse(ua_string)
                log_entry["ua_details"] = {
                    "browser": ua.browser.family,
                    "os": ua.os.family,
                    "device": ua.device.family
                }
            except Exception:
                pass # Fail silently if UA parsing breaks

enrichment_service = EnrichmentService()
