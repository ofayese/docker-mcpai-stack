# Error Handling Best Practices Guide

This guide outlines the error handling strategies implemented in the Docker MCP Stack and provides recommendations for consistent error management across all services.

## Error Handling Philosophy

The MCP Stack implements a multi-layered error handling approach:

1. **Prevention**: Input validation and early error detection
2. **Graceful Degradation**: Continue operation with reduced functionality
3. **Detailed Reporting**: Provide actionable error information
4. **Recovery**: Automatic retry and recovery mechanisms
5. **Monitoring**: Track errors for system health insights

## API Error Standards

### Error Response Format

All API errors follow a consistent JSON structure:

```json
{
  "error": {
    "type": "error_type_identifier",
    "message": "Human-readable error description",
    "details": {
      "field": "specific_field_name",
      "code": "ERROR_CODE",
      "suggestion": "How to fix this error"
    }
  }
}
```

### Error Types

#### 1. Validation Errors (400)

Client-side input validation failures:

```json
{
  "error": {
    "type": "validation_error",
    "message": "Required field is missing",
    "details": {
      "field": "messages",
      "required": true,
      "suggestion": "Include a 'messages' array in your request"
    }
  }
}
```

#### 2. Authentication Errors (401)

Authentication and authorization failures:

```json
{
  "error": {
    "type": "authentication_error",
    "message": "Invalid or missing API key",
    "details": {
      "header": "X-API-Key",
      "suggestion": "Include a valid API key in the X-API-Key header"
    }
  }
}
```

#### 3. Resource Not Found (404)

Missing resources or endpoints:

```json
{
  "error": {
    "type": "resource_not_found",
    "message": "Model not found",
    "details": {
      "model": "llama3-8b-v2",
      "available_models": ["llama3-8b", "smollm2-1.7b"],
      "suggestion": "Use one of the available models"
    }
  }
}
```

#### 4. Rate Limiting (429)

Request rate limiting:

```json
{
  "error": {
    "type": "rate_limit_exceeded",
    "message": "Too many requests",
    "details": {
      "limit": 100,
      "window": "1 hour",
      "retry_after": 3600,
      "suggestion": "Wait before making additional requests"
    }
  }
}
```

#### 5. Service Errors (500-503)

Internal service failures:

```json
{
  "error": {
    "type": "service_unavailable",
    "message": "Model service is temporarily unavailable",
    "details": {
      "service": "model-runner",
      "error_id": "srv-1642681234",
      "retry_after": 30,
      "suggestion": "Try again in a few moments"
    }
  }
}
```

## Implementation Examples

### FastAPI Error Handling

```python
from fastapi import HTTPException
import structlog

logger = structlog.get_logger()

class MCPError(HTTPException):
    """Base error class for MCP services"""
    
    def __init__(self, status_code: int, error_type: str, message: str, details: dict = None):
        self.error_type = error_type
        self.details = details or {}
        
        detail = {
            "error": {
                "type": error_type,
                "message": message,
                "details": details or {}
            }
        }
        super().__init__(status_code=status_code, detail=detail)

# Usage examples
async def validate_request(payload: dict):
    if not payload.get("messages"):
        raise MCPError(
            status_code=400,
            error_type="validation_error",
            message="Messages field is required",
            details={
                "field": "messages",
                "required": True,
                "suggestion": "Include a 'messages' array in your request"
            }
        )

async def handle_model_request(model_id: str, payload: dict):
    try:
        # Model processing logic
        result = await process_model_request(model_id, payload)
        return result
        
    except ModelNotFoundError:
        raise MCPError(
            status_code=404,
            error_type="model_not_found",
            message=f"Model '{model_id}' not found",
            details={
                "model": model_id,
                "suggestion": "Check available models via GET /models"
            }
        )
    except ModelTimeoutError:
        raise MCPError(
            status_code=504,
            error_type="timeout_error",
            message="Model request timed out",
            details={
                "timeout_seconds": 30,
                "model": model_id,
                "suggestion": "Try a smaller request or contact support"
            }
        )
    except Exception as e:
        logger.error("Unexpected model error", model=model_id, error=str(e))
        raise MCPError(
            status_code=500,
            error_type="internal_error",
            message="An unexpected error occurred",
            details={
                "error_id": f"model-{int(time.time())}",
                "suggestion": "Contact support with the error ID"
            }
        )
```

