from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.v1.endpoints import ingest, dashboard, auth, feed

app = FastAPI(
    title=settings.PROJECT_NAME,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS — origins driven by settings / .env
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def read_root():
    return {
        "message": "Aegis SIEM API is running",
        "docs": "/docs",
        "version": "2.0.0",
    }


@app.get("/health")
def health_check():
    from app.services.storage import storage_service
    import redis as _redis

    es_ok = storage_service.is_healthy()

    try:
        r = _redis.Redis.from_url(settings.REDIS_URL)
        r.ping()
        redis_ok = True
    except Exception:
        redis_ok = False

    return {
        "status": "healthy" if es_ok and redis_ok else "degraded",
        "services": {
            "api": "online",
            "elasticsearch": "online" if es_ok else "offline",
            "redis": "online" if redis_ok else "offline",
        },
    }


# Auth (public — issues JWT tokens)
app.include_router(auth.router, prefix=f"{settings.API_V1_STR}/auth", tags=["auth"])

# Protected dashboard routes
app.include_router(
    dashboard.router,
    prefix=f"{settings.API_V1_STR}/dashboard",
    tags=["dashboard"],
)

# Ingest (rate-limited + IP-block guarded)
app.include_router(
    ingest.router,
    prefix=f"{settings.API_V1_STR}/ingest",
    tags=["ingest"],
)

# WebSocket live-feed
app.include_router(feed.router, prefix=f"{settings.API_V1_STR}", tags=["feed"])
