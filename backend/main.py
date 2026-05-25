from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter
from slowapi.util import get_remote_address
from backend.api import agent, auth, dashboard, emails
from backend.core.config import get_settings
from backend.core.logging import configure_logging
from backend.db.base import Base
from backend.db.session import engine
from backend.db import models  # noqa: F401


settings = get_settings()
configure_logging(settings.log_level)
limiter = Limiter(key_func=get_remote_address)
frontend_origin = str(settings.frontend_url).rstrip("/")

app = FastAPI(title="AI Email Agent Platform", version="0.1.0")
app.state.limiter = limiter

app.add_middleware(
    CORSMiddleware,
    allow_origins=[frontend_origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api")
app.include_router(agent.router, prefix="/api")
app.include_router(emails.router, prefix="/api")
app.include_router(dashboard.router, prefix="/api")


@app.get("/health")
async def health() -> dict:
    return {"status": "ok", "service": "ai-email-agent"}


@app.on_event("startup")
async def create_database_schema() -> None:
    if settings.app_env == "development":
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
