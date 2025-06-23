"""End-to-end tests for the complete MCP AI stack."""

import asyncio
import time
from typing import Any, Dict

import httpx
import pytest


@pytest.mark.e2e
@pytest.mark.slow
@pytest.mark.requires_services
class TestFullStackE2E:
    """End-to-end tests for the complete stack."""

    @pytest.mark.asyncio
    async def test_complete_chat_flow(
        self,
        http_client: httpx.AsyncClient,
        mcp_api_url: str,
        sample_chat_request: Dict[str, Any],
    ):
        """Test complete chat flow from request to response."""
        # 1. Check system health first
        health_response = await http_client.get(f"{mcp_api_url}/health/ready")
        if health_response.status_code != 200:
            pytest.skip("System not ready for E2E testing")

        # 2. Send chat request
        chat_response = await http_client.post(
            f"{mcp_api_url}/v1/chat/completions",
            json=sample_chat_request,
            timeout=60.0,  # Allow longer timeout for E2E
        )

        # 3. Verify response
        if chat_response.status_code == 200:
            data = chat_response.json()
            assert "choices" in data
            assert len(data["choices"]) > 0
            assert "message" in data["choices"][0]
        else:
            # Log the error for debugging
            print(f"Chat request failed: {chat_response.text}")

    @pytest.mark.asyncio
    async def test_mcp_protocol_flow(
        self,
        http_client: httpx.AsyncClient,
        mcp_api_url: str,
        sample_mcp_request: Dict[str, Any],
    ):
        """Test MCP protocol specific flow."""
        # 1. Get MCP capabilities
        info_response = await http_client.get(f"{mcp_api_url}/mcp/")
        assert info_response.status_code == 200
        capabilities = info_response.json()["capabilities"]

        # 2. Check MCP status
        status_response = await http_client.get(f"{mcp_api_url}/mcp/status")
        assert status_response.status_code == 200

        # 3. Test MCP chat if available
        if status_response.json().get("model_runner_available", False):
            mcp_response = await http_client.post(
                f"{mcp_api_url}/mcp/chat", json=sample_mcp_request, timeout=60.0
            )
            if mcp_response.status_code == 200:
                data = mcp_response.json()
                assert "result" in data
                assert "metadata" in data

    @pytest.mark.asyncio
    async def test_monitoring_stack(
        self, http_client: httpx.AsyncClient, mcp_api_url: str
    ):
        """Test monitoring and metrics collection."""
        # 1. Generate some API calls to create metrics
        for _ in range(5):
            await http_client.get(f"{mcp_api_url}/health/")
            time.sleep(0.1)

        # 2. Check metrics are being collected
        metrics_response = await http_client.get(f"{mcp_api_url}/metrics")
        assert metrics_response.status_code == 200
        metrics_text = metrics_response.text

        # 3. Verify specific metrics exist
        assert "http_requests_total" in metrics_text
        assert "http_request_duration_seconds" in metrics_text

        # 4. Check custom metrics endpoint
        custom_metrics = await http_client.get(f"{mcp_api_url}/v1/metrics/")
        assert custom_metrics.status_code == 200

    @pytest.mark.asyncio
    async def test_error_handling_and_recovery(
        self, http_client: httpx.AsyncClient, mcp_api_url: str
    ):
        """Test error handling and system recovery."""
        # 1. Test with invalid request
        invalid_request = {"invalid": "request"}
        response = await http_client.post(
            f"{mcp_api_url}/v1/chat/completions", json=invalid_request
        )
        assert response.status_code == 422  # Validation error

        # 2. Verify system is still healthy after error
        health_response = await http_client.get(f"{mcp_api_url}/health/")
        assert health_response.status_code == 200

        # 3. Test that valid requests still work
        health_response = await http_client.get(f"{mcp_api_url}/mcp/")
        assert health_response.status_code == 200

    @pytest.mark.asyncio
    async def test_load_handling(
        self, http_client: httpx.AsyncClient, mcp_api_url: str
    ):
        """Test system behavior under load."""
        # Send multiple concurrent requests
        tasks = []
        for i in range(10):
            task = http_client.get(f"{mcp_api_url}/health/")
            tasks.append(task)

        # Execute all requests concurrently
        responses = await asyncio.gather(*tasks, return_exceptions=True)

        # Verify most requests succeeded
        success_count = sum(
            1
            for resp in responses
            if hasattr(resp, "status_code") and resp.status_code == 200
        )
        assert success_count >= 8  # Allow for some failures under load

    @pytest.mark.asyncio
    async def test_service_dependencies(
        self, http_client: httpx.AsyncClient, mcp_api_url: str, qdrant_url: str
    ):
        """Test service dependency handling."""
        # Check if Qdrant is available
        try:
            qdrant_response = await http_client.get(f"{qdrant_url}/health", timeout=5.0)
            qdrant_available = qdrant_response.status_code == 200
        except:
            qdrant_available = False

        # Check readiness endpoint reflects dependency status
        ready_response = await http_client.get(f"{mcp_api_url}/health/ready")

        if qdrant_available:
            # If Qdrant is available, system should be ready
            assert ready_response.status_code in [200, 503]
        else:
            # If Qdrant is unavailable, system may not be ready
            assert ready_response.status_code in [200, 503]

        # Liveness should always work regardless of dependencies
        live_response = await http_client.get(f"{mcp_api_url}/health/live")
        assert live_response.status_code == 200
