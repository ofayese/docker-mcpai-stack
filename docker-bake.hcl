# Docker Bake configuration for multi-platform builds
# Usage: docker buildx bake --set *.platform=linux/amd64,linux/arm64

variable "REGISTRY" {
  default = "docker.io"
}

variable "TAG" {
  default = "latest"
}

# Define platform targets
variable "PLATFORMS" {
  default = "linux/amd64,linux/arm64"
}

group "default" {
  targets = ["mcpai-api", "mcpai-worker", "mcpai-ui", "model-runner"]
}

group "core" {
  targets = ["mcpai-api", "mcpai-worker", "model-runner"]
}

group "ui" {
  targets = ["mcpai-ui"]
}

target "docker-metadata-action" {}

# Common target configurations
target "build-common" {
  context = "."
  platforms = split(",", PLATFORMS)
  cache-from = ["type=gha"]
  cache-to = ["type=gha,mode=max"]
  labels = {
    "org.opencontainers.image.created" = timestamp()
    "org.opencontainers.image.source" = "https://github.com/your-org/docker-mcpai-stack"
    "org.opencontainers.image.vendor" = "Docker MCPAI Stack"
  }
}

# MCP API Service
target "mcpai-api" {
  inherits = ["build-common"]
  dockerfile = "services/mcp-api/Dockerfile"
  tags = [
    "${REGISTRY}/mcpai-api:${TAG}",
    "${REGISTRY}/mcpai-api:latest"
  ]
  cache-from = [
    "type=gha,scope=mcp-api"
  ]
  cache-to = [
    "type=gha,scope=mcp-api,mode=max"
  ]
}

# MCP Worker Service
target "mcpai-worker" {
  inherits = ["build-common"]
  dockerfile = "services/mcp-worker/Dockerfile"
  tags = [
    "${REGISTRY}/mcpai-worker:${TAG}",
    "${REGISTRY}/mcpai-worker:latest"
  ]
  cache-from = [
    "type=gha,scope=mcp-worker"
  ]
  cache-to = [
    "type=gha,scope=mcp-worker,mode=max"
  ]
}

# UI Service
target "mcpai-ui" {
  inherits = ["build-common"]
  dockerfile = "services/ui/Dockerfile"
  tags = [
    "${REGISTRY}/mcpai-ui:${TAG}",
    "${REGISTRY}/mcpai-ui:latest"
  ]
  cache-from = [
    "type=gha,scope=ui"
  ]
  cache-to = [
    "type=gha,scope=ui,mode=max"
  ]
}

# Model Runner Service
target "model-runner" {
  inherits = ["build-common"]
  dockerfile = "services/model-runner/Dockerfile"
  tags = [
    "${REGISTRY}/mcpai-model-runner:${TAG}",
    "${REGISTRY}/mcpai-model-runner:latest"
  ]
  cache-from = [
    "type=gha,scope=model-runner"
  ]
  cache-to = [
    "type=gha,scope=model-runner,mode=max"
  ]
}

# Platform-specific targets
target "linux-amd64" {
  inherits = ["default"]
  platforms = ["linux/amd64"]
}

target "linux-arm64" {
  inherits = ["default"]
  platforms = ["linux/arm64"]
}

# Development targets (single platform for faster builds)
target "dev" {
  inherits = ["build-common"]
  platforms = ["linux/amd64"]
  tags = [
    "${REGISTRY}/mcpai-api:dev",
    "${REGISTRY}/mcpai-worker:dev",
    "${REGISTRY}/mcpai-ui:dev",
    "${REGISTRY}/mcpai-model-runner:dev"
  ]
}
