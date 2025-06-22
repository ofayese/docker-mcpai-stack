#!/bin/bash
# Enhanced backup script for docker-mcpai-stack
# Uses XZ compression for better compression ratio

set -e

# Configuration
BACKUP_DIR="./backups"
DATE=$(date +%Y-%m-%d-%H%M%S)
BACKUP_NAME="mcpai-backup-${DATE}"
FULL_BACKUP_PATH="${BACKUP_DIR}/${BACKUP_NAME}"

# Create backup directory
mkdir -p "${BACKUP_DIR}"
mkdir -p "${FULL_BACKUP_PATH}"

echo "Starting backup ${BACKUP_NAME}..."

# 1. Back up Qdrant data
echo "Backing up Qdrant database..."
docker exec mcpai-qdrant tar -c -C /qdrant/storage . | lz4 > "${FULL_BACKUP_PATH}/qdrant.tar.lz4"

# 2. Back up models (using XZ for better compression)
echo "Backing up models..."
docker run --rm -v mcpai_models:/models -v "${FULL_BACKUP_PATH}:/backup" alpine \
  tar -cJf /backup/models.tar.xz -C /models .

# 3. Back up MCP data
echo "Backing up MCP data..."
docker run --rm -v mcpai_mcp_data:/data -v "${FULL_BACKUP_PATH}:/backup" alpine \
  tar -cJf /backup/mcp_data.tar.xz -C /data .

# 4. Back up configuration
echo "Backing up configuration..."
cp .env "${FULL_BACKUP_PATH}/env-config.backup" 2>/dev/null || echo "No .env file found, skipping."
cp -r compose "${FULL_BACKUP_PATH}/compose-config"

# Create metadata file
cat > "${FULL_BACKUP_PATH}/metadata.json" << EOF
{
  "backup_name": "${BACKUP_NAME}",
  "date": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "docker_version": "$(docker --version)",
  "components": ["qdrant", "models", "mcp_data", "configuration"]
}
EOF

echo "Backup completed successfully at ${FULL_BACKUP_PATH}"
