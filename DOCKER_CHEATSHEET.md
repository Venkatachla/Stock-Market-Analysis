# Docker Quick Cheatsheet for StockPulse

## 🚀 Getting Started (Copy-Paste Commands)

### Windows Command Prompt
```cmd
REM Set your Docker username
set DOCKER_USERNAME=your-docker-username

REM Build image
docker build -t %DOCKER_USERNAME%/stockpulse:latest .

REM Run locally
docker run -p 8000:8000 %DOCKER_USERNAME%/stockpulse:latest

REM Push to Docker Hub
docker login
docker push %DOCKER_USERNAME%/stockpulse:latest
```

### Windows PowerShell
```powershell
# Set your Docker username
$env:DOCKER_USERNAME = "your-docker-username"

# Build image
docker build -t $env:DOCKER_USERNAME/stockpulse:latest .

# Run locally
docker run -p 8000:8000 $env:DOCKER_USERNAME/stockpulse:latest

# Push to Docker Hub
docker login
docker push $env:DOCKER_USERNAME/stockpulse:latest
```

### Linux/Mac (Bash)
```bash
# Set your Docker username
export DOCKER_USERNAME="your-docker-username"

# Build image
docker build -t ${DOCKER_USERNAME}/stockpulse:latest .

# Run locally
docker run -p 8000:8000 ${DOCKER_USERNAME}/stockpulse:latest

# Push to Docker Hub
docker login
docker push ${DOCKER_USERNAME}/stockpulse:latest
```

---

## 📦 Docker Compose (Easiest Method)

```bash
# Start all services
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

**Access:** `http://localhost:8000`

---

## 🔨 Build Commands

### Quick Build
```bash
docker build -t stockpulse:latest .
```

### Build with Progress
```bash
docker build --progress=plain -t stockpulse:latest .
```

### Build Specific Dockerfile
```bash
docker build -f Dockerfile -t stockpulse:latest .
```

### Build with Build Arguments
```bash
docker build \
  --build-arg NODE_ENV=production \
  --build-arg PYTHON_ENV=production \
  -t stockpulse:latest .
```

---

## 🐳 Run Commands

### Basic Run
```bash
docker run -p 8000:8000 stockpulse:latest
```

### Run in Background
```bash
docker run -d -p 8000:8000 --name my-app stockpulse:latest
```

### Run with Environment Variables
```bash
docker run -p 8000:8000 \
  -e DATABASE_URL=sqlite:///./db.sqlite3 \
  -e SECRET_KEY=your-secret-key \
  stockpulse:latest
```

### Run with .env File
```bash
docker run -p 8000:8000 --env-file .env.docker stockpulse:latest
```

### Run with Volume Mounts
```bash
docker run -p 8000:8000 \
  -v $(pwd)/db.sqlite3:/app/db.sqlite3 \
  -v $(pwd)/data:/app/data \
  stockpulse:latest
```

### Run with Auto-Restart
```bash
docker run -d \
  --restart unless-stopped \
  --name stockpulse-api \
  -p 8000:8000 \
  stockpulse:latest
```

### Run Interactively (Shell)
```bash
docker run -it stockpulse:latest /bin/bash
```

---

## 📊 Container Management

### List Containers
```bash
docker ps                    # Running containers
docker ps -a                 # All containers
docker ps -a --format table  # Formatted view
```

### Container Info
```bash
docker logs container-name           # View logs
docker logs -f container-name        # Follow logs
docker logs --tail 50 container-name # Last 50 lines
docker inspect container-name        # Detailed info
docker stats container-name          # Resource usage
```

### Container Control
```bash
docker start container-name   # Start stopped container
docker stop container-name    # Stop running container
docker restart container-name # Restart container
docker rm container-name      # Remove container
docker kill container-name    # Force stop
```

### Execute Commands Inside
```bash
docker exec container-name command          # Run command
docker exec -it container-name bash         # Interactive shell
docker exec container-name ls -la /app      # List files
docker exec container-name python --version # Check Python
```

---

## 🖼️ Image Management

### List Images
```bash
docker images                    # All images
docker images | grep stockpulse  # Filter by name
docker images --format table     # Formatted view
```

### Image Info
```bash
docker inspect image-id          # Detailed info
docker history stockpulse:latest # View layers
docker image inspect stockpulse:latest --format='{{.Size}}' # Size
```

