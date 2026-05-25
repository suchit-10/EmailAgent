from uuid import UUID
from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from backend.core.config import get_settings
from backend.core.security import decode_session_token
from backend.db.session import get_db


async def current_user_id(request: Request) -> UUID:
    settings = get_settings()
    token = request.cookies.get(settings.session_cookie_name)
    if not token:
        auth = request.headers.get("authorization", "")
        token = auth.removeprefix("Bearer ").strip() if auth.lower().startswith("bearer ") else ""
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")
    try:
        return UUID(decode_session_token(token, settings.jwt_secret))
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid session") from exc


async def db_session(db: AsyncSession = Depends(get_db)) -> AsyncSession:
    return db
