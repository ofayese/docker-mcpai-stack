#!/usr/bin/env pwsh
# PowerShell script for triggering SonarCloud analysis

param(
    [string]$Branch = "main"
)

Write-Host "Triggering SonarCloud analysis..." -ForegroundColor Green

# Check if we're in a git repository
if (-not (Test-Path ".git")) {
    Write-Error "This is not a git repository!"
    exit 1
}

# Check if we have uncommitted changes
$status = git status --porcelain
if ($status) {
    Write-Warning "You have uncommitted changes:"
    git status --short
    $response = Read-Host "Do you want to commit these changes first? (y/N)"
    if ($response -eq "y" -or $response -eq "Y") {
        $commitMessage = Read-Host "Enter commit message"
        git add .
        git commit -m "$commitMessage"
    }
}

# Push to trigger GitHub Actions
Write-Host "Pushing to GitHub to trigger SonarCloud analysis..." -ForegroundColor Blue
git push origin $Branch

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Code pushed successfully!" -ForegroundColor Green
    Write-Host "🚀 SonarCloud analysis will start automatically via GitHub Actions" -ForegroundColor Cyan
    Write-Host "📊 View results at: https://sonarcloud.io/organizations/ofayese/projects" -ForegroundColor Cyan
} else {
    Write-Error "❌ Failed to push to GitHub!"
    exit 1
}
