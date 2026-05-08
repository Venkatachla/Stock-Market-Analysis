# Docker Setup & Deployment Guide

## Quick Start

### Prerequisites
- Docker Desktop installed ([download](https://www.docker.com/products/docker-desktop))
- Docker Hub account ([signup](https://hub.docker.com/))
- For Mac/Linux: `chmod +x docker-build-push.sh`

### 1. Login to Docker Hub

**Windows (PowerShell):**
```powershell
docker login
# Enter your Docker Hub username and password
```

**Linux/Mac:**
```bash
docker login
# Enter your Docker Hub username and password
```

### 2. Build Docker Images

**Windows (PowerShell):**
```powershell
# Build both images (backend & frontend)
.\docker-build-push.ps1

# Build with specific version
.\docker-build-push.ps1 -Version 1.0.0

# Build backend only
.\docker-build-push.ps1 -SkipFrontend

# Build frontend only
.\docker-build-push.ps1 -SkipBackend
```

**Linux/Mac:**
```bash
# Build both images (backend & frontend)
./docker-build-push.sh

# Build with specific version
./docker-build-push.sh -v 1.0.0

# Build backend only
./docker-build-push.sh -b

# Build frontend only
./docker-build-push.sh -f
```

### 3. Push to Docker Hub

**Windows (PowerShell):**
```powershell
.\docker-build-push.ps1 -Push

# With specific version
.\docker-build-push.ps1 -Version 1.0.0 -Push
```

**Linux/Mac:**
```bash
./docker-build-push.sh -p

# With specific version
./docker-build-push.sh -v 1.0.0 -p
```

### 4. Verify Images on Docker Hub

Visit: `https://hub.docker.com/repositories/venkatachalav`

You should see:
- `stock-market-analyser-backend`
- `stock-market-analyser-frontend`

---

## Running Locally

### Using Docker Compose (Recommended)

```bash
# Start all services (backend + frontend)
docker-compose up

# Run in background
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down

# Rebuild and start
docker-compose up --build
```

The services will be available at:
- Frontend: `http://localhost` (port 80)
- Backend API: `http://localhost:8000`

### Using Individual Docker Run Commands

**Backend only:**
```bash
docker run -p 8000:8000 venkatachalav/stock-market-analyser-backend:latest
```

**Frontend only:**
```bash
docker run -p 80:80 venkatachalav/stock-market-analyser-frontend:latest
```

---

## Environment Configuration

### Setting Environment Variables

Create a `.env` file in the project root:

```env
SECRET_KEY=your-super-secret-key-here
RAZORPAY_KEY_ID=your-razorpay-key
RAZORPAY_KEY_SECRET=your-razorpay-secret
```

Then update `docker-compose.yml` to use it:

```yaml
env_file:
  - .env
```

---

## Image Details

### Backend Image (`Dockerfile.backend`)
- **Base:** Python 3.11 slim
- **Framework:** FastAPI + Uvicorn
- **Features:**
  - Multi-stage build for optimization
  - Health checks included
  - Runs on port 8000
  - Size: ~500MB

### Frontend Image (`Dockerfile.frontend`)
- **Base:** Node 20 Alpine → Nginx Alpine
- **Framework:** React 18 + Vite
- **Features:**
  - Multi-stage build (node build → nginx runtime)
  - Nginx with gzip compression
  - API proxy configured
  - WebSocket support
  - Runs on port 80
  - Size: ~50MB

---

## Troubleshooting

### Docker Login Failed
```bash
# Clear saved credentials and login again
docker logout
docker login
```

### Image Already Exists
```bash
# Remove existing image
docker rmi venkatachalav/stock-market-analyser-backend:latest

# Then rebuild
docker build -f Dockerfile.backend -t venkatachalav/stock-market-analyser-backend:latest .
```

### Port Already in Use
```bash
# Map to different port
docker run -p 9000:8000 venkatachalav/stock-market-analyser-backend:latest
```

### Build Fails
```bash
# Check Docker logs
docker logs [container_id]

# Force rebuild without cache
docker build --no-cache -f Dockerfile.backend .
```

### Database Permission Issues
```bash
# Ensure db.sqlite3 has correct permissions
chmod 666 db.sqlite3
```

---

## Production Deployment

### Using Docker Swarm

```bash
# Initialize swarm
docker swarm init

# Deploy stack
docker stack deploy -c docker-compose.yml stcok
```

### Using Kubernetes

```bash
# Create deployment
kubectl create deployment backend \
  --image=venkatachalav/stock-market-analyser-backend:latest

kubectl create deployment frontend \
  --image=venkatachalav/stock-market-analyser-frontend:latest

# Expose services
kubectl expose deployment backend --port=8000 --type=LoadBalancer
kubectl expose deployment frontend --port=80 --type=LoadBalancer
```

### Using Docker Hub Webhooks

1. Go to Docker Hub repository settings
2. Add webhook to trigger deployments
3. Configure your deployment server to pull and run latest images

---

## File Structure

```
STCOK/
├── Dockerfile.backend         # Backend FastAPI image
├── Dockerfile.frontend        # Frontend React/Nginx image
├── docker-compose.yml         # Local development setup
├── nginx.conf                 # Nginx configuration
├── .dockerignore             # Files to exclude from Docker build
├── docker-build-push.ps1      # Windows build script
├── docker-build-push.sh       # Linux/Mac build script
├── DOCKER_SETUP.md           # This file
├── api/
│   └── app.py                # FastAPI application
├── frontend/
│   ├── src/
│   ├── vite.config.ts
│   └── package.json
└── requirements.txt           # Python dependencies
```

---

## Docker Commands Reference

```bash
# Build image
docker build -t [username]/[image]:[tag] .

# Run container
docker run -p 8000:8000 [username]/[image]:[tag]

# List images
docker images

# List running containers
docker ps

# Stop container
docker stop [container_id]

# View logs
docker logs [container_id]

# Remove image
docker rmi [image_id]

# Push to registry
docker push [username]/[image]:[tag]

# Pull from registry
docker pull [username]/[image]:[tag]

# Docker Compose commands
docker-compose up              # Start services
docker-compose up -d           # Start in background
docker-compose down            # Stop and remove services
docker-compose logs -f         # View logs
docker-compose ps              # List services
```

---

## Performance Tips

1. **Use `.dockerignore`** - Exclude unnecessary files to reduce build context
2. **Multi-stage builds** - Reduce final image size
3. **Layer caching** - Order Dockerfile commands from least to most frequently changed
4. **Alpine images** - Use lightweight base images
5. **Gzip compression** - Enable in Nginx for faster transfers

---

## Next Steps

1. ✅ Build images locally
2. ✅ Test with `docker-compose up`
3. ✅ Push to Docker Hub
4. ✅ Deploy to production (AWS, Azure, DigitalOcean, etc.)
5. ✅ Set up monitoring and logs

For deployment platforms:
- **AWS:** ECR + ECS/Kubernetes
- **Azure:** Azure Container Registry + App Service
- **Google Cloud:** Artifact Registry + GKE
- **DigitalOcean:** Container Registry + App Platform
- **Heroku:** Heroku Container Registry

---

## Additional Resources

- [Docker Documentation](https://docs.docker.com/)
- [Docker Hub](https://hub.docker.com/)
- [Docker Compose](https://docs.docker.com/compose/)
- [Best Practices](https://docs.docker.com/develop/dev-best-practices/)
