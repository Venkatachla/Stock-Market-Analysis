# Kubernetes Deployment for STCOK

This directory contains Kubernetes manifests to deploy the STCOK trading system to a Kubernetes cluster (e.g., Docker Desktop).

## Prerequisites

- Docker Desktop with Kubernetes enabled
- `kubectl` command-line tool installed
- Docker images built: `stcok-backend:latest` and `stcok-frontend:latest`

## Quick Start

### 1. Build Docker Images

From project root:

```bash
# Build backend image
docker build -f Dockerfile.backend -t stcok-backend:latest .

# Build frontend image
docker build -f Dockerfile.frontend -t stcok-frontend:latest .
```

### 2. Deploy to Kubernetes

**Linux/Mac:**
```bash
cd k8s
bash deploy.sh
```

**Windows (PowerShell):**
```powershell
cd k8s
.\deploy.ps1
```

**Manual kubectl commands:**
```bash
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/secrets.yaml
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/backend-service.yaml
kubectl apply -f k8s/backend-deployment.yaml
kubectl apply -f k8s/frontend-service.yaml
kubectl apply -f k8s/frontend-deployment.yaml
```

## Access Points

Once deployed:

- **Frontend:** http://localhost:30001
- **Backend API:** http://localhost:30000

## Monitoring

### Check Deployments
```bash
kubectl get deployments -n stcok
kubectl describe deployment stcok-backend -n stcok
kubectl describe deployment stcok-frontend -n stcok
```

### Check Pods
```bash
kubectl get pods -n stcok
kubectl describe pod <pod-name> -n stcok
```

### View Logs
```bash
kubectl logs -f deployment/stcok-backend -n stcok
kubectl logs -f deployment/stcok-frontend -n stcok
kubectl logs <pod-name> -n stcok
```

### Check Services
```bash
kubectl get svc -n stcok
kubectl describe svc stcok-backend -n stcok
kubectl describe svc stcok-frontend -n stcok
```

## Cleanup

Remove all STCOK resources:

```bash
kubectl delete namespace stcok
```

Or individually:

```bash
kubectl delete deployment stcok-backend -n stcok
kubectl delete deployment stcok-frontend -n stcok
kubectl delete svc stcok-backend -n stcok
kubectl delete svc stcok-frontend -n stcok
kubectl delete configmap stcok-config -n stcok
kubectl delete secret stcok-secrets -n stcok
kubectl delete namespace stcok
```

## Configuration

### Updating Environment Variables

Edit `configmap.yaml` or `secrets.yaml` and reapply:

```bash
kubectl apply -f k8s/configmap.yaml
# Restart deployments to pick up new config
kubectl rollout restart deployment/stcok-backend -n stcok
kubectl rollout restart deployment/stcok-frontend -n stcok
```

## Troubleshooting

### Pods not starting
```bash
kubectl describe pod <pod-name> -n stcok
kubectl logs <pod-name> -n stcok
```

### Service not accessible
```bash
kubectl get svc -n stcok
kubectl port-forward svc/stcok-backend 8000:8000 -n stcok
kubectl port-forward svc/stcok-frontend 5173:5173 -n stcok
```

### ImagePullBackOff errors
Ensure Docker images are built:
```bash
docker images | grep stcok
```

## Production Considerations

Before deploying to production:

1. **Update secrets** - Replace placeholder values in `secrets.yaml`
2. **Resource limits** - Adjust CPU/memory based on your cluster
3. **Replicas** - Increase `replicas` for high availability
4. **Ingress** - Use an Ingress controller instead of NodePort
5. **Persistence** - Add PersistentVolumes for database
6. **Security** - Use network policies and RBAC

## References

- [Kubernetes Documentation](https://kubernetes.io/docs/)
- [Docker Desktop Kubernetes](https://docs.docker.com/desktop/kubernetes/)
- [kubectl Cheat Sheet](https://kubernetes.io/docs/reference/kubectl/cheatsheet/)
