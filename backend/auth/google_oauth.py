from datetime import datetime, timezone
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from backend.core.config import get_settings
from backend.core.security import TokenCipher
from backend.db.models import GoogleToken, User


def build_oauth_flow(state: str | None = None) -> Flow:
    settings = get_settings()
    flow = Flow.from_client_config(
        {
            "web": {
                "client_id": settings.google_client_id,
                "client_secret": settings.google_client_secret,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [settings.google_redirect_uri],
            }
        },
        scopes=settings.google_scopes,
        state=state,
    )
    flow.redirect_uri = settings.google_redirect_uri
    return flow


async def get_google_credentials(db: AsyncSession, user_id: str) -> Credentials:
    settings = get_settings()
    cipher = TokenCipher(settings.token_encryption_key)
    token = await db.scalar(select(GoogleToken).where(GoogleToken.user_id == user_id))
    if token is None:
        raise PermissionError("Google account is not connected")
    creds = Credentials(
        token=cipher.decrypt(token.encrypted_access_token),
        refresh_token=cipher.decrypt(token.encrypted_refresh_token) if token.encrypted_refresh_token else None,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=settings.google_client_id,
        client_secret=settings.google_client_secret,
        scopes=token.scopes,
    )
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
        token.encrypted_access_token = cipher.encrypt(creds.token)
        token.expires_at = creds.expiry
        await db.commit()
    return creds


async def upsert_google_token(db: AsyncSession, *, email: str, credentials: Credentials) -> User:
    settings = get_settings()
    cipher = TokenCipher(settings.token_encryption_key)
    user = await db.scalar(select(User).where(User.email == email))
    if user is None:
        user = User(email=email)
        db.add(user)
        await db.flush()
    token = await db.scalar(select(GoogleToken).where(GoogleToken.user_id == user.id))
    if token is None:
        token = GoogleToken(user_id=user.id)
        db.add(token)
    token.encrypted_access_token = cipher.encrypt(credentials.token)
    token.encrypted_refresh_token = cipher.encrypt(credentials.refresh_token) if credentials.refresh_token else token.encrypted_refresh_token
    token.expires_at = credentials.expiry or datetime.now(timezone.utc)
    token.scopes = list(credentials.scopes or [])
    await db.commit()
    await db.refresh(user)
    return user
