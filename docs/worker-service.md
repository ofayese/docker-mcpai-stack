# MCP Worker Service Documentation

The MCP Worker Service is a background task processor that handles asynchronous operations for the MCP AI Stack. It provides a scalable way to process tasks that don't need immediate responses, such as vector indexing, model caching, and data cleanup.

## Architecture

The worker service is built using Python's asyncio framework and includes:

- **Task Queue**: Async queue for managing background tasks
- **Task Processors**: Handlers for different types of tasks
- **Metrics**: Prometheus metrics for monitoring task processing
- **Health Checks**: Periodic health monitoring
- **Graceful Shutdown**: Proper cleanup on service termination

## Task Types

### 1. Vector Index Tasks (`vector_index`)

Handles vector database operations such as:

- Indexing new documents
- Updating existing vectors
- Batch processing of embeddings

```python
task = Task(
    id="vector-index-123",
    type="vector_index",
    payload={
        "documents": [...],
        "collection": "documents",
        "batch_size": 100
    },
    created_at=datetime.now()
)
```

### 2. Model Cache Tasks (`model_cache`)

Manages model caching operations:

- Pre-loading models into memory
- Model warmup procedures
- Cache eviction policies

```python
task = Task(
    id="model-cache-456",
    type="model_cache",
    payload={
        "model_id": "llama3-8b",
        "operation": "preload",
        "priority": "high"
    },
    created_at=datetime.now()
)
```

### 3. Data Cleanup Tasks (`data_cleanup`)

Performs maintenance operations:

- Cleaning temporary files
- Removing expired cache entries
- Database maintenance

```python
task = Task(
    id="cleanup-789",
    type="data_cleanup",
    payload={
        "target": "temp_files",
        "older_than": "24h"
    },
    created_at=datetime.now()
)
```

### 4. Health Check Tasks (`health_check`)

Internal health monitoring:

- Service connectivity checks
- Resource usage monitoring
- System health validation

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `ENVIRONMENT` | `production` | Runtime environment |
| `LOG_LEVEL` | `INFO` | Logging level |
| `METRICS_PORT` | `9090` | Prometheus metrics port |
| `WORKER_CONCURRENCY` | `4` | Number of concurrent tasks |
| `TASK_TIMEOUT` | `300` | Task timeout in seconds |
| `HEALTH_CHECK_INTERVAL` | `30` | Health check interval in seconds |

### Docker Configuration

The worker service is configured in `docker-compose.yml`:

```yaml
mcp-worker:
  build:
    context: ./services/mcp-worker
  environment:
    - ENVIRONMENT=${ENVIRONMENT:-production}
    - LOG_LEVEL=${LOG_LEVEL:-INFO}
    - METRICS_PORT=${METRICS_PORT:-9090}
  volumes:
    - mcp_data:/data
    - worker_temp:/tmp
  restart: unless-stopped
  healthcheck:
    test: ["CMD", "curl", "-f", "http://localhost:9090/metrics"]
    interval: 30s
    timeout: 10s
    retries: 3
```

## Metrics

The worker service exposes Prometheus metrics:

### Counters

- `mcp_worker_tasks_processed_total{task_type, status}`: Total tasks processed
- `mcp_worker_tasks_failed_total{task_type}`: Total failed tasks

### Histograms

- `mcp_worker_task_duration_seconds{task_type}`: Task processing duration

### Gauges

- `mcp_worker_active_tasks`: Number of currently active tasks
- `mcp_worker_health`: Worker health status (1=healthy, 0=unhealthy)

## Usage

### Adding Custom Task Types

1. **Create a Task Handler**:

```python
async def _handle_custom_task(self, task: Task) -> bool:
    try:
        logger.info("Processing custom task", task_id=task.id, payload=task.payload)
        
        # Your custom logic here
        result = await your_custom_function(task.payload)
        
        logger.info("Custom task completed", task_id=task.id, result=result)
        return True
        
    except Exception as e:
        logger.error("Custom task failed", task_id=task.id, error=str(e))
        return False
```

2. **Register the Handler**:

```python
def register_handlers(self):
    self.handlers = {
        # ... existing handlers ...
        'custom_task': self._handle_custom_task,
    }
```

### Submitting Tasks

Tasks can be submitted via the API or internal service calls:

```python
# Example: Submit a task via HTTP API (if implemented)
async with httpx.AsyncClient() as client:
    response = await client.post(
        "http://mcp-worker:8000/tasks",
        json={
            "type": "vector_index",
            "payload": {"documents": [...]}
        }
    )
```

## Monitoring

### Health Checks

The worker performs periodic health checks:

- Every 30 seconds (configurable)
- Updates health metrics
- Logs health status

### Log Analysis

Structured logs include:

```json
{
    "timestamp": "2024-01-15T10:30:00Z",
    "level": "info",
    "event": "task_processed",
    "task_id": "vector-index-123",
    "task_type": "vector_index",
    "duration": 2.5,
    "status": "success"
}
```

### Alerting

Recommended Prometheus alerts:

```yaml
# High task failure rate
- alert: WorkerHighFailureRate
  expr: rate(mcp_worker_tasks_processed_total{status="failed"}[5m]) > 0.1
  for: 2m
  labels:
    severity: warning
  annotations:
    summary: "High task failure rate in MCP Worker"

# Worker unhealthy
- alert: WorkerUnhealthy
  expr: mcp_worker_health == 0
  for: 1m
  labels:
    severity: critical
  annotations:
    summary: "MCP Worker is unhealthy"

# Task processing latency
- alert: WorkerHighLatency
  expr: histogram_quantile(0.95, mcp_worker_task_duration_seconds) > 30
  for: 5m
  labels:
    severity: warning
  annotations:
    summary: "High task processing latency"
```

## Development

### Local Development

1. **Start in Development Mode**:

```bash
cd services/mcp-worker
python -m src.worker --reload
```

2. **Run Tests**:

```bash
pytest tests/worker/
```

3. **Check Metrics**:

```bash
curl http://localhost:9090/metrics
```

### Debugging

Enable debug logging:

```bash
export LOG_LEVEL=DEBUG
python -m src.worker
```

Debug logs include:

- Task queue status
- Handler execution details
- Resource usage information

## Production Deployment

### Scaling

Scale workers horizontally:

```yaml
mcp-worker:
  deploy:
    replicas: 3
    resources:
      limits:
        cpus: '1.0'
        memory: 1G
```

### Resource Management

Configure appropriate limits:

- CPU: 1-2 cores per worker
- Memory: 1-2GB per worker
- Storage: Adequate temp space for tasks

### Backup and Recovery

Worker state is generally transient, but consider:

- Task queue persistence (if using external queue)
- Metrics data backup
- Configuration backup

## Troubleshooting

### Common Issues

1. **Worker Not Starting**:
   - Check Python dependencies
   - Verify environment variables
   - Check port availability

2. **Tasks Failing**:
   - Review task payload format
   - Check resource availability
   - Verify external service connectivity

3. **High Memory Usage**:
   - Reduce worker concurrency
   - Implement task payload limits
   - Add memory monitoring

### Debug Commands

```bash
# Check worker status
docker-compose ps mcp-worker

# View worker logs
docker-compose logs -f mcp-worker

# Check metrics
curl http://localhost:9090/metrics | grep mcp_worker

# Monitor resource usage
docker stats mcp-worker
```

For additional support, check the troubleshooting guide or open an issue in the repository.
