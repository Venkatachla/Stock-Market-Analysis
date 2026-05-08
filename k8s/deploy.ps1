# Windows PowerShell deployment script
Write-Host "🚀 Deploying STCOK to Kubernetes..." -ForegroundColor Green

Write-Host "📦 Creating namespace..." -ForegroundColor Yellow
kubectl apply -f k8s/namespace.yaml

Write-Host "🔐 Creating secrets and configuration..." -ForegroundColor Yellow
kubectl apply -f k8s/secrets.yaml
kubectl apply -f k8s/configmap.yaml

Write-Host "🔙 Deploying backend..." -ForegroundColor Yellow
kubectl apply -f k8s/backend-service.yaml
kubectl apply -f k8s/backend-deployment.yaml

Write-Host "🎨 Deploying frontend..." -ForegroundColor Yellow
kubectl apply -f k8s/frontend-service.yaml
kubectl apply -f k8s/frontend-deployment.yaml

Write-Host ""
Write-Host "✅ Deployment complete!" -ForegroundColor Green
Write-Host ""
Write-Host "📊 Kubernetes Resources:" -ForegroundColor Cyan
kubectl get ns,pods,svc -n stcok

Write-Host ""
Write-Host "🌐 Access points:" -ForegroundColor Cyan
Write-Host "  Backend:  http://localhost:30000"
Write-Host "  Frontend: http://localhost:30001"
Write-Host ""
Write-Host "📋 Tail logs:" -ForegroundColor Cyan
Write-Host "  kubectl logs -f deployment/stcok-backend -n stcok"
Write-Host "  kubectl logs -f deployment/stcok-frontend -n stcok"
