"""Application configuration management."""

from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List
from pathlib import Path

# Get the app directory
APP_DIR = Path(__file__).parent

class Settings(BaseSettings):
    """Application settings."""
    
    # Application
    APP_NAME: str = "REA Flight Portal"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    
    # VDC API Configuration
    VDC_API_BASE_URL: str = "https://api.stage.verteil.com/entrygate/rest/request"
    VDC_TOKEN_URL: str = "https://api.stage.verteil.com/oauth2/token"
    VDC_USERNAME: str = ""  # From VERTEIL_USERNAME in .env
    VDC_PASSWORD: str = ""  # From VERTEIL_PASSWORD in .env
    VDC_OFFICE_ID: str = "OFF3746"
    
    # Support both VDC_ and VERTEIL_ prefixes for backward compatibility
    VERTEIL_USERNAME: str = ""
    VERTEIL_PASSWORD: str = ""
    VERTEIL_OFFICE_ID: str = "OFF3746"
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Use VERTEIL_ values if VDC_ not set
        if not self.VDC_USERNAME and self.VERTEIL_USERNAME:
            self.VDC_USERNAME = self.VERTEIL_USERNAME
        if not self.VDC_PASSWORD and self.VERTEIL_PASSWORD:
            self.VDC_PASSWORD = self.VERTEIL_PASSWORD
        if self.VDC_OFFICE_ID == "OFF3746" and self.VERTEIL_OFFICE_ID != "OFF3746":
            self.VDC_OFFICE_ID = self.VERTEIL_OFFICE_ID
    
    # CORS - comma-separated string that will be split
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:3001,https://rea-flight-portal.vercel.app"
    
    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 5000
    
    model_config = SettingsConfigDict(
        env_file=str(APP_DIR / ".env"),
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"  # Ignore extra fields from old .env file
    )
    
    def get_cors_origins(self) -> List[str]:
        """Get CORS origins as a list."""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]


# Global settings instance
settings = Settings()
