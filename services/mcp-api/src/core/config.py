"""Configuration settings for MCP API Gateway"""

from pydantic import BaseSettings
import os
from typing import List


class Settings(BaseSettings):
    """
    Application settings loaded from environment or .env file
    """
    VERSION: str = "1.0.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "production"

    # Server settings
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "4000"))

    # External service URLs
    QDRANT_URL: str = os.getenv(
        "QDRANT_URL", "http://qdrant:6333"
    )
    MODEL_API_URL: str = os.getenv(
        "MODEL_API_URL", "http://model-runner:8080/v1"
    )
    OLLAMA_BASE_URL: str = os.getenv(
        "OLLAMA_BASE_URL", "http://model-runner:8080/v1"
    )

    # CORS settings
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:8080",
        "http://localhost:8501",
        "*"  # Allow all in development
    ]

    # Data directory
    DATA_DIR: str = os.getenv("DATA_DIR", "/data")

    # Logging level
    LOG_LEVEL: str = "INFO"

    # Monitoring
    PROMETHEUS_MULTIPROC_DIR: str = "/tmp"

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
