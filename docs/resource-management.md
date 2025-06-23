# Resource Management Configuration Guide

This guide provides recommendations for configuring resource limits, scaling, and performance optimization for the Docker MCP Stack.

## Current Resource Configuration

The stack includes the following resource limits defined in `compose/docker-compose.base.yml`:

### Model Runner

```yaml
deploy:
  resources:
    limits:
      memory: ${MODEL_MEMORY_LIMIT:-4g}
      cpus: "${MODEL_CPU_LIMIT:-2}"
    reservations:
      memory: 1g
      cpus: "0.5"
```

## Recommended Resource Configurations

### Development Environment

For local development with limited resources:

```bash
# .env configuration
MODEL_MEMORY_LIMIT=2g
MODEL_CPU_LIMIT=1
API_MEMORY_LIMIT=512m
API_CPU_LIMIT=0.5
WORKER_MEMORY_LIMIT=512m
WORKER_CPU_LIMIT=0.5
UI_MEMORY_LIMIT=256m
UI_CPU_LIMIT=0.25
```

### Production Environment (Small)

For production with moderate load:

```bash
# .env configuration
MODEL_MEMORY_LIMIT=8g
MODEL_CPU_LIMIT=4
API_MEMORY_LIMIT=1g
API_CPU_LIMIT=1
WORKER_MEMORY_LIMIT=1g
WORKER_CPU_LIMIT=1
UI_MEMORY_LIMIT=512m
UI_CPU_LIMIT=0.5
```

### Production Environment (Large)

For high-load production environments:

```bash
# .env configuration
MODEL_MEMORY_LIMIT=16g
MODEL_CPU_LIMIT=8
API_MEMORY_LIMIT=2g
API_CPU_LIMIT=2
WORKER_MEMORY_LIMIT=2g
WORKER_CPU_LIMIT=2
UI_MEMORY_LIMIT=1g
UI_CPU_LIMIT=1
```

## Dynamic Resource Scaling

### Connection Pool Management

#### API Service Connection Pooling

```python
# In services/mcp-api/src/core/config.py
class Settings(BaseSettings):
    # ... existing settings ...
    
    # Connection pool settings
    HTTP_POOL_CONNECTIONS: int = 100
    HTTP_POOL_MAXSIZE: int = 100
    HTTP_MAX_RETRIES: int = 3
    HTTP_TIMEOUT: int = 30
    
    # Rate limiting
    RATE_LIMIT_REQUESTS: int = 1000
    RATE_LIMIT_WINDOW: int = 3600  # 1 hour
    
    # Model-specific limits
    MAX_TOKENS_PER_REQUEST: int = 4096
    MAX_CONCURRENT_REQUESTS: int = 10

# Connection pool implementation
import httpx
from contextlib import asynccontextmanager

@asynccontextmanager
async def get_http_client():
    """Get HTTP client with connection pooling"""
    limits = httpx.Limits(
        max_keepalive_connections=settings.HTTP_POOL_CONNECTIONS,
        max_connections=settings.HTTP_POOL_MAXSIZE,
        keepalive_expiry=30.0
    )
    
    timeout = httpx.Timeout(
        connect=5.0,
        read=settings.HTTP_TIMEOUT,
        write=5.0,
        pool=1.0
    )
    
    async with httpx.AsyncClient(
        limits=limits,
        timeout=timeout,
        retries=settings.HTTP_MAX_RETRIES
    ) as client:
        yield client
```

#### Database Connection Pooling

```python
# For PostgreSQL connections
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.pool import QueuePool

engine = create_async_engine(
    settings.DATABASE_URL,
    poolclass=QueuePool,
    pool_size=20,
    max_overflow=30,
    pool_pre_ping=True,
    pool_recycle=300,
    echo=settings.DEBUG
)
```

### Memory Management

#### Model Memory Optimization

```python
# Model-specific memory configurations
MODEL_MEMORY_CONFIG = {
    "smollm2-1.7b": {
        "memory_limit": "2g",
        "context_length": 2048,
        "batch_size": 1
    },
    "llama3-8b": {
        "memory_limit": "8g", 
        "context_length": 4096,
        "batch_size": 1
    },
    "llama3-70b": {
        "memory_limit": "32g",
        "context_length": 4096,
        "batch_size": 1
    }
}

def get_model_memory_limit(model_id: str) -> str:
    """Get memory limit for specific model"""
    config = MODEL_MEMORY_CONFIG.get(model_id, {})
    return config.get("memory_limit", "4g")
```

#### Garbage Collection Optimization

