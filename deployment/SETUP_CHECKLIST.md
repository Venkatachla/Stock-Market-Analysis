# 📋 CI/CD Setup Checklist

Complete step-by-step guide to set up automated deployment pipeline.

## ✅ Pre-Setup Checks

- [ ] You have GitHub repository access with admin permissions
- [ ] You have Docker Hub account (username: `venkatachalav`)
- [ ] You have Kubernetes cluster running (local, cloud, or managed)
- [ ] You have `git`, `kubectl`, and `docker` CLI installed locally
- [ ] You are in the project root directory: `c:\Users\Venkatachala V\STCOK`

---

## Step 1: Verify Files Structure (5 minutes)

### ✅ Docker Files
- [ ] `deployment/docker/backend/Dockerfile` exists
- [ ] `deployment/docker/frontend/Dockerfile` exists
- [ ] `deployment/docker/frontend/nginx.conf` exists
- [ ] `.dockerignore` exists

### ✅ Kubernetes Files
- [ ] `deployment/kubernetes/configmap.yaml` exists
- [ ] `deployment/kubernetes/secret.yaml` exists
- [ ] `deployment/kubernetes/backend-deployment.yaml` exists
- [ ] `deployment/kubernetes/backend-service.yaml` exists
- [ ] `deployment/kubernetes/frontend-deployment.yaml` exists
- [ ] `deployment/kubernetes/frontend-service.yaml` exists
- [ ] `deployment/kubernetes/ingress.yaml` exists

### ✅ GitHub Actions
- [ ] `.github/workflows/docker-k8s-deploy.yml` exists

### ✅ Documentation
- [ ] `deployment/README.md` exists
- [ ] `deployment/CICD_DEPLOYMENT_GUIDE.md` exists
- [ ] `deployment/QUICK_START_CICD.md` exists
- [ ] `deployment/verify_cicd_setup.py` exists

**Verify:**
```bash
python deployment/verify_cicd_setup.py
```

---

## Step 2: Docker Hub Setup (5 minutes)

### Create Docker Access Token

