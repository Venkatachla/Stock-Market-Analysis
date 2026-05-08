# 🐳 StockPulse Docker - README

Welcome! This guide will help you get StockPulse running in Docker quickly.

## ⚡ Super Quick Start (5 minutes)

### Prerequisites
- Docker Desktop installed: https://docs.docker.com/desktop/install/
- Docker daemon running

### Build and Run
```bash
# 1. Build the image
docker build -t stockpulse:latest .

# 2. Run the container
docker run -p 8000:8000 stockpulse:latest

# 3. Open in browser
# http://localhost:8000
```

## 🎯 Available Resources

### 📚 Documentation
- **[DOCKER_CHEATSHEET.md](DOCKER_CHEATSHEET.md)** - Quick commands
- **[DOCKER_GUIDE.md](DOCKER_GUIDE.md)** - Complete guide (2,000+ lines)
- **[DOCKER_DAEMON_SETUP.md](DOCKER_DAEMON_SETUP.md)** - Troubleshooting
- **[DOCKER_INDEX.md](DOCKER_INDEX.md)** - Documentation index

### 🔧 Configuration
- **[Dockerfile](Dockerfile)** - Container build specification
- **[docker-compose.yml](docker-compose.yml)** - Multi-service setup
- **[.env.docker](.env.docker)** - Environment variables
- **[.dockerignore](.dockerignore)** - Build optimization

### 🚀 Automation
- **[docker-build-push.bat](docker-build-push.bat)** - Windows script
- **[docker-build-push.sh](docker-build-push.sh)** - Linux/Mac script

## 📋 Common Tasks

### Build Image
```bash
docker build -t stockpulse:latest .
```

### Run Locally
```bash
docker run -p 8000:8000 stockpulse:latest
```

### Run with Persistent Data
```bash
docker run -p 8000:8000 \
  -v ./db.sqlite3:/app/db.sqlite3 \
  -v ./data:/app/data \
  stockpulse:latest
```

### Use Docker Compose
```bash
docker-compose up -d
docker-compose down
```

### Push to Docker Hub
```bash
docker login
docker tag stockpulse:latest your-username/stockpulse:latest
docker push your-username/stockpulse:latest
```

## 🆘 Help & Troubleshooting

### Docker Daemon Not Running
See: [DOCKER_DAEMON_SETUP.md](DOCKER_DAEMON_SETUP.md)

### Build Failed
See: [DOCKER_GUIDE.md#troubleshooting](DOCKER_GUIDE.md#troubleshooting)

### Quick Reference
See: [DOCKER_CHEATSHEET.md](DOCKER_CHEATSHEET.md)

## 📊 System Info

- **Base Image:** Python 3.11-Slim
- **Port:** 8000
- **Database:** SQLite (persistent)
- **Build Time:** 3-5 minutes
- **Image Size:** ~1.2GB

## 🎯 Next Steps

1. Ensure Docker is running: `docker ps`
2. Build: `docker build -t stockpulse:latest .`
3. Run: `docker run -p 8000:8000 stockpulse:latest`
4. Test: Visit http://localhost:8000

---

**For detailed instructions, see [DOCKER_INDEX.md](DOCKER_INDEX.md)**
