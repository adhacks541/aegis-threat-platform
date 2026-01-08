import redis
import json
from app.core.config import settings

# Create a Redis connection pool
pool = redis.ConnectionPool.from_url(settings.REDIS_URL, decode_responses=True)

class QueueService:
    def __init__(self):
        self.redis = redis.Redis(connection_pool=pool)
        self.stream_name = "logs_stream"

    def push_log(self, log_data: dict):
        """
        Push a log entry to the Redis Stream.
        """
        # Redis Streams store keys/values as strings. We serialize the whole JSON-compatible dict to a string.
        # Alternatively, we could store fields individually.
        try:
            # We add it to the stream. '*' means auto-generate ID.
            self.redis.xadd(self.stream_name, {"data": json.dumps(log_data)})
            return True
        except Exception as e:
            print(f"Error pushing to Redis: {e}")
            return False

queue_service = QueueService()
