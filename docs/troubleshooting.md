# Troubleshooting Guide

This guide provides solutions for common issues encountered with the MCPAI Docker Stack.

## Quick Diagnostic Commands

### System Status Check

```bash
# Check all services status
make health-check

# View service logs
docker compose logs -f --tail=100

# Check resource usage
docker stats

# Check disk space
df -h

# Check memory usage
free -h
```

## Common Issues and Solutions

### 1. Container Startup Issues

#### Problem: Service fails to start

**Symptoms:**

- Container exits immediately
- Health checks fail
- Connection refused errors

**Diagnosis:**

```bash
# Check container status
docker compose ps

# View container logs
docker compose logs service-name

# Check container exit code
docker inspect container-name --format='{{.State.ExitCode}}'
```

**Solutions:**

```bash
# Fix permission issues
sudo chown -R 1000:1000 ./data

# Increase memory limits
# In docker-compose.yml
deploy:
  resources:
    limits:
      memory: 4G

# Check environment variables
docker compose config

# Rebuild containers
docker compose build --no-cache service-name
```

#### Problem: Out of disk space

**Symptoms:**

- "no space left on device" errors
- Container creation fails
- Database writes fail

**Diagnosis:**

```bash
# Check disk usage
df -h
du -sh /var/lib/docker/

# Check Docker system usage
docker system df
```

**Solutions:**

```bash
# Clean Docker system
docker system prune -a -f

# Remove unused volumes
docker volume prune -f

# Clean up logs
sudo journalctl --vacuum-time=3d

# Increase disk space or move Docker root
sudo systemctl stop docker
sudo mv /var/lib/docker /new/location/docker
sudo ln -s /new/location/docker /var/lib/docker
sudo systemctl start docker
```

### 2. Database Issues

#### Problem: PostgreSQL connection failed

**Symptoms:**

- "connection refused" errors
- Database not ready errors
- Authentication failures

**Diagnosis:**

```bash
# Check PostgreSQL status
docker compose exec postgres pg_isready -U admin -d mcp

# Check connection parameters
docker compose exec postgres psql -U admin -d mcp -c "SELECT version();"

# View PostgreSQL logs
docker compose logs postgres
```

**Solutions:**

```bash
# Reset database password
docker compose exec postgres psql -U admin -d mcp -c "ALTER USER admin PASSWORD 'new_password';"

# Recreate database
docker compose down postgres
docker volume rm docker-mcpai-stack_postgres_data
docker compose up -d postgres

# Check firewall/network
docker network ls
docker network inspect docker-mcpai-stack_default
```

#### Problem: Database performance issues

**Symptoms:**

- Slow query responses
- High CPU usage
- Connection pool exhaustion

**Diagnosis:**

```bash
# Check slow queries
docker compose exec postgres psql -U admin -d mcp -c "
SELECT query, calls, total_time, mean_time 
FROM pg_stat_statements 
ORDER BY total_time DESC 
LIMIT 10;"

# Check active connections
docker compose exec postgres psql -U admin -d mcp -c "
SELECT count(*) as active_connections 
FROM pg_stat_activity 
WHERE state = 'active';"
```

**Solutions:**

```bash
# Analyze and optimize queries
docker compose exec postgres psql -U admin -d mcp -c "
EXPLAIN ANALYZE SELECT * FROM your_table WHERE conditions;"

# Increase connection limits
# In docker-compose.yml environment:
- POSTGRES_MAX_CONNECTIONS=200

# Add database indexes
docker compose exec postgres psql -U admin -d mcp -c "
CREATE INDEX CONCURRENTLY idx_table_column ON table_name(column_name);"
```

### 3. API Service Issues

#### Problem: High response times

**Symptoms:**

- API responses > 1 second
- Timeout errors
- Queue buildup

**Diagnosis:**

```bash
# Check API metrics
curl http://localhost:4000/metrics | grep http_request_duration

# Monitor resource usage
docker stats mcpai-api

# Check for memory leaks
docker exec mcpai-api ps aux
```

**Solutions:**

```bash
# Increase worker processes
# In Dockerfile or compose environment:
- WORKERS=4
- WORKER_CLASS=uvicorn.workers.UvicornWorker

# Enable connection pooling
# In application code:
DATABASE_URL="postgresql+asyncpg://user:pass@host:5432/db?pool_size=20"

# Add caching
# Redis configuration in compose
redis:
  image: redis:7-alpine
  command: redis-server --maxmemory 1gb --maxmemory-policy allkeys-lru
```

#### Problem: Memory leaks

**Symptoms:**

