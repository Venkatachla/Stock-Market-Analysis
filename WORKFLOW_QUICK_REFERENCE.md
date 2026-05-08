# ⚡ WORKFLOW QUICK REFERENCE

## 🎯 What Changed

**Before:** GitHub Actions graph showed 4 monolithic jobs (Docker/Kubernetes hidden inside)  
**After:** GitHub Actions graph shows 7 separate, visible jobs with explicit dependencies

---

## 👀 HOW TO VIEW THE WORKFLOW GRAPH

### Step 1: Push Code
```bash
cd "c:\Users\Venkatachala V\STCOK"
git push origin main
# or
git push origin devops/docker-k8s-cicd
```

### Step 2: Open GitHub Actions
1. Go to your GitHub repository
2. Click **Actions** tab
3. Select the latest workflow run: "Docker Build & Kubernetes Deploy"

### Step 3: Click "Graph" Button
- In the workflow run view, click the **Graph** button
- You'll see a visual dependency graph

---

## 📊 WHAT YOU'LL SEE

### The Visual Graph (in GitHub Actions UI)

```
                           ┌─ build-test ─┐
                           │  [2 min]      │
                           └───────┬───────┘
                                   ↓
                       ┌─ sonar-analysis ─┐
                       │   [3 min]         │
                       └────────┬──────────┘
                                │
                    ┌───────────┴────────────┐
                    ↓                        ↓
           ┌─ docker-build ─┐      [in parallel possible]
           │   [5 min]       │
           └────────┬────────┘
                    ↓
            ┌─ docker-push ─┐
            │   [2 min]      │
            └────────┬───────┘
                     ↓
         ┌─ kubernetes-deploy ─┐
         │   [5 min]            │
         └──────────┬───────────┘
                    ↓
       ┌─ deployment-verification ─┐
       │   [3 min]                  │
       └──────────┬─────────────────┘
                  ↓
              ┌─ notify ─┐
              │ [1 min]  │
              └──────────┘
```

### Each Box is Clickable
- Click any job to see its detailed logs
- See exactly which step failed
- See execution time per job
- See Docker image layers
- See Kubernetes manifest application
- See health check results

---

## 🔄 DEPENDENCY CHAIN

| Job | Depends On | Purpose |
|-----|-----------|---------|
| **build-test** | None | Test code, build frontend |
| **sonar-analysis** | build-test | Code quality scan |
| **docker-build** | sonar-analysis | Build Docker images |
| **docker-push** | docker-build | Push to Docker Hub |
| **kubernetes-deploy** | docker-push | Deploy to Kubernetes |
| **deployment-verification** | kubernetes-deploy | Verify deployment healthy |
| **notify** | ALL 6 JOBS | Report status |

---

## ✅ WHAT EACH JOB DOES

### 1️⃣ build-test
```
✓ Install Python 3.11
✓ Install Node 18
✓ Run pytest tests
✓ Run npm linting
✓ Build frontend (npm run build)
```
**Status:** ✅ = Tests pass → Proceed to sonar-analysis  
**Status:** ❌ = Tests fail → Stop workflow

---

### 2️⃣ sonar-analysis
```
✓ Run SonarCloud scan
✓ Check code coverage
✓ Identify code smells
```
**Status:** ✅ = Code quality OK → Proceed to docker-build  
**Status:** ⚠️ = Issues found → Still proceeds (warning only)

---

### 3️⃣ docker-build
```
✓ Build backend Docker image
✓ Build frontend Docker image
✓ Cache Docker layers
```
**Output:** Images ready to push  
**Status:** ❌ = Build fails → Stop workflow

---

### 4️⃣ docker-push
```
✓ Login to Docker Hub (DOCKER_USERNAME + DOCKER_PASSWORD)
✓ Push backend to venkatachalav/stockpulse-backend:latest
✓ Push frontend to venkatachalav/stockpulse-frontend:latest
```
**Status:** ❌ = Push fails → Stop workflow

---

### 5️⃣ kubernetes-deploy
```
✓ Decode kubeconfig from KUBE_CONFIG_DATA secret
✓ Create namespace: stockpulse
✓ Create Docker registry secret
✓ Apply ConfigMap
✓ Apply Secrets
✓ Deploy backend (3 replicas)
✓ Deploy frontend (2 replicas)
✓ Apply Ingress
✓ Restart deployments
```
**Status:** ❌ = Deployment fails → Stop workflow

---

### 6️⃣ deployment-verification
```
✓ Check all pods status
✓ Check service status
✓ Verify backend rollout (FAILS if NOT ready)
✓ Verify frontend rollout (FAILS if NOT ready)
✓ Wait for pods ready
✓ Get pod logs
✓ Health check backend API
✓ Health check frontend
```
**Status:** ❌ = Pods not healthy → STOPS workflow (important!)  
**Status:** ✅ = All healthy → Proceed to notify

---

### 7️⃣ notify
```
✓ Report all 6 job statuses
✓ Summarize pipeline results
✓ Print success/failure message
```
**Always runs** (even if previous jobs fail)

---

## 🚀 TYPICAL EXECUTION FLOW

### Successful Run
```
Timestamp  Job                          Status    Time     Notes
──────────────────────────────────────────────────────────────
12:00 PM   build-test                   ✅ OK     2 min    Tests passed
12:02 PM   sonar-analysis               ✅ OK     3 min    No critical issues
12:05 PM   docker-build                 ✅ OK     5 min    Both images built
12:10 PM   docker-push                  ✅ OK     2 min    Pushed to Docker Hub
12:12 PM   kubernetes-deploy            ✅ OK     5 min    Manifests applied
12:17 PM   deployment-verification      ✅ OK     3 min    All pods healthy
12:20 PM   notify                       ✅ OK     1 min    SUCCESS!

Total Duration: 21 minutes
Result: PRODUCTION LIVE ✅
```

