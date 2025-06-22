# Production Deployment Guide

This guide covers deploying the MCPAI Docker Stack to production environments with security, monitoring, and high availability considerations.

## Prerequisites

### System Requirements

- Docker Engine 20.10+ with Docker Compose v2
- Linux host with kernel 4.15+ (Ubuntu 18.04+, CentOS 8+, RHEL 8+)
- Minimum 16GB RAM, 100GB storage, 8 CPU cores
- NVIDIA GPU with CUDA 11.8+ (for model inference)
- Valid domain name with DNS configuration

### Network Requirements

- Ports 80/443 open for HTTP/HTTPS traffic
- Internal network segmentation for services
- Firewall configuration for security
- SSL/TLS certificates (Let's Encrypt supported)

## Environment Configuration

### 1. Create Production Environment File

```bash
cp .env.example .env
```

### 2. Configure Required Variables

```bash
# Domain and SSL
DOMAIN=your-domain.com
ACME_EMAIL=admin@your-domain.com

# Container Registry
REGISTRY=your-registry.com
VERSION=v1.0.0

# Database Configuration
POSTGRES_DB=mcpai_prod
POSTGRES_USER=mcpai_user
POSTGRES_PASSWORD=secure_random_password_here
DATABASE_URL=postgresql://mcpai_user:secure_random_password_here@postgres:5432/mcpai_prod

# Redis Configuration
REDIS_PASSWORD=another_secure_password
REDIS_URL=redis://:another_secure_password@redis:6379

# API Security
SECRET_KEY=generate_strong_secret_key_here
CORS_ORIGINS=https://your-domain.com,https://api.your-domain.com

# Monitoring Credentials
GRAFANA_ADMIN_USER=admin
GRAFANA_ADMIN_PASSWORD=secure_grafana_password

# Alerting Configuration
SMTP_HOST=smtp.your-provider.com:587
SMTP_FROM=alerts@your-domain.com
SMTP_USER=your-smtp-user
SMTP_PASSWORD=your-smtp-password
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK

# Alert Recipients
DEFAULT_EMAIL=admin@your-domain.com
CRITICAL_EMAIL=oncall@your-domain.com
API_TEAM_EMAIL=api-team@your-domain.com
ML_TEAM_EMAIL=ml-team@your-domain.com
INFRA_TEAM_EMAIL=infra@your-domain.com

# Traefik Authentication (generate with htpasswd)
TRAEFIK_AUTH=admin:$2y$10$hashed_password_here

# Scaling Configuration
API_REPLICAS=3
GPU_MEMORY_FRACTION=0.8
CUDA_DEVICES=0,1
```

## Pre-Deployment Setup

### 1. Create Docker Network

```bash
docker network create web
```

### 2. Set Up SSL Certificates Directory

```bash
sudo mkdir -p /opt/mcpai/ssl
sudo chown 999:999 /opt/mcpai/ssl
```

### 3. Configure Log Rotation

```bash
sudo tee /etc/logrotate.d/mcpai << EOF
/var/lib/docker/containers/*/*.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
    create 0644 root root
}
EOF
```

### 4. Set Up Backup Storage

```bash
sudo mkdir -p /opt/mcpai/backups/{daily,weekly,monthly}
sudo chown -R 1000:1000 /opt/mcpai/backups
```

## Security Hardening

### 1. Docker Daemon Security

```bash
# Configure Docker daemon with security options
sudo tee /etc/docker/daemon.json << EOF
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  },
  "live-restore": true,
  "userland-proxy": false,
  "experimental": false,
  "metrics-addr": "127.0.0.1:9323",
  "default-ulimits": {
    "nofile": {
      "name": "nofile",
      "hard": 64000,
      "soft": 64000
    }
  }
}
EOF

sudo systemctl restart docker
```

### 2. Firewall Configuration

```bash
# UFW firewall rules
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw --force enable
```

### 3. System Limits

```bash
# Increase system limits
echo "* soft nofile 65536" | sudo tee -a /etc/security/limits.conf
echo "* hard nofile 65536" | sudo tee -a /etc/security/limits.conf
echo "vm.max_map_count=262144" | sudo tee -a /etc/sysctl.conf
sudo sysctl -p
```

## Deployment Process

### 1. Pull Latest Images

```bash
make pull-images
```

### 2. Run Security Scans

```bash
make security-scan
```

### 3. Deploy Infrastructure

```bash
# Deploy monitoring stack first
docker compose -f compose/docker-compose.monitoring.yml --profile monitoring up -d

# Deploy main application
docker compose -f compose/docker-compose.production.yml up -d
```

### 4. Verify Deployment

```bash
# Check service health
make health-check

# Verify all services are running
docker compose -f compose/docker-compose.production.yml ps

# Check logs for errors
docker compose -f compose/docker-compose.production.yml logs --tail=100
```

## Post-Deployment Configuration

### 1. Configure Monitoring Dashboards

1. Access Grafana at `https://grafana.your-domain.com`
2. Login with configured credentials
3. Verify all datasources are connected
4. Import additional dashboards as needed

### 2. Set Up Backup Jobs

```bash
# Add to crontab
0 2 * * * /opt/mcpai/scripts/backup.sh full
0 6,14,22 * * * /opt/mcpai/scripts/backup.sh incremental
```

### 3. Configure Log Aggregation

1. Verify Loki is collecting logs
2. Set up log retention policies
3. Configure log-based alerts

## Monitoring and Alerting

### Health Checks

The following endpoints provide health information:

- API Health: `https://api.your-domain.com/health`
- Prometheus: `https://prometheus.your-domain.com/-/healthy`
- Grafana: `https://grafana.your-domain.com/api/health`

### Critical Alerts

Ensure these alerts are configured and tested:

- Service Down alerts
- High error rate alerts
- Resource exhaustion alerts
- Security incident alerts

### Log Monitoring

Monitor these log patterns:

- Authentication failures
- API error responses (5xx)
- Database connection issues
- GPU utilization warnings

## Scaling and Performance

### Horizontal Scaling

```bash
# Scale API service
docker compose -f compose/docker-compose.production.yml up -d --scale mcp-api=5

# Scale with environment variable
API_REPLICAS=5 docker compose -f compose/docker-compose.production.yml up -d
```

### Performance Tuning

1. **Database Optimization**
   - Configure connection pooling
   - Tune PostgreSQL parameters
   - Monitor query performance

2. **Cache Optimization**
   - Adjust Redis memory limits
   - Configure cache TTL values
   - Monitor cache hit rates

3. **GPU Optimization**
   - Tune GPU memory allocation
   - Configure model batching
   - Monitor GPU utilization

## Backup and Recovery

### Automated Backups

```bash
# Full backup (daily at 2 AM)
0 2 * * * /opt/mcpai/scripts/backup.sh full

# Incremental backup (every 8 hours)
0 6,14,22 * * * /opt/mcpai/scripts/backup.sh incremental
```

### Recovery Procedures

1. **Database Recovery**

   ```bash
   ./scripts/restore.sh database backup_file.sql
   ```

2. **Complete System Recovery**

   ```bash
   ./scripts/restore.sh full backup_directory
   ```

3. **Rolling Back Deployment**

   ```bash
   VERSION=previous_version docker compose -f compose/docker-compose.production.yml up -d
   ```

## Maintenance Procedures

### Updates and Patches

1. **Security Updates**

   ```bash
   # Update base system
   sudo apt update && sudo apt upgrade -y
   
   # Update Docker images
   docker compose -f compose/docker-compose.production.yml pull
   docker compose -f compose/docker-compose.production.yml up -d
   ```

2. **Application Updates**

   ```bash
   # Deploy new version
   VERSION=v1.1.0 docker compose -f compose/docker-compose.production.yml up -d
   ```

### Log Management

```bash
# Clean old logs
docker system prune -f
docker volume prune -f

# Rotate application logs
sudo logrotate -f /etc/logrotate.d/mcpai
```

### Certificate Renewal

Certificates are automatically renewed by Traefik, but verify:

```bash
# Check certificate status
docker logs mcpai-traefik | grep -i certificate
```

## Troubleshooting

### Common Issues

1. **Service Won't Start**
   - Check logs: `docker compose logs service_name`
   - Verify environment variables
   - Check resource availability

2. **SSL Certificate Issues**
   - Verify DNS settings
   - Check Traefik logs
   - Ensure port 80 is accessible

3. **Database Connection Problems**
   - Check database logs
   - Verify credentials
   - Test connectivity

4. **Performance Issues**
   - Monitor resource usage
   - Check database queries
   - Review application logs

### Emergency Procedures

1. **Service Outage**

   ```bash
   # Quick restart
   docker compose -f compose/docker-compose.production.yml restart
   
   # Full rebuild if needed
   docker compose -f compose/docker-compose.production.yml down
   docker compose -f compose/docker-compose.production.yml up -d
   ```

2. **Security Incident**

   ```bash
   # Immediate isolation
   docker compose -f compose/docker-compose.production.yml down
   
   # Check for compromised containers
   docker system events
   ```

## Support and Contacts

### Emergency Contacts

- On-call Engineer: <oncall@your-domain.com>
- Security Team: <security@your-domain.com>
- Infrastructure Team: <infra@your-domain.com>

### Monitoring Dashboards

- Grafana: <https://grafana.your-domain.com>
- Prometheus: <https://prometheus.your-domain.com>
- Alertmanager: <https://alertmanager.your-domain.com>

### Documentation

- API Documentation: <https://api.your-domain.com/docs>
- Runbooks: <https://docs.your-domain.com/runbooks>
- Architecture: <https://docs.your-domain.com/architecture>
