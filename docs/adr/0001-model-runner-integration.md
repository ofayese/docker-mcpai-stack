# ADR 0001: Model Runner Integration

## Status

Accepted

## Context

We need a standardized way to serve LLM models in our docker-mcpai-stack. Options include:

1. Custom Python-based model serving
2. Ollama integration
3. Docker Model Runner integration

## Decision

We will use Docker Model Runner as our primary model serving solution.

## Rationale

- Provides a standardized OpenAI-compatible API
- Optimized for Docker environments
- GPU acceleration support
- Prometheus metrics built-in
- Multi-architecture support
- Actively maintained by Docker

## Consequences

- We'll need to adapt our API to work with Model Runner's endpoints
- We'll need to document the model management workflow
- We'll gain better performance and standardization