### Circuit Breaker Pattern

Implement circuit breakers for external service calls:

```python
import asyncio
from datetime import datetime, timedelta

class CircuitBreaker:
    def __init__(self, failure_threshold=5, recovery_timeout=60):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
    
    async def call(self, func, *args, **kwargs):
        if self.state == "OPEN":
            if self._should_attempt_reset():
                self.state = "HALF_OPEN"
            else:
                raise MCPError(
                    status_code=503,
                    error_type="circuit_breaker_open",
                    message="Service temporarily unavailable",
                    details={
                        "retry_after": self.recovery_timeout,
                        "suggestion": "Service is experiencing issues, try again later"
                    }
                )
        
        try:
            result = await func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise
    
    def _should_attempt_reset(self):
        return (
            self.last_failure_time and
            datetime.now() - self.last_failure_time > timedelta(seconds=self.recovery_timeout)
        )
    
    def _on_success(self):
        self.failure_count = 0
        self.state = "CLOSED"
    
    def _on_failure(self):
        self.failure_count += 1
        self.last_failure_time = datetime.now()
        
        if self.failure_count >= self.failure_threshold:
            self.state = "OPEN"

# Usage
model_circuit_breaker = CircuitBreaker()

async def call_model_service(payload):
    return await model_circuit_breaker.call(
        httpx_client.post,
        f"{MODEL_API_URL}/chat/completions",
        json=payload
    )
```

### Retry Logic

Implement exponential backoff for transient failures:

```python
import asyncio
import random

async def retry_with_backoff(func, max_retries=3, base_delay=1, max_delay=60):
    """Retry function with exponential backoff"""
    
    for attempt in range(max_retries):
        try:
            return await func()
        except Exception as e:
            if attempt == max_retries - 1:
                # Last attempt failed
                raise MCPError(
                    status_code=503,
                    error_type="service_unavailable",
                    message="Service unavailable after retries",
                    details={
                        "attempts": max_retries,
                        "last_error": str(e),
                        "suggestion": "Service may be experiencing issues"
                    }
                )
            
            # Calculate delay with jitter
            delay = min(base_delay * (2 ** attempt), max_delay)
            jitter = delay * 0.1 * random.random()
            await asyncio.sleep(delay + jitter)
            
            logger.warning(
                "Retrying after failure",
                attempt=attempt + 1,
                max_retries=max_retries,
                delay=delay,
                error=str(e)
            )

# Usage
async def make_model_request():
    async def _request():
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{MODEL_API_URL}/chat/completions",
                json=payload,
                timeout=30
            )
            response.raise_for_status()
            return response.json()
    
    return await retry_with_backoff(_request)
```

## Error Monitoring and Alerting

### Structured Error Logging

```python
import structlog

logger = structlog.get_logger()

def log_error(error_type: str, message: str, **context):
    """Log errors with consistent structure"""
    logger.error(
        "error_occurred",
        error_type=error_type,
        message=message,
        **context
    )

# Usage
try:
    result = await process_request()
except ValidationError as e:
    log_error(
        error_type="validation_error",
        message="Request validation failed",
        field=e.field,
        value=e.value,
        user_id=request.user_id
    )
    raise MCPError(
        status_code=400,
        error_type="validation_error",
        message=str(e)
    )
```

### Error Metrics

Track error patterns with Prometheus:

```python
from prometheus_client import Counter, Histogram

error_counter = Counter(
    'mcp_errors_total',
    'Total errors by type and service',
    ['service', 'error_type', 'status_code']
)

error_duration = Histogram(
    'mcp_error_handling_duration_seconds',
    'Time spent handling errors',
    ['service', 'error_type']
)

def track_error(service: str, error_type: str, status_code: int):
    error_counter.labels(
        service=service,
        error_type=error_type,
        status_code=status_code
    ).inc()
```

### Prometheus Alerts

