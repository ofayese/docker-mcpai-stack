.PHONY: help up gpu-up dev gpu-dev down build rebuild clean logs ps
.PHONY: test test-unit test-integration test-e2e test-load test-all test-osx test-linux
.PHONY: lint format docs docs-serve pull-models build-multiarch coverage sbom
.PHONY: monitoring backup restore metrics security-scan
.PHONY: dev-setup env-check health-check

# Show help for each of the Makefile recipes.
help: ## Show this help message
	@echo "Docker MCPAI Stack - Developer Commands"
	@echo "======================================="
	@echo ""
	@echo "🚀 DEVELOPMENT"
	@grep -E '^[a-zA-Z0-9_-]*dev[a-zA-Z0-9_-]*:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'
	@echo ""
	@echo "🏗️  BUILD & DEPLOYMENT"
	@grep -E '^(build|up|down|rebuild):.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'
	@echo ""
	@echo "🧪 TESTING"
	@grep -E '^test[a-zA-Z0-9_-]*:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'
	@echo ""
	@echo "📊 MONITORING & METRICS"
	@grep -E '^(monitoring|metrics|backup|restore):.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'
	@echo ""
	@echo "🔧 UTILITIES"
	@grep -E '^(clean|lint|format|docs|logs|ps|env-check|health-check):.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# Default profile (cpu or gpu)
PROFILE ?= cpu

# Docker compose command with base file
COMPOSE = docker compose -f compose/docker-compose.base.yml

up: ## Start stack (CPU mode)
	$(COMPOSE) --profile $(PROFILE) up -d

monitoring: ## Start stack with monitoring services
	$(COMPOSE) -f compose/docker-compose.monitoring.yml --profile $(PROFILE) --profile monitoring up -d

dev: ## Start development stack with hot-reload
	$(COMPOSE) -f compose/compose.dev.yaml --profile dev up

gpu-up: ## Start stack (GPU mode)
	$(COMPOSE) --profile gpu up -d

gpu-dev: ## Start GPU development stack with hot-reload
	$(COMPOSE) -f compose/compose.gpu.yaml --profile gpu up

down: ## Stop and remove all containers
	$(COMPOSE) down

test: test-unit ## Run all unit tests (default)

test-unit: ## Run unit tests only
	@echo "🧪 Running unit tests..."
	docker compose -f compose/docker-compose.test.yml --profile unit run --rm mcp-api-unit-tests

test-integration: ## Run integration tests
	@echo "🔗 Running integration tests..."
	docker compose -f compose/docker-compose.test.yml --profile integration up --exit-code-from mcp-api-integration
	docker compose -f compose/docker-compose.test.yml --profile integration down

test-e2e: ## Run end-to-end tests
	@echo "🌐 Running E2E tests..."
	docker compose -f compose/docker-compose.test.yml --profile e2e up --exit-code-from e2e-tests
	docker compose -f compose/docker-compose.test.yml --profile e2e down

test-load: ## Start load testing with Locust
	@echo "📈 Starting load tests..."
	@echo "Locust web interface will be available at http://localhost:8089"
	docker compose -f compose/docker-compose.test.yml --profile load up

test-all: ## Run complete test suite
	@echo "🎯 Running complete test suite..."
	$(MAKE) test-unit
	$(MAKE) test-integration
	$(MAKE) test-e2e
	@echo "✅ All tests completed!"

test-reports: ## Start test reports server
	@echo "📊 Starting test reports server..."
	@echo "Reports available at http://localhost:8082"
	docker compose -f compose/docker-compose.test.yml --profile reports up -d

test-osx: ## Run tests on macOS (ARM64)
	# macOS specific test commands
	echo "Running on macOS (ARM64)"
	docker compose run --rm mcpai-api pytest -m "not slow"

test-linux: ## Run tests on Linux
	# Linux specific test commands
	echo "Running on Linux"
	docker compose run --rm mcpai-api pytest

lint: ## Run linters
	docker compose run --rm mcpai-api bash -c "ruff check . && black --check ."

format: ## Format code with black and ruff
	docker compose run --rm mcpai-api bash -c "black . && ruff check --fix ."

docs: ## Generate documentation
	docker compose run --rm mcpai-api bash -c "cd docs && mkdocs build"
	@echo "Documentation built in docs/site/"

docs-serve: ## Serve documentation locally
	docker compose run --rm -p 8000:8000 mcpai-api bash -c "cd docs && mkdocs serve -a 0.0.0.0:8000"
	@echo "Documentation available at http://localhost:8000/"

pull-models: ## Pull all required models
	@echo "Pulling models..."
	docker model pull ai/llama3:8b
	docker model pull ai/mistral:7b
	@echo "Models downloaded successfully."

build-multiarch: ## Build multi-architecture images
	docker buildx bake --set *.platform=linux/amd64,linux/arm64

