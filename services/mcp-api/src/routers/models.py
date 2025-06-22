"""Models router for model management"""

from fastapi import APIRouter
from fastapi.responses import JSONResponse

router = APIRouter()


@router.get("/")
async def list_models():
    """List available models"""
    # TODO: Implement model listing from model-runner
    return JSONResponse(
        status_code=200,
        content={
            "data": [
                {
                    "id": "smollm2-1.7b",
                    "object": "model", 
                    "created": 1640995200,
                    "owned_by": "docker-mcp-stack"
                }
            ]
        }
    )


@router.get("/{model_id}")
async def get_model(model_id: str):
    """Get specific model information"""
    # TODO: Implement model details from model-runner
    return JSONResponse(
        status_code=200,
        content={
            "id": model_id,
            "object": "model",
            "created": 1640995200,
            "owned_by": "docker-mcp-stack"
        }
    )
