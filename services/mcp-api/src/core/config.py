"""Configuration settings for MCP API Gateway"""

import os
from typing import List

class Settings:
    VERSION: str = "1.0.0"
    
    # Server settings
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "4000"))
    
    # External service URLs
    MODEL_API_URL: str = os.getenv("MODEL_API_URL", "http://model-runner:8080/v1")
    QDRANT_URL: str = os.getenv("QDRANT_URL", "http://qdrant:6333")
    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://model-runner:8080/v1")
    
    # CORS settings
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:8080",
        "http://localhost:8501",
        "*"  # Allow all in development
    ]
    
    # Data directory
    DATA_DIR: str = os.getenv("DATA_DIR", "/data")
    
    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    # Environment
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "production")

settings = Settings()
