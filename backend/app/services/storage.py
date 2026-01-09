from elasticsearch import Elasticsearch
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

class StorageService:
    def __init__(self):
        self.es = Elasticsearch(settings.ELASTICSEARCH_URL)
        # ILM Aliases
        self.log_alias = "logs-write"
        self.alert_alias = "alerts-write"
        self.incident_alias = "incidents-write"

    def index_log(self, log_data: dict):
        """
        Index a log entry and its associated alerts/incidents into separate indices.
        """
        try:
            # 1. Store the Full Log (Normalized)
            # We don't need to manually create indices anymore (ILM templates handle it on write)
            self.es.index(index=self.log_alias, document=log_data)
            
            # 2. Store Alerts (if any)
            # We extract them to a lighter "alerts" index for fast dashboarding (30d retention)
            if log_data.get('alerts'):
                for alert_msg in log_data['alerts']:
                    alert_doc = {
                        "timestamp": log_data.get("timestamp"),
                        "source_ip": log_data.get("ip"),
                        "rule_name": alert_msg,
                        "severity": log_data.get("severity", "MEDIUM"),
                        "full_log_id": log_data.get("id", "unknown"), # Ideally link back
                        "metadata": log_data.get("metadata")
                    }
                    self.es.index(index=self.alert_alias, document=alert_doc)
            
            # 3. Store Incidents (if any)
            # High value, long retention (90d)
            if log_data.get('incidents'):
                for incident in log_data['incidents']:
                    incident_doc = {
                        "timestamp": log_data.get("timestamp"),
                        "incident": incident,
                        "severity": "CRITICAL",
                        "log_reference": log_data
                    }
                    self.es.index(index=self.incident_alias, document=incident_doc)

            return "indexed"
        except Exception as e:
            logger.error(f"Error indexing log: {e}")
            return None

storage_service = StorageService()
