from fastapi import APIRouter, Depends
from app.services.storage import storage_service
from app.core.security import get_current_user
import logging

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/stats")
async def get_stats(current_user: dict = Depends(get_current_user)):
    """
    Get high-level stats from Elasticsearch indices.
    """
    logs_count = storage_service.count("logs-write")
    alerts_count = storage_service.count("alerts-write")
    incidents_count = storage_service.count("incidents-write")

    # Recent critical alerts (last 24 h) — ES 8.x keyword-only
    recent_crit = storage_service.count(
        "alerts-write",
        query={
            "bool": {
                "must": [{"match": {"severity": "CRITICAL"}}],
                "filter": [{"range": {"timestamp": {"gte": "now-24h"}}}],
            }
        },
    )

    return {
        "total_logs": logs_count,
        "total_alerts": alerts_count,
        "total_incidents": incidents_count,
        "critical_last_24h": recent_crit,
        "eps": 5234,           # simulated
        "avg_response_ms": 42, # simulated
    }


@router.get("/incidents")
async def get_incidents(limit: int = 10, current_user: dict = Depends(get_current_user)):
    """Get recent incidents."""
    return storage_service.search(
        "incidents-write",
        size=limit,
        sort=[{"timestamp": {"order": "desc"}}],
    )


@router.get("/alerts")
async def get_alerts(limit: int = 20, current_user: dict = Depends(get_current_user)):
    """Get recent alerts."""
    return storage_service.search(
        "alerts-write",
        size=limit,
        sort=[{"timestamp": {"order": "desc"}}],
    )


@router.get("/logs")
async def get_logs(
    limit: int = 50,
    query: str | None = None,
    current_user: dict = Depends(get_current_user),
):
    """Get raw logs, optional query string filter."""
    q = {"query_string": {"query": query}} if query else None
    return storage_service.search(
        "logs-write",
        size=limit,
        sort=[{"timestamp": {"order": "desc"}}],
        query=q,
    )
