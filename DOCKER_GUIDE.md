# StockPulse Docker Deployment Guide

## 📋 Table of Contents
1. [Prerequisites](#prerequisites)
2. [Quick Start](#quick-start)
3. [Building the Image](#building-the-image)
4. [Running Locally](#running-locally)
5. [Pushing to Docker Hub](#pushing-to-docker-hub)
6. [Production Deployment](#production-deployment)
7. [Troubleshooting](#troubleshooting)
8. [Advanced Configuration](#advanced-configuration)

---

## Prerequisites

### Required Software
- **Docker Desktop** (20.10+)
  - [Download for Windows](https://docs.docker.com/desktop/install/windows-install/)
  - [Download for Mac](https://docs.docker.com/desktop/install/mac-install/)
  - [Download for Linux](https://docs.docker.com/engine/install/)

- **Docker Hub Account**
  - Sign up at [hub.docker.com](https://hub.docker.com)
  - Note your Docker username

### System Requirements
- **Disk Space:** 2GB minimum (1GB base image + 1GB application)
- **RAM:** 2GB minimum (4GB recommended)
- **CPU:** 2 cores minimum

### Verify Installation
```bash
docker --version
docker run hello-world
docker login  # Verify Docker Hub access
```

---

## Quick Start

### Option 1: Using Docker Compose (Recommended)
```bash
# Navigate to project root
cd /path/to/STCOK

# Start services
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### Option 2: Using Build Scripts

**Windows:**
```cmd
docker-build-push.bat
```

**Linux/Mac:**
```bash
bash docker-build-push.sh
```

---

## Building the Image

### Manual Build

**Step 1: Set Your Docker Username**
```bash
# Windows (PowerShell)
$env:DOCKER_USERNAME = "your-docker-username"

# Linux/Mac (Bash)
export DOCKER_USERNAME="your-docker-username"
```

**Step 2: Build the Image**
```bash
docker build -t ${DOCKER_USERNAME}/stockpulse:latest .
```

**Step 3: Verify Build**
```bash
docker images | grep stockpulse
```

Expected output:
```
REPOSITORY             TAG       IMAGE ID       CREATED         SIZE
your-username/stockpulse   latest    abc123def456   2 minutes ago   1.2GB
```

### Build Arguments

```bash
# With build arguments
docker build \
  --build-arg NODE_ENV=production \
  --build-arg PYTHON_ENV=production \
  -t ${DOCKER_USERNAME}/stockpulse:latest .
```

### Multi-Stage Build Details

1. **Stage 1: Frontend Builder (Node 18)**
   - Installs dependencies: `npm install`
   - Builds React app: `npm run build`
   - Output: `/app/frontend/dist`

2. **Stage 2: Runtime (Python 3.11)**
   - Installs Python dependencies: `pip install -r requirements.txt`
   - Copies built frontend
   - Runs Uvicorn server on port 8000

---

## Running Locally

### Basic Run

```bash
docker run -p 8000:8000 ${DOCKER_USERNAME}/stockpulse:latest
```

Access at: `http://localhost:8000`

### With Environment Variables

```bash
docker run \
  -p 8000:8000 \
  -e DATABASE_URL=sqlite:///./db.sqlite3 \
  -e SECRET_KEY=your-secret-key-here \
  -e VITE_API_URL=http://localhost:8000 \
  ${DOCKER_USERNAME}/stockpulse:latest
```

### With Volume Mounts (Persistent Data)

```bash
docker run \
  -p 8000:8000 \
  -v $(pwd)/db.sqlite3:/app/db.sqlite3 \
  -v $(pwd)/data:/app/data \
  ${DOCKER_USERNAME}/stockpulse:latest
```

### With .env File

```bash
docker run \
  -p 8000:8000 \
  --env-file .env.docker \
  ${DOCKER_USERNAME}/stockpulse:latest
```

### Interactive Mode (Development)

```bash
docker run -it \
  -p 8000:8000 \
  -v $(pwd):/app \
  ${DOCKER_USERNAME}/stockpulse:latest \
  bash
```

### Named Container with Auto-Restart

```bash
docker run \
  -d \
  --name stockpulse-api \
  -p 8000:8000 \
  --restart unless-stopped \
  ${DOCKER_USERNAME}/stockpulse:latest
```

**Manage Named Container:**
```bash
# Check status
docker ps | grep stockpulse-api

# View logs
docker logs stockpulse-api

# Stop container
docker stop stockpulse-api

# Start container
docker start stockpulse-api

# Remove container
docker rm stockpulse-api
```

---

## Pushing to Docker Hub

### Prerequisites
```bash
# Login to Docker Hub
docker login
# Enter username and password when prompted
```

### Step-by-Step Push

**Step 1: Tag Image**
```bash
docker tag stockpulse:latest ${DOCKER_USERNAME}/stockpulse:latest
```

**Step 2: Verify Tag**
```bash
docker images | grep stockpulse
```

**Step 3: Push to Docker Hub**
```bash
docker push ${DOCKER_USERNAME}/stockpulse:latest
```

**Step 4: Verify on Docker Hub**
```bash
# Visit https://hub.docker.com/repositories
# Look for: ${DOCKER_USERNAME}/stockpulse
```

### Push with Version Tags

```bash
# Tag with version
docker tag stockpulse:latest ${DOCKER_USERNAME}/stockpulse:1.0.0
docker tag stockpulse:latest ${DOCKER_USERNAME}/stockpulse:latest

# Push both
docker push ${DOCKER_USERNAME}/stockpulse:1.0.0
docker push ${DOCKER_USERNAME}/stockpulse:latest
```

### Automated Tagging and Push

```bash
#!/bin/bash
DOCKER_USERNAME="your-username"
VERSION="1.0.0"

# Build
docker build -t ${DOCKER_USERNAME}/stockpulse:${VERSION} .

# Tag latest
docker tag ${DOCKER_USERNAME}/stockpulse:${VERSION} ${DOCKER_USERNAME}/stockpulse:latest

# Push both
docker push ${DOCKER_USERNAME}/stockpulse:${VERSION}
docker push ${DOCKER_USERNAME}/stockpulse:latest

echo "✅ Pushed to Docker Hub: ${DOCKER_USERNAME}/stockpulse"
```

---

## Production Deployment

### Environment Configuration

**Create .env for production:**
```env
# Database
DATABASE_URL=postgresql://user:pass@db.example.com:5432/stockpulse

# Security
SECRET_KEY=your-very-secure-production-key-change-me-32-chars-minimum!
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# API Configuration
FRONTEND_URL=https://stockpulse.com
VITE_API_URL=https://api.stockpulse.com

# Payments
RAZORPAY_KEY_ID=your-production-key-id
RAZORPAY_KEY_SECRET=your-production-key-secret

# Logging
LOG_LEVEL=info
DEBUG=false
```

### Running Production Container

```bash
docker run \
  -d \
  --name stockpulse-prod \
  -p 8000:8000 \
  --restart always \
  --env-file .env.production \
  -v /data/stockpulse/db:/app/db \
  -v /data/stockpulse/data:/app/data \
  --health-cmd='curl -f http://localhost:8000/health || exit 1' \
  --health-interval=30s \
  --health-timeout=10s \
  --health-retries=3 \
  your-username/stockpulse:latest
```

### Docker Compose Production

```bash
# Use production compose file
docker-compose -f docker-compose.yml up -d

# Monitor services
docker-compose ps
docker-compose logs -f

# Update and restart
docker-compose pull
docker-compose up -d
```

### Nginx Reverse Proxy

```nginx
upstream stockpulse {
    server localhost:8000;
}

server {
    listen 80;
    server_name api.stockpulse.com;

    location / {
        proxy_pass http://stockpulse;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

---

## Troubleshooting

### Container Won't Start

```bash
# Check logs
docker logs stockpulse-api

# Specific error
docker logs stockpulse-api --tail 50

# Follow logs in real-time
docker logs -f stockpulse-api
```

### Port Already in Use

```bash
# Find process on port 8000
# Windows
netstat -ano | findstr :8000

# Linux/Mac
lsof -i :8000

# Use different port
docker run -p 9000:8000 stockpulse:latest
```

### Database Connection Issues

```bash
# Verify volume mount
docker inspect stockpulse-api | grep -A 3 Mounts

# Check database file
docker exec stockpulse-api ls -la /app/db.sqlite3

# Reset database
docker exec stockpulse-api python -c "import db_utils; db_utils.init_db()"
```

### Memory Issues

```bash
# Check container resource usage
docker stats stockpulse-api

# Limit memory usage
docker run \
  -m 2g \
  --memory-swap 2g \
  -p 8000:8000 \
  stockpulse:latest
```

### Health Check Failures

```bash
# Manual health check
curl http://localhost:8000/health

# Inside container
docker exec stockpulse-api curl http://localhost:8000/health

# Detailed health
docker exec stockpulse-api curl -v http://localhost:8000/health
```

---

## Advanced Configuration

### Custom Docker Network

```bash
# Create network
docker network create stockpulse-net

# Run container on network
docker run \
  --network stockpulse-net \
  --name stockpulse-api \
  -p 8000:8000 \
  stockpulse:latest
```

### Docker Registry (Private)

```bash
# Tag for private registry
docker tag stockpulse:latest registry.example.com/stockpulse:latest

# Login to private registry
docker login registry.example.com

# Push to private registry
docker push registry.example.com/stockpulse:latest

# Pull from private registry
docker pull registry.example.com/stockpulse:latest
```

### Build Optimization

```bash
# Multi-stage build (already used in Dockerfile)
# Reduces final image size by excluding build dependencies

# Build without cache
docker build --no-cache -t stockpulse:latest .

# View build layers
docker history stockpulse:latest

# Check image size
docker images | grep stockpulse
```

### Debugging Inside Container

```bash
# Open shell in running container
docker exec -it stockpulse-api /bin/bash

# Check Python environment
docker exec stockpulse-api python --version
docker exec stockpulse-api pip list

# Check Node environment
docker exec stockpulse-api node --version

# View environment variables
docker exec stockpulse-api env
```

---

## Performance Optimization

### Image Size Reduction

Current size: ~1.2GB (includes Python runtime + Node runtime in intermediate stages)

**Techniques applied:**
- Multi-stage build (removes Node from final image)
- Alpine Linux for Python base
- `.dockerignore` to exclude unnecessary files

### Layer Caching

```bash
# Order matters for caching efficiency
# 1. Copy dependency files first
# 2. Install dependencies
# 3. Copy source code
# 4. Build application

# This allows Docker to reuse layers if dependencies don't change
```

### Runtime Performance

```bash
# Run with resource limits
docker run \
  --cpus="2" \
  --memory="2g" \
  -p 8000:8000 \
  stockpulse:latest
```

---

## Security Best Practices

### 1. Secret Management
```bash
# ❌ Don't: Hardcode secrets
docker run -e SECRET_KEY=mykey123 ...

# ✅ Do: Use .env file (not in version control)
docker run --env-file .env.production ...

# ✅ Better: Use Docker secrets or external vault
```

### 2. Non-Root User
```dockerfile
# Dockerfile should include
RUN useradd -m -u 1000 appuser
USER appuser
```

### 3. Image Scanning
```bash
# Scan for vulnerabilities
docker scan stockpulse:latest

# Update base images regularly
docker pull python:3.11-slim
```

### 4. Read-Only Filesystem
```bash
docker run --read-only \
  -v /tmp \
  -v /app/db \
  -p 8000:8000 \
  stockpulse:latest
```

---

## Quick Reference

| Command | Purpose |
|---------|---------|
| `docker build -t stockpulse:latest .` | Build image |
| `docker run -p 8000:8000 stockpulse:latest` | Run container |
| `docker ps` | List running containers |
| `docker logs stockpulse-api` | View container logs |
| `docker exec stockpulse-api bash` | Shell into container |
| `docker push user/stockpulse:latest` | Push to Docker Hub |
| `docker compose up -d` | Start all services |
| `docker compose down` | Stop all services |

---

## Support

- **Docker Documentation:** https://docs.docker.com/
- **Docker Hub:** https://hub.docker.com/
- **Troubleshooting:** See [Troubleshooting](#troubleshooting) section above

---

**Last Updated:** April 2026  
**Version:** 1.0.0
