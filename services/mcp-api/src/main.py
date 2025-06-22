"""
MCP API Gateway - Main FastAPI application
Provides unified API for Model Context Protocol services
"""

import os
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from prometheus_client import (
    Counter, 
    Histogram, 
    generate_latest, 
    CONTENT_TYPE_LATEST
)
import uvicorn

from .routers import chat, models, health, mcp
from .core.config import settings
from .core.monitoring import setup_metrics

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

# Metrics
request_count = Counter(
    'mcp_api_requests_total', 
    'Total API requests', 
    ['method', 'endpoint', 'status']
)
request_duration = Histogram(
    'mcp_api_request_duration_seconds', 
    'Request duration', 
    ['method', 'endpoint']
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    logger.info("Starting MCP API Gateway", version=settings.VERSION)
    
    # Initialize metrics
    setup_metrics()
    
    # Initialize connections
    # Set up Qdrant client for vector store
    try:
        from qdrant_client import QdrantClient
        app.state.qdrant = QdrantClient(url=settings.QDRANT_URL)
        logger.info("Initialized Qdrant client", url=settings.QDRANT_URL)
    except Exception as e:
        logger.error("Failed to initialize Qdrant client", error=str(e))
        raise
    # Check Model Runner health
    try:
        import httpx
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{settings.MODEL_API_URL}/health", timeout=5)
        if resp.status_code != 200:
            raise RuntimeError(f"Model runner unhealthy: {resp.status_code}")
        logger.info("Model runner is healthy")
    except Exception as e:
        logger.error("Model runner health check failed", error=str(e))
        raise
    
    yield
    
    logger.info("Shutting down MCP API Gateway")


# Create FastAPI app
app = FastAPI(
    title="MCP API Gateway",
    description="Unified API for Model Context Protocol services",
    version=settings.VERSION,
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def monitoring_middleware(request: Request, call_next):
    """Add monitoring to all requests"""
    method = request.method
    endpoint = request.url.path
    
    with request_duration.labels(method=method, endpoint=endpoint).time():
        response = await call_next(request)
    
    request_count.labels(
        method=method,
        endpoint=endpoint,
        status=response.status_code
    ).inc()
    
    return response


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler"""
    logger.error("Unhandled exception", exc_info=exc, path=request.url.path)
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "detail": str(exc)}
    )


# Include routers
app.include_router(health.router, prefix="/health", tags=["health"])
app.include_router(models.router, prefix="/v1/models", tags=["models"])
app.include_router(chat.router, prefix="/v1/chat", tags=["chat"])
app.include_router(mcp.router, prefix="/mcp", tags=["mcp"])


@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "MCP API Gateway",
        "version": settings.VERSION,
        "status": "healthy",
        "endpoints": {
            "health": "/health",
            "models": "/v1/models",
            "chat": "/v1/chat/completions",
            "mcp": "/mcp",
            "metrics": "/metrics"
        }
    }


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=4000,
        reload=True if os.getenv("ENVIRONMENT") == "development" else False
    )
