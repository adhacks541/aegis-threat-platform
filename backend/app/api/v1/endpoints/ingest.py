from fastapi import APIRouter, HTTPException, Depends
from app.models.log import LogEntry
from app.services.queue import queue_service

router = APIRouter()

@router.post("/logs", status_code=202)
def ingest_log(log: LogEntry):
    """
    Ingest a new log entry and push it to the processing queue.
    """
    # Convert Pydantic model to dict, ensuring datetime is serializable if needed (Pydantic .dict() or .model_dump() handles this usually, but json.dumps might need help with datetime if not converting to str)
    # json_encoders in Config can help, or we can just let push_log handle serialization.
    # For safety with json.dumps inside the service, let's use jsonable_encoder or just default=str in service.
    # Actually, Pydantic's .json() is deprecated in v2, but we are using v2 maybe? requirements said pydantic-settings which implies v2.
    # Let's use model_dump with mode='json' if v2, or just dict and handle datetime.
    
    log_data = log.dict()
    # Serialize datetime objects to string
    log_data['timestamp'] = log_data['timestamp'].isoformat()
    
    success = queue_service.push_log(log_data)
    
    if not success:
        raise HTTPException(status_code=500, detail="Failed to queue log entry")
        
    return {"status": "queued", "message": "Log accepted"}
