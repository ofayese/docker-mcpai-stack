"""Health check router"""

from fastapi import APIRouter
from fastapi.responses import JSONResponse

router = APIRouter()


@router.get("/")
async def health_check():
    """Basic health check endpoint"""
    return JSONResponse(
        status_code=200,
        content={"status": "healthy", "service": "mcp-api"}
    )


@router.get("/ready")
async def readiness_check():
    """Readiness check for Kubernetes"""
    # TODO: Add checks for dependencies (Qdrant, Model Runner, etc.)
    return JSONResponse(
        status_code=200,
        content={"status": "ready", "service": "mcp-api"}
    )


@router.get("/live")
async def liveness_check():
    """Liveness check for Kubernetes"""
    return JSONResponse(
        status_code=200,
        content={"status": "alive", "service": "mcp-api"}
    )
