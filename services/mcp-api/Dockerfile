# MCP API Gateway
# FastAPI-based service for MCP protocol handling
FROM python:3.12-slim AS base

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Development stage
FROM base AS development

# Install development dependencies
RUN pip install --no-cache-dir pytest pytest-asyncio httpx black ruff

# Copy application code
COPY src/ ./src/

# Enable hot reload and debugging
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV DEBUG=true

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "4000", "--reload"]

# Test stage
FROM development AS test

# Copy test files
COPY tests/ ./tests/

# Set test environment
ENV ENVIRONMENT=test

CMD ["pytest", "-xvs"]

# Production stage
FROM python:3.12-slim AS production

WORKDIR /app

# Install runtime dependencies only
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy installed packages from base stage
COPY --from=base /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=base /usr/local/bin /usr/local/bin

# Copy application code
COPY src/ ./src/

# Create data directory
RUN mkdir -p /data

# Set production environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV ENVIRONMENT=production

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
  CMD curl -f http://localhost:4000/health || exit 1

# Expose port
EXPOSE 4000

# Start the application
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "4000"]
