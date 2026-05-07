# StockPulse Docker + Kubernetes Deployment

## 1) Build Docker Images

From repository root:

```bash
# Backend
docker build -f deployment/docker/backend/Dockerfile -t <dockerhub-username>/stockpulse-backend:v1.0.0 .

# Frontend
docker build -f deployment/docker/frontend/Dockerfile -t <dockerhub-username>/stockpulse-frontend:v1.0.0 .
```

## 2) Push to Docker Hub

```bash
docker push <dockerhub-username>/stockpulse-backend:v1.0.0
docker push <dockerhub-username>/stockpulse-frontend:v1.0.0
```

## 3) Update Kubernetes Image References

Edit:
- `deployment/kubernetes/backend-deployment.yaml`
- `deployment/kubernetes/frontend-deployment.yaml`

Replace `your-dockerhub-username` with your real Docker Hub username.

## 4) Configure Secrets Before Deploy

Edit `deployment/kubernetes/secret.yaml` and replace all `REPLACE_ME...` values.
Do not deploy with placeholder values.

## 5) Apply Kubernetes Manifests

```bash
kubectl apply -f deployment/kubernetes/configmap.yaml
kubectl apply -f deployment/kubernetes/secret.yaml
kubectl apply -f deployment/kubernetes/backend-deployment.yaml
kubectl apply -f deployment/kubernetes/backend-service.yaml
kubectl apply -f deployment/kubernetes/frontend-deployment.yaml
kubectl apply -f deployment/kubernetes/frontend-service.yaml
kubectl apply -f deployment/kubernetes/ingress.yaml
```

## 6) Ingress Host Mapping (Local)

Ingress uses `stockpulse.local`. Add this in your hosts file:

- Linux/Mac: `/etc/hosts`
- Windows: `C:\Windows\System32\drivers\etc\hosts`

Entry:

```txt
127.0.0.1 stockpulse.local
```

## Notes

- Frontend production API base defaults to `/`, which assumes same-origin routing via ingress/nginx.
- `deployment/docker/frontend/nginx.conf` proxies `/api` to `backend-service:8000` (Kubernetes service DNS).
- Current ConfigMap uses SQLite (`sqlite:///./db.sqlite3`), suitable for demo/dev. Use persistent storage or external DB for production.
