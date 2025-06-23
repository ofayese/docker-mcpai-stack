#!/usr/bin/env pwsh
# PowerShell script for markdown linting operations
# Docker MCP Stack - Documentation Linting Utility

param(
    [Parameter(Mandatory = $true)]
    [ValidateSet("check", "fix", "report", "help")]
    [string]$Action,
    
    [string]$Path = ".",
    [string]$Output = "markdown-lint-report.txt"
)

function Show-Help {
    Write-Host "Docker MCP Stack - Markdown Linting Utility" -ForegroundColor Green
    Write-Host "=============================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "Usage: ./scripts/lint-docs.ps1 -Action <action> [options]" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Actions:" -ForegroundColor Cyan
    Write-Host "  check   - Check markdown files for issues"
    Write-Host "  fix     - Auto-fix markdown issues where possible"
    Write-Host "  report  - Generate detailed linting report"
    Write-Host "  help    - Show this help message"
    Write-Host ""
    Write-Host "Options:" -ForegroundColor Cyan
    Write-Host "  -Path    - Path to check (default: current directory)"
    Write-Host "  -Output  - Output file for reports (default: markdown-lint-report.txt)"
    Write-Host ""
    Write-Host "Examples:" -ForegroundColor Magenta
    Write-Host "  ./scripts/lint-docs.ps1 -Action check"
    Write-Host "  ./scripts/lint-docs.ps1 -Action fix -Path docs/"
    Write-Host "  ./scripts/lint-docs.ps1 -Action report -Output custom-report.txt"
}

function Test-Prerequisites {
    # Check if markdownlint-cli is installed
    try {
        $null = Get-Command markdownlint -ErrorAction Stop
    }
    catch {
        Write-Error "markdownlint-cli is not installed. Run 'npm install' first."
        exit 1
    }
}

function Invoke-MarkdownLint {
    param([string]$Command)
    
    Write-Host "Running: $Command" -ForegroundColor Yellow
    Invoke-Expression $Command
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Markdown linting completed with issues." -ForegroundColor Red
        exit $LASTEXITCODE
    }
    else {
        Write-Host "Markdown linting completed successfully!" -ForegroundColor Green
    }
}

# Main script logic
switch ($Action) {
    "check" {
        Test-Prerequisites
        $cmd = "markdownlint '$Path/**/*.md' --ignore node_modules --config .markdownlint.json"
        Invoke-MarkdownLint $cmd
    }
    
    "fix" {
        Test-Prerequisites
        $cmd = "markdownlint '$Path/**/*.md' --ignore node_modules --config .markdownlint.json --fix"
        Invoke-MarkdownLint $cmd
    }
    
    "report" {
        Test-Prerequisites
        $cmd = "markdownlint '$Path/**/*.md' --ignore node_modules --config .markdownlint.json --output '$Output'"
        Invoke-MarkdownLint $cmd
        Write-Host "Report generated: $Output" -ForegroundColor Green
    }
    
    "help" {
        Show-Help
    }
}
