from functools import lru_cache
from pydantic import AnyHttpUrl, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_env: str = "development"
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    frontend_url: AnyHttpUrl = "http://localhost:3000"
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/email_agent"
    chroma_host: str = "localhost"
    chroma_port: int = 8000
    jwt_secret: str = Field(min_length=16)
    token_encryption_key: str = Field(min_length=16)
    groq_api_key: str = ""
    groq_base_url: str = "https://api.groq.com/openai/v1"
    google_client_id: str = ""
    google_client_secret: str = ""
    google_redirect_uri: str = "http://localhost:8000/api/auth/google/callback"
    session_cookie_name: str = "email_agent_session"
    log_level: str = "INFO"

    @property
    def google_scopes(self) -> list[str]:
        return [
            "openid",
            "https://www.googleapis.com/auth/userinfo.email",
            "https://www.googleapis.com/auth/gmail.readonly",
            "https://www.googleapis.com/auth/gmail.send",
            "https://www.googleapis.com/auth/gmail.modify",
            "https://www.googleapis.com/auth/calendar.events",
        ]


@lru_cache
def get_settings() -> Settings:
    return Settings()