```python
# In worker service
import gc
import asyncio

class ResourceManager:
    """Manage memory and resources"""
    
    def __init__(self):
        self.gc_interval = 60  # seconds
        self.gc_task = None
    
    async def start_gc_monitoring(self):
        """Start garbage collection monitoring"""
        self.gc_task = asyncio.create_task(self._gc_loop())
    
    async def _gc_loop(self):
        """Periodic garbage collection"""
        while True:
            await asyncio.sleep(self.gc_interval)
            
            # Force garbage collection
            collected = gc.collect()
            
            if collected > 0:
                logger.info("Garbage collection", objects_collected=collected)
            
            # Check memory usage
            import psutil
            memory = psutil.virtual_memory()
            
            if memory.percent > 80:
                logger.warning("High memory usage", 
                             percent=memory.percent,
                             available_gb=memory.available / (1024**3))
```

## Performance Monitoring

### Resource Metrics Collection

```python
# Enhanced monitoring metrics
from prometheus_client import Gauge, Histogram

# Resource usage metrics
memory_usage = Gauge('mcp_service_memory_bytes', 'Memory usage in bytes', ['service'])
cpu_usage = Gauge('mcp_service_cpu_percent', 'CPU usage percentage', ['service'])
disk_usage = Gauge('mcp_service_disk_bytes', 'Disk usage in bytes', ['service', 'mount'])

# Connection pool metrics
connection_pool_size = Gauge('mcp_connection_pool_size', 'Connection pool size', ['service'])
connection_pool_active = Gauge('mcp_connection_pool_active', 'Active connections', ['service'])

# Model-specific metrics
model_memory_usage = Gauge('mcp_model_memory_bytes', 'Model memory usage', ['model_id'])
model_inference_queue = Gauge('mcp_model_inference_queue_size', 'Inference queue size', ['model_id'])

async def collect_resource_metrics():
    """Collect and update resource metrics"""
    import psutil
    import os
    
    # Memory usage
    process = psutil.Process(os.getpid())
    memory_info = process.memory_info()
    memory_usage.labels(service='mcp-api').set(memory_info.rss)
    
    # CPU usage
    cpu_percent = process.cpu_percent()
    cpu_usage.labels(service='mcp-api').set(cpu_percent)
    
    # Disk usage
    disk = psutil.disk_usage('/')
    disk_usage.labels(service='mcp-api', mount='/').set(disk.used)
```

### Alerting Configuration

```yaml
# Prometheus alerts for resource management
groups:
  - name: resource_alerts
    rules:
      - alert: HighMemoryUsage
        expr: mcp_service_memory_bytes / (1024^3) > 0.8 * ${MODEL_MEMORY_LIMIT}
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High memory usage detected"
          description: "Service {{ $labels.service }} using {{ $value }}GB memory"

      - alert: HighCPUUsage
        expr: mcp_service_cpu_percent > 80
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High CPU usage detected"
          description: "Service {{ $labels.service }} using {{ $value }}% CPU"

      - alert: DiskSpaceLow
        expr: (disk_free_bytes / disk_size_bytes) * 100 < 10
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "Low disk space"
          description: "Only {{ $value }}% disk space remaining"

      - alert: ConnectionPoolExhaustion
        expr: mcp_connection_pool_active / mcp_connection_pool_size > 0.9
        for: 1m
        labels:
          severity: warning
        annotations:
          summary: "Connection pool nearly exhausted"
          description: "{{ $value }}% of connection pool in use"
```

## Auto-scaling Configuration

### Docker Swarm Scaling

```yaml
# docker-compose.production.yml
version: "3.9"

services:
  mcp-api:
    deploy:
      replicas: 3
      update_config:
        parallelism: 1
        delay: 10s
        failure_action: rollback
      restart_policy:
        condition: on-failure
        delay: 5s
        max_attempts: 3
      resources:
        limits:
          memory: ${API_MEMORY_LIMIT:-1g}
          cpus: "${API_CPU_LIMIT:-1}"
        reservations:
          memory: 512m
          cpus: "0.5"

  mcp-worker:
    deploy:
      replicas: 2
      resources:
        limits:
          memory: ${WORKER_MEMORY_LIMIT:-1g}
          cpus: "${WORKER_CPU_LIMIT:-1}"
        reservations:
          memory: 512m
          cpus: "0.5"
```

### Kubernetes Horizontal Pod Autoscaler

```yaml
# k8s/hpa.yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: mcp-api-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: mcp-api
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
  behavior:
    scaleDown:
      stabilizationWindowSeconds: 300
      policies:
      - type: Pods
        value: 1
        periodSeconds: 60
    scaleUp:
      stabilizationWindowSeconds: 60
      policies:
      - type: Pods
        value: 2
        periodSeconds: 60
```

