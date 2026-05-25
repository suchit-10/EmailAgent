import httpx
from fastapi import APIRouter, Depends, Response
from fastapi.responses import RedirectResponse
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from backend.api.deps import current_user_id
from backend.auth.google_oauth import build_oauth_flow, upsert_google_token
from backend.core.config import get_settings
from backend.core.security import create_session_token
from backend.db.models import EmailMessage, GoogleToken, User
from backend.db.session import get_db


router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/google/login")
async def google_login() -> RedirectResponse:
    flow = build_oauth_flow()
    auth_url, _ = flow.authorization_url(access_type="offline", include_granted_scopes="true", prompt="consent")
    return RedirectResponse(auth_url)


@router.get("/google/callback")
async def google_callback(code: str, db: AsyncSession = Depends(get_db)) -> RedirectResponse:
    settings = get_settings()
    flow = build_oauth_flow()
    flow.fetch_token(code=code)
    credentials = flow.credentials
    async with httpx.AsyncClient() as client:
        info = await client.get("https://openidconnect.googleapis.com/v1/userinfo", headers={"Authorization": f"Bearer {credentials.token}"})
        info.raise_for_status()
    user = await upsert_google_token(db, email=info.json()["email"], credentials=credentials)
    response = RedirectResponse(f"{settings.frontend_url}/")
    token = create_session_token(str(user.id), settings.jwt_secret)
    response.set_cookie(
        settings.session_cookie_name,
        token,
        httponly=True,
        secure=settings.app_env == "production",
        samesite="lax",
        max_age=60 * 60 * 24 * 7,
    )
    return response


@router.post("/logout")
async def logout(response: Response) -> dict:
    response.delete_cookie(get_settings().session_cookie_name)
    return {"ok": True}


@router.get("/me")
async def me(user_id=Depends(current_user_id), db: AsyncSession = Depends(get_db)) -> dict:
    user = await db.get(User, user_id)
    token = await db.scalar(select(GoogleToken).where(GoogleToken.user_id == user_id))
    synced = await db.scalar(select(func.count()).select_from(EmailMessage).where(EmailMessage.user_id == user_id))
    return {
        "authenticated": user is not None,
        "email": user.email if user else None,
        "google_connected": token is not None,
        "synced_emails": synced or 0,
        "scopes": token.scopes if token else [],
    }
