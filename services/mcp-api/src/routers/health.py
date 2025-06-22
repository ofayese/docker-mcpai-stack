"""Health check router"""

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
import httpx
from ..core.config import settings

router = APIRouter()


@router.get("/")
async def health_check():
    """Basic health check endpoint"""
    return JSONResponse(
        status_code=200,
        content={"status": "healthy", "service": "mcp-api"}
    )


@router.get("/ready")
async def readiness_check(request: Request):
    """Readiness check that verifies dependencies are available"""
    health_status = {
        "status": "ready",
        "services": {
            "qdrant": False,
            "model_runner": False
        }
    }
    # Check Qdrant connection
    try:
        qdrant = request.app.state.qdrant
        # Attempt a call to list collections
        _ = qdrant.get_collections()
        health_status["services"]["qdrant"] = True
    except Exception:
        health_status["status"] = "not_ready"
    # Check Model Runner
    try:
        async with httpx.AsyncClient() as client:
            url = f"{settings.MODEL_API_URL}/health"
            resp = await client.get(
                url,
                timeout=5
            )
        if resp.status_code == 200:
            health_status["services"]["model_runner"] = True
        else:
            health_status["status"] = "not_ready"
    except Exception:
        health_status["status"] = "not_ready"
    return JSONResponse(status_code=200, content=health_status)


@router.get("/live")
async def liveness_check():
    """Liveness check that verifies the service is running"""
    return JSONResponse(status_code=200, content={"status": "alive"})
