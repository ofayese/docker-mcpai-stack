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
async def mcp_request(request: Dict[str, Any]):
    """
    Handle MCP protocol requests

    This endpoint processes standard MCP protocol messages including:
    - initialize
    - tools/list
    - tools/call
    - resources/list
    - resources/read
    - prompts/list
    - prompts/get
    """
    active_requests.inc()
    start_time = time.time()

    try:
        method = request.get("method")
        if not method:
            raise HTTPException(
                status_code=400, detail="Method field is required in MCP request"
            )

        # Handle different MCP methods
        if method == "initialize":
            return await _handle_initialize(request)
        elif method == "tools/list":
            return await _handle_tools_list(request)
        elif method == "tools/call":
            return await _handle_tools_call(request)
        elif method == "resources/list":
            return await _handle_resources_list(request)
        elif method == "resources/read":
            return await _handle_resources_read(request)
        elif method == "prompts/list":
            return await _handle_prompts_list(request)
        elif method == "prompts/get":
            return await _handle_prompts_get(request)
        else:
            raise HTTPException(
                status_code=400, detail=f"Unsupported MCP method: {method}"
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in MCP request: {str(e)}")
        http_requests_total.labels(
            method="POST", endpoint="/mcp/request", status_code=500
        ).inc()
        raise HTTPException(
            status_code=500, detail=f"Error processing MCP request: {str(e)}"
        )
    finally:
        duration = time.time() - start_time
        http_request_duration_seconds.labels(
            method="POST", endpoint="/mcp/request"
        ).observe(duration)
        active_requests.dec()


async def _handle_initialize(request: Dict[str, Any]) -> Dict[str, Any]:
    """Handle MCP initialize request"""
    return {
        "jsonrpc": "2.0",
        "id": request.get("id"),
        "result": {
            "protocolVersion": "2024-11-05",
            "capabilities": {
                "tools": {"listChanged": True},
                "resources": {"subscribe": True, "listChanged": True},
                "prompts": {"listChanged": True},
            },
            "serverInfo": {"name": "docker-mcpai-stack", "version": "1.0.0"},
        },
    }


async def _handle_tools_list(request: Dict[str, Any]) -> Dict[str, Any]:
    """Handle MCP tools/list request"""
    return {
        "jsonrpc": "2.0",
        "id": request.get("id"),
        "result": {
            "tools": [
                {
                    "name": "generate_text",
                    "description": "Generate text using the configured LLM",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "prompt": {
                                "type": "string",
                                "description": "The text prompt",
                            },
                            "max_tokens": {
                                "type": "integer",
                                "description": "Maximum tokens to generate",
                            },
                            "temperature": {
                                "type": "number",
                                "description": "Sampling temperature",
                            },
                        },
                        "required": ["prompt"],
                    },
                },
                {
                    "name": "search_vector_db",
                    "description": "Search the vector database for relevant context",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "query": {"type": "string", "description": "Search query"},
                            "limit": {
                                "type": "integer",
                                "description": "Number of results to return",
                            },
                        },
                        "required": ["query"],
                    },
                },
            ]
        },
    }


async def _handle_tools_call(request: Dict[str, Any]) -> Dict[str, Any]:
    """Handle MCP tools/call request"""
    params = request.get("params", {})
    tool_name = params.get("name")
    arguments = params.get("arguments", {})

    if tool_name == "generate_text":
        return await _call_generate_text(request.get("id"), arguments)
    elif tool_name == "search_vector_db":
        return await _call_search_vector_db(request.get("id"), arguments)
    else:
        raise HTTPException(status_code=400, detail=f"Unknown tool: {tool_name}")


async def _handle_resources_list(request: Dict[str, Any]) -> Dict[str, Any]:
    """Handle MCP resources/list request"""
    return {
        "jsonrpc": "2.0",
        "id": request.get("id"),
        "result": {
            "resources": [
                {
                    "uri": "file://models",
                    "name": "Available Models",
                    "description": "List of available LLM models",
                    "mimeType": "application/json",
                },
                {
                    "uri": "file://vector-collections",
                    "name": "Vector Collections",
                    "description": "Available vector database collections",
                    "mimeType": "application/json",
                },
            ]
        },
    }


