# Performance Optimization Guide

This guide covers performance optimization strategies for the MCPAI Docker Stack across different components and deployment scenarios.

## System-Level Optimizations

### 1. Operating System Tuning

#### Kernel Parameters

```bash
# /etc/sysctl.conf optimizations
vm.swappiness=10                    # Reduce swapping
vm.max_map_count=262144            # For memory mapping
vm.dirty_ratio=15                  # Dirty page cache ratio
vm.dirty_background_ratio=5        # Background dirty pages
net.core.rmem_max=16777216         # Network buffer sizes
net.core.wmem_max=16777216
net.ipv4.tcp_rmem=4096 87380 16777216
net.ipv4.tcp_wmem=4096 65536 16777216
net.ipv4.tcp_congestion_control=bbr # Better congestion control
fs.file-max=2097152                # Max open files
```

#### CPU Governor

```bash
# Set CPU governor to performance
echo performance | sudo tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor
```

#### NUMA Configuration

```bash
# For multi-socket systems
echo never | sudo tee /sys/kernel/mm/transparent_hugepage/enabled
echo never | sudo tee /sys/kernel/mm/transparent_hugepage/defrag
```

### 2. Docker Optimization

#### Docker Daemon Configuration

```json
{
  "storage-driver": "overlay2",
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  },
  "default-ulimits": {
    "nofile": {
      "hard": 65536,
      "soft": 65536
    }
  },
  "exec-opts": ["native.cgroupdriver=systemd"],
  "live-restore": true,
  "experimental": false,
  "metrics-addr": "127.0.0.1:9323",
  "data-root": "/var/lib/docker"
}
```

## Application Performance

### 1. API Service Optimization

#### FastAPI Configuration

```python
# In main.py
app = FastAPI(
    title="MCPAI API",
    debug=False,  # Disable in production
    docs_url=None,  # Disable docs in production
    redoc_url=None,  # Disable redoc in production
)

# Use uvicorn with optimized settings
uvicorn.run(
    app,
    host="0.0.0.0",
    port=8000,
    workers=4,  # Adjust based on CPU cores
    loop="uvloop",  # Faster event loop
    http="httptools",  # Faster HTTP parser
    access_log=False,  # Disable access logs in production
    log_level="warning"
)
```

#### Connection Pooling

```python
# Database connection pooling
DATABASE_URL = "postgresql+asyncpg://user:pass@host:5432/db?pool_size=20&max_overflow=0"

# Redis connection pooling
redis_pool = redis.ConnectionPool(
    host='redis',
    port=6379,
    db=0,
    max_connections=100,
    retry_on_timeout=True
)
```

#### Caching Strategy

```python
# Multi-level caching
@lru_cache(maxsize=1000)
def expensive_computation(input_data):
    # Application-level cache
    pass

# Redis for distributed caching
async def get_cached_result(key: str):
    cached = await redis.get(key)
    if cached:
        return json.loads(cached)
    
    result = await compute_result()
    await redis.setex(key, 3600, json.dumps(result))
    return result
```

### 2. Database Optimization

#### PostgreSQL Configuration

```sql
-- postgresql.conf optimizations
shared_buffers = '4GB'                    -- 25% of total RAM
effective_cache_size = '12GB'             -- 75% of total RAM
work_mem = '256MB'                        -- Per query work memory
maintenance_work_mem = '1GB'              -- Maintenance operations
checkpoint_completion_target = 0.9        -- Checkpoint timing
wal_buffers = '64MB'                      -- WAL buffer size
default_statistics_target = 100           -- Query planner statistics
random_page_cost = 1.1                    -- SSD optimization
effective_io_concurrency = 200            -- SSD optimization
max_worker_processes = 8                  -- Parallel workers
max_parallel_workers_per_gather = 4       -- Parallel query workers
max_parallel_workers = 8                  -- Max parallel workers
max_parallel_maintenance_workers = 4      -- Maintenance workers
```

#### Index Optimization

```sql
-- Create appropriate indexes
CREATE INDEX CONCURRENTLY idx_requests_created_at ON requests(created_at);
CREATE INDEX CONCURRENTLY idx_responses_request_id ON responses(request_id);
CREATE INDEX CONCURRENTLY idx_users_email ON users(email) WHERE active = true;

-- Partial indexes for better performance
CREATE INDEX CONCURRENTLY idx_active_sessions 
ON sessions(user_id) 
WHERE expires_at > NOW();

-- Composite indexes for complex queries
CREATE INDEX CONCURRENTLY idx_requests_status_created 
ON requests(status, created_at DESC);
```

#### Query Optimization

