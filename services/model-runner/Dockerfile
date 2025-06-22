# Model Runner - Unified LLM API Service
# Based on Docker Model Runner with llama.cpp backend
FROM docker/model-runner:latest AS base

# Add custom configuration and scripts
WORKDIR /app

# Copy configuration files
COPY config/ /config/
COPY scripts/ /scripts/

# Create model cache directory
RUN mkdir -p /models

# Set environment variables
ENV MODEL_CACHE=/models
ENV CONFIG_PATH=/config
ENV RUNNER_HTTP_ADDR=0.0.0.0:8080
ENV LLAMA_SERVER_VARIANT=cpu

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
  CMD curl -f http://localhost:8080/health || exit 1

# Expose port
EXPOSE 8080

# Start the model runner
CMD ["model-runner", "--addr", "0.0.0.0:8080"]
