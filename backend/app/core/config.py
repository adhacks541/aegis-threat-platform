from pydantic_settings import BaseSettings
from typing import List
import json


class Settings(BaseSettings):
    PROJECT_NAME: str = "Aegis – Intelligent SIEM & Intrusion Detection System"
    API_V1_STR: str = "/api/v1"

    REDIS_URL: str = "redis://localhost:6379/0"
    ELASTICSEARCH_URL: str = "http://localhost:9200"
    ELASTICSEARCH_USERNAME: str = "elastic"
    ELASTICSEARCH_PASSWORD: str = ""  # set in .env / Render env vars

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
        # bcrypt of "admin" — override in .env with a real hash
        "$2b$12$GpTgMrps0Nrrx10tE89SvOAzkSk9NDUTORkF3ditb0kv7ft3Q56NC"
    )

    # Store as plain str so pydantic-settings v2 doesn't try to JSON-parse it
    # (List[str] fields get JSON-parsed before validators run → SettingsError)
    # Accepts:  https://a.com,https://b.com  OR  ["https://a.com"]  OR  https://a.com
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:3001"

    @property
    def cors_origins_list(self) -> List[str]:
        v = self.CORS_ORIGINS.strip()
        if v.startswith("["):
            try:
                origins = json.loads(v)
            except json.JSONDecodeError:
                origins = [o.strip() for o in v.split(",") if o.strip()]
        else:
            origins = [o.strip() for o in v.split(",") if o.strip()]
        # Always allow all Vercel preview/prod URLs (safe for this project)
        origins.append("https://*.vercel.app")
        return origins

    class Config:
        case_sensitive = True
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
