# Troubleshooting Guide

This guide provides solutions to common issues encountered when working with the docker-mcpai-stack.

## Common Issues

### 1. Docker Compose Fails to Start

- **Check Docker daemon is running**
- **Check for port conflicts**
- **Review logs with `docker compose logs`**

### 2. GPU Not Detected

- Ensure NVIDIA drivers and Docker NVIDIA runtime are installed
- Use `docker info | grep -i nvidia` to verify

### 3. Service Healthcheck Fails

- Inspect service logs: `docker compose logs <service>`
- Check healthcheck command in compose file

### 4. Model Not Loading

- Ensure model files are present in the `models/` directory or volume
- Check model runner logs for errors

### 5. Permission Issues

- Ensure you are not running as root unless required
- Check file and directory permissions

### 6. Backup/Restore Problems

- Ensure backup files exist and are not corrupted
- Check available disk space

## Getting More Help

- Review the [README](../../README.md) for setup instructions
- Open an issue on GitHub with detailed logs and steps to reproduce
