"""Chat completions router"""

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse
import time
import httpx
from ..core.config import settings
from ..core.monitoring import model_inference_count, model_inference_duration

router = APIRouter()



@router.post("/completions")
async def chat_completions(request: Request):
    """OpenAI-compatible chat completions endpoint with metrics."""
    payload = await request.json()
    model = payload.get("model", "unknown")
    start = time.time()
    try:
        async with httpx.AsyncClient() as client:
            url = f"{settings.MODEL_API_URL}/chat/completions"
            resp = await client.post(
                url,
                json=payload,
                timeout=30
            )
        status_label = "success" if resp.status_code == 200 else "error"
        model_inference_count.labels(model_id=model, status=status_label).inc()
        elapsed = time.time() - start
        model_inference_duration.labels(model_id=model).observe(elapsed)
        return JSONResponse(status_code=resp.status_code, content=resp.json())
    except Exception as e:
        model_inference_count.labels(model_id=model, status="error").inc()
        raise HTTPException(status_code=500, detail=str(e))
