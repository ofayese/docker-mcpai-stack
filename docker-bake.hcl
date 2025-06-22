group "default" {
  targets = ["mcpai-api", "mcpai-worker", "mcpai-ui"]
}

target "docker-metadata-action" {}

target "build-common" {
  context = "."
  platforms = ["linux/amd64", "linux/arm64"]
  cache-from = ["type=gha"]
  cache-to = ["type=gha,mode=max"]
}

target "mcpai-api" {
  inherits = ["build-common"]
  dockerfile = "services/mcp-api/Dockerfile"
  tags = ["mcpai-api:latest"]
}

target "mcpai-worker" {
  inherits = ["build-common"]
  dockerfile = "services/mcp-worker/Dockerfile"
  tags = ["mcpai-worker:latest"]
}

target "mcpai-ui" {
  inherits = ["build-common"]
  dockerfile = "services/ui/Dockerfile"
  tags = ["mcpai-ui:latest"]
}
