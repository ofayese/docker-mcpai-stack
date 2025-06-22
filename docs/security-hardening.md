# Security Hardening Guidelines for MCPAI Docker Stack

## Container Security Best Practices

### 1. Base Image Security

- Use minimal base images (alpine, distroless)
- Regularly update base images
- Scan images for vulnerabilities with Trivy
- Use specific image tags, not 'latest'

### 2. User Privileges

- Run containers as non-root users
- Use USER directive in Dockerfiles
- Set security contexts in compose files
- Use read-only root filesystems where possible

### 3. Network Security

- Use custom networks instead of default bridge
- Implement network segmentation
- Use internal networks for service communication
- Limit exposed ports to necessary services only

### 4. Secrets Management

- Use Docker secrets or external secret management
- Never hardcode credentials in images or compose files
- Use environment variables for configuration
- Rotate secrets regularly

### 5. Resource Limits

- Set CPU and memory limits for all containers
- Use ulimits to prevent resource exhaustion
- Implement health checks for all services
- Monitor resource usage continuously

## File Security Configuration

### .dockerignore Templates

Create .dockerignore files to exclude sensitive files:

```
.git
.env*
secrets/
*.key
*.pem
node_modules
__pycache__
.pytest_cache
```

### Security Labels

Add security labels to containers:

```yaml
labels:
  - "security.scan=enabled"
  - "security.level=production"
  - "security.contact=security@company.com"
```

### Health Checks

Implement comprehensive health checks:

```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
  interval: 30s
  timeout: 10s
  retries: 3
  start_period: 40s
```

## Network Security

### Firewall Rules

Configure host firewall to:

- Allow only necessary incoming ports
- Block direct access to internal services
- Log all rejected connections
- Use fail2ban for intrusion prevention

### TLS/SSL Configuration

- Use TLS 1.2+ for all external communications
- Implement certificate rotation
- Use strong cipher suites
- Enable HSTS headers

### Service Mesh (Optional)

Consider implementing Istio or Linkerd for:

- Mutual TLS between services
- Fine-grained access control
- Traffic encryption
- Service-to-service authentication

## Monitoring and Alerting

### Security Metrics

Monitor these security-related metrics:

- Failed authentication attempts
- Privilege escalation attempts
- Unusual network traffic
- Container escape attempts
- File system modifications

### Alert Rules

Create alerts for:

- High CPU/memory usage (potential DoS)
- Multiple failed login attempts
- Unexpected container restarts
- Security scan failures
- Certificate expiration

## Compliance and Auditing

### Container Scanning

Implement regular security scanning:

```bash
# Trivy security scanning
trivy image --severity HIGH,CRITICAL myimage:tag

# Container runtime security
falco --rules-file=/etc/falco/falco_rules.yaml
```

### Audit Logging

Enable audit logging for:

- Container lifecycle events
- Authentication and authorization
- Configuration changes
- Network access patterns

### Compliance Frameworks

Consider compliance with:

- CIS Docker Benchmark
- NIST Cybersecurity Framework
- SOC 2 Type II
- ISO 27001

## Incident Response

### Security Incident Playbook

1. **Detection**: Automated alerts and monitoring
2. **Containment**: Isolate affected containers
3. **Investigation**: Analyze logs and forensics
4. **Eradication**: Remove threats and patch vulnerabilities
5. **Recovery**: Restore services and validate security
6. **Lessons Learned**: Update procedures and controls

### Backup and Recovery

- Automated daily backups
- Test restore procedures regularly
- Store backups securely off-site
- Implement point-in-time recovery

## Development Security

### Secure Development Lifecycle

- Security training for developers
- Code review for security issues
- Static and dynamic security testing
- Dependency vulnerability scanning

### CI/CD Security

- Secure build pipelines
- Image signing and verification
- Automated security testing
- Secrets scanning in repositories

## Production Deployment

### Environment Hardening

- Disable unnecessary services
- Configure log rotation
- Set up centralized logging
- Implement monitoring and alerting

### Access Control

- Multi-factor authentication
- Role-based access control
- Principle of least privilege
- Regular access reviews

### Data Protection

- Encryption at rest and in transit
- Data classification and handling
- Privacy controls and compliance
- Secure data disposal
