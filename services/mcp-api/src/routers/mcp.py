"""MCP protocol router"""

from fastapi import APIRouter
from fastapi.responses import JSONResponse

router = APIRouter()


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
                "sqlite"
            ]
        }
    )


@router.post("/request")
async def mcp_request():
    """Handle MCP protocol requests"""
    # TODO: Implement MCP request handling
    return JSONResponse(
        status_code=200,
        content={"status": "ok"}
    )
