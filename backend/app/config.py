"""
Application configuration using Pydantic Settings.
"""

from pathlib import Path
from typing import List
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Application
    APP_NAME: str = "Floor Plan Generator"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = True
    
    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]
    
    # File Storage
    UPLOAD_DIR: Path = Path("./uploads")
    EXPORT_DIR: Path = Path("./exports")
    MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024  # 10 MB
    
    # Geometry Defaults
    DEFAULT_UNIT: str = "meters"  # meters or feet
    GRID_SNAP: float = 0.15  # 150mm grid for wall alignment
    
    # Setback Defaults (meters)
    DEFAULT_FRONT_SETBACK: float = 3.0
    DEFAULT_BACK_SETBACK: float = 2.0
    DEFAULT_SIDE_SETBACK: float = 1.5
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# Global settings instance
settings = Settings()

# Ensure directories exist
settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
settings.EXPORT_DIR.mkdir(parents=True, exist_ok=True)
