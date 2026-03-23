from pydantic_settings import BaseSettings
from typing import List


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

    # CORS allowed origins (space-separated list in .env)
    CORS_ORIGINS: List[str] = ["http://localhost:3000"]

    class Config:
        case_sensitive = True
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
