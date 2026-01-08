from fastapi import FastAPI
from app.core.config import settings
from app.api.v1.endpoints import ingest

app = FastAPI(title=settings.PROJECT_NAME)

@app.get("/")
def read_root():
    return {"message": "Welcome to the SIEM API"}

app.include_router(ingest.router, prefix=f"{settings.API_V1_STR}/ingest", tags=["ingest"])
