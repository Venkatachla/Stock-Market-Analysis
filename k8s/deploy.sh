#!/bin/bash

echo "🚀 Deploying STCOK to Kubernetes..."

# Create namespace
echo "📦 Creating namespace..."
kubectl apply -f k8s/namespace.yaml

# Create secrets and configmap
echo "🔐 Creating secrets and configuration..."
kubectl apply -f k8s/secrets.yaml
kubectl apply -f k8s/configmap.yaml

# Deploy backend
echo "🔙 Deploying backend..."
kubectl apply -f k8s/backend-service.yaml
kubectl apply -f k8s/backend-deployment.yaml

# Deploy frontend
echo "🎨 Deploying frontend..."
kubectl apply -f k8s/frontend-service.yaml
kubectl apply -f k8s/frontend-deployment.yaml

echo ""
echo "✅ Deployment complete!"
echo ""
echo "📊 Kubernetes Resources:"
kubectl get ns,pods,svc -n stcok
echo ""
echo "🌐 Access points:"
echo "  Backend:  http://localhost:30000"
echo "  Frontend: http://localhost:30001"
echo ""
echo "📋 Tail logs:"
echo "  kubectl logs -f deployment/stcok-backend -n stcok"
echo "  kubectl logs -f deployment/stcok-frontend -n stcok"
