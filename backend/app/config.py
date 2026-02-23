"""
CortexLab Backend Configuration

Load environment variables and provide typed configuration settings.
"""

from functools import lru_cache
from pydantic import Field
from pydantic.fields import AliasChoices
from pydantic_settings import BaseSettings, SettingsConfigDict
import secrets


_DEFAULT_SECRET = secrets.token_hex(32)


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,   # allow using field name OR alias
        case_sensitive=False,    # accept GROK_API or grok_api
    )

    # Database
    database_url: str = Field(
        default="sqlite+aiosqlite:///./cortexlab.db",
        description="Database connection URL",
    )

    # Google OAuth
    google_client_id: str = Field(default="", description="Google OAuth Client ID")
    google_client_secret: str = Field(default="", description="Google OAuth Client Secret")

    # Gemini AI
    google_api_key: str = Field(default="", description="Google API Key for Gemini")

    # Groq AI — accept GROK_API (user's name) OR GROQ_API_KEY (standard name)
    groq_api_key: str = Field(
        default="",
        description="Groq API Key",
        validation_alias=AliasChoices("GROK_API", "GROQ_API", "GROQ_API_KEY", "groq_api_key"),
    )

    # Session
    session_secret_key: str = Field(
        default=_DEFAULT_SECRET,
        description="Secret key for signing session tokens",
    )

    # External APIs
    serpapi_key: str = Field(
        default="",
        description="SerpAPI key for Google Scholar searches",
        validation_alias=AliasChoices("SERPAPI_KEY", "serpapi_key"),
    )

    # File Storage
    upload_dir: str = Field(default="./uploads", description="Directory for uploaded files")

    # CORS
    frontend_url: str = Field(
        default="http://localhost:5173",
        description="Frontend URL for CORS",
    )


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