### Image Operations
```bash
docker tag source-image:tag dest-image:tag  # Tag image
docker rmi image-id                         # Remove image
docker rmi image-id -f                      # Force remove
docker pull image-name                      # Pull from registry
docker push image-name                      # Push to registry
```

---

## 🔄 Docker Hub Operations

### Login/Logout
```bash
docker login              # Login to Docker Hub
docker logout             # Logout from Docker Hub
docker login registry.url # Login to private registry
```

### Tagging for Docker Hub
```bash
# Format: docker tag SOURCE IMAGE_ID USERNAME/REPOSITORY:TAG
docker tag stockpulse:latest username/stockpulse:latest
docker tag stockpulse:latest username/stockpulse:1.0.0
```

### Push to Docker Hub
```bash
docker push username/stockpulse:latest   # Push latest
docker push username/stockpulse:1.0.0    # Push specific version
docker push username/stockpulse          # Push all tags
```

### Pull from Docker Hub
```bash
docker pull username/stockpulse:latest
docker pull username/stockpulse:1.0.0
```

---

## 🧹 Cleanup

### Remove Stopped Containers
```bash
docker container prune
# or
docker rm $(docker ps -aq)
```

### Remove Unused Images
```bash
docker image prune
docker image prune -a  # Remove all unused
```

### Remove Unused Volumes
```bash
docker volume prune
```

### Remove Everything (⚠️ CAREFUL!)
```bash
docker system prune -a --volumes
```

---

## 🔍 Troubleshooting

### Port Already in Use
```bash
# Find container using port
docker ps | grep 8000

# Find process on port
# Windows
netstat -ano | findstr :8000

# Linux/Mac
lsof -i :8000

# Use different port
docker run -p 9000:8000 stockpulse:latest
```

### Container Crashes on Start
```bash
docker logs container-name
docker logs container-name --tail 100
```

### Health Check Failed
```bash
# Manual health check
curl http://localhost:8000/health

# Inside container
docker exec container-name curl http://localhost:8000/health
```

### Out of Disk Space
```bash
docker system prune -a  # Clean up
df -h                   # Check disk usage
```

### Memory Issues
```bash
docker stats              # Check memory usage
docker run -m 2g container  # Limit to 2GB
```

---

## 🌐 Networking

### Create Network
```bash
docker network create my-network
docker run --network my-network stockpulse:latest
```

### List Networks
```bash
docker network ls
docker network inspect my-network
```

### Container Communication
```bash
# From container perspective
docker exec container-name ping other-container
docker exec container-name curl http://other-container:8000
```

---

## 📋 Common Workflows

### Development Build & Run
```bash
docker build -t stockpulse:dev .
docker run -it \
  -p 8000:8000 \
  -v $(pwd):/app \
  stockpulse:dev
```

### Production Build & Deploy
```bash
# Build
docker build -t username/stockpulse:1.0.0 .

# Test
docker run -d --name test-app \
  -e DATABASE_URL=sqlite:///./test.db \
  username/stockpulse:1.0.0

# Verify
sleep 5
curl http://localhost:8000/health

# Push
docker push username/stockpulse:1.0.0
```

### Full CI/CD Pipeline
```bash
# Build image
docker build -t username/stockpulse:latest .

# Run tests
docker run --rm username/stockpulse:latest python -m pytest

# Build production image
docker build --build-arg ENVIRONMENT=production -t username/stockpulse:prod .

# Push to registry
docker push username/stockpulse:prod

# Deploy
docker run -d \
  --restart always \
  -p 8000:8000 \
  --env-file .env.production \
  username/stockpulse:prod
```

---

## 💡 Pro Tips

1. **Use .dockerignore** - Exclude unnecessary files from build context
2. **Layer caching** - Order RUN commands to maximize cache hits
3. **Multi-stage builds** - Reduce final image size (already used)
4. **Health checks** - Always include health endpoints
5. **Logging** - Use stdout/stderr, not files
6. **Non-root user** - Run containers as unprivileged user
7. **Environment variables** - Externalize configuration
8. **Volume mounts** - Use for persistent data

---

## 📚 Resources

- **Docker Docs:** https://docs.docker.com/
- **Docker Hub:** https://hub.docker.com/
- **Best Practices:** https://docs.docker.com/develop/dev-best-practices/
- **Dockerfile Reference:** https://docs.docker.com/engine/reference/builder/

---

**Version:** 1.0 | **Updated:** April 2026
