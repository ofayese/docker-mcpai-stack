#!/bin/bash
# Restore script for docker-mcpai-stack

set -e

# Check arguments
if [ $# -lt 1 ]; then
  echo "Usage: $0 <backup-name> [--force]"
  echo "Available backups:"
  ls -1 ./backups
  exit 1
fi

BACKUP_NAME=$1
FORCE=0

if [ "$2" == "--force" ]; then
  FORCE=1
fi

BACKUP_PATH="./backups/${BACKUP_NAME}"

# Check if backup exists
if [ ! -d "${BACKUP_PATH}" ]; then
  echo "Error: Backup '${BACKUP_NAME}' not found in ./backups"
  exit 1
fi

# Check if metadata exists
if [ ! -f "${BACKUP_PATH}/metadata.json" ]; then
  echo "Error: Invalid backup - metadata.json not found"
  exit 1
fi

echo "Preparing to restore backup: ${BACKUP_NAME}"
cat "${BACKUP_PATH}/metadata.json"

# Confirm unless --force is used
if [ $FORCE -eq 0 ]; then
  read -p "This will overwrite existing data. Continue? (y/N): " CONFIRM
  if [ "$CONFIRM" != "y" ] && [ "$CONFIRM" != "Y" ]; then
    echo "Restore cancelled."
    exit 0
  fi
fi

# Stop running services
echo "Stopping running services..."
docker compose -f compose/compose.yaml down

# Restore Qdrant data
if [ -f "${BACKUP_PATH}/qdrant.tar.lz4" ]; then
  echo "Restoring Qdrant data..."
  docker volume rm mcpai_qdrant_data || true
  docker volume create mcpai_qdrant_data
  lz4 -d "${BACKUP_PATH}/qdrant.tar.lz4" | docker run --rm -i -v mcpai_qdrant_data:/data alpine tar -x -C /data
fi

# Restore models
if [ -f "${BACKUP_PATH}/models.tar.xz" ]; then
  echo "Restoring models..."
  docker volume rm mcpai_models || true
  docker volume create mcpai_models
  docker run --rm -v mcpai_models:/models -v "${BACKUP_PATH}:/backup" alpine \
    tar -xf /backup/models.tar.xz -C /models
fi

# Restore MCP data
if [ -f "${BACKUP_PATH}/mcp_data.tar.xz" ]; then
  echo "Restoring MCP data..."
  docker volume rm mcpai_mcp_data || true
  docker volume create mcpai_mcp_data
  docker run --rm -v mcpai_mcp_data:/data -v "${BACKUP_PATH}:/backup" alpine \
    tar -xf /backup/mcp_data.tar.xz -C /data
fi

# Restore configuration if needed
if [ -f "${BACKUP_PATH}/env-config.backup" ]; then
  if [ $FORCE -eq 1 ] || [ ! -f .env ]; then
    echo "Restoring .env configuration..."
    cp "${BACKUP_PATH}/env-config.backup" .env
  else
    echo "Existing .env file found. Use --force to overwrite."
    cp "${BACKUP_PATH}/env-config.backup" .env.backup
  fi
fi

echo "Restore completed successfully. You can now start services with 'docker compose up'"
