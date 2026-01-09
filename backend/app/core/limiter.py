import redis
from fastapi import Request, HTTPException
from app.core.config import settings

class RateLimiter:
    def __init__(self, requests_per_minute: int = 1000):
        self.limit = requests_per_minute
        self.redis = redis.Redis.from_url(settings.REDIS_URL, decode_responses=True)

    async def __call__(self, request: Request):
        client_ip = request.client.host
        key = f"rate_limit:{client_ip}"
        
        # Increment counter (Lua script for atomicity would be better in ultra-high load, but this is fine for now)
        current = self.redis.incr(key)
        
        if current == 1:
            self.redis.expire(key, 60) # Reset every minute
            
        if current > self.limit:
            raise HTTPException(
                status_code=429, 
                detail="Too Many Requests. Rate limit exceeded."
            )

# Dependency used in routes
limiter = RateLimiter(requests_per_minute=1000)