async def _handle_resources_read(request: Dict[str, Any]) -> Dict[str, Any]:
    """Handle MCP resources/read request"""
    params = request.get("params", {})
    uri = params.get("uri")

    if uri == "file://models":
        # Return available models from model runner
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{settings.MODEL_API_URL}/models", timeout=5.0
                )
                if response.status_code == 200:
                    models_data = response.json()
                else:
                    models_data = {"models": ["gpt-3.5-turbo", "llama-7b"]}
        except:
            models_data = {"models": ["gpt-3.5-turbo", "llama-7b"]}

        return {
            "jsonrpc": "2.0",
            "id": request.get("id"),
            "result": {
                "contents": [
                    {
                        "uri": uri,
                        "mimeType": "application/json",
                        "text": str(models_data),
                    }
                ]
            },
        }
    elif uri == "file://vector-collections":
        # Return vector collections info
        collections_data = {"collections": ["documents", "embeddings", "chat_history"]}
        return {
            "jsonrpc": "2.0",
            "id": request.get("id"),
            "result": {
                "contents": [
                    {
                        "uri": uri,
                        "mimeType": "application/json",
                        "text": str(collections_data),
                    }
                ]
            },
        }
    else:
        raise HTTPException(status_code=404, detail=f"Resource not found: {uri}")


async def _handle_prompts_list(request: Dict[str, Any]) -> Dict[str, Any]:
    """Handle MCP prompts/list request"""
    return {
        "jsonrpc": "2.0",
        "id": request.get("id"),
        "result": {
            "prompts": [
                {
                    "name": "summarize",
                    "description": "Summarize text content",
                    "arguments": [
                        {
                            "name": "text",
                            "description": "Text to summarize",
                            "required": True,
                        },
                        {
                            "name": "length",
                            "description": "Summary length preference",
                            "required": False,
                        },
                    ],
                },
                {
                    "name": "analyze",
                    "description": "Analyze and extract insights from data",
                    "arguments": [
                        {
                            "name": "data",
                            "description": "Data to analyze",
                            "required": True,
                        },
                        {
                            "name": "focus",
                            "description": "Analysis focus area",
                            "required": False,
                        },
                    ],
                },
            ]
        },
    }


async def _handle_prompts_get(request: Dict[str, Any]) -> Dict[str, Any]:
    """Handle MCP prompts/get request"""
    params = request.get("params", {})
    prompt_name = params.get("name")
    arguments = params.get("arguments", {})

    if prompt_name == "summarize":
        text = arguments.get("text", "")
        length = arguments.get("length", "medium")
        prompt_text = (
            f"Please provide a {length} summary of the following text:\n\n{text}"
        )
    elif prompt_name == "analyze":
        data = arguments.get("data", "")
        focus = arguments.get("focus", "general insights")
        prompt_text = (
            f"Please analyze the following data with focus on {focus}:\n\n{data}"
        )
    else:
        raise HTTPException(status_code=404, detail=f"Prompt not found: {prompt_name}")

    return {
        "jsonrpc": "2.0",
        "id": request.get("id"),
        "result": {
            "description": f"Generated prompt for {prompt_name}",
            "messages": [
                {"role": "user", "content": {"type": "text", "text": prompt_text}}
            ],
        },
    }


async def _call_generate_text(
    request_id: str, arguments: Dict[str, Any]
) -> Dict[str, Any]:
    """Call the generate_text tool"""
    prompt = arguments.get("prompt")
    max_tokens = arguments.get("max_tokens", 2048)
    temperature = arguments.get("temperature", 0.7)

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{settings.MODEL_API_URL}/chat/completions",
                json={
                    "model": "gpt-3.5-turbo",
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": max_tokens,
                    "temperature": temperature,
                },
                timeout=60.0,
            )

            if response.status_code == 200:
                result = response.json()
                generated_text = (
                    result.get("choices", [{}])[0].get("message", {}).get("content", "")
                )

                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {"content": [{"type": "text", "text": generated_text}]},
                }
            else:
                raise HTTPException(
                    status_code=response.status_code, detail="Error generating text"
                )

    except httpx.HTTPError as e:
        raise HTTPException(
            status_code=500, detail=f"Error calling model runner: {str(e)}"
        )


async def _call_search_vector_db(
    request_id: str, arguments: Dict[str, Any]
) -> Dict[str, Any]:
    """Call the search_vector_db tool"""
    query = arguments.get("query")
    limit = arguments.get("limit", 5)

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{settings.QDRANT_URL}/collections/documents/points/search",
                json={"vector": {"text": query}, "limit": limit, "with_payload": True},
                timeout=10.0,
            )

            if response.status_code == 200:
                search_results = response.json()
                formatted_results = [
                    f"Score: {result.get('score', 0):.3f} - {result.get('payload', {}).get('text', 'No content')}"
                    for result in search_results.get("result", [])
                ]

                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {
                        "content": [
                            {
                                "type": "text",
                                "text": (
                                    "\n".join(formatted_results)
                                    if formatted_results
                                    else "No results found"
                                ),
                            }
                        ]
                    },
                }
            else:
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {
                        "content": [
                            {
                                "type": "text",
                                "text": "Vector search temporarily unavailable",
                            }
                        ]
                    },
                }

    except httpx.HTTPError:
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "content": [
                    {"type": "text", "text": "Vector search temporarily unavailable"}
                ]
            },
        }