coverage: ## Generate test coverage report
	docker compose run --rm mcpai-api pytest --cov=src --cov-report=html

sbom: ## Generate Software Bill of Materials
	@echo "Generating SBOM for all services..."
	mkdir -p sbom
	trivy image --format cyclonedx mcpai-api > sbom/mcpai-api.json
	trivy image --format cyclonedx mcpai-worker > sbom/mcpai-worker.json
	@echo "SBOM generated in sbom/ directory"

backup: ## Create backup of all data volumes
	./scripts/backup.sh

restore: ## Restore from backup (usage: make restore BACKUP=backup-name)
	./scripts/restore.sh $(BACKUP)

metrics: ## Open Grafana metrics dashboard
	@echo "Opening Grafana dashboard at http://localhost:3000"
	@echo "Default credentials: admin/admin"
	@xdg-open http://localhost:3000 || open http://localhost:3000 || echo "Please open http://localhost:3000"

clean: ## Clean up volumes and containers
	$(COMPOSE) down -v
	docker system prune -f

rebuild: ## Rebuild and restart services
	$(COMPOSE) --profile $(PROFILE) up -d --build

logs: ## View logs from all services
	$(COMPOSE) logs -f

ps: ## Show running containers
	$(COMPOSE) ps

build: ## Build all service images
	@echo "🏗️  Building all service images..."
	$(COMPOSE) build

security-scan: ## Run security scans on images
	@echo "🔒 Running security scans..."
	@echo "Scanning MCP API image..."
	trivy image docker-mcpai-stack_mcp-api:latest
	@echo "Scanning UI image..."
	trivy image docker-mcpai-stack_ui:latest
	@echo "Scanning Mock Model Runner image..."
	trivy image docker-mcpai-stack_mock-model-runner:latest

env-check: ## Check environment setup
	@echo "🔍 Checking environment setup..."
	@echo "Docker version:"
	@docker --version
	@echo "Docker Compose version:"
	@docker compose version
	@echo "Available disk space:"
	@df -h
	@echo "Environment variables:"
	@echo "PROFILE: $(PROFILE)"

health-check: ## Check health of running services
	@echo "🏥 Checking service health..."
	@echo "MCP API:"
	@curl -f http://localhost:4000/health/ 2>/dev/null && echo "✅ Healthy" || echo "❌ Unhealthy"
	@echo "UI:"
	@curl -f http://localhost:8501 2>/dev/null && echo "✅ Healthy" || echo "❌ Unhealthy"
	@echo "Qdrant:"
	@curl -f http://localhost:6333/health 2>/dev/null && echo "✅ Healthy" || echo "❌ Unhealthy"
	@echo "Prometheus:"
	@curl -f http://localhost:9090/-/healthy 2>/dev/null && echo "✅ Healthy" || echo "❌ Unhealthy"
	@echo "Grafana:"
	@curl -f http://localhost:3000/api/health 2>/dev/null && echo "✅ Healthy" || echo "❌ Unhealthy"

dev-setup: ## Setup development environment
	@echo "🛠️  Setting up development environment..."
	@if [ ! -f .env ]; then \
		echo "Creating .env from .env.example..."; \
		cp .env.example .env; \
	fi
	@echo "Installing pre-commit hooks..."
	@docker compose -f compose/docker-compose.dev.yml run --rm mcp-api bash -c "pip install pre-commit && pre-commit install"
	@echo "✅ Development environment ready!"

## Production
.PHONY: prod-deploy prod-scale prod-restart prod-logs prod-backup prod-restore

prod-deploy: ## Deploy to production environment
	@echo "🚀 Deploying to production..."
	docker compose -f compose/docker-compose.production.yml pull
	docker compose -f compose/docker-compose.production.yml up -d
	@echo "✅ Production deployment complete"

prod-scale: ## Scale production services (usage: make prod-scale service=mcp-api replicas=3)
	@if [ -z "$(service)" ] || [ -z "$(replicas)" ]; then \
		echo "❌ Usage: make prod-scale service=<service_name> replicas=<number>"; \
		exit 1; \
	fi
	docker compose -f compose/docker-compose.production.yml up -d --scale $(service)=$(replicas)

prod-restart: ## Restart production services
	@echo "🔄 Restarting production services..."
	docker compose -f compose/docker-compose.production.yml restart
	@echo "✅ Production restart complete"

prod-logs: ## Follow production logs
	docker compose -f compose/docker-compose.production.yml logs -f

prod-backup: ## Create production backup
	@echo "💾 Creating production backup..."
	./scripts/backup.sh full
	@echo "✅ Backup complete"

prod-restore: ## Restore from backup (usage: make prod-restore backup=<backup_file>)
	@if [ -z "$(backup)" ]; then \
		echo "❌ Usage: make prod-restore backup=<backup_file>"; \
		exit 1; \
	fi
	./scripts/restore.sh $(backup)
