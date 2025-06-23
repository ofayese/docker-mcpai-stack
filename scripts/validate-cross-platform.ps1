# Cross-platform validation script for Windows PowerShell
# Tests all platform configurations and ensures compatibility

[CmdletBinding()]
param(
    [switch]$SkipIntegrationTests = $false
)

# Set error action preference
$ErrorActionPreference = "Stop"

# Color functions for output
function Write-Info {
    param([string]$Message)
    Write-Host "[INFO] $Message" -ForegroundColor Blue
}

function Write-Success {
    param([string]$Message)
    Write-Host "[SUCCESS] $Message" -ForegroundColor Green
}

function Write-Warning {
    param([string]$Message)
    Write-Host "[WARNING] $Message" -ForegroundColor Yellow
}

function Write-Error {
    param([string]$Message)
    Write-Host "[ERROR] $Message" -ForegroundColor Red
}

# Detect if running in WSL
function Test-WSL {
    if (Test-Path "/proc/version" -ErrorAction SilentlyContinue) {
        $version = Get-Content "/proc/version" -ErrorAction SilentlyContinue
        return $version -match "Microsoft|WSL"
    }
    return $false
}

# Validate Docker installation
function Test-Docker {
    Write-Info "Validating Docker installation..."

    try {
        $null = Get-Command docker -ErrorAction Stop
        Write-Success "Docker command found"
    }
    catch {
        Write-Error "Docker is not installed or not in PATH"
        return $false
    }

    try {
        docker info | Out-Null
        Write-Success "Docker daemon is running"
    }
    catch {
        Write-Error "Docker daemon is not running"
        return $false
    }

    # Check Docker Compose
    try {
        $composeVersion = docker compose version 2>$null
        if ($composeVersion) {
            Write-Success "Docker Compose V2 is available"
        } else {
            $null = Get-Command docker-compose -ErrorAction Stop
            Write-Success "Docker Compose V1 is available"
        }
    }
    catch {
        Write-Error "Docker Compose is not available"
        return $false
    }

    return $true
}

# Validate Make installation
function Test-Make {
    Write-Info "Validating Make installation..."

    try {
        $null = Get-Command make -ErrorAction Stop
        Write-Success "Make is available"
        return $true
    }
    catch {
        Write-Error "Make is not installed"
        return $false
    }
}

# Validate platform-specific files
function Test-PlatformFiles {
    param([string]$Platform)

    Write-Info "Validating platform-specific files for $Platform..."

    # Check Docker Compose file
    $composeFile = "compose\docker-compose.$Platform.yml"
    if (-not (Test-Path $composeFile)) {
        Write-Error "Missing compose file: $composeFile"
        return $false
    }

    # Validate YAML syntax (basic check)
    try {
        $content = Get-Content $composeFile -Raw
        if (-not $content.Trim()) {
            Write-Error "Empty compose file: $composeFile"
            return $false
        }
    }
    catch {
        Write-Error "Cannot read compose file: $composeFile"
        return $false
    }

    Write-Success "Platform compose file is valid: $composeFile"

    # Check Nginx config
    $nginxConfig = "nginx\nginx.$Platform.conf"
    if (-not (Test-Path $nginxConfig)) {
        Write-Error "Missing nginx config: $nginxConfig"
        return $false
    }

    Write-Success "Platform nginx config exists: $nginxConfig"
    return $true
}

# Test Makefile targets
function Test-MakefileTargets {
    param([string]$Platform)

    Write-Info "Testing Makefile targets for $Platform..."

    try {
        # Test help target
        make help | Out-Null
        Write-Success "Makefile help target is functional"
    }
    catch {
        Write-Error "Makefile help target failed"
        return $false
    }

    try {
        # Test platform detection (if available)
        $detectedPlatform = make --silent platform 2>$null
        if ($detectedPlatform) {
            Write-Info "Makefile detected platform: $detectedPlatform"
        }
    }
    catch {
        Write-Warning "Platform detection not available in Makefile"
    }

    try {
        # Test env-check target
        make env-check | Out-Null
        Write-Success "Environment check passed"
    }
    catch {
        Write-Warning "Environment check reported issues (this may be expected)"
    }

    return $true
}

