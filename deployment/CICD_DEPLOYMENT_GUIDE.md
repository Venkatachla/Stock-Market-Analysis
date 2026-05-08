# StockPulse CI/CD Deployment Guide

Complete automation setup for Docker, Docker Hub, Kubernetes, and GitHub Actions.

## 📋 Table of Contents

1. [Prerequisites](#prerequisites)
2. [GitHub Secrets Setup](#github-secrets-setup)
3. [Kubernetes Cluster Setup](#kubernetes-cluster-setup)
4. [Docker Hub Configuration](#docker-hub-configuration)
5. [Pipeline Workflow](#pipeline-workflow)
6. [Verification & Testing](#verification--testing)
7. [Troubleshooting](#troubleshooting)

---

## Prerequisites

Before setting up CI/CD, ensure you have:

- ✅ GitHub repository access with admin permissions
- ✅ Docker Hub account (username: `venkatachalav`)
- ✅ Kubernetes cluster (local, cloud, or managed)
- ✅ `kubectl` CLI installed and configured
- ✅ Docker installed locally
- ✅ Git installed

---

## GitHub Secrets Setup

### Step 1: Generate Docker Hub Token

1. Go to [Docker Hub](https://hub.docker.com/)
2. Login to your account
3. Navigate to **Account Settings** → **Security** → **New Access Token**
4. Create token named `github-actions-cicd`
5. Copy the token (you won't see it again)

### Step 2: Configure GitHub Repository Secrets

Navigate to your GitHub repository:

```
Settings → Secrets and variables → Actions → New repository secret
```

Add the following secrets:

#### 1. DOCKER_USERNAME
```
Value: venkatachalav
```

#### 2. DOCKER_PASSWORD
```
Value: <your-docker-hub-token>
```

#### 3. KUBE_CONFIG_DATA

Generate base64 encoded kubeconfig:

```bash
# On your local machine
cat ~/.kube/config | base64 -w 0
```

Then add as GitHub Secret:
```
Value: <base64-encoded-kubeconfig>
```

#### 4. Optional Secrets

Add these if needed:

**JWT_SECRET:**
```bash
openssl rand -base64 32
```

**NEWS_API_KEY:**
```bash
# Your NewsAPI key if using news features
```

**DATABASE_URL:**
```bash
# Your database connection string
# Format: postgresql://user:password@host:5432/dbname
```

---

## Kubernetes Cluster Setup

### Option 1: Local Kubernetes (Docker Desktop / Minikube)

#### Using Docker Desktop:
```bash
# Enable Kubernetes in Docker Desktop
# Settings → Kubernetes → Enable Kubernetes
```

#### Using Minikube:
```bash
# Start cluster
minikube start --cpus 4 --memory 8192 --driver docker

# Get kubeconfig
minikube update-context
cat ~/.kube/config | base64 -w 0
```

### Option 2: Cloud Kubernetes (EKS, GKE, AKS)

For AWS EKS:
```bash
# Get kubeconfig
aws eks update-kubeconfig --name stockpulse-cluster --region us-east-1

# Encode for GitHub
cat ~/.kube/config | base64 -w 0
```

### Create Namespace

```bash
kubectl create namespace stockpulse
```

### Create Docker Registry Secret

```bash
kubectl create secret docker-registry dockerhub-secret \
  --docker-server=docker.io \
  --docker-username=venkatachalav \
  --docker-password=<your-docker-token> \
  -n stockpulse
```

---

## Docker Hub Configuration

### Configure Repository Settings

1. Go to [Docker Hub - My Repositories](https://hub.docker.com/repositories)

2. Create two repositories:
   - **stockpulse-backend** (private)
   - **stockpulse-frontend** (private)

3. For each repository:
   - Settings → Visibility → Private
   - Settings → Build Settings → (optional automated builds)

### Verify Push Access

```bash
# Login locally (for testing)
docker login -u venkatachalav

# Tag and push test image
docker tag myimage:latest venkatachalav/stockpulse-backend:test
docker push venkatachalav/stockpulse-backend:test
```

---

## Pipeline Workflow

### Automatic Trigger Events

The CI/CD pipeline triggers automatically on:

```yaml
- Push to main branch
- Push to devops/docker-k8s-cicd branch
- Changes in:
  - api/**
  - frontend/**
  - requirements.txt
  - deployment/**
  - .github/workflows/docker-k8s-deploy.yml
```

### Pipeline Stages

#### Stage 1: Test & Build
- ✅ Checkout code
- ✅ Setup Python 3.11
- ✅ Setup Node 18
- ✅ Install dependencies (backend + frontend)
- ✅ Run tests
- ✅ Build frontend

#### Stage 2: Build & Push Docker Images
- ✅ Setup Docker Buildx
- ✅ Login to Docker Hub
- ✅ Build backend image
- ✅ Build frontend image
- ✅ Push both images to Docker Hub

**Docker Images:**
```
docker.io/venkatachalav/stockpulse-backend:latest
docker.io/venkatachalav/stockpulse-frontend:latest
```

#### Stage 3: Deploy to Kubernetes
- ✅ Setup kubectl
- ✅ Configure kubeconfig
- ✅ Create namespace
- ✅ Apply ConfigMaps
- ✅ Apply Secrets
- ✅ Deploy backend (3 replicas)
- ✅ Deploy frontend (2 replicas)
- ✅ Create services
- ✅ Configure ingress
- ✅ Perform rolling restart
- ✅ Verify deployment status
- ✅ Wait for pods ready
- ✅ Collect logs

#### Stage 4: Notify Status
- ✅ Report success/failure
- ✅ Send final status

---

## Verification & Testing

### Manual Trigger (GitHub Actions)

1. Go to **Actions** tab in GitHub
2. Select **Docker Build & Kubernetes Deploy**
3. Click **Run workflow** → Select branch → **Run workflow**

### Verify Pipeline Execution

```bash
# Watch GitHub Actions
# GitHub → Actions → Docker Build & Kubernetes Deploy → Latest run

# Monitor Docker Hub
# Hub.docker.com → Repositories → Tags section

# Check Kubernetes deployment
kubectl get deployments -n stockpulse
kubectl get pods -n stockpulse
kubectl get svc -n stockpulse
```

### Verify Pods are Running

```bash
# Check backend pods
kubectl get pods -n stockpulse -l app=stockpulse-backend
kubectl logs -n stockpulse -l app=stockpulse-backend

# Check frontend pods
kubectl get pods -n stockpulse -l app=stockpulse-frontend
kubectl logs -n stockpulse -l app=stockpulse-frontend
```

### Test API Connectivity

```bash
# Port forward to backend
kubectl port-forward -n stockpulse svc/backend-service 8000:8000

# Test endpoint
curl http://localhost:8000/health

# Port forward to frontend
kubectl port-forward -n stockpulse svc/frontend-service 3000:80

# Open browser
# http://localhost:3000
```

### Verify Rolling Updates

```bash
# Trigger a new deployment
git push origin main

# Watch rollout progress
kubectl rollout status deployment/stockpulse-backend -n stockpulse -w
kubectl rollout status deployment/stockpulse-frontend -n stockpulse -w

# Check history
kubectl rollout history deployment/stockpulse-backend -n stockpulse
```

---

## Troubleshooting

### Issue: Images Not Pushed to Docker Hub

**Solution:**
```bash
# Verify Docker Hub token is correct
# Check GitHub Secrets: Settings → Secrets → DOCKER_PASSWORD

# Verify username
echo ${{ secrets.DOCKER_USERNAME }}

# Test locally
docker login -u venkatachalav -p <token>
```

### Issue: Kubeconfig Error

**Solution:**
```bash
# Verify kubeconfig is base64 encoded
file ~/.kube/config
# Should NOT contain "YAML" in output

# Re-encode
cat ~/.kube/config | base64 -w 0 > /tmp/kube64.txt
cat /tmp/kube64.txt
# Copy entire output to GitHub Secret: KUBE_CONFIG_DATA
```

### Issue: Pods Not Running

**Solution:**
```bash
# Check pod status
kubectl describe pod -n stockpulse <pod-name>

# Check events
kubectl get events -n stockpulse

# Check image pull
kubectl get pods -n stockpulse -o jsonpath='{.items[*].status.containerStatuses[*].imageID}'

# If image not found, verify Docker Hub secret
kubectl get secret dockerhub-secret -n stockpulse -o yaml
```

### Issue: API Not Accessible

**Solution:**
```bash
# Check service
kubectl get svc backend-service -n stockpulse

# Check endpoints
kubectl get endpoints -n stockpulse

# Check network policies
kubectl get networkpolicies -n stockpulse

# Test connectivity
kubectl run -it --rm debug --image=curlimages/curl --restart=Never -- \
  curl http://backend-service:8000/health -n stockpulse
```

### Issue: Frontend Not Connecting to Backend

**Solution:**

Check nginx configuration in frontend Dockerfile:
```nginx
location /api/ {
    proxy_pass http://backend-service:8000;
}
```

Verify service DNS:
```bash
kubectl exec -it -n stockpulse <frontend-pod> -- \
  nslookup backend-service
```

---

## Quick Commands Reference

### Deployment Operations

```bash
# View all resources
kubectl get all -n stockpulse

# Restart deployment
kubectl rollout restart deployment/stockpulse-backend -n stockpulse
kubectl rollout restart deployment/stockpulse-frontend -n stockpulse

# Scale deployment
kubectl scale deployment stockpulse-backend --replicas=5 -n stockpulse

# View deployment history
kubectl rollout history deployment/stockpulse-backend -n stockpulse

# Rollback to previous version
kubectl rollout undo deployment/stockpulse-backend -n stockpulse

# View pod logs
kubectl logs -n stockpulse -l app=stockpulse-backend --tail=100 -f

# Exec into pod
kubectl exec -it -n stockpulse <pod-name> -- /bin/bash

# Port forward
kubectl port-forward -n stockpulse svc/backend-service 8000:8000
```

### Docker Hub Management

```bash
# Login to Docker Hub
docker login -u venkatachalav

# Pull image
docker pull venkatachalav/stockpulse-backend:latest

# Build and push locally
docker build -t venkatachalav/stockpulse-backend:v1.0 .
docker push venkatachalav/stockpulse-backend:v1.0

# View image history
docker history venkatachalav/stockpulse-backend:latest
```

---

## Next Steps

1. ✅ Add GitHub Secrets
2. ✅ Configure Kubernetes cluster
3. ✅ Create Docker Hub repositories
4. ✅ Push changes to repository
5. ✅ Monitor GitHub Actions
6. ✅ Verify Kubernetes deployments
7. ✅ Test API connectivity

---

## Support & Documentation

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Kubernetes Documentation](https://kubernetes.io/docs/)
- [Docker Hub Documentation](https://docs.docker.com/docker-hub/)
- [Docker Documentation](https://docs.docker.com/)

---

**Status:** ✅ Production-Ready CI/CD Pipeline
