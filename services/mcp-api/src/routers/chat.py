"""Chat completions router"""

import time

import httpx
import structlog
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse

from ..core.config import settings
from ..core.monitoring import model_inference_count, model_inference_duration

router = APIRouter()
logger = structlog.get_logger()


class APIError(HTTPException):
    """Custom API error with detailed information"""

    def __init__(
        self, status_code: int, error_type: str, message: str, details: dict = None
    ):
        self.error_type = error_type
        self.details = details or {}
        detail = {
            "error": {"type": error_type, "message": message, "details": details or {}}
        }
        super().__init__(status_code=status_code, detail=detail)


@router.post("/completions")
async def chat_completions(request: Request):
    """OpenAI-compatible chat completions endpoint with enhanced error handling."""
    payload = await request.json()
    model = payload.get("model", "unknown")
    start = time.time()

    try:
        # Validate required fields
        if not payload.get("messages"):
            raise APIError(
                status_code=400,
                error_type="validation_error",
                message="Messages field is required",
                details={"field": "messages"},
            )

        async with httpx.AsyncClient() as client:
            url = f"{settings.MODEL_API_URL}/chat/completions"

            try:
                resp = await client.post(url, json=payload, timeout=30)

                # Handle different response status codes
                if resp.status_code == 200:
                    model_inference_count.labels(model_id=model, status="success").inc()
                    elapsed = time.time() - start
                    model_inference_duration.labels(model_id=model).observe(elapsed)
                    return JSONResponse(status_code=200, content=resp.json())
                elif resp.status_code == 400:
                    model_inference_count.labels(
                        model_id=model, status="client_error"
                    ).inc()
                    error_detail = (
                        resp.json()
                        if resp.headers.get("content-type", "").startswith(
                            "application/json"
                        )
                        else {"error": resp.text}
                    )
                    raise APIError(
                        status_code=400,
                        error_type="model_validation_error",
                        message="Invalid request to model service",
                        details=error_detail,
                    )
                elif resp.status_code == 404:
                    model_inference_count.labels(
                        model_id=model, status="model_not_found"
                    ).inc()
                    raise APIError(
                        status_code=404,
                        error_type="model_not_found",
                        message=f"Model '{model}' not found",
                        details={"model": model},
                    )
                elif resp.status_code >= 500:
                    model_inference_count.labels(
                        model_id=model, status="server_error"
                    ).inc()
                    raise APIError(
                        status_code=502,
                        error_type="model_service_error",
                        message="Model service is currently unavailable",
                        details={"upstream_status": resp.status_code},
                    )
                else:
                    model_inference_count.labels(model_id=model, status="error").inc()
                    raise APIError(
                        status_code=resp.status_code,
                        error_type="unexpected_response",
                        message="Unexpected response from model service",
                        details={"upstream_status": resp.status_code},
                    )

            except httpx.TimeoutException:
                model_inference_count.labels(model_id=model, status="timeout").inc()
                logger.warning("Model service timeout", model=model, url=url)
                raise APIError(
                    status_code=504,
                    error_type="timeout_error",
                    message="Model service request timed out",
                    details={"timeout_seconds": 30},
                )
            except httpx.ConnectError:
                model_inference_count.labels(
                    model_id=model, status="connection_error"
                ).inc()
                logger.error("Failed to connect to model service", model=model, url=url)
                raise APIError(
                    status_code=503,
                    error_type="connection_error",
                    message="Unable to connect to model service",
                    details={"service_url": url},
                )

    except APIError:
        # Re-raise our custom API errors
        raise
    except Exception as e:
        model_inference_count.labels(model_id=model, status="internal_error").inc()
        logger.error("Unexpected error in chat completions", error=str(e), model=model)
        raise APIError(
            status_code=500,
            error_type="internal_error",
            message="An unexpected error occurred",
            details={"error_id": f"chat-{int(time.time())}"},
        )
    finally:
        elapsed = time.time() - start
        model_inference_duration.labels(model_id=model).observe(elapsed)