```yaml
groups:
  - name: error_alerts
    rules:
      - alert: HighErrorRate
        expr: rate(mcp_errors_total[5m]) > 0.1
        for: 2m
        labels:
          severity: warning
        annotations:
          summary: "High error rate detected"
          description: "Error rate is {{ $value }} errors/sec"

      - alert: CriticalServiceError
        expr: rate(mcp_errors_total{status_code=~"5.."}[1m]) > 0.05
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Critical service errors detected"
          
      - alert: AuthenticationErrors
        expr: rate(mcp_errors_total{error_type="authentication_error"}[5m]) > 0.02
        for: 2m
        labels:
          severity: warning
        annotations:
          summary: "High authentication error rate"
```

## UI Error Handling

### React/Frontend Error Boundaries

```typescript
// Error boundary component
class APIErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    console.error('API Error:', error, errorInfo);
    
    // Send error to monitoring service
    this.reportError(error, errorInfo);
  }

  reportError(error, errorInfo) {
    fetch('/api/errors', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        error: error.toString(),
        errorInfo,
        url: window.location.href,
        userAgent: navigator.userAgent,
        timestamp: new Date().toISOString()
      })
    });
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="error-fallback">
          <h2>Something went wrong</h2>
          <p>We're working to fix this issue.</p>
          <button onClick={() => window.location.reload()}>
            Retry
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}

// API error handling
async function makeAPIRequest(url, options = {}) {
  try {
    const response = await fetch(url, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options.headers
      }
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new APIError(response.status, errorData.error);
    }

    return await response.json();
    
  } catch (error) {
    if (error instanceof APIError) {
      // Handle known API errors
      handleAPIError(error);
      throw error;
    } else {
      // Handle network or other errors
      console.error('Network error:', error);
      throw new APIError(500, {
        type: 'network_error',
        message: 'Unable to connect to the service'
      });
    }
  }
}

class APIError extends Error {
  constructor(status, errorData) {
    super(errorData.message);
    this.status = status;
    this.type = errorData.type;
    this.details = errorData.details;
  }
}

function handleAPIError(error) {
  switch (error.type) {
    case 'validation_error':
      showValidationError(error);
      break;
    case 'rate_limit_exceeded':
      showRateLimitError(error);
      break;
    case 'model_not_found':
      showModelNotFoundError(error);
      break;
    default:
      showGenericError(error);
  }
}
```

## Best Practices Summary

1. **Consistent Error Format**: Use standardized error response structure
2. **Detailed Error Information**: Provide actionable error details
3. **Error Classification**: Categorize errors by type and severity
4. **Graceful Degradation**: Continue operation when possible
5. **Retry Logic**: Implement appropriate retry mechanisms
6. **Circuit Breakers**: Prevent cascade failures
7. **Monitoring**: Track error patterns and rates
8. **User Experience**: Provide helpful error messages
9. **Security**: Don't expose sensitive information in errors
10. **Recovery**: Implement automatic recovery where possible

## Testing Error Scenarios

```python
# pytest examples for error handling
import pytest
from fastapi.testclient import TestClient

def test_validation_error():
    response = client.post("/api/chat/completions", json={})
    assert response.status_code == 400
    error = response.json()["error"]
    assert error["type"] == "validation_error"
    assert "messages" in error["details"]["field"]

def test_model_not_found():
    response = client.post(
        "/api/chat/completions",
        json={"messages": [{"role": "user", "content": "test"}], "model": "nonexistent"}
    )
    assert response.status_code == 404
    error = response.json()["error"]
    assert error["type"] == "model_not_found"
    assert "nonexistent" in error["details"]["model"]

def test_rate_limiting():
    # Make requests until rate limited
    for _ in range(100):
        response = client.post("/api/chat/completions", json=valid_payload)
        if response.status_code == 429:
            error = response.json()["error"]
            assert error["type"] == "rate_limit_exceeded"
            assert "retry_after" in error["details"]
            break
    else:
        pytest.fail("Rate limiting not triggered")
```

This error handling strategy ensures consistent, informative, and recoverable error management across the entire MCP Stack.