- [ ] Go to: https://hub.docker.com/
- [ ] Sign in to your account
- [ ] Click profile icon → **Account Settings**
- [ ] Click **Security** tab
- [ ] Click **New Access Token**
- [ ] Token description: `github-actions-cicd`
- [ ] Access permissions: **Read, Write, Delete**
- [ ] Click **Generate**
- [ ] **Copy the token** (you won't see it again!)

### Create Docker Hub Repositories

- [ ] Create repository: `stockpulse-backend`
  - [ ] Visibility: **Private**
- [ ] Create repository: `stockpulse-frontend`
  - [ ] Visibility: **Private**

**Keep the Docker token safe - you'll need it next!**

---

## Step 3: Setup Git Branch (2 minutes)

```bash
# Verify branch
git branch

# Create and checkout branch if needed
git checkout -b devops/docker-k8s-cicd
```

- [ ] On branch: `devops/docker-k8s-cicd`

**Command:**
```bash
git checkout -b devops/docker-k8s-cicd
```

---

## Step 4: Configure GitHub Secrets (5 minutes)

### Go to Repository Settings

1. Go to your GitHub repository
2. Click **Settings** tab
3. Click **Secrets and variables** (left menu)
4. Click **Actions**

### Add Secret: DOCKER_USERNAME

- [ ] Click **New repository secret**
- [ ] Name: `DOCKER_USERNAME`
- [ ] Value: `venkatachalav`
- [ ] Click **Add secret**

### Add Secret: DOCKER_PASSWORD

- [ ] Click **New repository secret**
- [ ] Name: `DOCKER_PASSWORD`
- [ ] Value: `<your-docker-hub-token-from-step-2>`
- [ ] Click **Add secret**

### Add Secret: KUBE_CONFIG_DATA

#### Generate Base64 Kubeconfig

**Windows (PowerShell):**
```powershell
[Convert]::ToBase64String([IO.File]::ReadAllBytes("$env:USERPROFILE\.kube\config"))
```

**Linux/Mac (Bash):**
```bash
cat ~/.kube/config | base64 -w 0
```

**Important:** Copy the ENTIRE output (it's one long line)

#### Add to GitHub

- [ ] Click **New repository secret**
- [ ] Name: `KUBE_CONFIG_DATA`
- [ ] Value: `<full-base64-output>`
- [ ] Click **Add secret**

### Verify Secrets

- [ ] All 3 secrets visible in GitHub Settings
- [ ] No secrets exposed publicly

---

## Step 5: Configure Kubernetes (5 minutes)

### Create Namespace

```bash
kubectl create namespace stockpulse
```

- [ ] Namespace created

**Verify:**
```bash
kubectl get namespace stockpulse
```

### Create Docker Registry Secret

```bash
kubectl create secret docker-registry dockerhub-secret \
  --docker-server=docker.io \
  --docker-username=venkatachalav \
  --docker-password=<your-docker-token> \
  -n stockpulse
```

- [ ] Secret created

**Verify:**
```bash
kubectl get secrets -n stockpulse
```

---

## Step 6: Verify Local Setup (5 minutes)

### Check Local Tools

```bash
# Check Docker
docker --version

# Check kubectl
kubectl version --client

# Check git
git --version

# Verify cluster connection
kubectl cluster-info
```

- [ ] Docker installed
- [ ] kubectl installed
- [ ] Connected to Kubernetes cluster

### Run Verification Script

```bash
python deployment/verify_cicd_setup.py
```

- [ ] All checks passed ✓

---

## Step 7: Commit Changes (2 minutes)

```bash
# Check status
git status

# Stage all changes
git add .

# Commit with message
git commit -m "feat: add Docker & Kubernetes CI/CD pipeline"

# Push to GitHub
git push origin devops/docker-k8s-cicd
```

- [ ] Changes committed
- [ ] Changes pushed to GitHub

---

## Step 8: Monitor First Pipeline Run (15 minutes)

### Watch GitHub Actions

1. Go to your GitHub repository
2. Click **Actions** tab
3. Look for: **Docker Build & Kubernetes Deploy**
4. Watch the workflow run

**Expected stages:**
- [ ] Test & Build (2-3 min) ✓
- [ ] Build & Push Docker (3-5 min) ✓
- [ ] Deploy to Kubernetes (2-3 min) ✓
- [ ] Notify Status (1 min) ✓

### Monitor Docker Hub

- [ ] `venkatachalav/stockpulse-backend:latest` pushed ✓
- [ ] `venkatachalav/stockpulse-frontend:latest` pushed ✓

### Verify Kubernetes Deployment

```bash
# Check deployments
kubectl get deployments -n stockpulse

# Check pods
kubectl get pods -n stockpulse

# Check services
kubectl get svc -n stockpulse

# View logs
kubectl logs -n stockpulse -l app=stockpulse-backend

# Port forward to test
kubectl port-forward -n stockpulse svc/backend-service 8000:8000
```

- [ ] Backend deployment running (3 replicas)
- [ ] Frontend deployment running (2 replicas)
- [ ] Services accessible
- [ ] Pods healthy

---

## Step 9: Verify Full System (10 minutes)

### Test Backend API

```bash
# Port forward
kubectl port-forward -n stockpulse svc/backend-service 8000:8000

# Test health endpoint (in another terminal)
curl http://localhost:8000/health
```

- [ ] Backend health check responds ✓

### Test Frontend

```bash
# Port forward (stop previous port-forward first)
kubectl port-forward -n stockpulse svc/frontend-service 80:80

# Open in browser
# http://localhost

# Or test with curl
curl http://localhost/health
```

- [ ] Frontend accessible ✓
- [ ] Frontend connects to backend ✓
- [ ] No errors in browser console ✓

### Test API Connectivity

```bash
# Check if frontend can reach backend
kubectl exec -it -n stockpulse <frontend-pod> -- \
  wget -O - http://backend-service:8000/health
```

- [ ] Frontend resolves backend service ✓

---

## Step 10: Test Rolling Updates (5 minutes)

### Make a Code Change

```bash
# Edit a file
echo "# Updated" >> api/app_fixed.py

# Commit and push
git add .
git commit -m "test: verify CI/CD pipeline"
git push origin devops/docker-k8s-cicd
```

- [ ] Change committed and pushed

### Watch Pipeline Run

- [ ] GitHub Actions triggered automatically ✓
- [ ] Docker images rebuilt ✓
- [ ] Images pushed to Docker Hub ✓
- [ ] Kubernetes deployment updated ✓
- [ ] Pods restarted with zero downtime ✓

**Monitor:**
```bash
# Watch deployment rollout
kubectl rollout status deployment/stockpulse-backend -n stockpulse -w

# In another terminal, watch pods
kubectl get pods -n stockpulse -w
```

---

## Step 11: Create Pull Request (Optional)

- [ ] Create Pull Request: `devops/docker-k8s-cicd` → `main`
- [ ] GitHub Actions runs on PR ✓
- [ ] All checks pass ✓
- [ ] Merge to main ✓
- [ ] Verify deployment updated ✓

---

## Troubleshooting Checklist

### If GitHub Actions Fails

- [ ] Check GitHub Actions logs
- [ ] Verify DOCKER_USERNAME secret
- [ ] Verify DOCKER_PASSWORD secret
- [ ] Verify KUBE_CONFIG_DATA is base64 encoded (no newlines)
- [ ] Check Docker Hub token hasn't expired

### If Docker Build Fails

```bash
# Test locally
docker build -t test:latest -f deployment/docker/backend/Dockerfile .
```

- [ ] Dockerfile syntax correct
- [ ] All dependencies installed
- [ ] Image builds locally

### If Kubernetes Deployment Fails

```bash
# Check events
kubectl get events -n stockpulse

# Describe pod
kubectl describe pod <pod-name> -n stockpulse

# Check image pull
kubectl get pods -n stockpulse -o jsonpath='{.items[*].status.containerStatuses[*].image}'
```

- [ ] Docker images accessible from cluster
- [ ] Correct image pull policy set
- [ ] Registry credentials valid

### If API Not Accessible

```bash
# Test connectivity
kubectl run -it --rm debug --image=curlimages/curl --restart=Never -- \
  curl http://backend-service:8000/health -n stockpulse
```

- [ ] Service DNS resolves
- [ ] Pods are ready
- [ ] Network policies allow traffic

---

## 🎉 Success!

When all checks are marked ✓, your CI/CD pipeline is fully functional:

✅ **Automatic Triggers**
- GitHub push triggers pipeline
- No manual steps needed

✅ **Automatic Builds**
- Docker images built automatically
- Multi-stage builds for optimization

✅ **Automatic Push**
- Images pushed to Docker Hub
- Private repositories

✅ **Automatic Deployment**
- Kubernetes manifests applied
- Deployments updated
- Zero-downtime rolling updates

✅ **Automatic Verification**
- Health checks running
- Logs available
- Status reported

---

## Quick Reference

### Common Commands

```bash
# View pipeline logs
kubectl logs -n stockpulse -l app=stockpulse-backend -f

# Restart deployments manually
kubectl rollout restart deployment/stockpulse-backend -n stockpulse
kubectl rollout restart deployment/stockpulse-frontend -n stockpulse

# Scale pods
kubectl scale deployment stockpulse-backend --replicas=5 -n stockpulse

# View deployment history
kubectl rollout history deployment/stockpulse-backend -n stockpulse

# Port forward
kubectl port-forward -n stockpulse svc/backend-service 8000:8000

# Get all resources
kubectl get all -n stockpulse
```

---

## Next Steps

1. Monitor pipeline runs in GitHub Actions
2. Keep Docker Hub token secure
3. Update kubeconfig if credentials change
4. Monitor logs regularly
5. Plan Kubernetes upgrades
6. Setup alerts and monitoring (optional)

---

**Status:** ✅ Ready for Production
