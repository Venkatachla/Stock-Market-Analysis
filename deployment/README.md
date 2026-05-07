# StockPulse Deployment Configuration

Complete CI/CD pipeline with Docker, Kubernetes, and GitHub Actions automation.

## 📁 Directory Structure

```
deployment/
├── docker/                          # Docker configurations
│   ├── backend/
│   │   └── Dockerfile             # Multi-stage build for backend
│   ├── frontend/
│   │   ├── Dockerfile             # Multi-stage Node + nginx build
│   │   └── nginx.conf             # Production nginx configuration
│
├── kubernetes/                      # Kubernetes manifests
│   ├── configmap.yaml             # Environment configuration
│   ├── secret.yaml                # Secrets template
│   ├── backend-deployment.yaml    # Backend deployment (3 replicas)
│   ├── backend-service.yaml       # Backend service
│   ├── frontend-deployment.yaml   # Frontend deployment (2 replicas)
│   ├── frontend-service.yaml      # Frontend LoadBalancer service
│   └── ingress.yaml               # Ingress configuration
│
├── CICD_DEPLOYMENT_GUIDE.md       # Complete setup guide
├── QUICK_START_CICD.md            # 5-minute quick start
├── verify_cicd_setup.py           # Verification script
└── README.md                       # This file
```

## 🚀 Quick Start

### 1. **Verify Setup (1 minute)**
```bash
cd deployment
python verify_cicd_setup.py
```

### 2. **Add GitHub Secrets (3 minutes)**

Go to: **Settings → Secrets and variables → Actions**

Add secrets:
- `DOCKER_USERNAME` = `venkatachalav`
- `DOCKER_PASSWORD` = Your Docker Hub token
- `KUBE_CONFIG_DATA` = Base64 encoded kubeconfig

### 3. **Commit & Push (2 minutes)**
```bash
git add .
git commit -m "feat: add Docker & Kubernetes CI/CD pipeline"
git push origin devops/docker-k8s-cicd
```

### 4. **Monitor Pipeline (5-10 minutes)**

Go to GitHub → Actions → Docker Build & Kubernetes Deploy

---

## 📋 What Gets Deployed

### Backend Container
- **Image:** `venkatachalav/stockpulse-backend:latest`
- **Base:** `python:3.11-slim`
- **Port:** 8000
- **Replicas:** 3 (rolling updates)
- **Resources:** 250m CPU / 512Mi RAM (request), 500m / 1Gi (limit)

### Frontend Container
- **Image:** `venkatachalav/stockpulse-frontend:latest`
- **Base:** `nginx:alpine`
- **Port:** 80
- **Replicas:** 2 (zero-downtime updates)
- **Resources:** 100m CPU / 256Mi RAM (request), 300m / 512Mi (limit)

---

## 🔄 Automatic Workflow

```
Code Push → GitHub Actions Triggered
    ↓
Test & Build Stage (2-3 min)
    ├─ Checkout code
    ├─ Install dependencies
    ├─ Run tests
    └─ Build frontend
    ↓
Docker Build & Push (3-5 min)
    ├─ Build backend image
    ├─ Build frontend image
    └─ Push to Docker Hub
    ↓
Kubernetes Deploy (2-3 min)
    ├─ Apply manifests
    ├─ Restart deployments
    ├─ Wait for ready
    └─ Verify status
    ↓
✅ Production Updated
```

---

## 🔐 Security Features

- ✅ **No hardcoded credentials** - Uses GitHub Secrets
- ✅ **Image pull secrets** - Kubernetes pulls from Docker Hub securely
- ✅ **RBAC ready** - Proper role-based access control
- ✅ **Resource limits** - Prevents resource exhaustion
- ✅ **Health checks** - Liveness and readiness probes
- ✅ **Security headers** - Nginx security configuration
- ✅ **Base64 encoded secrets** - Kubernetes secret management
- ✅ **Private images** - Docker Hub repositories are private

---

## 🎯 Key Features

### Rolling Deployments
- Zero-downtime updates
- Gradual pod replacement
- Automatic rollback on failure

### Health Checks
- **Liveness probe:** Restarts failed pods
- **Readiness probe:** Routes traffic only to healthy pods
- **TCP/HTTP health endpoints**