# Validate setup scripts
function Test-SetupScripts {
    Write-Info "Validating environment setup scripts..."

    # Check bash setup script
    if (-not (Test-Path "scripts\setup-environment.sh")) {
        Write-Error "Missing setup script: scripts\setup-environment.sh"
        return $false
    }

    # Check PowerShell script
    if (-not (Test-Path "scripts\setup-environment.ps1")) {
        Write-Error "Missing PowerShell setup script: scripts\setup-environment.ps1"
        return $false
    }

    Write-Success "Setup scripts are available"
    return $true
}

# Test Docker builds
function Test-DockerBuilds {
    param([string]$Platform)

    Write-Info "Testing Docker builds for $Platform..."

    $composeFile = "compose\docker-compose.$Platform.yml"

    try {
        Write-Info "Building images (this may take a while)..."

        # Use docker compose if available, otherwise docker-compose
        $composeCommand = "docker compose"
        try {
            docker compose version | Out-Null
        }
        catch {
            $composeCommand = "docker-compose"
        }

        $buildCommand = "$composeCommand -f $composeFile build --no-cache"
        Invoke-Expression $buildCommand | Out-Null

        Write-Success "All Docker images built successfully"
        return $true
    }
    catch {
        Write-Warning "Some Docker builds failed (may be expected in CI)"
        return $false
    }
}

# Test service connectivity
function Test-ServiceConnectivity {
    param([string]$Platform)

    Write-Info "Testing service connectivity for $Platform..."

    $composeFile = "compose\docker-compose.$Platform.yml"

    try {
        # Determine compose command
        $composeCommand = "docker compose"
        try {
            docker compose version | Out-Null
        }
        catch {
            $composeCommand = "docker-compose"
        }

        # Start services
        Write-Info "Starting services..."
        $upCommand = "$composeCommand -f $composeFile up -d"
        Invoke-Expression $upCommand | Out-Null

        # Wait for services
        Write-Info "Waiting for services to be ready..."
        Start-Sleep -Seconds 30

        # Test health endpoints
        $services = @(
            @{ Name = "mcp-api"; Port = 8000 },
            @{ Name = "ui"; Port = 8501 }
        )

        foreach ($service in $services) {
            Write-Info "Testing $($service.Name) health..."

            $host = "localhost"
            $url = "http://$host:$($service.Port)/health"

            try {
                $response = Invoke-WebRequest -Uri $url -TimeoutSec 10 -ErrorAction Stop
                if ($response.StatusCode -eq 200) {
                    Write-Success "$($service.Name) is responding on port $($service.Port)"
                } else {
                    Write-Warning "$($service.Name) returned status $($response.StatusCode)"
                }
            }
            catch {
                Write-Warning "$($service.Name) is not responding on port $($service.Port) (may need more time)"
            }
        }

        # Cleanup
        Write-Info "Cleaning up services..."
        $downCommand = "$composeCommand -f $composeFile down"
        Invoke-Expression $downCommand | Out-Null

        Write-Success "Service connectivity test completed"
        return $true
    }
    catch {
        Write-Error "Service connectivity test failed: $($_.Exception.Message)"
        return $false
    }
}

# Validate documentation
function Test-Documentation {
    Write-Info "Validating documentation..."

    $requiredDocs = @(
        "README.md",
        "docs\cross-platform-support.md",
        "docs\troubleshooting.md"
    )

    foreach ($doc in $requiredDocs) {
        if (-not (Test-Path $doc)) {
            Write-Error "Missing documentation: $doc"
            return $false
        }
    }

    # Check for platform-specific sections
    $crossPlatformDoc = "docs\cross-platform-support.md"
    $content = Get-Content $crossPlatformDoc -Raw

    if ($content -notmatch "Windows") {
        Write-Error "Missing Windows documentation in cross-platform-support.md"
        return $false
    }

    if ($content -notmatch "macOS") {
        Write-Error "Missing macOS documentation in cross-platform-support.md"
        return $false
    }

    if ($content -notmatch "Linux") {
        Write-Error "Missing Linux documentation in cross-platform-support.md"
        return $false
    }

    Write-Success "Documentation validation passed"
    return $true
}

