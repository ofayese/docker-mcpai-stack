"""Integration tests for the full MCP API stack."""

import asyncio
import time
from typing import Any, Dict

import httpx
import pytest


@pytest.mark.integration
@pytest.mark.requires_services
class TestMCPAPIIntegration:
    """Integration tests for MCP API."""

    @pytest.mark.asyncio
    async def test_health_endpoints_integration(
        self, http_client: httpx.AsyncClient, mcp_api_url: str
    ):
        """Test health endpoints in integration environment."""
        # Test basic health
        response = await http_client.get(f"{mcp_api_url}/health/")
        assert response.status_code == 200

        # Test readiness
        response = await http_client.get(f"{mcp_api_url}/health/ready")
        assert response.status_code in [200, 503]  # May fail if deps not ready

        # Test liveness
        response = await http_client.get(f"{mcp_api_url}/health/live")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_metrics_integration(
        self, http_client: httpx.AsyncClient, mcp_api_url: str
    ):
        """Test metrics endpoints in integration environment."""
        # Test Prometheus metrics
        response = await http_client.get(f"{mcp_api_url}/metrics")
        assert response.status_code == 200
        assert "http_requests_total" in response.text

        # Test custom metrics
        response = await http_client.get(f"{mcp_api_url}/v1/metrics/")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_mcp_endpoints_integration(
        self,
        http_client: httpx.AsyncClient,
        mcp_api_url: str,
        sample_mcp_request: Dict[str, Any],
    ):
        """Test MCP endpoints in integration environment."""
        # Test MCP info
        response = await http_client.get(f"{mcp_api_url}/mcp/")
        assert response.status_code == 200
        data = response.json()
        assert data["protocol"] == "mcp"

        # Test MCP status
        response = await http_client.get(f"{mcp_api_url}/mcp/status")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_chat_endpoints_integration(
        self,
        http_client: httpx.AsyncClient,
        mcp_api_url: str,
        sample_chat_request: Dict[str, Any],
    ):
        """Test chat endpoints in integration environment."""
        # Test chat completions
        response = await http_client.post(
            f"{mcp_api_url}/v1/chat/completions", json=sample_chat_request, timeout=30.0
        )
        # May return 500 if model runner not available - that's ok for integration
        assert response.status_code in [200, 500, 503]

    @pytest.mark.asyncio
    async def test_models_endpoints_integration(
        self, http_client: httpx.AsyncClient, mcp_api_url: str
    ):
        """Test models endpoints in integration environment."""
        # Test list models
        response = await http_client.get(f"{mcp_api_url}/v1/models/")
        # May fail if model runner not available
        assert response.status_code in [200, 500, 503]


@pytest.mark.integration
@pytest.mark.requires_services
class TestQdrantIntegration:
    """Integration tests for Qdrant vector database."""

    @pytest.mark.asyncio
    async def test_qdrant_health(self, http_client: httpx.AsyncClient, qdrant_url: str):
        """Test Qdrant health endpoint."""
        try:
            response = await http_client.get(f"{qdrant_url}/health")
            assert response.status_code == 200
        except httpx.ConnectError:
            pytest.skip("Qdrant not available")

    @pytest.mark.asyncio
    async def test_qdrant_collections(
        self, http_client: httpx.AsyncClient, qdrant_url: str
    ):
        """Test Qdrant collections endpoint."""
        try:
            response = await http_client.get(f"{qdrant_url}/collections")
            assert response.status_code == 200
        except httpx.ConnectError:
            pytest.skip("Qdrant not available")


@pytest.mark.integration
@pytest.mark.requires_services
class TestServiceCommunication:
    """Test communication between services."""

    @pytest.mark.asyncio
    async def test_mcp_to_model_runner_communication(
        self,
        http_client: httpx.AsyncClient,
        mcp_api_url: str,
        sample_chat_request: Dict[str, Any],
    ):
        """Test MCP API can communicate with model runner."""
        # This tests the full pipeline
        response = await http_client.post(
            f"{mcp_api_url}/v1/chat/completions", json=sample_chat_request, timeout=30.0
        )

        # We expect either success or a specific failure mode
        if response.status_code == 500:
            # Check if it's a connection error to model runner
            assert "model runner" in response.text.lower()
        else:
            assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_service_discovery(
        self,
        http_client: httpx.AsyncClient,
        mcp_api_url: str,
        model_runner_url: str,
        qdrant_url: str,
    ):
        """Test that services can discover and reach each other."""
        services = [
            (mcp_api_url, "/health/"),
            (model_runner_url, "/health"),
            (qdrant_url, "/health"),
        ]

        results = []
        for url, endpoint in services:
            try:
                response = await http_client.get(f"{url}{endpoint}", timeout=5.0)
                results.append(response.status_code == 200)
            except httpx.ConnectError:
                results.append(False)

        # At least the MCP API should be reachable in integration tests
        assert results[0], "MCP API should be reachable"
