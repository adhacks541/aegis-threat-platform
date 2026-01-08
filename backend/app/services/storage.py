from elasticsearch import Elasticsearch
from app.core.config import settings

class StorageService:
    def __init__(self):
        self.es = Elasticsearch(settings.ELASTICSEARCH_URL)
        self.index_name = "logs"

    def create_index(self):
        """Create the index with mapping if it doesn't exist."""
        if not self.es.indices.exists(index=self.index_name):
            mapping = {
                "mappings": {
                    "properties": {
                        "source": {"type": "keyword"},
                        "level": {"type": "keyword"},
                        "message": {"type": "text"},
                        "timestamp": {"type": "date"},
                        "metadata": {"type": "object"}
                    }
                }
            }
            self.es.indices.create(index=self.index_name, body=mapping)

    def index_log(self, log_data: dict):
        """Index a single log entry."""
        try:
            # ensure index exists
            self.create_index() 
            res = self.es.index(index=self.index_name, document=log_data)
            return res['result']
        except Exception as e:
            print(f"Error indexing log: {e}")
            return None

storage_service = StorageService()
