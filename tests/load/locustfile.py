"""Load tests for the MCP AI Stack using Locust."""

import json

from locust import HttpUser, between, task


class MCPAPIUser(HttpUser):
    """Simulate a user interacting with the MCP API."""

    wait_time = between(1, 5)  # Wait 1-5 seconds between requests

    def on_start(self):
        """Initialize user session."""
        # Check if API is healthy before starting
        with self.client.get("/health/", catch_response=True) as response:
            if response.status_code != 200:
                response.failure("API not healthy on startup")

    @task(3)
    def health_check(self):
        """Test health endpoint (most frequent)."""
        self.client.get("/health/")

    @task(2)
    def health_ready(self):
        """Test readiness endpoint."""
        self.client.get("/health/ready")

    @task(1)
    def health_live(self):
        """Test liveness endpoint."""
        self.client.get("/health/live")

    @task(2)
    def mcp_info(self):
        """Test MCP info endpoint."""
        self.client.get("/mcp/")

    @task(1)
    def mcp_status(self):
        """Test MCP status endpoint."""
        self.client.get("/mcp/status")

    @task(1)
    def list_models(self):
        """Test models listing endpoint."""
        with self.client.get("/v1/models/", catch_response=True) as response:
            # May fail if model runner not available - that's ok
            if response.status_code not in [200, 500, 503]:
                response.failure(f"Unexpected status code: {response.status_code}")

    @task(1)
    def metrics_endpoint(self):
        """Test metrics endpoint."""
        self.client.get("/metrics")

    @task(1)
    def custom_metrics(self):
        """Test custom metrics endpoint."""
        self.client.get("/v1/metrics/")

    @task(1)
    def chat_completion(self):
        """Test chat completion endpoint (lower frequency due to cost)."""
        payload = {
            "model": "gpt-3.5-turbo",
            "messages": [
                {"role": "user", "content": "Hello, this is a load test message."}
            ],
            "temperature": 0.7,
            "max_tokens": 50,
        }

        with self.client.post(
            "/v1/chat/completions", json=payload, catch_response=True, timeout=30
        ) as response:
            if response.status_code == 200:
                try:
                    data = response.json()
                    if "choices" not in data:
                        response.failure("Invalid response format")
                except json.JSONDecodeError:
                    response.failure("Invalid JSON response")
            elif response.status_code in [500, 503]:
                # Expected if model runner is not available
                response.success()
            else:
                response.failure(f"Unexpected status code: {response.status_code}")

    @task(1)
    def mcp_chat(self):
        """Test MCP chat endpoint."""
        payload = {
            "model": "gpt-3.5-turbo",
            "messages": [{"role": "user", "content": "MCP load test message"}],
            "context": {"type": "load_test"},
        }

        with self.client.post(
            "/mcp/chat", json=payload, catch_response=True, timeout=30
        ) as response:
            if response.status_code == 200:
                try:
                    data = response.json()
                    if "result" not in data:
                        response.failure("Invalid MCP response format")
                except json.JSONDecodeError:
                    response.failure("Invalid JSON response")
            elif response.status_code in [400, 500, 503]:
                # Expected errors are ok
                response.success()
            else:
                response.failure(f"Unexpected status code: {response.status_code}")


class HealthCheckUser(HttpUser):
    """Lightweight user that only does health checks."""

    wait_time = between(0.5, 2)
    weight = 3  # Higher weight = more users of this type

    @task
    def health_check_only(self):
        """Only perform health checks."""
        self.client.get("/health/")


class MetricsUser(HttpUser):
    """User focused on metrics endpoints."""

    wait_time = between(5, 15)  # Less frequent
    weight = 1

    @task(2)
    def prometheus_metrics(self):
        """Check Prometheus metrics."""
        self.client.get("/metrics")

    @task(1)
    def custom_metrics(self):
        """Check custom metrics."""
        self.client.get("/v1/metrics/")
