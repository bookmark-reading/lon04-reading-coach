"""Application configuration using Pydantic Settings."""

from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=[".env.local", ".env"],  # Try .env.local first, then .env
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application settings
    app_name: str = "lon04-reading-coach"
    app_version: str = "0.1.0"
    debug: bool = False
    
    # API settings
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    
    # Logging
    log_level: str = "INFO"
    
    # AWS Configuration
    aws_region: str = "us-west-2"
    aws_access_key_id: Optional[str] = None
    aws_secret_access_key: Optional[str] = None
    aws_session_token: Optional[str] = None
    
    # Nova Sonic Configuration
    nova_model_id: str = "amazon.nova-sonic-v1:0"
    nova_max_tokens: int = 1024
    nova_temperature: float = 0.7
    nova_top_p: float = 0.9
    nova_sample_rate_hz: int = 16000
    nova_channels: int = 1
    
    # Reading Agent Selection
    reading_agent_type: str = "simple"  # "simple" or "nova_sonic"


# Create a singleton instance
settings = Settings()
