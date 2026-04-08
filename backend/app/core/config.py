from pydantic_settings import BaseSettings
from pydantic import field_validator
from typing import List, Any
import json


class Settings(BaseSettings):
    PROJECT_NAME: str = "Aegis – Intelligent SIEM & Intrusion Detection System"
    API_V1_STR: str = "/api/v1"

    REDIS_URL: str = "redis://localhost:6379/0"
    ELASTICSEARCH_URL: str = "http://localhost:9200"

    # Real World APIs
    IPINFO_TOKEN: str = ""
    ABUSEIPDB_API_KEY: str = ""

    # JWT
    SECRET_KEY: str = "change-me-in-production-use-openssl-rand-hex-32"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # Admin credentials (override via .env)
    ADMIN_USERNAME: str = "admin"
    ADMIN_PASSWORD_HASH: str = (
        # bcrypt of "aegis-admin" — override in .env with a real hash
        "$2b$12$KIX/Py6QEsKuvKKpLEtVJuBjXNFE9J.Q0WZRYUDf3JIApFHBvP3Ci"
    )

    # CORS allowed origins — accepts:
    #   - JSON array:          '["https://a.com","https://b.com"]'
    #   - Comma-separated:     'https://a.com,https://b.com'
    #   - Single origin:       'https://a.com'
    CORS_ORIGINS: List[str] = ["http://localhost:3000"]

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: Any) -> List[str]:
        if isinstance(v, list):
            return v
        if isinstance(v, str):
            v = v.strip()
            # Try JSON array first: ["https://..."]
            if v.startswith("["):
                try:
                    return json.loads(v)
                except json.JSONDecodeError:
                    pass
            # Fall back to comma-separated
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v

    class Config:
        case_sensitive = True
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
