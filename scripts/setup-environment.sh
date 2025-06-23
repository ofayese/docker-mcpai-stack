#!/bin/bash

# Docker MCP Stack - Cross-Platform Environment Setup
# This script sets up the necessary directories and configurations for all supported platforms

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Detect operating system
detect_os() {
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        OS="linux"
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        OS="macos"
    elif [[ "$OSTYPE" == "cygwin" ]] || [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "win32" ]]; then
        OS="windows"
    elif [[ -n "$WSL_DISTRO_NAME" ]]; then
        OS="windows"  # WSL
    else
        print_error "Unknown operating system: $OSTYPE"
        exit 1
    fi

    print_status "Detected OS: $OS"
}

# Create necessary directories
create_directories() {
    print_status "Creating necessary directories..."

    if [[ "$OS" == "windows" ]]; then
        DATA_DIR="$USERPROFILE/.mcpai"
    else
        DATA_DIR="$HOME/.mcpai"
    fi

    # Create main directories
    mkdir -p "$DATA_DIR/models"
    mkdir -p "$DATA_DIR/data"
    mkdir -p "$DATA_DIR/qdrant"
    mkdir -p "$DATA_DIR/logs"
    mkdir -p "$DATA_DIR/config"

    print_success "Created directories in: $DATA_DIR"
}

# Create .env file with platform-specific defaults
create_env_file() {
    print_status "Creating .env file with platform-specific defaults..."

    ENV_FILE=".env"

    if [[ -f "$ENV_FILE" ]]; then
        print_warning ".env file already exists. Creating backup..."
        cp "$ENV_FILE" "$ENV_FILE.backup.$(date +%Y%m%d_%H%M%S)"
    fi

    cat > "$ENV_FILE" << EOF
# Docker MCP Stack Environment Configuration
# Generated on $(date) for $OS

# ================================
# PLATFORM DETECTION
# ================================
DETECTED_OS=$OS

# ================================
# SERVICE PORTS
# ================================
MCP_API_PORT=4000
UI_PORT=8501
QDRANT_PORT=6333
QDRANT_GRPC_PORT=6334
PROMETHEUS_PORT=9090
GRAFANA_PORT=3000
NGINX_HTTP_PORT=80
NGINX_HTTPS_PORT=443
NGINX_OLLAMA_PORT=11434

# ================================
# RESOURCE LIMITS (adjust based on your system)
# ================================
EOF

    # Platform-specific resource limits
    if [[ "$OS" == "macos" ]]; then
        cat >> "$ENV_FILE" << EOF
# macOS optimized settings
MODEL_MEMORY_LIMIT=8g
MODEL_CPU_LIMIT=4
API_MEMORY_LIMIT=1g
API_CPU_LIMIT=1
WORKER_MEMORY_LIMIT=2g
WORKER_CPU_LIMIT=1.5
UI_MEMORY_LIMIT=512m
UI_CPU_LIMIT=0.5

# macOS Docker platform
DOCKER_PLATFORM=linux/arm64

# Apple Silicon optimizations
GGML_METAL=1
GGML_METAL_NDEBUG=1
EOF
    elif [[ "$OS" == "linux" ]]; then
        cat >> "$ENV_FILE" << EOF
# Linux optimized settings
MODEL_MEMORY_LIMIT=6g
MODEL_CPU_LIMIT=3
API_MEMORY_LIMIT=1g
API_CPU_LIMIT=1
WORKER_MEMORY_LIMIT=2g
WORKER_CPU_LIMIT=1.5
UI_MEMORY_LIMIT=512m
UI_CPU_LIMIT=0.5

# Linux Docker platform
DOCKER_PLATFORM=linux/amd64

# Linux optimizations
OMP_NUM_THREADS=4
EOF
    else # windows
        cat >> "$ENV_FILE" << EOF
# Windows/WSL2 optimized settings
MODEL_MEMORY_LIMIT=4g
MODEL_CPU_LIMIT=2
API_MEMORY_LIMIT=1g
API_CPU_LIMIT=1
WORKER_MEMORY_LIMIT=2g
WORKER_CPU_LIMIT=1.5
UI_MEMORY_LIMIT=512m
UI_CPU_LIMIT=0.5

# Windows Docker platform
DOCKER_PLATFORM=linux/amd64

# Use host Ollama on Windows
OLLAMA_BASE_URL=http://host.docker.internal:11434/v1
MODEL_API_URL=http://host.docker.internal:11434/v1
EOF
    fi

    cat >> "$ENV_FILE" << EOF

# ================================
# OLLAMA CONFIGURATION
# ================================
# Uncomment and modify if using external Ollama instance
# OLLAMA_BASE_URL=http://localhost:11434/v1
# MODEL_API_URL=http://localhost:11434/v1

# ================================
# MONITORING & LOGGING
# ================================
GRAFANA_ADMIN_PASSWORD=admin
LOG_LEVEL=INFO

# ================================
# DEVELOPMENT SETTINGS
# ================================
DEBUG=false
DEV_MODE=false
HOT_RELOAD=false
EOF

    print_success "Created .env file with $OS-specific settings"
}

# Check dependencies
check_dependencies() {
    print_status "Checking dependencies..."

    # Check Docker
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed. Please install Docker first."
        exit 1
    fi

    # Check Docker Compose
    if ! docker compose version &> /dev/null; then
        print_error "Docker Compose is not available. Please install Docker Compose first."
        exit 1
    fi

    print_success "All dependencies are installed"
}

# Print platform-specific instructions
print_instructions() {
    print_success "Environment setup complete!"
    echo ""
    print_status "Platform-specific quick start commands:"
    echo ""

    if [[ "$OS" == "windows" ]]; then
        echo "  🪟 Windows:"
        echo "    make up-windows     # Start stack"
        echo "    make dev-windows    # Start development environment"
        echo "    make test-windows   # Run tests"
        echo ""
        print_warning "For Windows users:"
        echo "  - Use PowerShell or WSL2 for best experience"
        echo "  - Ensure Docker Desktop is running"
        echo "  - Consider installing Ollama locally for better performance"
    elif [[ "$OS" == "linux" ]]; then
        echo "  🐧 Linux:"
        echo "    make up-linux       # Start stack"
        echo "    make dev-linux      # Start development environment"
        echo "    make test-linux     # Run tests"
        echo ""
        print_status "For GPU acceleration, use:"
        echo "    make gpu-up         # Start with GPU support"
    else # macos
        echo "  🍎 macOS:"
        echo "    make up-macos       # Start stack"
        echo "    make dev-macos      # Start development environment"
        echo "    make test-macos     # Run tests"
        echo ""
        print_status "For Apple Silicon Macs:"
        echo "  - Docker will automatically use ARM64 images"
        echo "  - Consider using host Ollama for better Metal acceleration"
    fi

    echo ""
    print_status "Universal commands (auto-detect OS):"
    echo "    make up             # Start stack (auto-detect)"
    echo "    make dev            # Start development environment (auto-detect)"
    echo "    make help           # Show all available commands"
    echo ""
    print_status "Next steps:"
    echo "  1. Review the .env file and adjust settings as needed"
    echo "  2. Run 'make env-check' to verify your setup"
    echo "  3. Run 'make up' to start the stack"
    echo "  4. Visit http://localhost:8501 to access the UI"
}

# Main execution
main() {
    echo "🚀 Docker MCP Stack - Cross-Platform Setup"
    echo "=========================================="
    echo ""

    detect_os
    check_dependencies
    create_directories
    create_env_file
    print_instructions
}

# Run main function
main "$@"
