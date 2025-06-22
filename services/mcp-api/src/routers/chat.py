"""Chat completions router"""

from fastapi import APIRouter
from fastapi.responses import JSONResponse

router = APIRouter()


@router.post("/completions")
async def chat_completions():
    """OpenAI-compatible chat completions endpoint"""
    # TODO: Implement chat completions via model-runner
    return JSONResponse(
        status_code=200,
        content={
            "choices": [
                {
                    "message": {
                        "role": "assistant",
                        "content": "Hello! This is a placeholder response."
                    }
                }
            ]
        }
    )
