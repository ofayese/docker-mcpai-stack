#!/bin/bash
# Bash script for offline SonarQube analysis using Docker

CONFIG_FILE=${1:-"sonar-project.local.properties"}

echo "🔍 Running SonarQube analysis offline using Docker..."
echo "📄 Using configuration file: $CONFIG_FILE"

# Check if the config file exists
if [ ! -f "$CONFIG_FILE" ]; then
    echo "❌ Configuration file '$CONFIG_FILE' not found!"
    echo "Available configuration files:"
    ls sonar-project*.properties 2>/dev/null || echo "  No sonar-project*.properties files found"
    exit 1
fi

# Check if Docker is running
if ! docker version >/dev/null 2>&1; then
    echo "❌ Docker is not running or not installed. Please start Docker."
    exit 1
fi

# Run SonarQube Scanner with Docker
echo "🐳 Starting Docker container..."
docker run --rm -v "$(pwd):/usr/src" sonarsource/sonar-scanner-cli -Dproject.settings="$CONFIG_FILE"

if [ $? -eq 0 ]; then
    echo "✅ SonarQube analysis completed successfully!"
    echo "🌐 View results at: http://localhost:9000"
else
    echo "❌ SonarQube analysis failed!"
    exit 1
fi
