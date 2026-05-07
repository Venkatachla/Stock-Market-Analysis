# ⚡ CI/CD Quick Start - 5 Minutes

## Step 1: Add GitHub Secrets (3 minutes)

Go to: **Settings → Secrets and variables → Actions**

Add these secrets:

```
DOCKER_USERNAME = venkatachalav
DOCKER_PASSWORD = <your-docker-hub-token>
KUBE_CONFIG_DATA = <base64-encoded-kubeconfig>
```

**Get Docker Token:**
- Docker Hub → Account Settings → Security → New Access Token
- Copy token

**Get Kubeconfig (base64):**
```bash
cat ~/.kube/config | base64 -w 0
```

Copy entire output to KUBE_CONFIG_DATA

---

## Step 2: Verify Setup (1 minute)

```bash
# Check branch
git branch
# Should show: * devops/docker-k8s-cicd

# Verify files exist
ls -la deployment/docker/backend/Dockerfile
ls -la deployment/docker/frontend/Dockerfile
ls -la deployment/kubernetes/
ls -la .github/workflows/docker-k8s-deploy.yml
```

---

## Step 3: Commit & Push (1 minute)

```bash
# Commit all changes
git add .
git commit -m "feat: add Docker & Kubernetes CI/CD pipeline"

# Push to GitHub
git push origin devops/docker-k8s-cicd
```

---

## Step 4: Monitor Pipeline

Go to: **GitHub → Actions → Docker Build & Kubernetes Deploy**

Watch stages:
1. ✅ Test & Build (2-3 min)
2. ✅ Build & Push Docker (3-5 min)
3. ✅ Deploy to Kubernetes (2-3 min)
4. ✅ Notify Status (1 min)

**Total time: ~10 minutes**

---

## Verify Kubernetes Deployment

```bash
# Check deployments
kubectl get deployments -n stockpulse

# Check pods
kubectl get pods -n stockpulse

# Check services
kubectl get svc -n stockpulse

# View logs
kubectl logs -n stockpulse -l app=stockpulse-backend --tail=20

# Port forward for testing
kubectl port-forward -n stockpulse svc/backend-service 8000:8000
# Test: curl http://localhost:8000/health
```

---

## ⚠️ If Pipeline Fails

1. **Check GitHub Actions logs**
   - Click the failed job
   - See which step failed
   - Common issues below:

2. **Docker Hub token issue**
   - Verify DOCKER_PASSWORD in secrets
   - Test locally: `docker login -u venkatachalav`

3. **Kubeconfig issue**
   - Verify it's base64 encoded: `file ~/.kube/config`
   - Must be single line in KUBE_CONFIG_DATA secret
   - Re-encode: `cat ~/.kube/config | base64 -w 0`

4. **Kubernetes deployment failed**
   - Check: `kubectl get events -n stockpulse`
   - Check: `kubectl describe pod <pod-name> -n stockpulse`
   - Verify images pulled: `kubectl get pods -o jsonpath='{.items[*].status.containerStatuses[*].imageID}'`

---

## Next Push (Automatic CI/CD)

```bash
# Make a code change
echo "# Updated" >> api/app_fixed.py

# Commit and push
git add .
git commit -m "update: minor improvement"
git push origin main

# GitHub Actions automatically:
# ✅ Runs tests
# ✅ Builds Docker images
# ✅ Pushes to Docker Hub
# ✅ Deploys to Kubernetes
# ✅ Restarts pods
# ✅ Zero manual steps!
```

---

## 🎯 You're Done!

- ✅ Full CI/CD automation setup
- ✅ Docker images automatically built
- ✅ Automatic Docker Hub push
- ✅ Automatic Kubernetes deployment
- ✅ Production-ready pipeline

**Time to fully automated deployment: ~15 minutes total**