```sql
-- Use EXPLAIN ANALYZE to optimize queries
EXPLAIN (ANALYZE, BUFFERS) 
SELECT * FROM requests 
WHERE status = 'pending' 
ORDER BY created_at 
LIMIT 10;

-- Optimize with CTEs and window functions
WITH recent_requests AS (
    SELECT request_id, created_at,
           ROW_NUMBER() OVER (ORDER BY created_at DESC) as rn
    FROM requests 
    WHERE created_at > NOW() - INTERVAL '1 hour'
)
SELECT * FROM recent_requests WHERE rn <= 100;
```

### 3. Redis Configuration

#### Memory Optimization

```bash
# redis.conf optimizations
maxmemory 8gb                           # Set memory limit
maxmemory-policy allkeys-lru           # Eviction policy
save 900 1                             # Persistence settings
save 300 10
save 60 10000
tcp-keepalive 60                       # TCP keepalive
timeout 300                            # Client timeout
tcp-backlog 511                        # TCP listen backlog
```

#### Data Structure Optimization

```python
# Use efficient data structures
# Hash for small objects
redis.hset("user:1", mapping={"name": "John", "email": "john@example.com"})

# Sorted sets for rankings
redis.zadd("leaderboard", {"user1": 100, "user2": 95})

# Sets for unique collections
redis.sadd("online_users", "user1", "user2")

# Lists for queues
redis.lpush("task_queue", task_data)
```

## Container Optimization

### 1. Resource Limits

#### Memory Optimization

```yaml
# docker-compose.yml
services:
  mcp-api:
    deploy:
      resources:
        limits:
          memory: 2G
        reservations:
          memory: 1G
    environment:
      - PYTHONMALLOC=malloc  # Use system malloc
      - MALLOC_ARENA_MAX=2   # Limit malloc arenas
```

#### CPU Optimization

```yaml
services:
  model-runner:
    deploy:
      resources:
        limits:
          cpus: '4.0'
        reservations:
          cpus: '2.0'
    cpuset: "0-3"  # Pin to specific CPU cores
```

### 2. Image Optimization

#### Multi-stage Builds

