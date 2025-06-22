from fastapi import FastAPI, Request, HTTPException
import time
import random
import uuid
import os
from datetime import datetime
from typing import Dict, Any

app = FastAPI(title="Mock Model Runner", version="1.0.0")

# Configuration
MOCK_LATENCY = float(os.getenv("MOCK_LATENCY", "0.1"))
MOCK_RESPONSES = os.getenv("MOCK_RESPONSES", "default")

# Sample models
MODELS = [
    {
        "id": "gpt-3.5-turbo",
        "object": "model",
        "created": 1640995200,
        "owned_by": "mock-org"
    },
    {
        "id": "llama-7b",
        "object": "model",
        "created": 1640995200,
        "owned_by": "mock-org"
    },
    {
        "id": "mistral-7b",
        "object": "model",
        "created": 1640995200,
        "owned_by": "mock-org"
    }
]

@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "healthy", "service": "mock-model-runner"}

@app.get("/v1/models")
async def list_models():
    """List available models"""
    return {
        "data": MODELS,
        "object": "list"
    }

@app.get("/v1/models/{model_id}")
async def get_model(model_id: str):
    """Get specific model information"""
    for model in MODELS:
        if model["id"] == model_id:
            return model
    raise HTTPException(status_code=404, detail="Model not found")

@app.post("/v1/chat/completions")
async def chat_completions(request: Request):
    """Mock chat completions endpoint"""
    body = await request.json()

    # Extract parameters
    model_id = body.get("model", "gpt-3.5-turbo")
    messages = body.get("messages", [])
    max_tokens = body.get("max_tokens", 100)
    temperature = body.get("temperature", 0.7)

    # Simulate processing time
    time.sleep(MOCK_LATENCY)

    # Get last user message
    last_message = ""
    for msg in reversed(messages):
        if msg.get("role") == "user":
            last_message = msg.get("content", "")
            break

    # Generate mock response based on mode
    if MOCK_RESPONSES == "test":
        response = f"Test response for: {last_message[:50]}..."
    elif MOCK_RESPONSES == "error":
        raise HTTPException(status_code=500, detail="Mock error")
    else:
        responses = [
            f"I understand you're asking about: {last_message}",
            "That's an interesting question. Let me help you with that.",
            f"Based on your message '{last_message}', here's my response.",
            "I'm a mock AI assistant, but I'll do my best to help!"
        ]
        response = random.choice(responses)

    # Return OpenAI-compatible response
    return {
        "id": f"chatcmpl-{uuid.uuid4()}",
        "object": "chat.completion",
        "created": int(datetime.now().timestamp()),
        "model": model_id,
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": response
                },
                "finish_reason": "stop"
            }
        ],
        "usage": {
            "prompt_tokens": len(last_message.split()),
            "completion_tokens": len(response.split()),
            "total_tokens": len(last_message.split()) + len(response.split())
        }
    }

@app.get("/metrics")
async def metrics():
    """Prometheus-style metrics endpoint"""
    return """# HELP mock_requests_total Total requests
# TYPE mock_requests_total counter
mock_requests_total 42

# HELP mock_response_duration_seconds Response duration
# TYPE mock_response_duration_seconds histogram
mock_response_duration_seconds_bucket{le="0.1"} 10
mock_response_duration_seconds_bucket{le="0.5"} 20
mock_response_duration_seconds_bucket{le="1.0"} 30
mock_response_duration_seconds_bucket{le="+Inf"} 30
mock_response_duration_seconds_sum 15.5
mock_response_duration_seconds_count 30
"""

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
