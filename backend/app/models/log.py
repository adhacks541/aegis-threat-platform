from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime

class LogEntry(BaseModel):
    source: str = Field(..., description="Source of the log API, e.g., 'nginx', 'firewall', 'app'")
    level: str = Field("INFO", description="Log level")
    message: str = Field(..., description="Raw log message")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: Optional[Dict[str, Any]] = Field(default={}, description="Additional metadata")

    class Config:
        json_schema_extra = {
            "example": {
                "source": "nginx",
                "level": "ERROR",
                "message": "Connection refused from 192.168.1.5",
                "timestamp": "2023-10-27T10:00:00Z",
                "metadata": {"host": "web-01"}
            }
        }
