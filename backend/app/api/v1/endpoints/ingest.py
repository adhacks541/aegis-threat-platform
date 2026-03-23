from fastapi import APIRouter, HTTPException, Depends, Header, Request, Body
from typing import List, Optional, Union
from datetime import datetime
from app.models.log import LogEntry
from app.services.queue import queue_service
from app.core.limiter import limiter
from app.core.config import settings
from app.core.security import get_current_user
import redis

r = redis.Redis.from_url(settings.REDIS_URL, decode_responses=True)

router = APIRouter()


def check_blocked(request: Request):
    ip = request.client.host
    if r.exists(f"blocked:{ip}"):
        raise HTTPException(
            status_code=403,
            detail="Access Denied: Your IP is blocked due to suspicious activity.",
        )


@router.post(
    "/logs",
    status_code=202,
    dependencies=[Depends(limiter), Depends(check_blocked)],
)
async def ingest_logs(
    logs: Union[LogEntry, List[LogEntry]],
    x_source_host: Optional[str] = Header(None),
    x_app_name: Optional[str] = Header(None),
    request: Request = None,
    current_user: dict = Depends(get_current_user),
):
    """Ingest structured logs (single or batch). Async push to Redis."""
    if not isinstance(logs, list):
        logs = [logs]

    timestamp = datetime.utcnow().isoformat()
    queued_count = 0

    for log in logs:
        log_data = log.dict()

        if not log_data.get("timestamp"):
            log_data["timestamp"] = timestamp
        else:
            log_data["timestamp"] = log_data["timestamp"].isoformat()

        if x_source_host or x_app_name:
            log_data.setdefault("metadata", {})
            if x_source_host:
                log_data["metadata"]["source_host"] = x_source_host
            if x_app_name:
                log_data["metadata"]["app_name"] = x_app_name

        if queue_service.push_log(log_data):
            queued_count += 1

    return {"status": "queued", "count": queued_count}


@router.post(
    "/raw",
    status_code=202,
    dependencies=[Depends(limiter), Depends(check_blocked)],
)
async def ingest_raw(
    request: Request,
    body: str = Body(..., media_type="text/plain"),
    x_source_host: Optional[str] = Header(None),
    x_app_name: Optional[str] = Header(None),
    current_user: dict = Depends(get_current_user),
):
    """Ingest raw text logs (e.g. from syslog/rsyslog agents)."""
    log_data = {
        "timestamp": datetime.utcnow().isoformat(),
        "level": "INFO",
        "source": "raw_ingest",
        "message": body,
        "metadata": {
            "source_ip": request.client.host,
            "raw_format": "text",
        },
    }

    if x_source_host:
        log_data["metadata"]["source_host"] = x_source_host
    if x_app_name:
        log_data["metadata"]["app_name"] = x_app_name

    if queue_service.push_log(log_data):
        return {"status": "queued", "message": "Raw log accepted"}

    raise HTTPException(status_code=500, detail="Failed to queue raw log")