### Failed Run (Example)
```
Timestamp  Job                          Status     Time     Notes
──────────────────────────────────────────────────────────────
12:00 PM   build-test                   ✅ OK      2 min
12:02 PM   sonar-analysis               ✅ OK      3 min
12:05 PM   docker-build                 ❌ FAIL    5 min    Dockerfile syntax error
12:05 PM   docker-push                  ⊘ SKIP            (can't push failed image)
12:05 PM   kubernetes-deploy            ⊘ SKIP            (no image to deploy)
12:05 PM   deployment-verification      ⊘ SKIP
12:05 PM   notify                       ❌ FAIL    1 min    Pipeline failed

Total Duration: 11 minutes
Result: STOPPED AT docker-build ❌
Action: Fix Dockerfile, push again
```

---

## 🔍 DEBUGGING WORKFLOW FAILURES

### Job Failed? Click It
1. Click the red ❌ job in the graph
2. Scroll to the failed step
3. Read the error message
4. Fix the issue
5. Push again

### Example: docker-build Failed
```log
Step "Build backend image" failed with:
ERROR: Docker daemon failed with error: "permission denied"

SOLUTION: Check Dockerfile permissions or syntax
```

---

## 📈 MONITORING

### In GitHub Actions UI

**Jobs List (Left Sidebar)**
- Click each job for detailed logs
- See step-by-step execution
- See durations per step

**Graph View**
- Visual dependency visualization
- See which jobs run sequentially
- See which jobs block others

**Logs Tab**
- Full workflow logs
- All job outputs
- Docker build layers
- Kubectl commands
- Health check results

---

## 🎨 HOW DIFFERENT JOBS APPEAR

### In Graph View (Visual)
```
Each job appears as a colored box:
✅ Success = Green
❌ Failed = Red
⏳ In Progress = Blue
⊘ Skipped = Gray
```

### In List View (Text)
```
✅ build-test — Build & Test
   ✓ Install dependencies
   ✓ Run tests
   ✓ Build frontend

✅ sonar-analysis — SonarCloud Analysis
   ✓ Code quality scan

✅ docker-build — Docker Build
   ✓ Build backend image
   ✓ Build frontend image

✅ docker-push — Docker Push
   ✓ Push to Docker Hub

✅ kubernetes-deploy — Kubernetes Deploy
   ✓ Apply manifests
   ✓ Restart pods

✅ deployment-verification — Deployment Verification
   ✓ Verify pods healthy
   ✓ Health checks passed

✅ notify — Notify Status
   ✓ Pipeline completed successfully!
```

---

## 🔐 REQUIRED SECRETS (GitHub)

Must be configured in GitHub repository settings:

| Secret | Used By | Example |
|--------|---------|---------|
| `DOCKER_USERNAME` | docker-push | venkatachalav |
| `DOCKER_PASSWORD` | docker-push | dckr_pat_jEFU... |
| `KUBE_CONFIG_DATA` | kubernetes-deploy, deployment-verification | base64-encoded kubeconfig |
| `SONAR_TOKEN` | sonar-analysis | (optional, for SonarCloud) |

---

## 📝 KEY POINTS

✅ **Docker and Kubernetes now appear as SEPARATE JOBS**
- Docker build is separate from Docker push
- Kubernetes deploy is separate from verification
- Each has its own logs and status

✅ **Each job has a SINGLE RESPONSIBILITY**
- Test = testing only
- Build = building only
- Push = pushing only
- Deploy = deployment only
- Verify = verification only

✅ **Clear dependency chain**
- Jobs run sequentially
- Each job waits for previous to complete
- Clear what blocks what

✅ **Better error visibility**
- See exactly which step failed
- No mixing of concerns
- Easy to retry single jobs

✅ **Production-grade architecture**
- Microservices-style CI/CD
- Industry standard pattern
- Easy to scale and maintain

---

## 💡 COMMON TASKS

### Retry a Failed Job
1. Click "Re-run failed jobs" in GitHub Actions UI
2. Only failed jobs re-run (saves time)

### View Docker Build Logs
1. Click "docker-build" job
2. Click "Build backend image" step
3. See Docker build layers

### View Deployment Status
1. Click "deployment-verification" job
2. See pod status, rollout status, health checks

### Check Kubernetes Logs
1. Click "kubernetes-deploy" or "deployment-verification" job
2. See kubectl commands and pod logs

---

## 🎯 SUMMARY

### What You Get
✅ 7 separate, visible jobs in GitHub Actions graph  
✅ Clear dependency visualization  
✅ Detailed logging per job  
✅ Easy debugging (know exactly where it failed)  
✅ Flexible retries (retry individual jobs)  
✅ Production-ready CI/CD architecture  

### Time Savings
- **Before:** 1 monolithic log to debug
- **After:** 7 focused logs to understand
- Result: Faster debugging, better visibility

### Next Steps
1. Push code to trigger workflow
2. Watch GitHub Actions graph
3. See all 7 jobs execute in sequence
4. Verify deployment health checks
5. Celebrate when all green! 🎉

---

*Quick Reference Version: 1.0*  
*Updated: May 8, 2026*
