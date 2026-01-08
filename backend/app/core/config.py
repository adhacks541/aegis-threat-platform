from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "Aegis – Intelligent SIEM & Intrusion Detection System"
    API_V1_STR: str = "/api/v1"
    
    REDIS_URL: str = "redis://localhost:6379/0"
    ELASTICSEARCH_URL: str = "http://localhost:9200"

    class Config:
        case_sensitive = True

settings = Settings()
