from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import init_db
from app.seed import seed_database

app = FastAPI(title="LogicForge API", version="1.0.0")

origins = [
    origin.strip()
    for origin in settings.frontend_origins.split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def startup_event() -> None:
    init_db()
    seed_database()

@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "LogicForge"}

from app.routes import router

app.include_router(router, prefix="/api/v1")
