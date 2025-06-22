.PHONY: help up gpu-up dev gpu-dev down test lint format docs pull-models build-multiarch coverage sbom

# Show help for each of the Makefile recipes.
help: ## Show this help message
	@echo "Docker MCPAI Stack - Developer Commands"
	@echo "------------------------------------"
	@grep -E '^[a-zA-Z0-9_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

up: ## Start stack (CPU mode)
	docker compose -f compose/compose.yaml up -d

gpu-up: ## Start stack (GPU mode)
	docker compose -f compose/compose.yaml -f compose/compose.gpu.yaml --profile gpu up -d

dev: ## Start development stack with hot-reload
	docker compose -f compose/compose.yaml -f compose/compose.dev.yaml up

gpu-dev: ## Start GPU development stack with hot-reload
	docker compose -f compose/compose.yaml -f compose/compose.gpu.yaml -f compose/compose.dev.yaml --profile gpu up

down: ## Stop and remove all containers
	docker compose -f compose/compose.yaml down

test: ## Run tests
	docker compose run --rm mcpai-api pytest

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
