from fastapi import APIRouter
from ..core.monitoring import get_metrics

router = APIRouter()

@router.get("/metrics", tags=["metrics"])
def metrics():
    """Return application metrics for Prometheus scraping or UI display."""
    return get_metrics()

@router.get("/summary", tags=["metrics"])
def metrics_summary():
    """Return a summary of available metric names and descriptions."""
    return {
        "metrics": [
            {"name": "requests_total", "description": "Total API requests"},
            {"name": "active_requests", "description": "Number of active requests being processed"},
            {"name": "model_inferences_total", "description": "Total model inference requests"},
            {"name": "system_info", "description": "System information about the MCP API"}
        ]
    }
