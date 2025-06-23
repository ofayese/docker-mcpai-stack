# Docker MCP Stack - Windows Environment Setup
# PowerShell script for setting up the environment on Windows

param(
    [switch]$Force = $false
)

# Colors for output
$Colors = @{
    Red = 'Red'
    Green = 'Green'
    Yellow = 'Yellow'
    Blue = 'Blue'
    White = 'White'
}

function Write-Status {
    param([string]$Message)
    Write-Host "[INFO] $Message" -ForegroundColor $Colors.Blue
}

function Write-Success {
    param([string]$Message)
    Write-Host "[SUCCESS] $Message" -ForegroundColor $Colors.Green
}

function Write-Warning {
    param([string]$Message)
    Write-Host "[WARNING] $Message" -ForegroundColor $Colors.Yellow
}

function Write-Error {
    param([string]$Message)
    Write-Host "[ERROR] $Message" -ForegroundColor $Colors.Red
}

function Test-Dependencies {
    Write-Status "Checking dependencies..."

    # Check Docker
    try {
        $dockerVersion = docker --version
        Write-Success "Docker found: $dockerVersion"
    }
    catch {
        Write-Error "Docker is not installed or not in PATH. Please install Docker Desktop first."
        exit 1
    }

    # Check Docker Compose
    try {
        $composeVersion = docker compose version
        Write-Success "Docker Compose found: $composeVersion"
    }
    catch {
        Write-Error "Docker Compose is not available. Please update Docker Desktop."
        exit 1
    }

    # Check WSL2 (optional but recommended)
    try {
        $wslVersion = wsl --version
        Write-Success "WSL2 detected - recommended for better performance"
    }
    catch {
        Write-Warning "WSL2 not detected. Consider installing WSL2 for better Docker performance."
    }
}

function New-Directories {
    Write-Status "Creating necessary directories..."

    $DataDir = "$env:USERPROFILE\.mcpai"

    # Create main directories
    $Directories = @(
        "$DataDir\models",
        "$DataDir\data",
        "$DataDir\qdrant",
        "$DataDir\logs",
        "$DataDir\config"
    )

    foreach ($Dir in $Directories) {
        if (!(Test-Path $Dir)) {
            New-Item -ItemType Directory -Path $Dir -Force | Out-Null
            Write-Status "Created: $Dir"
        }
    }

    Write-Success "Created directories in: $DataDir"
}

function New-EnvFile {
    Write-Status "Creating .env file with Windows-specific defaults..."

    $EnvFile = ".env"

    if ((Test-Path $EnvFile) -and !$Force) {
        Write-Warning ".env file already exists. Creating backup..."
        $BackupName = ".env.backup.$(Get-Date -Format 'yyyyMMdd_HHmmss')"
        Copy-Item $EnvFile $BackupName
        Write-Status "Backup created: $BackupName"
    }

    $EnvContent = @"
# Docker MCP Stack Environment Configuration
# Generated on $(Get-Date) for Windows

# ================================
# PLATFORM DETECTION
# ================================
DETECTED_OS=windows

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
# RESOURCE LIMITS (Windows/WSL2 optimized)
# ================================
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

# ================================
# OLLAMA CONFIGURATION (Host-based for Windows)
# ================================
# Using host.docker.internal to connect to local Ollama
OLLAMA_BASE_URL=http://host.docker.internal:11434/v1
MODEL_API_URL=http://host.docker.internal:11434/v1

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

# ================================
# WINDOWS-SPECIFIC SETTINGS
# ================================
# Set to true if using WSL2
WSL2_ENABLED=true

# Volume mount type for Windows
VOLUME_TYPE=bind
"@

    Set-Content -Path $EnvFile -Value $EnvContent
    Write-Success "Created .env file with Windows-specific settings"
}

function Show-Instructions {
    Write-Success "Environment setup complete!"
    Write-Host ""
    Write-Status "Windows-specific quick start commands:"
    Write-Host ""
    Write-Host "  🪟 Windows PowerShell:" -ForegroundColor $Colors.Blue
    Write-Host "    make up-windows     # Start stack"
    Write-Host "    make dev-windows    # Start development environment"
    Write-Host "    make test-windows   # Run tests"
    Write-Host ""
    Write-Warning "For best Windows experience:"
    Write-Host "  - Use PowerShell or Windows Terminal"
    Write-Host "  - Ensure Docker Desktop is running and WSL2 backend is enabled"
    Write-Host "  - Consider installing Ollama locally:"
    Write-Host "    winget install Ollama.Ollama"
    Write-Host "  - If using local Ollama, it will be automatically detected"
    Write-Host ""
    Write-Status "Universal commands (auto-detect OS):"
    Write-Host "    make up             # Start stack (auto-detect)"
    Write-Host "    make dev            # Start development environment (auto-detect)"
    Write-Host "    make help           # Show all available commands"
    Write-Host ""
    Write-Status "Next steps:"
    Write-Host "  1. Review the .env file and adjust settings as needed"
    Write-Host "  2. Run 'make env-check' to verify your setup"
    Write-Host "  3. Run 'make up-windows' to start the stack"
    Write-Host "  4. Visit http://localhost:8501 to access the UI"
    Write-Host ""
    Write-Status "Troubleshooting:"
    Write-Host "  - If you encounter permission issues, run PowerShell as Administrator"
    Write-Host "  - For WSL2 issues, ensure Docker Desktop is using WSL2 backend"
    Write-Host "  - Check Docker Desktop settings for resource allocation"
}

function Main {
    Write-Host "🚀 Docker MCP Stack - Windows Setup" -ForegroundColor $Colors.Green
    Write-Host "====================================" -ForegroundColor $Colors.Green
    Write-Host ""

    Test-Dependencies
    New-Directories
    New-EnvFile
    Show-Instructions
}

# Run main function
Main
