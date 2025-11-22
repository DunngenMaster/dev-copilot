import os
from typing import List, Optional
from pydantic import field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Redis configuration
    redis_url: Optional[str] = None
    cache_ttl_seconds: int = 1800
    
    # Semantic vector cache configuration
    semantic_cache: str = "on"
    vector_dims: int = 128  # Upgraded from 32 for better semantic precision
    
    # CORS configuration
    cors_origins: List[str] = ["http://localhost:3000", "http://localhost:5173"]
    
    # Logging configuration
    log_level: str = "INFO"
    
    # API configuration
    api_host: str = "127.0.0.1"
    api_port: int = 8000
    
    # Application metadata
    app_name: str = "Dev-Copilot API"
    app_version: str = "1.0.0"
    
    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        """Parse CORS_ORIGINS from comma-separated string or list."""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v
    
    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v):
        """Validate log level is one of the standard levels."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        v_upper = v.upper()
        if v_upper not in valid_levels:
            raise ValueError(f"LOG_LEVEL must be one of: {', '.join(valid_levels)}")
        return v_upper
    
    class Config:
        # Environment file configuration
        env_file = ".env"
        env_file_encoding = "utf-8"
        # Case sensitivity
        case_sensitive = False
        # Allow extra fields
        extra = "ignore"


# Global settings instance
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """
    Get application settings singleton.
    
    Returns:
        Settings: Application configuration settings
    """
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


def reload_settings() -> Settings:
    """
    Force reload of settings from environment.
    
    Returns:
        Settings: Refreshed application configuration settings
    """
    global _settings
    _settings = Settings()
    return _settings