"""Monitoring and metrics setup"""

import prometheus_client
from prometheus_client import Counter, Histogram, Gauge
from fastapi import FastAPI

# Define metrics
REQUEST_COUNT = Counter(
    'http_requests_total', 
    'Total HTTP Requests Count', 
    ['method', 'endpoint', 'status_code']
)

REQUEST_LATENCY = Histogram(
    'http_request_duration_seconds', 
    'HTTP Request Latency', 
    ['method', 'endpoint']
)

ACTIVE_REQUESTS = Gauge(
    'http_requests_active',
    'Active HTTP Requests',
    ['method', 'endpoint']
)

MODEL_INVOCATIONS = Counter(
    'model_invocations_total',
    'Total Model Invocation Count',
    ['model_name', 'status']
)

def setup_metrics(app: FastAPI):
    """Configure metrics for the FastAPI application"""
    # Expose metrics endpoint
    app.add_route("/metrics", prometheus_client.make_asgi_app())
    
    @app.middleware("http")
    async def monitor_requests(request, call_next):
        method = request.method
        path = request.url.path
        
        # Track active requests
        ACTIVE_REQUESTS.labels(method=method, endpoint=path).inc()
        
        # Track request latency
        with REQUEST_LATENCY.labels(method=method, endpoint=path).time():
            response = await call_next(request)
        
        # Track request count
        REQUEST_COUNT.labels(
            method=method, 
            endpoint=path, 
            status_code=response.status_code
        ).inc()
        
        # Decrease active requests
        ACTIVE_REQUESTS.labels(method=method, endpoint=path).dec()
        
        return response