### Service Discovery
- Backend service: `backend-service:8000`
- Frontend service: `frontend-service:80`
- API routing: `/api` → backend

### Load Balancing
- Backend: ClusterIP (internal)
- Frontend: LoadBalancer (external access)
- Ingress: Optional external routing

### Configuration Management
- **ConfigMap:** Environment variables
- **Secrets:** Sensitive data
- **nginx.conf:** Frontend routing

---

## 📊 Kubernetes Resources

### Deployments
```bash
kubectl get deployments -n stockpulse
```

### Pods
```bash
kubectl get pods -n stockpulse
kubectl get pods -n stockpulse -o wide  # See node assignments
```

### Services
```bash
kubectl get svc -n stockpulse
```

### Events
```bash
kubectl get events -n stockpulse
```

### Logs
```bash
# Backend logs
kubectl logs -n stockpulse -l app=stockpulse-backend -f

# Frontend logs
kubectl logs -n stockpulse -l app=stockpulse-frontend -f

# Previous pod logs (if restarted)
kubectl logs -n stockpulse <pod-name> --previous
```

---

## 🔧 Common Operations

### Restart Deployments
```bash
# Automatic during CI/CD, but can be manual:
kubectl rollout restart deployment/stockpulse-backend -n stockpulse
kubectl rollout restart deployment/stockpulse-frontend -n stockpulse
```

### Scale Deployments
```bash
kubectl scale deployment stockpulse-backend --replicas=5 -n stockpulse
kubectl scale deployment stockpulse-frontend --replicas=3 -n stockpulse
```

### View Rollout History
```bash
kubectl rollout history deployment/stockpulse-backend -n stockpulse
```

### Rollback to Previous Version
```bash
kubectl rollout undo deployment/stockpulse-backend -n stockpulse
```

### Port Forward for Testing
```bash
# Backend
kubectl port-forward -n stockpulse svc/backend-service 8000:8000
# Test: curl http://localhost:8000/health

# Frontend
kubectl port-forward -n stockpulse svc/frontend-service 3000:80
# Test: open http://localhost:3000
```

---

## 🐛 Troubleshooting

### Images Not Pushing
- **Check:** Docker Hub token expiry
- **Fix:** Generate new token, update GitHub Secret
- **Command:** `docker login -u venkatachalav`

### Kubeconfig Error
- **Check:** Is it base64 encoded? (single line)
- **Fix:** `cat ~/.kube/config | base64 -w 0`
- **Verify:** Copy full output to KUBE_CONFIG_DATA

### Pods Not Starting
- **Check:** `kubectl describe pod <pod-name> -n stockpulse`
- **Check:** `kubectl get events -n stockpulse`
- **Check:** Docker image exists: `docker pull venkatachalav/stockpulse-backend:latest`

### API Not Accessible
- **Check:** Service running: `kubectl get svc -n stockpulse`
- **Check:** Pod ready: `kubectl get pods -n stockpulse`
- **Check:** Network policy: `kubectl get networkpolicies -n stockpulse`
- **Test:** `kubectl run -it --rm debug --image=curlimages/curl -- curl http://backend-service:8000/health`

---

## 📚 Documentation

- **CICD_DEPLOYMENT_GUIDE.md** - Full setup with all steps
- **QUICK_START_CICD.md** - 5-minute quick start
- **verify_cicd_setup.py** - Automated verification
- **GitHub Actions:** `.github/workflows/docker-k8s-deploy.yml`

---

## 🔗 Helpful Links

- [Kubernetes Documentation](https://kubernetes.io/docs/)
- [Docker Documentation](https://docs.docker.com/)
- [GitHub Actions Guide](https://docs.github.com/en/actions)
- [Docker Hub](https://hub.docker.com/)

---

## ✅ Success Criteria

After setup, verify:

- ✅ GitHub Secrets configured
- ✅ Dockerfiles build successfully
- ✅ Docker images pushed to Docker Hub
- ✅ Kubernetes manifests apply without errors
- ✅ Pods running and ready
- ✅ Services accessible
- ✅ Backend API responding (health check)
- ✅ Frontend accessible and connected to backend
- ✅ Rolling updates working (no downtime)
- ✅ Logs visible for debugging

---

**Status:** ✅ Production-Ready
