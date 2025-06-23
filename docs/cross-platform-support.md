# Cross-Platform Support

The Docker MCP Stack supports Windows, Linux, and macOS with platform-specific optimizations for the best experience on each operating system.

## Quick Start by Platform

### 🪟 Windows

#### Prerequisites
- Docker Desktop with WSL2 backend (recommended)
- PowerShell 5.1+ or PowerShell Core 7+
- Make for Windows (optional, or use PowerShell scripts)

#### Setup
```powershell
# Run the Windows setup script
.\scripts\setup-environment.ps1

# Start the stack
make up-windows
# or use PowerShell
docker compose -f compose/docker-compose.base.yml -f compose/docker-compose.windows.yml --profile cpu up -d
```

#### Windows-Specific Features
- Automatic host Ollama integration via `host.docker.internal`
- WSL2 optimized volume mounts
- PowerShell setup and management scripts
- Windows-specific resource limits

### 🐧 Linux

#### Prerequisites
- Docker Engine 20.10+
- Docker Compose V2
- Make
- Bash

#### Setup
```bash
# Run the Linux setup script
chmod +x scripts/setup-environment.sh
./scripts/setup-environment.sh

# Start the stack
make up-linux
```

#### Linux-Specific Features
- Containerized model runner with full control
- GPU acceleration support (CUDA)
- Optimized for server deployments
- Native volume mounting

### 🍎 macOS

#### Prerequisites
- Docker Desktop for Mac
- Make (included with Xcode Command Line Tools)
- Bash or Zsh

#### Setup
```bash
# Install Xcode Command Line Tools (if not already installed)
xcode-select --install

# Run the macOS setup script
chmod +x scripts/setup-environment.sh
./scripts/setup-environment.sh

# Start the stack
make up-macos
```

#### macOS-Specific Features
- Apple Silicon (M1/M2) optimization with ARM64 images
- Metal GPU acceleration for supported models
- Host Ollama integration option
- Optimized volume mounting for macOS

## Platform Detection

The Makefile automatically detects your operating system and applies the appropriate configuration:

```bash
# Auto-detect OS and start
make up

# Check detected platform
make env-check
```

## Platform-Specific Configurations

### Volume Mounting Strategies

| Platform | Strategy | Benefits |
|----------|----------|----------|
| Windows | `host.docker.internal` + bind mounts | Better performance with WSL2 |
| Linux | Direct bind mounts | Native performance |
| macOS | Optimized bind mounts | Reduced file system overhead |

### Resource Recommendations

| Platform | Memory | CPU | Notes |
|----------|--------|-----|-------|
| Windows | 4-8GB | 2-4 cores | Depends on WSL2 allocation |
| Linux | 6-16GB | 3-8 cores | Can use full system resources |
| macOS | 8-16GB | 4-8 cores | Benefits from unified memory |

### Model Runner Configuration

#### Windows
- Uses host Ollama by default (`host.docker.internal:11434`)
- Model runner container disabled to avoid conflicts
- Best performance with local Ollama installation

#### Linux
- Containerized model runner with full control
- Supports GPU acceleration (NVIDIA CUDA)
- Can be configured for distributed deployments

#### macOS
- Choice between host Ollama or containerized runner
- Apple Silicon optimizations (Metal GPU support)
- ARM64 container images for better performance

## Environment Variables

Each platform has optimized default environment variables:

### Common Variables
```bash
MCP_API_PORT=4000
UI_PORT=8501
QDRANT_PORT=6333
PROMETHEUS_PORT=9090
GRAFANA_PORT=3000
```

### Platform-Specific Variables

#### Windows
```bash
OLLAMA_BASE_URL=http://host.docker.internal:11434/v1
MODEL_API_URL=http://host.docker.internal:11434/v1
DOCKER_PLATFORM=linux/amd64
```

#### Linux
```bash
OLLAMA_BASE_URL=http://model-runner:8080/v1
MODEL_API_URL=http://model-runner:8080/v1
DOCKER_PLATFORM=linux/amd64
OMP_NUM_THREADS=4
```

#### macOS
```bash
OLLAMA_BASE_URL=http://host.docker.internal:11434/v1
MODEL_API_URL=http://host.docker.internal:11434/v1
DOCKER_PLATFORM=linux/arm64
GGML_METAL=1
```

## Troubleshooting by Platform

### Windows Issues

**Docker Desktop not starting:**
```powershell
# Ensure WSL2 is enabled
wsl --set-default-version 2

# Restart Docker Desktop
# Check Docker Desktop settings for WSL2 integration
```

**Permission errors:**
```powershell
# Run PowerShell as Administrator
# Check Docker Desktop resource access settings
```

**Slow performance:**
```powershell
# Ensure files are in WSL2 filesystem, not Windows filesystem
# Increase Docker Desktop memory allocation
# Use local Ollama instead of containerized version
```

### Linux Issues

**GPU not detected:**
```bash
# Install NVIDIA Container Toolkit
sudo apt-get update
sudo apt-get install -y nvidia-container-toolkit
sudo systemctl restart docker

# Use GPU profile
make gpu-up
```

**Permission errors:**
```bash
# Add user to docker group
sudo usermod -aG docker $USER
# Log out and log back in
```

### macOS Issues

**Slow volume mounting:**
```bash
# Use named volumes instead of bind mounts for better performance
# Consider using host Ollama for model operations
```

**Apple Silicon compatibility:**
```bash
# Ensure ARM64 images are used
export DOCKER_PLATFORM=linux/arm64
make up-macos
```

## Performance Optimization

### Windows
1. Use WSL2 with Docker Desktop
2. Store project files in WSL2 filesystem
3. Install Ollama locally for better model performance
4. Increase Docker Desktop memory allocation

### Linux
1. Use GPU acceleration when available
2. Optimize Docker daemon settings
3. Use SSD storage for volumes
4. Configure resource limits based on system capacity

### macOS
1. Leverage Apple Silicon optimizations
2. Use Metal GPU acceleration
3. Consider host Ollama for better performance
4. Optimize Docker Desktop settings

## Development Workflows

### Cross-Platform Development
```bash
# Auto-detect platform and start development environment
make dev

# Platform-specific development
make dev-windows  # Windows
make dev-linux    # Linux
make dev-macos    # macOS
```

### Testing Across Platforms
```bash
# Test on current platform
make test

# Platform-specific testing
make test-windows
make test-linux
make test-macos
```

### Building for Multiple Platforms
```bash
# Build multi-architecture images
make build-multiarch

# Platform-specific builds
docker buildx build --platform linux/amd64,linux/arm64 .
```

## Migration Between Platforms

### Moving from Windows to Linux/macOS
1. Export data volumes: `make backup`
2. Transfer backup files
3. Run setup script on new platform
4. Restore data: `make restore BACKUP=backup-name`

### Moving from Linux/macOS to Windows
1. Export data volumes: `make backup`
2. Transfer backup files to Windows
3. Run PowerShell setup script
4. Restore data: `make restore BACKUP=backup-name`
5. Configure host Ollama if needed

## Contributing

When contributing cross-platform features:

1. Test on all three platforms
2. Update platform-specific documentation
3. Consider performance implications for each OS
4. Update environment variables and configurations
5. Test the setup scripts on each platform

For more detailed information, see:
- [Windows Setup Guide](docs/setup/windows.md)
- [Linux Setup Guide](docs/setup/linux.md)
- [macOS Setup Guide](docs/setup/macos.md)
