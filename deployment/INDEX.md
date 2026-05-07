# 📚 CI/CD Deployment Documentation Index

Complete documentation for StockPulse automated deployment pipeline.

## 📖 Quick Navigation

### For First-Time Setup
1. **Start Here:** [SETUP_CHECKLIST.md](SETUP_CHECKLIST.md) - Step-by-step guide with verification
2. **Quick Start:** [QUICK_START_CICD.md](QUICK_START_CICD.md) - 5-minute quick reference
3. **Full Guide:** [CICD_DEPLOYMENT_GUIDE.md](CICD_DEPLOYMENT_GUIDE.md) - Comprehensive setup with all details

### For Daily Operations
- **Troubleshooting:** See CICD_DEPLOYMENT_GUIDE.md → Troubleshooting section
- **Common Commands:** See deployment/README.md → Common Operations section
- **Logs & Monitoring:** kubectl commands reference

### For Verification & Testing
- **Automated Verification:** [verify_cicd_setup.py](verify_cicd_setup.py) - Python verification script
- **Deployment Status:** GitHub Actions → Actions tab → Docker Build & Kubernetes Deploy

---

## 📋 Documentation Files

### 1. [README.md](README.md)
**Main deployment documentation**
- Directory structure overview
- Features and capabilities
- Quick start guide
- Common operations reference
- Troubleshooting basics

**When to read:** First time understanding the deployment structure

### 2. [SETUP_CHECKLIST.md](SETUP_CHECKLIST.md)
**Step-by-step setup verification checklist**
- Pre-setup checks
- Docker Hub configuration
- GitHub Secrets setup
- Kubernetes configuration
- Verification procedures
- Troubleshooting checklist

**When to read:** Before starting setup or during setup

### 3. [QUICK_START_CICD.md](QUICK_START_CICD.md)
**Fast setup reference (5 minutes)**
- Essential steps only
- What to do if something fails
- Minimalist guide for experienced users

**When to read:** Already familiar with DevOps, need quick reference

### 4. [CICD_DEPLOYMENT_GUIDE.md](CICD_DEPLOYMENT_GUIDE.md)
**Complete comprehensive guide**
- Prerequisites
- GitHub Secrets in detail
- Kubernetes cluster setup options (local, cloud)
- Docker Hub configuration
- Pipeline workflow stages
- Verification procedures
- Detailed troubleshooting
- Quick command reference

**When to read:** Need complete details or troubleshooting complex issues

---

## 🐳 Docker Configuration

### Backend Dockerfile
```
deployment/docker/backend/Dockerfile
```
- Multi-stage build for optimization
- Python 3.11-slim base
- Includes health checks
- Exposes port 8000

### Frontend Dockerfile
```
deployment/docker/frontend/Dockerfile
```
- Node 18 for build stage
- nginx:alpine for production
- Optimized image size
- Includes health checks
- Exposes port 80

### Frontend nginx Configuration
```
deployment/docker/frontend/nginx.conf
```
- Production-ready settings
- API proxy to backend
- Cache configuration
- Security headers
- React Router support

---

## ☸️ Kubernetes Configuration

### Deployments
- **Backend:** `backend-deployment.yaml` - 3 replicas, rolling updates
- **Frontend:** `frontend-deployment.yaml` - 2 replicas, zero-downtime updates

### Services
- **Backend:** `backend-service.yaml` - Internal ClusterIP service
- **Frontend:** `frontend-service.yaml` - External LoadBalancer service

### Configuration Management
- **ConfigMap:** `configmap.yaml` - Environment variables
- **Secret:** `secret.yaml` - Sensitive data template
- **Ingress:** `ingress.yaml` - External routing (optional)

### Features
- Health checks (liveness & readiness probes)
- Resource limits and requests
- Pod anti-affinity for distribution
- Rolling update strategy
- Graceful shutdown handling

---

## 🚀 GitHub Actions Workflow

### File Location
```
.github/workflows/docker-k8s-deploy.yml
```

### Pipeline Stages
1. **Test & Build** - Runs tests, builds frontend
2. **Build & Push Docker** - Creates and pushes images to Docker Hub
3. **Deploy to Kubernetes** - Applies manifests and restarts deployments
4. **Notify Status** - Reports success/failure

### Triggers
- Push to `main` branch
- Push to `devops/docker-k8s-cicd` branch
- On changes to:
  - `api/**`
  - `frontend/**`
  - `requirements.txt`
  - `deployment/**`
  - `.github/workflows/docker-k8s-deploy.yml`

### Duration
- Total pipeline: ~10-15 minutes
- Can be triggered manually via GitHub Actions UI

---

## 🔐 GitHub Secrets Required

### Required Secrets
1. **DOCKER_USERNAME** - Docker Hub username
2. **DOCKER_PASSWORD** - Docker Hub access token
3. **KUBE_CONFIG_DATA** - Base64 encoded kubeconfig

### Optional Secrets
- **JWT_SECRET** - For authentication
- **NEWS_API_KEY** - For news features
- **DATABASE_URL** - Database connection string

---

## 🔧 Setup Scripts

### Linux/Mac
```bash
bash deployment/setup-cicd.sh
```

### Windows
```cmd
deployment\setup-cicd.bat
```