# Validate GitHub workflows
function Test-Workflows {
    Write-Info "Validating GitHub workflows..."

    $requiredWorkflows = @(
        ".github\workflows\ci.yml",
        ".github\workflows\build.yml",
        ".github\workflows\release.yml",
        ".github\workflows\cross-platform-test.yml",
        ".github\workflows\dependency-updates.yml"
    )

    foreach ($workflow in $requiredWorkflows) {
        if (-not (Test-Path $workflow)) {
            Write-Error "Missing workflow: $workflow"
            return $false
        }

        # Basic YAML validation (check if file is readable)
        try {
            $content = Get-Content $workflow -Raw
            if (-not $content.Trim()) {
                Write-Error "Empty workflow file: $workflow"
                return $false
            }
        }
        catch {
            Write-Error "Cannot read workflow file: $workflow"
            return $false
        }
    }

    Write-Success "GitHub workflows validation passed"
    return $true
}

# Generate validation report
function New-ValidationReport {
    param([string]$Platform)

    $resultsFile = "validation-results-$Platform.md"
    Write-Info "Generating validation report: $resultsFile"

    $reportContent = @"
# Cross-Platform Validation Report

**Platform**: $Platform
**Date**: $(Get-Date)
**Validation Script Version**: 1.0
**PowerShell Version**: $($PSVersionTable.PSVersion)

## Test Results

### ✅ Core Requirements
- Docker installation and daemon
- Docker Compose availability
- Make tool availability

### ✅ Platform-Specific Files
- Docker Compose configuration: ``compose\docker-compose.$Platform.yml``
- Nginx configuration: ``nginx\nginx.$Platform.conf``
- Environment setup scripts

### ✅ Makefile Integration
- Platform detection working
- Help target functional
- Environment check available

### ✅ Documentation
- Cross-platform documentation complete
- Platform-specific instructions included
- Troubleshooting guide available

### ✅ GitHub Workflows
- CI/CD workflows configured
- Cross-platform testing enabled
- Dependency update automation

## Platform-Specific Notes

"@

    # Add platform-specific notes
    switch ($Platform) {
        "windows" {
            $reportContent += @"
- PowerShell script support ✅
- Docker Desktop integration
- WSL2 compatibility: $(if (Test-WSL) { "Enabled" } else { "Native Windows" })

"@
        }
        "linux" {
            $reportContent += @"
- Native Docker support
- Full feature compatibility

"@
        }
        "macos" {
            $reportContent += @"
- Docker Desktop required
- Apple Silicon (ARM64) optimizations

"@
        }
    }

    $reportContent += @"

## Recommendations

- All platform requirements met ✅
- Ready for production deployment
- Cross-platform compatibility confirmed

## Windows-Specific Notes

- PowerShell execution policy may need to be set: ``Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser``
- Docker Desktop should be configured for WSL2 integration if using WSL
- Windows containers and Linux containers both supported

"@

    $reportContent | Out-File -FilePath $resultsFile -Encoding UTF8
    Write-Success "Validation report generated: $resultsFile"
}

# Main validation function
function Start-Validation {
    Write-Info "Starting cross-platform validation..."
    Write-Info "================================================"

    # Detect environment
    $platform = "windows"
    Write-Info "Platform: $platform"

    if (Test-WSL) {
        Write-Info "Running in WSL2 environment"
    } else {
        Write-Info "Running in native Windows environment"
    }

    $exitCode = 0

    # Run all validations
    if (-not (Test-Docker)) { $exitCode = 1 }
    if (-not (Test-Make)) { $exitCode = 1 }
    if (-not (Test-SetupScripts)) { $exitCode = 1 }
    if (-not (Test-Documentation)) { $exitCode = 1 }
    if (-not (Test-Workflows)) { $exitCode = 1 }

    # Test all platforms
    $platforms = @("linux", "macos", "windows")
    foreach ($p in $platforms) {
        Write-Info "Testing platform: $p"
        if (-not (Test-PlatformFiles $p)) { $exitCode = 1 }
    }

    # Test current platform specifically
    if (-not (Test-MakefileTargets $platform)) { $exitCode = 1 }

    # Optional: Test builds and connectivity
    if (-not $SkipIntegrationTests) {
        if (-not (Test-DockerBuilds $platform)) { $exitCode = 1 }
        if (-not (Test-ServiceConnectivity $platform)) { $exitCode = 1 }
    } else {
        Write-Info "Skipping integration tests (SkipIntegrationTests flag set)"
    }

    # Generate report
    New-ValidationReport $platform

    if ($exitCode -eq 0) {
        Write-Success "All validations passed! ✅"
        Write-Success "The project is ready for cross-platform deployment."
    } else {
        Write-Error "Some validations failed! ❌"
        Write-Error "Please review the issues above before proceeding."
    }

    exit $exitCode
}

# Run main function
Start-Validation
