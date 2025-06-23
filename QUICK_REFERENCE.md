# Docker MCPAI Stack - Quick Reference

## 🚀 Platform Support

| Platform | Status | Setup Command | Start Command |
|----------|---------|---------------|---------------|
| 🐧 **Linux** | ✅ Full Support | `./scripts/setup-environment.sh` | `make up-linux` |
| 🍎 **macOS** | ✅ Full Support | `./scripts/setup-environment.sh` | `make up-macos` |
| 🪟 **Windows** | ✅ Full Support | `.\scripts\setup-environment.ps1` | `make up-windows` |

## ⚡ Quick Commands

### Universal Commands (Auto-Detection)
```bash
make up          # Start with platform auto-detection
make dev         # Development mode with hot-reload
make test        # Run cross-platform tests
make down        # Stop all services
make logs        # View service logs
make help        # Show all available commands
```

### Platform-Specific Commands
```bash
# Linux
make up-linux dev-linux test-linux

# macOS (including Apple Silicon)
make up-macos dev-macos test-macos

# Windows (including WSL2)
make up-windows dev-windows test-windows
```

### Environment Setup
```bash
# Bash (Linux/macOS/WSL2)
chmod +x scripts/setup-environment.sh
./scripts/setup-environment.sh

# PowerShell (Windows)
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
.\scripts\setup-environment.ps1
```

### Validation & Testing
```bash
# Bash validation
./scripts/validate-cross-platform.sh

# PowerShell validation
.\scripts\validate-cross-platform.ps1

# Skip integration tests (faster)
.\scripts\validate-cross-platform.ps1 -SkipIntegrationTests
```

## 🔧 Service URLs

| Service | URL | Description |
|---------|-----|-------------|
| **UI** | http://localhost:8501 | Streamlit web interface |
| **API** | http://localhost:8000 | REST API and OpenAPI docs |
| **Grafana** | http://localhost:3000 | Monitoring dashboard |
| **Prometheus** | http://localhost:9090 | Metrics collection |

## 📁 Key Configuration Files

| File | Purpose | Platform |
|------|---------|----------|
| `compose/docker-compose.linux.yml` | Linux optimizations | Linux |
| `compose/docker-compose.macos.yml` | macOS/Apple Silicon support | macOS |
| `compose/docker-compose.windows.yml` | Windows/WSL2 integration | Windows |
| `nginx/nginx.*.conf` | Platform-specific routing | All |
| `.env` | Environment variables | All |

## 🛠️ Development Workflow

### 1. Initial Setup
```bash
# Choose your platform setup
./scripts/setup-environment.sh      # Bash
.\scripts\setup-environment.ps1     # PowerShell

# Verify installation
./scripts/validate-cross-platform.sh
```

### 2. Development
```bash
# Start development environment
make dev

# View logs
make logs

# Restart specific service
docker-compose restart mcp-api
```

### 3. Testing
```bash
# Run all tests
make test

# Run specific test types
make test-unit
make test-integration
make test-e2e
```

### 4. Production
```bash
# Production deployment
make up ENVIRONMENT=production

# Health check
curl http://localhost:8000/health
```

## 🚨 Troubleshooting

### Common Issues

#### Docker Not Found
```bash
# Verify Docker installation
docker --version
docker info
```

#### Permission Denied (Linux)
```bash
# Add user to docker group
sudo usermod -aG docker $USER
# Logout and login again
```

#### WSL2 Issues (Windows)
```powershell
# Enable WSL2 and Docker Desktop integration
wsl --set-default-version 2
# Restart Docker Desktop
```

#### Port Conflicts
```bash
# Check what's using ports
netstat -tulpn | grep :8000
netstat -tulpn | grep :8501

# Kill processes if needed
sudo kill -9 <PID>
```

#### Memory Issues
```bash
# Check available memory
free -h                    # Linux
vm_stat                    # macOS
Get-ComputerInfo          # Windows PowerShell

# Increase Docker memory allocation in Docker Desktop
```

### Platform-Specific Troubleshooting

#### Linux
- Check SELinux/AppArmor: `getenforce` or `aa-status`
- Verify user permissions: `groups $USER`
- Check systemd services: `systemctl status docker`

#### macOS
- Verify Docker Desktop settings in preferences
- Check Apple Silicon compatibility for custom images
- Monitor Activity Monitor for resource usage

#### Windows
- Ensure WSL2 is enabled: `wsl --list --verbose`
- Check Docker Desktop WSL2 integration
- Verify PowerShell execution policy: `Get-ExecutionPolicy`

## 📚 Documentation Links

- [Cross-Platform Support Guide](docs/cross-platform-support.md)
- [Troubleshooting Guide](docs/troubleshooting.md)
- [Production Deployment](docs/production-deployment.md)
- [API Reference](docs/api-reference.md)
- [Implementation Summary](CROSS_PLATFORM_IMPLEMENTATION.md)

## 🔄 CI/CD & Automation

### GitHub Actions Workflows
- **CI**: Cross-platform testing on every push
- **Build**: Multi-architecture Docker images
- **Release**: Platform-specific release packages
- **Dependencies**: Weekly automated updates

### Local Automation
```bash
# Setup development environment
make setup

# Run full validation suite
make validate

# Clean up everything
make clean

# Reset to clean state
make reset
```

## 📊 Performance Benchmarks

| Platform | Startup Time | Memory Usage | CPU Usage |
|----------|--------------|--------------|-----------|
| Linux | ~30-45s | 2-4GB | Low |
| macOS | ~45-60s | 4-6GB | Medium |
| Windows | ~60-90s | 3-5GB | Medium |

## 🆘 Getting Help

1. **Check Documentation**: Start with [docs/](docs/) directory
2. **Run Diagnostics**: `./scripts/validate-cross-platform.sh`
3. **Check Logs**: `make logs`
4. **GitHub Issues**: Report platform-specific issues
5. **Community**: Join our discussions

---

**Platform Status**: 🐧 Linux ✅ | 🍎 macOS ✅ | 🪟 Windows ✅
**Last Updated**: December 2024
