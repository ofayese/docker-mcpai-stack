"""MCP protocol router"""

import logging
import time
from typing import Any, Dict, List, Optional

import httpx
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from ..core.config import settings
from ..core.monitoring import (
    active_requests,
    http_request_duration_seconds,
    http_requests_total,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/mcp", tags=["mcp"])


class MCPRequest(BaseModel):
    """Base class for MCP requests"""

    model: str
    context: Optional[Dict[str, Any]] = None
    messages: Optional[List[Dict[str, str]]] = None
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = 2048


class MCPResponse(BaseModel):
    """Base class for MCP responses"""

    model: str
    result: Any
    context: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None


@router.get("/")
async def mcp_info():
    """MCP service information"""
    return JSONResponse(
        status_code=200,
        content={
            "protocol": "mcp",
            "version": "1.0.0",
            "capabilities": [
                "time",
                "fetch",
                "filesystem",
                "postgres",
                "git",
                "sqlite",
            ],
            "implementation": "docker-mcpai-stack",
            "endpoints": {
                "process": "/mcp/process",
                "chat": "/mcp/chat",
                "status": "/mcp/status",
            },
        },
    )


@router.post("/process", response_model=MCPResponse)
async def process_mcp_request(request: MCPRequest):
    """
    Process a Model Context Protocol request
    """
    active_requests.inc()
    start_time = time.time()
    try:
        logger.info(f"Processing MCP request for model: {request.model}")

        # Forward request to model runner
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{settings.MODEL_API_URL}/mcp/process",
                json=request.dict(),
                timeout=60.0,
            )

            if response.status_code == 200:
                result = response.json()
                http_requests_total.labels(
                    method="POST", endpoint="/mcp/process", status_code=200
                ).inc()
                return result
            else:
                http_requests_total.labels(
                    method="POST",
                    endpoint="/mcp/process",
                    status_code=response.status_code,
                ).inc()
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Error from model runner: {response.text}",
                )
    except httpx.HTTPError as e:
        logger.error(f"Error communicating with model runner: {str(e)}")
        http_requests_total.labels(
            method="POST", endpoint="/mcp/process", status_code=500
        ).inc()
        raise HTTPException(
            status_code=500, detail=f"Error communicating with model runner: {str(e)}"
        )
    finally:
        duration = time.time() - start_time
        http_request_duration_seconds.labels(
            method="POST", endpoint="/mcp/process"
        ).observe(duration)
        active_requests.dec()


@router.get("/status")
async def mcp_status():
    """
    Get MCP implementation status
    """
    try:
        # Check model runner availability
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{settings.MODEL_API_URL}/health", timeout=5.0)
            model_runner_available = response.status_code == 200
    except:
        model_runner_available = False

    return {
        "status": "operational" if model_runner_available else "degraded",
        "version": "1.0.0",
        "implementation": "docker-mcpai-stack",
        "supported_models": ["gpt-3.5-turbo", "llama-7b"],
        "model_runner_available": model_runner_available,
        "capabilities": ["time", "fetch", "filesystem", "postgres", "git", "sqlite"],
    }


@router.post("/chat")
async def mcp_chat(request: MCPRequest):
    """
    Chat-specific MCP endpoint with enhanced context handling
    """
    active_requests.inc()
    start_time = time.time()
    try:
        if not request.messages:
            raise HTTPException(
                status_code=400, detail="Messages are required for chat requests"
            )

        # Enhance request with MCP context
        enhanced_request = request.dict()
        enhanced_request["context"] = {
            **(request.context or {}),
            "protocol": "mcp",
            "endpoint": "chat",
            "timestamp": int(time.time()),
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{settings.MODEL_API_URL}/chat/completions",
                json=enhanced_request,
                timeout=60.0,
            )

            if response.status_code == 200:
                result = response.json()
                http_requests_total.labels(
                    method="POST", endpoint="/mcp/chat", status_code=200
                ).inc()

                return MCPResponse(
                    model=request.model,
                    result=result,
                    context=enhanced_request["context"],
                    metadata={
                        "protocol_version": "mcp-1.0.0",
                        "processing_time": response.elapsed.total_seconds(),
                    },
                )
            else:
                http_requests_total.labels(
                    method="POST",
                    endpoint="/mcp/chat",
                    status_code=response.status_code,
                ).inc()
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Error from model runner: {response.text}",
                )
    except httpx.HTTPError as e:
        logger.error(f"Error in MCP chat: {str(e)}")
        http_requests_total.labels(
            method="POST", endpoint="/mcp/chat", status_code=500
        ).inc()
        raise HTTPException(status_code=500, detail=f"Error in MCP chat: {str(e)}")
    finally:
        duration = time.time() - start_time
        http_request_duration_seconds.labels(
            method="POST", endpoint="/mcp/chat"
        ).observe(duration)
        active_requests.dec()


@router.post("/request")
async def mcp_request():
    """Handle MCP protocol requests"""
    # TODO: Implement MCP request handling
    return JSONResponse(status_code=200, content={"status": "ok"})
