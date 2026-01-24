"""
CortexLab Backend Configuration

Load environment variables and provide typed configuration settings.
"""

from functools import lru_cache
from pydantic_settings import BaseSettings
from pydantic import Field
import secrets


# Auto-generate a session secret for this run (fine for dev, single-server prod)
_DEFAULT_SECRET = secrets.token_hex(32)


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Database
    database_url: str = Field(
        default="sqlite+aiosqlite:///./cortexlab.db",
        description="Database connection URL"
    )
    
    # Google OAuth
    google_client_id: str = Field(
        default="",
        description="Google OAuth Client ID"
    )
    
    # Gemini AI
    google_api_key: str = Field(
        default="",
        description="Google API Key for Gemini"
    )
    
    # Session - auto-generated if not provided
    session_secret_key: str = Field(
        default=_DEFAULT_SECRET,
        description="Secret key for signing session tokens (auto-generated if not set)"
    )
    
    # External APIs
    serpapi_key: str = Field(
        default="",
        description="SerpAPI key for Google Scholar searches"
    )
    
    # File Storage
    upload_dir: str = Field(
        default="./uploads",
        description="Directory for uploaded files"
    )
    
    # CORS
    frontend_url: str = Field(
        default="http://localhost:5173",
        description="Frontend URL for CORS"
    )
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
