# Enhanced Docker MCPAI Stack

A comprehensive production-ready stack for AI applications with monitoring, metrics, and backup capabilities.

## 🚀 Features

- 🤖 **Model Serving**: Docker Model Runner integration with OpenAI-compatible API
- 🔍 **Vector Database**: Qdrant for embeddings and similarity search
- ⚡ **FastAPI Backend**: MCP (Model Context Protocol) gateway with metrics
- 🎨 **Streamlit UI**: Modern web interface for model interaction
- 📊 **Monitoring Stack**: Prometheus, Grafana, and Loki integration
- 🔄 **Auto Backup**: Automated backup and restore scripts
- 🐳 **Production Ready**: Health checks, logging, and scaling support

## 📋 Prerequisites

- Docker 24.0+ and Docker Compose v2
- Make (optional, for convenience commands)
- 8GB+ RAM recommended
- NVIDIA GPU (optional, for GPU acceleration)

## 🏃 Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/docker-mcpai-stack.git
cd docker-mcpai-stack
```

### 2. Start the Stack

**CPU Mode (Default):**

```bash
make up
# or
docker compose -f compose/docker-compose.base.yml --profile cpu up -d
```

**GPU Mode:**

```bash
make PROFILE=gpu up
# or
docker compose -f compose/docker-compose.base.yml --profile gpu up -d
```

**With Monitoring:**

```bash
make monitoring
```

### 3. Access Services

- **UI Dashboard**: <http://localhost:8501>
- **API Documentation**: <http://localhost:4000/docs>
- **Prometheus**: <http://localhost:9090>
- **Grafana**: <http://localhost:3000> (admin/admin)
- **Qdrant**: <http://localhost:6333/dashboard>

## 📊 Monitoring & Metrics

The stack includes comprehensive monitoring:

- **Prometheus**: Metrics collection and alerting
- **Grafana**: Visualization dashboards
- **Loki**: Centralized logging
- **Custom Metrics**: API requests, model inference times, system health

Key metrics tracked:

- API request counts by endpoint
- Model inference duration and success rates
- Active request counters
- System resource usage

## 💾 Backup & Restore

### Create Backup

```bash
make backup
# or
./scripts/backup.sh
```

### Restore from Backup

```bash
make restore BACKUP=backup-name
# or
./scripts/restore.sh backup-name
```

Backups include:

- Qdrant vector database
- Model cache and configurations
- MCP data and logs
- Environment configurations

## 🛠️ Development

### Development Mode

```bash
make dev
```

This starts the stack with:

- Hot-reload enabled
- Debug logging
- Development profiles

### Available Commands

```bash
make help                 # Show all available commands
make up                   # Start CPU stack
make gpu-up              # Start GPU stack
make monitoring          # Start with monitoring
make down                # Stop all services
make logs                # View logs
make ps                  # Show running containers
make clean               # Clean up volumes
make rebuild             # Rebuild and restart
```

## 🔧 Configuration

Environment variables can be set in `.env` file:

```env
# API Configuration
MODEL_API_URL=http://model-runner:8080/v1
QDRANT_URL=http://qdrant:6333
MCP_API_PORT=4000

# Monitoring
PROMETHEUS_PORT=9090
GRAFANA_PORT=3000
GRAFANA_ADMIN_PASSWORD=secure_password

# GPU Support
NVIDIA_VISIBLE_DEVICES=all
```

## 📁 Project Structure

```
docker-mcpai-stack/
├── compose/                 # Docker Compose configurations
│   ├── docker-compose.base.yml
│   ├── docker-compose.monitoring.yml
│   └── docker-compose.*.yml
├── services/               # Application services
│   ├── mcp-api/           # FastAPI MCP gateway
│   ├── mcp-worker/        # Background processing
│   ├── model-runner/      # Model serving
│   └── ui/                # Streamlit interface
├── grafana/               # Grafana configurations
│   ├── dashboards/
│   └── datasources/
├── prometheus/            # Prometheus configuration
├── scripts/              # Utility scripts
│   ├── backup.sh
│   └── restore.sh
└── Makefile              # Development commands
```

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Streamlit UI  │────│   MCP API       │────│  Model Runner   │
│   (Port 8501)   │    │   (Port 4000)   │    │   (Port 8080)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                        │                        │
         └────────────────────────┼────────────────────────┘
                                  │
                    ┌─────────────────┐
                    │     Qdrant      │
                    │   (Port 6333)   │
                    └─────────────────┘
                                  │
              ┌───────────────────┼───────────────────┐
              │                   │                   │
    ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
    │   Prometheus    │ │     Grafana     │ │      Loki       │
    │   (Port 9090)   │ │   (Port 3000)   │ │   (Port 3100)   │
    └─────────────────┘ └─────────────────┘ └─────────────────┘
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🐛 Troubleshooting

### Common Issues

**Service won't start:**

```bash
make down && make clean && make up
```

**Port conflicts:**
Check and modify ports in `.env` file

**GPU not detected:**
Ensure NVIDIA Container Toolkit is installed

**Backup fails:**
Check disk space and Docker volume permissions

For more help, check the logs:

```bash
make logs
```
