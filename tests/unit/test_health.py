"""Unit tests for MCP API health endpoints."""

import os
import sys
from unittest.mock import AsyncMock, Mock, patch

import pytest
from fastapi.testclient import TestClient

# Add the source path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../services/mcp-api"))

from src.main import app


@pytest.fixture
def client():
    """Test client for the FastAPI app."""
    return TestClient(app)


class TestHealthEndpoints:
    """Test health check endpoints."""

    def test_root_endpoint(self, client):
        """Test the root endpoint returns basic info."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "name" in data
        assert "version" in data
        assert "status" in data

    def test_health_basic(self, client):
        """Test basic health check."""
        response = client.get("/health/")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "timestamp" in data

    @patch("httpx.AsyncClient.get")
    def test_health_ready_success(self, mock_get, client):
        """Test ready endpoint when all dependencies are healthy."""
        # Mock successful responses
        mock_response = Mock()
        mock_response.status_code = 200
        mock_get.return_value.__aenter__.return_value = mock_response

        response = client.get("/health/ready")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ready"

    @patch("httpx.AsyncClient.get")
    def test_health_ready_failure(self, mock_get, client):
        """Test ready endpoint when dependencies are unhealthy."""
        # Mock failed responses
        mock_response = Mock()
        mock_response.status_code = 500
        mock_get.return_value.__aenter__.return_value = mock_response

        response = client.get("/health/ready")
        assert response.status_code == 503
        data = response.json()
        assert data["status"] == "not ready"

    def test_health_live(self, client):
        """Test liveness endpoint."""
        response = client.get("/health/live")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "alive"


class TestMetricsEndpoint:
    """Test metrics endpoints."""

    def test_metrics_endpoint(self, client):
        """Test Prometheus metrics endpoint."""
        response = client.get("/metrics")
        assert response.status_code == 200
        assert "text/plain" in response.headers.get("content-type", "")

    def test_custom_metrics_endpoint(self, client):
        """Test custom metrics endpoint."""
        response = client.get("/v1/metrics/")
        assert response.status_code == 200
        data = response.json()
        assert "metrics" in data


@pytest.mark.asyncio
class TestMCPEndpoints:
    """Test MCP protocol endpoints."""

    def test_mcp_info(self, client):
        """Test MCP info endpoint."""
        response = client.get("/mcp/")
        assert response.status_code == 200
        data = response.json()
        assert data["protocol"] == "mcp"
        assert "version" in data
        assert "capabilities" in data

    def test_mcp_status(self, client):
        """Test MCP status endpoint."""
        response = client.get("/mcp/status")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "implementation" in data

    @patch("httpx.AsyncClient.post")
    def test_mcp_chat_missing_messages(self, mock_post, client):
        """Test MCP chat endpoint with missing messages."""
        request_data = {"model": "gpt-3.5-turbo", "context": {"type": "test"}}

        response = client.post("/mcp/chat", json=request_data)
        assert response.status_code == 400
        data = response.json()
        assert "Messages are required" in data["detail"]
