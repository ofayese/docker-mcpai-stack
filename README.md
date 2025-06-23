# docker-mcpai-stack

✨ A modern, cross-platform GenAI development environment with modular services

![Docker MCPAI Stack Demo](assets/demo.gif)

## ✨ Features

- 🚀 **Cross-platform**: Works on Linux, macOS, and Windows (WSL2) with auto-detection
- 🔌 **Modular Architecture**: Mix and match services to fit your needs
- 🧠 **Multiple Models**: Use any GGUF model with Docker Model Runner
- 🖥️ **GPU Acceleration**: CUDA support for faster inference
- 📈 **Observability**: Prometheus, Grafana, and Loki integration
- 🔒 **Security**: Non-root containers, vulnerability scanning, SBOM
- 👨‍💻 **Developer Experience**: VS Code devcontainer, hot-reload, and more

## 🚀 Quick Start

### Auto-Detection (Recommended)
```bash
# Clone the repository
git clone https://github.com/your-org/docker-mcpai-stack
cd docker-mcpai-stack

# Setup environment (auto-detects your OS)
chmod +x scripts/setup-environment.sh
./scripts/setup-environment.sh

# Start with auto-detection
make up

# Access the UI at http://localhost:8501
```

### Platform-Specific Quick Start

#### 🪟 Windows
```powershell
# Setup environment
.\scripts\setup-environment.ps1

# Start the stack
make up-windows
```

#### 🐧 Linux
```bash
# Setup environment
./scripts/setup-environment.sh

# Start the stack
make up-linux

# For GPU acceleration
make gpu-up
```

#### 🍎 macOS
```bash
# Setup environment
./scripts/setup-environment.sh

# Start the stack
make up-macos
```

## 📚 Documentation

- [Cross-Platform Support](docs/cross-platform-support.md)
- [Architecture Overview](docs/architecture/overview.md)
- [API Reference](docs/api/reference.md)
- [Developer Guide](docs/guides/developer.md)
- [Operations Guide](docs/guides/operations.md)
- [Troubleshooting](docs/guides/debug.md)

## 🔧 Development

```bash
# Start development environment with hot-reload
make dev

# Run tests
make test

# Format code
make format

# Generate documentation
make docs
```

## 🛠️ DevContainer Support

This project includes a devcontainer configuration for VS Code and GitHub Codespaces. Just open in VS Code and click "Reopen in Container" when prompted.

## 🆘 Troubleshooting

See the [Troubleshooting Guide](docs/guides/debug.md) for common issues and solutions.

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
