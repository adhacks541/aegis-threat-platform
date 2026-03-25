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

    def is_healthy(self) -> bool:
        try:
            return self.es.ping()
        except Exception:
            return False

    def index_log(self, log_data: dict):
        """
        Index a log entry and its associated alerts/incidents into separate indices.
        Uses ES 8.x keyword-only API (no body= kwarg).
        """
        try:
            # 1. Store the Full Log (Normalized)
            self.es.index(index=self.log_alias, document=log_data)

            # 2. Store Alerts (if any)
            if log_data.get("alerts"):
                for alert_msg in log_data["alerts"]:
                    alert_doc = {
                        "timestamp": log_data.get("timestamp"),
                        "source_ip": log_data.get("ip"),
                        "rule_name": alert_msg,
                        "severity": log_data.get("severity", "MEDIUM"),
                        "full_log_id": log_data.get("id", "unknown"),
                        "metadata": log_data.get("metadata"),
                    }
                    self.es.index(index=self.alert_alias, document=alert_doc)

            # 3. Store Incidents (if any)
            if log_data.get("incidents"):
                for incident in log_data["incidents"]:
                    incident_doc = {
                        "timestamp": log_data.get("timestamp"),
                        "incident": incident,
                        "severity": "CRITICAL",
                        "log_reference": log_data,
                    }
                    self.es.index(index=self.incident_alias, document=incident_doc)

            return "indexed"
        except Exception as e:
            logger.error(f"Error indexing log: {e}")
            return None

    # ---- Dashboard helpers (ES 8.x API: keyword args, no body=) ----

    def count(self, index: str, query: dict | None = None) -> int:
        try:
            if query:
                res = self.es.count(index=index, query=query)
            else:
                res = self.es.count(index=index)
            return res["count"]
        except Exception as e:
            logger.error(f"ES count error on {index}: {e}")
            return 0

    def search(self, index: str, size: int = 20, sort: list | None = None,
               query: dict | None = None) -> list:
        try:
            kwargs: dict = {"index": index, "size": size}
            if sort:
                kwargs["sort"] = sort
            if query:
                kwargs["query"] = query
            res = self.es.search(**kwargs)
            return [h["_source"] for h in res["hits"]["hits"]]
        except Exception as e:
            logger.error(f"ES search error on {index}: {e}")
            return []


storage_service = StorageService()
