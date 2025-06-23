#!/usr/bin/env pwsh
# PowerShell script for offline SonarQube analysis using Docker

param(
    [string]$ConfigFile = "sonar-project.local.properties"
)

Write-Host "Running SonarQube analysis offline using Docker..." -ForegroundColor Green
Write-Host "Using configuration file: $ConfigFile" -ForegroundColor Yellow

# Check if the config file exists
if (-not (Test-Path $ConfigFile)) {
    Write-Error "Configuration file '$ConfigFile' not found!"
    Write-Host "Available configuration files:" -ForegroundColor Yellow
    Get-ChildItem -Filter "sonar-project*.properties" | ForEach-Object { Write-Host "  - $($_.Name)" }
    exit 1
}

# Check if Docker is running
try {
    docker version | Out-Null
    if ($LASTEXITCODE -ne 0) {
        throw "Docker not responding"
    }
} catch {
    Write-Error "Docker is not running or not installed. Please start Docker Desktop."
    exit 1
}

# Run SonarQube Scanner with Docker
Write-Host "Starting Docker container..." -ForegroundColor Blue
docker run --rm -v "${PWD}:/usr/src" sonarsource/sonar-scanner-cli -Dproject.settings=$ConfigFile

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ SonarQube analysis completed successfully!" -ForegroundColor Green
    Write-Host "View results at: http://localhost:9000" -ForegroundColor Cyan
} else {
    Write-Error "❌ SonarQube analysis failed!"
    exit 1
}
