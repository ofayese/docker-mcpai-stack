"""Models router for model management"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
import httpx
from app.core.config import settings

router = APIRouter()


@router.get("/")
async def list_models():
    """List available models from the model-runner service."""
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{settings.MODEL_API_URL}/models",
                timeout=10
            )
        if resp.status_code == 200:
            return resp.json()
        raise HTTPException(
            status_code=resp.status_code,
            detail=resp.text
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{model_id}")
async def get_model(model_id: str):
    """Fetch details for a specific model from the model-runner service."""
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{settings.MODEL_API_URL}/models/{model_id}",
                timeout=10
            )
        if resp.status_code == 200:
            return resp.json()
        raise HTTPException(
            status_code=resp.status_code,
            detail=resp.text
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
