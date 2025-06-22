import asyncio
from typing import AsyncGenerator

import httpx
import pytest


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def http_client() -> AsyncGenerator[httpx.AsyncClient, None]:
    """HTTP client for testing API endpoints."""
    async with httpx.AsyncClient() as client:
        yield client


@pytest.fixture
def mcp_api_url() -> str:
    """MCP API base URL for testing."""
    return "http://localhost:4000"


@pytest.fixture
def model_runner_url() -> str:
    """Model Runner API base URL for testing."""
    return "http://localhost:8080"


@pytest.fixture
def ui_url() -> str:
    """UI base URL for testing."""
    return "http://localhost:8501"


@pytest.fixture
def qdrant_url() -> str:
    """Qdrant base URL for testing."""
    return "http://localhost:6333"


@pytest.fixture
def sample_chat_request():
    """Sample chat request for testing."""
    return {
        "model": "gpt-3.5-turbo",
        "messages": [{"role": "user", "content": "Hello, world!"}],
        "temperature": 0.7,
        "max_tokens": 100,
    }


@pytest.fixture
def sample_mcp_request():
    """Sample MCP request for testing."""
    return {
        "model": "gpt-3.5-turbo",
        "context": {"type": "test"},
        "messages": [{"role": "user", "content": "Test MCP request"}],
    }


# Pytest configuration
def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line("markers", "unit: Unit tests")
    config.addinivalue_line("markers", "integration: Integration tests")
    config.addinivalue_line("markers", "e2e: End-to-end tests")
    config.addinivalue_line("markers", "slow: Slow tests")
    config.addinivalue_line(
        "markers", "requires_services: Tests that require running services"
    )
