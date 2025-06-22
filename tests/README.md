# Testing Guide

This directory contains comprehensive tests for the Docker MCP AI Stack.

## Test Structure

```
tests/
├── unit/                   # Unit tests for individual components
├── integration/            # Integration tests for service communication  
├── e2e/                   # End-to-end tests for complete workflows
├── load/                  # Load tests using Locust
├── conftest.py            # Test configuration and fixtures
├── Dockerfile.e2e         # E2E test container
├── Dockerfile.load        # Load test container
└── README.md              # This file
```

## Running Tests

### Prerequisites

1. Docker and Docker Compose installed
2. Services built: `make build`

### Unit Tests

Run unit tests for individual services:

```bash
# Run MCP API unit tests
docker compose -f compose/docker-compose.test.yml run --rm mcp-api-unit-tests

# Or using make
make test-unit
```

### Integration Tests

Run integration tests that verify service communication:

```bash
# Start test services and run integration tests
docker compose -f compose/docker-compose.test.yml --profile integration up --exit-code-from mcp-api-integration

# Or using make
make test-integration
```

### End-to-End Tests

Run complete workflow tests:

```bash
# Run E2E tests
docker compose -f compose/docker-compose.test.yml --profile e2e up --exit-code-from e2e-tests

# Or using make
make test-e2e
```

### Load Tests

Run performance tests using Locust:

```bash
# Start load testing
docker compose -f compose/docker-compose.test.yml --profile load up

# Access Locust web interface at http://localhost:8089
# Configure number of users and spawn rate
# Start test against http://mcp-api-test:4000
```

### All Tests

Run the complete test suite:

```bash
make test-all
```

## Test Configuration

### Environment Variables

Test configuration is managed through environment variables:

- `ENVIRONMENT=test` - Sets test environment
- `LOG_LEVEL=DEBUG` - Enables debug logging
- `PYTEST_ARGS` - Custom pytest arguments
- `TARGET_HOST` - Load test target (for Locust)

### Test Profiles

Docker Compose profiles for different test types:

- `test` - Basic test services
- `unit` - Unit tests only
- `integration` - Integration tests
- `e2e` - End-to-end tests  
- `load` - Load testing
- `reports` - Test reporting service

### Test Data

Tests use:

- Ephemeral Qdrant instance with temporary storage
- Mock model runner for predictable responses
- Test fixtures in `conftest.py`

## Writing Tests

### Unit Tests

```python
import pytest
from unittest.mock import Mock, patch

def test_example():
    # Test individual functions/classes
    assert True
```

### Integration Tests

```python
import pytest
import httpx

@pytest.mark.integration
@pytest.mark.requires_services
async def test_api_integration(http_client, mcp_api_url):
    response = await http_client.get(f"{mcp_api_url}/health/")
    assert response.status_code == 200
```

### E2E Tests

```python
import pytest

@pytest.mark.e2e
@pytest.mark.slow
async def test_complete_workflow(http_client, mcp_api_url):
    # Test complete user workflows
    pass
```

### Load Tests

Add new user behaviors to `tests/load/locustfile.py`:

```python
from locust import HttpUser, task

class NewUser(HttpUser):
    @task
    def new_endpoint(self):
        self.client.get("/new/endpoint")
```

## Test Reports

Test results and coverage reports are available:

- Coverage HTML: `htmlcov/index.html`
- JUnit XML: `junit.xml`
- Load test reports: Locust web interface

Access test reports:

```bash
# Start test reports server
docker compose -f compose/docker-compose.test.yml --profile reports up

# View at http://localhost:8082
```

## Continuous Integration

Tests run automatically in CI/CD:

- `.github/workflows/ci.yml` - Main CI pipeline
- Unit tests run on every PR
- Integration tests on main branch
- Load tests on releases

## Troubleshooting

### Common Issues

1. **Services not ready**: Wait for health checks to pass
2. **Port conflicts**: Check if ports 4001, 6334, 8081 are available
3. **Permission errors**: Ensure Docker has proper permissions
4. **Memory issues**: Increase Docker memory limits

### Debug Mode

Enable verbose test output:

```bash
export PYTEST_ARGS="-v --tb=long --log-cli-level=DEBUG"
docker compose -f compose/docker-compose.test.yml run --rm mcp-api-unit-tests
```

### Viewing Logs

```bash
# View test service logs
docker compose -f compose/docker-compose.test.yml logs mcp-api-test

# Follow logs in real-time
docker compose -f compose/docker-compose.test.yml logs -f
```

## Performance Benchmarks

Expected performance baselines:

- Health endpoint: < 50ms response time
- Chat completion: < 2s response time
- Metrics endpoint: < 100ms response time
- System can handle 100 concurrent users

## Test Coverage Goals

- Unit test coverage: > 80%
- Integration test coverage: > 60%
- Critical paths: 100% coverage

## Contributing

When adding new features:

1. Write unit tests for new functions/classes
2. Add integration tests for new endpoints
3. Update E2E tests for new workflows
4. Consider load testing impact
5. Update this documentation