- Increasing memory usage over time
- OOM (Out of Memory) errors
- Container restarts

**Diagnosis:**

```bash
# Monitor memory usage over time
docker exec mcpai-api cat /proc/meminfo

# Python memory profiling
docker exec mcpai-api python -c "
import psutil
import os
process = psutil.Process(os.getpid())
print(f'Memory: {process.memory_info().rss / 1024 / 1024:.2f} MB')
"
```

**Solutions:**

```bash
# Add memory limits
# In docker-compose.yml:
deploy:
  resources:
    limits:
      memory: 2G

# Use memory profiling tools
pip install memory-profiler
python -m memory_profiler your_script.py

# Implement periodic restarts
restart: unless-stopped
```

### 4. GPU Issues

#### Problem: CUDA out of memory

**Symptoms:**

- "CUDA out of memory" errors
- Model loading fails
- Inference requests timeout

**Diagnosis:**

```bash
# Check GPU usage
nvidia-smi

# Monitor GPU memory
docker exec model-runner nvidia-smi --query-gpu=memory.used,memory.free,memory.total --format=csv
```

**Solutions:**

```bash
# Reduce batch size
# In model configuration:
BATCH_SIZE=1
MAX_SEQUENCE_LENGTH=512

# Enable gradient checkpointing
# In model code:
model.gradient_checkpointing_enable()

# Use CPU fallback
# In environment:
CUDA_VISIBLE_DEVICES=""  # Force CPU usage
```

#### Problem: GPU not accessible

**Symptoms:**

- "NVIDIA-SMI has failed" errors
- GPU not detected in container
- CUDA initialization failed

**Diagnosis:**

```bash
# Check host GPU
nvidia-smi

# Check Docker GPU support
docker run --rm --gpus all nvidia/cuda:11.0-base nvidia-smi

# Check container GPU access
docker exec model-runner nvidia-smi
```

**Solutions:**

```bash
# Install nvidia-docker2
curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | sudo tee /etc/apt/sources.list.d/nvidia-docker.list
sudo apt-get update && sudo apt-get install -y nvidia-docker2
sudo systemctl restart docker

# Update docker-compose.yml
services:
  model-runner:
    runtime: nvidia
    environment:
      - NVIDIA_VISIBLE_DEVICES=all
```

### 5. Network Issues

#### Problem: Service communication failures

**Symptoms:**

- "connection refused" between services
- Intermittent connectivity
- DNS resolution failures

**Diagnosis:**

```bash
# Test service connectivity
docker compose exec mcp-api ping postgres
docker compose exec mcp-api nslookup postgres

# Check network configuration
docker network ls
docker network inspect docker-mcpai-stack_default

# Check port bindings
docker compose ps
netstat -tlnp | grep :5432
```

**Solutions:**

```bash
# Recreate network
docker compose down
docker network prune
docker compose up -d

# Use explicit network configuration
networks:
  mcpai-network:
    driver: bridge
    ipam:
      config:
        - subnet: 172.20.0.0/16

# Check firewall rules
sudo ufw status
sudo iptables -L
```

#### Problem: External connectivity issues

**Symptoms:**

- Cannot reach external APIs
- DNS resolution fails
- SSL certificate errors

**Diagnosis:**

```bash
# Test external connectivity
docker compose exec mcp-api ping 8.8.8.8
docker compose exec mcp-api nslookup google.com
docker compose exec mcp-api curl -I https://api.github.com
```

**Solutions:**

```bash
# Configure DNS
# In docker-compose.yml:
services:
  mcp-api:
    dns:
      - 8.8.8.8
      - 1.1.1.1

# Add proxy configuration if needed
environment:
  - HTTP_PROXY=http://proxy:8080
  - HTTPS_PROXY=http://proxy:8080
  - NO_PROXY=localhost,127.0.0.1,postgres,redis
```

### 6. Monitoring Issues

#### Problem: Prometheus not collecting metrics

**Symptoms:**

- Empty dashboards in Grafana
- Missing metrics data
- Scrape failures

**Diagnosis:**

```bash
# Check Prometheus targets
curl http://localhost:9090/api/v1/targets

# Check service metrics endpoints
curl http://localhost:4000/metrics

# View Prometheus logs
docker compose logs prometheus
```

**Solutions:**

```bash
# Fix service discovery
# In prometheus.yml:
scrape_configs:
  - job_name: 'mcp-api'
    static_configs:
      - targets: ['mcp-api:8000']
    metrics_path: '/metrics'

# Restart Prometheus
docker compose restart prometheus

# Check network connectivity
docker compose exec prometheus ping mcp-api
```

