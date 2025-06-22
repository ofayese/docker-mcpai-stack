"""
Monitoring and metrics setup
"""

import os
import platform
import time
from prometheus_client import Counter, Histogram, Gauge, Info

# Define metrics

# Request metrics
request_count = Counter(
    'mcp_api_requests_total',
    'Total API requests',
    ['method', 'endpoint', 'status']
)

request_duration = Histogram(
    'mcp_api_request_duration_seconds',
    'Request duration in seconds',
    ['method', 'endpoint'],
    buckets=(
        0.01, 0.025, 0.05, 0.075, 0.1,
        0.25, 0.5, 0.75, 1.0,
        2.5, 5.0, 7.5, 10.0
    )
)

# Model metrics
model_inference_count = Counter(
    'mcp_model_inferences_total',
    'Total model inference requests',
    ['model_id', 'status']
)

model_inference_duration = Histogram(
    'mcp_model_inference_duration_seconds',
    'Model inference duration in seconds',
    ['model_id'],
    buckets=(
        0.1, 0.5, 1.0, 2.0,
        5.0, 10.0, 20.0,
        30.0, 60.0
    )
)

# System metrics
active_requests = Gauge(
    'mcp_api_active_requests',
    'Number of active requests being processed'
)

system_info = Info(
    'mcp_api_system_info',
    'System information about the MCP API'
)


def setup_metrics():
    """Initialize metrics with system information."""
    system_info.info({
        'version': os.getenv('VERSION', 'unknown'),
        'python_version': platform.python_version(),
        'platform': platform.platform(),
        'cpu_count': str(os.cpu_count())
    })



def get_metrics():
    """
    Return a summary of key metrics as a JSON-serializable dict for UI display.
    """
    metrics = {}
    metrics['requests_total'] = request_count._value.get()
    metrics['active_requests'] = active_requests._value.get()
    metrics['model_inferences_total'] = model_inference_count._value.get()
    metrics['system_info'] = system_info._info
    return metrics


class MetricsMiddleware:
    """Middleware to track request metrics."""

    async def __call__(self, request, call_next):
        active_requests.inc()
        start_time = time.time()
        try:
            response = await call_next(request)
            status_code = response.status_code
            # Record request metrics
            request_count.labels(
                method=request.method,
                endpoint=request.url.path,
                status=status_code
            ).inc()
            request_duration.labels(
                method=request.method,
                endpoint=request.url.path
            ).observe(time.time() - start_time)
            return response
        except Exception as e:
            request_count.labels(
                method=request.method,
                endpoint=request.url.path,
                status=500
            ).inc()
            raise e
        finally:
            active_requests.dec()

