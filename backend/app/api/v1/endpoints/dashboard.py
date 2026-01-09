from fastapi import APIRouter
from app.services.storage import storage_service

router = APIRouter()

@router.get("/stats")
def get_stats():
    """
    Get aggregate stats for dashboard.
    """
    # 1. Total Logs
    total_logs = storage_service.es.count(index="logs").get('count', 0)
    
    # 2. High Severity Alerts
    high_alerts = storage_service.es.count(index="logs", body={
        "query": {"match": {"severity": "HIGH"}}
    }).get('count', 0)
    
    # 3. Critical Incidents
    incidents = storage_service.es.count(index="logs", body={
        "query": {"match": {"severity": "CRITICAL"}}
    }).get('count', 0)
    
    return {
        "total_logs": total_logs,
        "high_alerts": high_alerts,
        "critical_incidents": incidents
    }

@router.get("/activity")
def get_activity():
    """
    Get logs per hour for the timeline chart.
    Uses ES Date Histogram Aggregation.
    """
    query = {
        "size": 0,
        "aggs": {
            "logs_over_time": {
                "date_histogram": {
                    "field": "timestamp",
                    "calendar_interval": "hour"
                }
            }
        }
    }
    res = storage_service.es.search(index="logs", body=query)
    buckets = res.get('aggregations', {}).get('logs_over_time', {}).get('buckets', [])
    
    # Format for Recharts: [{name: '10:00', logs: 50}, ...]
    data = []
    for b in buckets:
        data.append({
            "name": b['key_as_string'], 
            "logs": b['doc_count']
        })
    return data

@router.get("/map")
def get_map_data():
    """
    Get GeoIP locations for the map.
    Only returns logs with geo data.
    """
    query = {
        "size": 100,
        "query": {
            "exists": {"field": "geo"}
        },
        "_source": ["ip", "geo", "severity"]
    }
    res = storage_service.es.search(index="logs", body=query)
    hits = res.get('hits', {}).get('hits', [])
    
    data = []
    for h in hits:
        src = h['_source']
        if 'geo' in src and src['geo'].get('lat') != 0:
            data.append({
                "ip": src.get('ip'),
                "lat": src['geo']['lat'],
                "lon": src['geo']['lon'],
                "severity": src.get('severity', 'INFO')
            })
    return data

@router.get("/recent")
def get_recent_alerts():
    """
    Get recent critical/high alerts for the feed.
    """
    query = {
        "size": 10,
        "sort": [{"timestamp": "desc"}],
        "query": {
            "terms": {"severity": ["HIGH", "CRITICAL"]}
        }
    }
    res = storage_service.es.search(index="logs", body=query)
    hits = res.get('hits', {}).get('hits', [])
    return [h['_source'] for h in hits]