## Optimization Strategies

### 1. Model Loading Optimization

```python
# Lazy model loading
class ModelManager:
    def __init__(self):
        self.loaded_models = {}
        self.model_cache_size = 3
    
    async def load_model(self, model_id: str):
        """Load model with memory management"""
        if model_id in self.loaded_models:
            return self.loaded_models[model_id]
        
        # Check cache size
        if len(self.loaded_models) >= self.model_cache_size:
            # Evict least recently used model
            lru_model = min(self.loaded_models.items(), 
                          key=lambda x: x[1].last_used)
            del self.loaded_models[lru_model[0]]
            logger.info("Evicted model from cache", model=lru_model[0])
        
        # Load new model
        model = await self._load_model_impl(model_id)
        self.loaded_models[model_id] = model
        return model
```

### 2. Request Batching

```python
# Batch inference requests
class InferenceBatcher:
    def __init__(self, batch_size=4, timeout=0.1):
        self.batch_size = batch_size
        self.timeout = timeout
        self.pending_requests = []
    
    async def add_request(self, request):
        """Add request to batch"""
        future = asyncio.Future()
        self.pending_requests.append((request, future))
        
        if len(self.pending_requests) >= self.batch_size:
            await self._process_batch()
        
        return await future
    
    async def _process_batch(self):
        """Process accumulated requests"""
        if not self.pending_requests:
            return
        
        batch = self.pending_requests[:self.batch_size]
        self.pending_requests = self.pending_requests[self.batch_size:]
        
        requests = [req for req, _ in batch]
        futures = [fut for _, fut in batch]
        
        try:
            results = await self._batch_inference(requests)
            for future, result in zip(futures, results):
                future.set_result(result)
        except Exception as e:
            for future in futures:
                future.set_exception(e)
```

### 3. Caching Strategies

```python
# Response caching with TTL
import time
from typing import Dict, Any

class ResponseCache:
    def __init__(self, ttl=300):  # 5 minutes
        self.cache: Dict[str, tuple[Any, float]] = {}
        self.ttl = ttl
    
    def get(self, key: str) -> Any:
        """Get cached response"""
        if key in self.cache:
            value, timestamp = self.cache[key]
            if time.time() - timestamp < self.ttl:
                return value
            else:
                del self.cache[key]
        return None
    
    def set(self, key: str, value: Any):
        """Cache response"""
        self.cache[key] = (value, time.time())
    
    def generate_key(self, model: str, messages: list) -> str:
        """Generate cache key for request"""
        import hashlib
        content = f"{model}:{str(messages)}"
        return hashlib.md5(content.encode()).hexdigest()
```

## Resource Monitoring Dashboard

### Grafana Dashboard Configuration

```json
{
  "dashboard": {
    "title": "MCP Stack Resource Monitoring",
    "panels": [
      {
        "title": "Memory Usage by Service",
        "type": "graph",
        "targets": [
          {
            "expr": "mcp_service_memory_bytes / (1024^3)",
            "legendFormat": "{{ service }}"
          }
        ]
      },
      {
        "title": "CPU Usage by Service", 
        "type": "graph",
        "targets": [
          {
            "expr": "mcp_service_cpu_percent",
            "legendFormat": "{{ service }}"
          }
        ]
      },
      {
        "title": "Connection Pool Status",
        "type": "stat",
        "targets": [
          {
            "expr": "mcp_connection_pool_active / mcp_connection_pool_size * 100",
            "legendFormat": "Pool Utilization %"
          }
        ]
      }
    ]
  }
}
```

## Troubleshooting Resource Issues

### Memory Leaks

```bash
# Monitor memory growth
docker stats --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.MemPerc}}"

# Profile Python memory usage
pip install memory-profiler
python -m memory_profiler your_script.py

# Use py-spy for live profiling
pip install py-spy
py-spy top --pid <process_id>
```

### CPU Performance

```bash
# Monitor CPU usage
top -p $(docker inspect --format '{{.State.Pid}}' mcp-api)

# Profile with perf
perf top -p <process_id>

# Python profiling
python -m cProfile -o profile.stats your_script.py
```

### I/O Bottlenecks

```bash
# Monitor disk I/O
iotop -p $(docker inspect --format '{{.State.Pid}}' mcp-api)

# Check file descriptors
lsof -p <process_id> | wc -l

# Monitor network connections
netstat -an | grep :4000
```

This resource management configuration ensures optimal performance and scalability of the Docker MCP Stack across different deployment scenarios.
