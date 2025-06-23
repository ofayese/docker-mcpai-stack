# Security Configuration Guide

This guide provides recommendations for securing the Docker MCP Stack in production environments.

## 1. CORS Configuration

### Development Environment

In development, CORS is automatically configured to allow local development servers:

- `http://localhost:3000`
- `http://localhost:8080`
- `http://localhost:8501`
- `http://127.0.0.1:*` (all localhost addresses)

### Production Environment

In production, CORS must be explicitly configured:

```bash
# Set specific allowed origins (required for production)
CORS_ORIGINS=https://your-domain.com,https://api.your-domain.com,https://app.your-domain.com
```

**Security Note**: Never use `*` for CORS origins in production as it allows requests from any domain.

## 2. Service Exposure

### Internal Services

The following services should only be accessible internally:

- Qdrant (port 6333) - Vector database
- Model Runner (port 8080) - ML model inference
- Prometheus (port 9090) - Metrics collection
- MCP Worker metrics (port 9090) - Worker metrics

### External Access

Only these services should be exposed to external traffic:

- Nginx (ports 80/443) - Web server and reverse proxy
- MCP API (port 4000) - API gateway (behind Nginx)
- UI (port 8501) - Web interface (behind Nginx)

### Recommended Nginx Configuration

```nginx
# Deny direct access to internal services
location /internal/ {
    deny all;
    return 403;
}

# Rate limiting for API endpoints
location /api/ {
    limit_req zone=api burst=20 nodelay;
    proxy_pass http://mcp-api:4000;
}

# Security headers
add_header X-Frame-Options DENY;
add_header X-Content-Type-Options nosniff;
add_header X-XSS-Protection "1; mode=block";
add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
```

## 3. Authentication and Authorization

### API Authentication

Implement API key authentication for production:

```python
# In your API configuration
API_KEY_HEADER = "X-API-Key"
VALID_API_KEYS = ["your-secure-api-key-here"]

# Add to middleware
async def api_key_middleware(request: Request, call_next):
    if request.url.path.startswith("/api/"):
        api_key = request.headers.get(API_KEY_HEADER)
        if api_key not in VALID_API_KEYS:
            return JSONResponse(status_code=401, content={"error": "Invalid API key"})
    return await call_next(request)
```

### Service-to-Service Authentication

Use internal network segmentation and service mesh for inter-service communication.

## 4. Environment Variables Security

### Sensitive Data

Never commit sensitive data to version control:

```bash
# Use strong passwords
POSTGRES_PASSWORD=$(openssl rand -base64 32)
GRAFANA_ADMIN_PASSWORD=$(openssl rand -base64 16)

# Use environment-specific secrets
GITHUB_TOKEN=${GITHUB_TOKEN}
GITLAB_TOKEN=${GITLAB_TOKEN}
SENTRY_DSN=${SENTRY_DSN}
```

### Secret Management

Use Docker secrets or external secret management:

```yaml
# docker-compose.production.yml
secrets:
  postgres_password:
    external: true
  api_keys:
    external: true

services:
  postgres:
    secrets:
      - postgres_password
    environment:
      POSTGRES_PASSWORD_FILE: /run/secrets/postgres_password
```

## 5. Network Security

### Docker Network Isolation

```yaml
# Create separate networks for different tiers
networks:
  frontend:
    driver: bridge
  backend:
    driver: bridge
  monitoring:
    driver: bridge

services:
  nginx:
    networks:
      - frontend
  
  mcp-api:
    networks:
      - frontend
      - backend
  
  qdrant:
    networks:
      - backend
```

### Firewall Rules

Configure host firewall to only allow necessary ports:

```bash
# Allow only necessary external ports
ufw allow 80/tcp    # HTTP
ufw allow 443/tcp   # HTTPS
ufw allow 22/tcp    # SSH (from specific IPs only)

# Deny all other external access
ufw default deny incoming
ufw default allow outgoing
```

## 6. Resource Limits and DoS Protection

### Container Resource Limits

```yaml
services:
  mcp-api:
    deploy:
      resources:
        limits:
          cpus: '1.0'
          memory: 1G
        reservations:
          cpus: '0.5'
          memory: 512M
```

### Rate Limiting

Implement rate limiting at multiple levels:

1. Nginx rate limiting (requests per second)
2. Application-level rate limiting (per user/API key)
3. Model inference rate limiting (to prevent resource exhaustion)

## 7. Monitoring and Alerting

### Security Monitoring

Monitor for suspicious activity:

```yaml
# Prometheus alerts for security events
- alert: HighErrorRate
  expr: rate(mcp_api_requests_total{status=~"4..|5.."}[5m]) > 0.1
  
- alert: UnauthorizedAccess
  expr: rate(mcp_api_requests_total{status="401"}[5m]) > 0.05
  
- alert: ModelAbuseDetection
  expr: rate(mcp_model_inferences_total[1m]) > 100
```

### Audit Logging

Enable comprehensive audit logging:

```python
# Log all API requests with security context
@middleware("http")
async def audit_middleware(request: Request, call_next):
    start_time = time.time()
    client_ip = request.headers.get("X-Forwarded-For", request.client.host)
    
    logger.info("api_request", 
                method=request.method,
                url=str(request.url),
                client_ip=client_ip,
                user_agent=request.headers.get("User-Agent"))
    
    response = await call_next(request)
    
    logger.info("api_response",
                status_code=response.status_code,
                duration=time.time() - start_time,
                client_ip=client_ip)
    
    return response
```

## 8. Data Protection

### Encryption in Transit

- Use TLS 1.3 for all external communications
- Use internal TLS for sensitive inter-service communication
- Implement certificate rotation

### Encryption at Rest

- Encrypt sensitive database fields
- Use encrypted storage for model files
- Implement backup encryption

### Data Retention

- Implement data retention policies
- Secure data deletion procedures
- GDPR/privacy compliance measures

## 9. Regular Security Updates

### Container Image Updates

```bash
# Regular security updates
docker pull --all-tags
docker system prune -f

# Scan for vulnerabilities
docker scout cves <image-name>
```

### Dependency Updates

```bash
# Check for security vulnerabilities
pip audit
npm audit

# Update dependencies regularly
pip install --upgrade pip
pip install --upgrade -r requirements.txt
```

## 10. Incident Response

### Security Incident Checklist

1. **Immediate Response**
   - Isolate affected services
   - Preserve logs and evidence
   - Notify security team

2. **Investigation**
   - Analyze audit logs
   - Check for data exfiltration
   - Assess scope of compromise

3. **Recovery**
   - Patch vulnerabilities
   - Reset compromised credentials
   - Verify system integrity

4. **Post-Incident**
   - Document lessons learned
   - Update security procedures
   - Implement additional monitoring

## Implementation Checklist

- [ ] Configure environment-specific CORS settings
- [ ] Implement API authentication
- [ ] Set up network isolation
- [ ] Configure resource limits
- [ ] Enable audit logging
- [ ] Set up security monitoring
- [ ] Implement rate limiting
- [ ] Configure TLS/encryption
- [ ] Set up backup encryption
- [ ] Create incident response procedures
- [ ] Regular security reviews and updates

For questions or security concerns, contact your security team or open an issue in the repository.
