from fastapi import APIRouter, HTTPException
from app.services.storage import storage_service
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/stats")
async def get_stats():
    """
    Get high-level stats from Elasticsearch indices (logs-*, alerts-*, incidents-*).
    """
    try:
        es = storage_service.es
        
        # Count documents in aliases (or wildcard patterns)
        logs_count = es.count(index="logs-write")['count']
        alerts_count = es.count(index="alerts-write")['count']
        incidents_count = es.count(index="incidents-write")['count']
        
        # Get recent critical alerts count
        recent_crit = es.count(index="alerts-write", body={
            "query": {
                "bool": {
                    "must": [{"match": {"severity": "CRITICAL"}}],
                    "filter": [{"range": {"timestamp": {"gte": "now-24h"}}}]
                }
            }
        })['count']

        return {
            "total_logs": logs_count,
            "total_alerts": alerts_count,
            "total_incidents": incidents_count,
            "critical_last_24h": recent_crit
        }
    except Exception as e:
        logger.error(f"Stats Error: {e}")
        return {"total_logs": 0, "total_alerts": 0, "total_incidents": 0, "critical_last_24h": 0}

@router.get("/incidents")
async def get_incidents(limit: int = 10):
    """
    Get recent incidents from incidents-*
    """
    try:
        res = storage_service.es.search(index="incidents-write", size=limit, sort=[{"timestamp": "desc"}])
        return [h['_source'] for h in res['hits']['hits']]
    except Exception as e:
        logger.error(f"Incidents Error: {e}")
        return []

@router.get("/alerts")
async def get_alerts(limit: int = 20):
    """
    Get recent alerts from alerts-*
    """
    try:
        res = storage_service.es.search(index="alerts-write", size=limit, sort=[{"timestamp": "desc"}])
        return [h['_source'] for h in res['hits']['hits']]
    except Exception as e:
        logger.error(f"Alerts Error: {e}")
        return []

@router.get("/logs")
async def get_logs(limit: int = 50, query: str = None):
    """
    Get raw logs from logs-*, optional simple query string.
    """
    try:
        body = {"sort": [{"timestamp": "desc"}]}
        if query:
            body["query"] = {"query_string": {"query": query}}
            
        res = storage_service.es.search(index="logs-write", body=body, size=limit)
        return [h['_source'] for h in res['hits']['hits']]
    except Exception as e:
        logger.error(f"Logs Error: {e}")
        return []
