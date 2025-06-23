"""Configuration settings for MCP API Gateway"""

import os
from typing import List

from pydantic import BaseSettings


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
    QDRANT_URL: str = os.getenv("QDRANT_URL", "http://qdrant:6333")
    MODEL_API_URL: str = os.getenv("MODEL_API_URL", "http://model-runner:8080/v1")
    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://model-runner:8080/v1")

    # CORS settings - Environment specific
    CORS_ORIGINS: List[str] = []

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Set CORS origins based on environment
        if self.ENVIRONMENT == "development":
            self.CORS_ORIGINS = [
                "http://localhost:3000",
                "http://localhost:8080",
                "http://localhost:8501",
                "http://127.0.0.1:3000",
                "http://127.0.0.1:8080",
                "http://127.0.0.1:8501",
            ]
        elif self.ENVIRONMENT == "testing":
            self.CORS_ORIGINS = [
                "http://localhost:3000",
                "http://localhost:8080",
                "http://localhost:8501",
            ]
        else:  # production
            # In production, explicitly set allowed origins
            cors_origins_env = os.getenv("CORS_ORIGINS", "")
            if cors_origins_env:
                self.CORS_ORIGINS = [
                    origin.strip() for origin in cors_origins_env.split(",")
                ]
            else:
                # Default to empty for security - must be explicitly configured
                self.CORS_ORIGINS = []

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