```dockerfile
# Optimized Dockerfile
FROM python:3.11-slim as builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

FROM python:3.11-slim
WORKDIR /app
COPY --from=builder /root/.local /root/.local
COPY . .
ENV PATH=/root/.local/bin:$PATH
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

#### Layer Optimization

```dockerfile
# Minimize layers and use .dockerignore
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && \
    pip cache purge && \
    rm -rf /tmp/*

# Use specific base images
FROM python:3.11-slim  # Instead of python:3.11
```

## Network Performance

### 1. Load Balancing

#### Traefik Configuration

```yaml
# traefik dynamic config
http:
  services:
    api-service:
      loadBalancer:
        healthCheck:
          path: /health
          interval: 30s
          timeout: 10s
        servers:
          - url: "http://api1:8000"
          - url: "http://api2:8000"
          - url: "http://api3:8000"
```

#### Connection Pooling

```python
# HTTP client optimization
import aiohttp

connector = aiohttp.TCPConnector(
    limit=100,              # Total connection pool size
    limit_per_host=30,      # Per-host connection limit
    keepalive_timeout=30,   # Keep connections alive
    enable_cleanup_closed=True
)

session = aiohttp.ClientSession(
    connector=connector,
    timeout=aiohttp.ClientTimeout(total=30)
)
```

### 2. Network Tuning

#### TCP Optimization

```bash
# Network stack tuning
net.core.netdev_max_backlog=5000
net.ipv4.tcp_fin_timeout=30
net.ipv4.tcp_keepalive_time=1200
net.ipv4.tcp_max_syn_backlog=8192
net.ipv4.tcp_max_tw_buckets=5000
net.ipv4.tcp_fastopen=3
net.ipv4.tcp_mtu_probing=1
```

## GPU Optimization

### 1. Model Runner Performance

#### CUDA Configuration

```python
# CUDA memory management
import torch

# Set memory growth
torch.cuda.set_per_process_memory_fraction(0.8)
torch.cuda.empty_cache()

# Enable TensorFloat-32 for A100
torch.backends.cuda.matmul.allow_tf32 = True
torch.backends.cudnn.allow_tf32 = True

# Use mixed precision
from torch.cuda.amp import GradScaler, autocast

scaler = GradScaler()
with autocast():
    outputs = model(inputs)
```

#### Model Optimization

```python
# Model compilation (PyTorch 2.0+)
model = torch.compile(model, mode="reduce-overhead")

# Quantization for inference
model = torch.quantization.quantize_dynamic(
    model, {torch.nn.Linear}, dtype=torch.qint8
)

# Batch inference
def batch_inference(inputs, batch_size=32):
    for i in range(0, len(inputs), batch_size):
        batch = inputs[i:i+batch_size]
        with torch.no_grad():
            yield model(batch)
```

### 2. Memory Management

#### GPU Memory Monitoring

```python
def monitor_gpu_memory():
    if torch.cuda.is_available():
        allocated = torch.cuda.memory_allocated()
        cached = torch.cuda.memory_reserved()
        total = torch.cuda.get_device_properties(0).total_memory
        
        print(f"Allocated: {allocated / 1e9:.2f} GB")
        print(f"Cached: {cached / 1e9:.2f} GB")
        print(f"Total: {total / 1e9:.2f} GB")
```

## Monitoring and Profiling

### 1. Application Profiling

#### Python Profiling

```python
import cProfile
import pstats
from line_profiler import LineProfiler

# Function profiling
def profile_function(func):
    profiler = LineProfiler()
    profiler.add_function(func)
    profiler.enable_by_count()
    result = func()
    profiler.disable_by_count()
    profiler.print_stats()
    return result

# Memory profiling
from memory_profiler import profile

@profile
def memory_intensive_function():
    # Function implementation
    pass
```

#### Database Query Analysis

```sql
-- Enable query logging
ALTER SYSTEM SET log_statement = 'all';
ALTER SYSTEM SET log_min_duration_statement = 1000;  -- Log slow queries

-- Analyze query performance
SELECT 
    query,
    calls,
    total_time,
    mean_time,
    rows
FROM pg_stat_statements 
ORDER BY total_time DESC 
LIMIT 10;
```

### 2. Performance Metrics

#### Custom Metrics

```python
from prometheus_client import Histogram, Counter, Gauge

# Request duration histogram
REQUEST_DURATION = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration',
    ['method', 'endpoint']
)

# Active connections gauge
ACTIVE_CONNECTIONS = Gauge(
    'active_connections_total',
    'Number of active connections'
)

# Error counter
ERROR_COUNTER = Counter(
    'errors_total',
    'Total number of errors',
    ['error_type']
)
```

## Load Testing

### 1. Locust Configuration

#### Performance Testing

```python
from locust import HttpUser, task, between

class APIUser(HttpUser):
    wait_time = between(1, 3)
    
    def on_start(self):
        # Setup test data
        self.auth_token = self.get_auth_token()
    
    @task(3)
    def get_health(self):
        self.client.get("/health")
    
    @task(2)
    def create_request(self):
        payload = {"data": "test"}
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        self.client.post("/api/requests", json=payload, headers=headers)
    
    @task(1)
    def heavy_computation(self):
        self.client.post("/api/compute", json={"complexity": "high"})
```

### 2. Stress Testing

#### System Limits

```bash
# Test system limits
ulimit -n 65536          # Open files
ulimit -u 32768          # User processes
echo 1 > /proc/sys/net/ipv4/tcp_tw_reuse  # Reuse TIME_WAIT sockets
```

## Performance Monitoring Dashboard

### 1. Key Metrics to Monitor

#### Application Metrics

- Request rate (requests/second)
- Response time percentiles (p50, p95, p99)
- Error rate (errors/total requests)
- Active connections
- Database connection pool usage
- Cache hit rates

#### System Metrics

- CPU utilization (per core)
- Memory usage (RSS, virtual)
- Disk I/O (read/write operations)
- Network I/O (bytes in/out)
- GPU utilization and memory

#### Business Metrics

- User sessions
- Model inference latency
- Queue depth
- Throughput (operations/minute)

### 2. Alerting Thresholds

#### Performance Alerts

```yaml
# Grafana alerting rules
- alert: HighResponseTime
  expr: histogram_quantile(0.95, http_request_duration_seconds) > 1.0
  for: 5m
  
- alert: HighErrorRate
  expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.1
  for: 2m
  
- alert: DatabaseSlowQueries
  expr: pg_stat_database_tup_returned / pg_stat_database_tup_fetched < 0.1
  for: 5m
```

## Optimization Checklist

### Pre-Production

- [ ] Load test with expected traffic
- [ ] Profile CPU and memory usage
- [ ] Optimize database queries
- [ ] Configure connection pooling
- [ ] Set up caching layers
- [ ] Tune container resources
- [ ] Enable monitoring and alerts

### Production

- [ ] Monitor key performance metrics
- [ ] Set up automated scaling
- [ ] Regular performance reviews
- [ ] Capacity planning
- [ ] Incident response procedures
- [ ] Performance regression testing
- [ ] Continuous optimization