Both scripts:
- Check prerequisites
- Verify file structure
- Setup Kubernetes namespace
- Display setup instructions
- Optionally commit and push changes

---

## ✅ Verification Script

### Run Verification
```bash
python deployment/verify_cicd_setup.py
```

Checks:
- ✓ Docker configuration files
- ✓ Kubernetes manifest files
- ✓ GitHub Actions workflow
- ✓ Docker CLI installed
- ✓ kubectl CLI installed
- ✓ Kubernetes cluster accessible
- ✓ Git branch status
- ✓ File content validation
- ✓ Deployment readiness

---

## 📊 Typical Workflow

### Initial Setup (First Time)
1. Read: SETUP_CHECKLIST.md
2. Run: `python deployment/verify_cicd_setup.py`
3. Setup Docker Hub token
4. Add GitHub Secrets
5. Run setup script: `setup-cicd.sh` or `setup-cicd.bat`
6. Commit and push changes
7. Monitor GitHub Actions

### Daily Operations
1. Make code changes
2. Commit and push
3. GitHub Actions runs automatically
4. Check: GitHub Actions → Actions tab
5. Verify: `kubectl get pods -n stockpulse`

### Troubleshooting
1. Check GitHub Actions logs
2. See CICD_DEPLOYMENT_GUIDE.md → Troubleshooting
3. Run: `python deployment/verify_cicd_setup.py`
4. Check Kubernetes events: `kubectl get events -n stockpulse`

---

## 🎯 Production Deployment Readiness

### Pre-Deployment Checks
- [ ] All GitHub Secrets configured
- [ ] Docker Hub token created
- [ ] Kubernetes cluster running
- [ ] Namespace created
- [ ] Docker registry secret added
- [ ] Verification script passes
- [ ] Local Docker build successful
- [ ] kubectl connects to cluster

### Post-Deployment Verification
- [ ] GitHub Actions pipeline completes successfully
- [ ] Docker images in Docker Hub
- [ ] Kubernetes pods running and healthy
- [ ] Services accessible
- [ ] Backend API responding
- [ ] Frontend accessible and connected
- [ ] Logs visible and no errors
- [ ] Rolling updates working

---

## 🔗 External Resources

### Documentation
- [Kubernetes Documentation](https://kubernetes.io/docs/)
- [Docker Documentation](https://docs.docker.com/)
- [GitHub Actions Guide](https://docs.github.com/en/actions)
- [Docker Hub](https://hub.docker.com/)

### Useful Commands
```bash
# See deployment/README.md → Common Operations
# Or see CICD_DEPLOYMENT_GUIDE.md → Quick Commands Reference
```

---

## 📝 File Structure

```
deployment/
├── docker/
│   ├── backend/Dockerfile
│   └── frontend/
│       ├── Dockerfile
│       └── nginx.conf
├── kubernetes/
│   ├── configmap.yaml
│   ├── secret.yaml
│   ├── backend-deployment.yaml
│   ├── backend-service.yaml
│   ├── frontend-deployment.yaml
│   ├── frontend-service.yaml
│   └── ingress.yaml
├── README.md (this file)
├── SETUP_CHECKLIST.md
├── QUICK_START_CICD.md
├── CICD_DEPLOYMENT_GUIDE.md
├── verify_cicd_setup.py
├── setup-cicd.sh
└── setup-cicd.bat

.github/
└── workflows/
    └── docker-k8s-deploy.yml
```

---

## 🚨 Common Issues Quick Reference

| Issue | Solution | Reference |
|-------|----------|-----------|
| Docker images not pushing | Check Docker token, update GitHub Secret | CICD_DEPLOYMENT_GUIDE.md → Troubleshooting |
| Kubeconfig error | Verify base64 encoding (single line) | SETUP_CHECKLIST.md → Step 4 |
| Pods not starting | Check `kubectl describe pod` and events | CICD_DEPLOYMENT_GUIDE.md → Troubleshooting |
| API not accessible | Verify service and network policies | CICD_DEPLOYMENT_GUIDE.md → Troubleshooting |

---

## ✨ What's Included

✅ **Production-Ready Dockerfiles**
- Multi-stage builds for optimization
- Health checks included
- Security best practices

✅ **Kubernetes Configuration**
- Rolling updates (zero downtime)
- Resource limits and requests
- Pod anti-affinity
- Health checks (liveness & readiness)

✅ **Full CI/CD Automation**
- GitHub Actions workflow
- Automatic Docker builds
- Automatic Docker Hub push
- Automatic Kubernetes deployment
- Automatic pod restart

✅ **Comprehensive Documentation**
- Setup checklist with verification
- Quick start guide
- Full deployment guide
- Troubleshooting reference
- Command reference

✅ **Setup Tools**
- Python verification script
- Bash setup script (Linux/Mac)
- Batch setup script (Windows)

---

## 📞 Support

For issues:
1. Check the relevant documentation file above
2. Run verification script: `python deployment/verify_cicd_setup.py`
3. Check GitHub Actions logs
4. Review Kubernetes events: `kubectl get events -n stockpulse`

---

**Status:** ✅ Complete Production-Ready CI/CD Pipeline

**Last Updated:** May 7, 2026
**Version:** 1.0
**Environment:** Docker + Kubernetes + GitHub Actions
