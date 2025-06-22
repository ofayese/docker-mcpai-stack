# Streamlit UI Service
FROM python:3.12-slim AS base

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Development stage
FROM base AS development

# Copy application code
COPY src/ ./src/

# Set development environment variables
ENV PYTHONUNBUFFERED=1
ENV STREAMLIT_SERVER_PORT=8501
ENV STREAMLIT_SERVER_ADDRESS=0.0.0.0
ENV STREAMLIT_SERVER_RUNONSAVE=true

# Enable file watching for hot reload
CMD ["streamlit", "run", "src/app.py", "--server.port", "8501", "--server.address", "0.0.0.0", "--server.fileWatcherType", "poll"]

# Production stage
FROM base AS production

# Copy application code
COPY src/ ./src/

# Create non-root user
RUN adduser --disabled-password --gecos "" streamlit
USER streamlit

# Set production environment variables
ENV PYTHONUNBUFFERED=1
ENV STREAMLIT_SERVER_PORT=8501
ENV STREAMLIT_SERVER_ADDRESS=0.0.0.0
ENV STREAMLIT_SERVER_HEADLESS=true

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
  CMD curl -f http://localhost:8501/_stcore/health || exit 1

# Expose Streamlit port
EXPOSE 8501

# Start Streamlit
CMD ["streamlit", "run", "src/app.py", "--server.port", "8501", "--server.address", "0.0.0.0"]