#### Problem: Grafana dashboard not loading

**Symptoms:**

- Blank dashboards
- "No data" messages
- Datasource connection errors

**Diagnosis:**

```bash
# Check Grafana logs
docker compose logs grafana

# Test datasource connection
curl -u admin:admin http://localhost:3000/api/datasources/proxy/1/api/v1/query?query=up
```

**Solutions:**

```bash
# Recreate datasource configuration
# In grafana/datasources/prometheus.yaml:
apiVersion: 1
datasources:
  - name: Prometheus
    type: prometheus
    url: http://prometheus:9090
    access: proxy

# Import dashboards manually
curl -X POST \
  http://admin:admin@localhost:3000/api/dashboards/db \
  -H 'Content-Type: application/json' \
  -d @grafana/dashboards/dashboard.json
```

### 7. Performance Issues

#### Problem: High CPU usage

**Symptoms:**

- System slowdown
- Request timeouts
- High load averages

**Diagnosis:**

```bash
# Check CPU usage by container
docker stats --no-stream

# Check system load
uptime
top -c

# Profile application
docker exec mcp-api python -m cProfile -o profile.stats your_script.py
```

**Solutions:**

```bash
# Limit CPU usage
# In docker-compose.yml:
deploy:
  resources:
    limits:
      cpus: '2.0'

# Optimize application code
# Use async/await patterns
# Implement connection pooling
# Add caching layers

# Scale horizontally
docker compose up -d --scale mcp-api=3
```

## Log Analysis

### Centralized Logging

```bash
# View all logs with timestamps
docker compose logs -f -t

# Filter logs by service
docker compose logs -f mcp-api

# Search logs for errors
docker compose logs | grep -i error

# Follow logs for specific time range
docker compose logs --since="2024-01-01T00:00:00Z" --until="2024-01-01T23:59:59Z"
```

### Log Patterns to Monitor

```bash
# Error patterns
grep -E "(ERROR|FATAL|Exception|Failed)" logs/*

# Performance patterns
grep -E "(slow|timeout|performance)" logs/*

# Security patterns
grep -E "(unauthorized|forbidden|failed login)" logs/*
```

## Emergency Procedures

### Service Recovery

```bash
# Quick restart all services
docker compose restart

# Force recreate problematic service
docker compose up -d --force-recreate mcp-api

# Rollback to previous version
docker compose down
docker tag mcpai-api:latest mcpai-api:backup
docker pull mcpai-api:previous
docker compose up -d
```

### Data Recovery

```bash
# Restore from backup
./scripts/restore.sh /backups/latest

# Database point-in-time recovery
docker compose exec postgres pg_basebackup -U admin -D /backup -Ft -z -P

# Volume recovery
docker volume create --name postgres_data_recovery
docker run --rm -v postgres_data_recovery:/recovery alpine cp -r /backup/* /recovery/
```

### System Recovery

```bash
# Free up disk space quickly
docker system prune -a -f --volumes
sudo journalctl --vacuum-time=1d
sudo apt-get clean

# Kill runaway processes
docker compose down
docker kill $(docker ps -q)
docker system prune -f

# Restart Docker daemon
sudo systemctl restart docker
```

## Prevention Strategies

### Monitoring Setup

1. Set up comprehensive alerts
2. Monitor resource usage trends
3. Regular health checks
4. Performance benchmarking

### Maintenance Schedule

```bash
# Weekly tasks
- Update system packages
- Review logs for patterns
- Check disk space
- Verify backups

# Monthly tasks
- Update Docker images
- Security scan
- Performance review
- Capacity planning
```

### Documentation

1. Keep runbooks updated
2. Document configuration changes
3. Maintain troubleshooting history
4. Share knowledge with team

## Getting Help

### Community Resources

- GitHub Issues: [Project Repository](https://github.com/your-org/docker-mcpai-stack)
- Documentation: [Wiki Pages](https://github.com/your-org/docker-mcpai-stack/wiki)
- Discussions: [Community Forum](https://github.com/your-org/docker-mcpai-stack/discussions)

### Support Channels

- Email: <support@your-domain.com>
- Slack: #mcpai-support
- Emergency: <oncall@your-domain.com>

### Diagnostic Information to Collect

When reporting issues, include:

```bash
# System information
uname -a
docker --version
docker compose version

# Service status
docker compose ps
docker compose logs --tail=100

# Resource usage
docker stats --no-stream
df -h
free -h

# Configuration
docker compose config
env | grep -E "(POSTGRES|REDIS|API)"
```
