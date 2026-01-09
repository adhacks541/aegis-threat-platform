from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "Aegis – Intelligent SIEM & Intrusion Detection System"
    API_V1_STR: str = "/api/v1"
    
    REDIS_URL: str = "redis://localhost:6379/0"
    ELASTICSEARCH_URL: str = "http://localhost:9200"
    
    # Real World APIs
    IPINFO_TOKEN: str = "e2d479151455f7" 
    ABUSEIPDB_API_KEY: str = "cc863a3bdcf0d8612018904d07c8cf6a36879037a3b82cd5bd6567da20b2803d1bf81ef8ccac189f"

    class Config:
        case_sensitive = True

settings = Settings()
