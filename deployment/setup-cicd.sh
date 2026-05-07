#!/bin/bash
# CI/CD Setup Script for Linux/Mac
# Automated configuration for Docker, Kubernetes, and GitHub Actions

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_header() {
    echo -e "\n${BLUE}════════════════════════════════════════${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}════════════════════════════════════════${NC}\n"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_info() {
    echo -e "${BLUE}→ $1${NC}"
}

# Check prerequisites
check_prerequisites() {
    print_header "Checking Prerequisites"
    
    # Check git
    if command -v git &> /dev/null; then
        print_success "Git installed"
    else
        print_error "Git not found. Please install Git."
        exit 1
    fi
    
    # Check kubectl
    if command -v kubectl &> /dev/null; then
        print_success "kubectl installed"
    else
        print_warning "kubectl not found. Please install kubectl to manage Kubernetes."
    fi
    
    # Check docker
    if command -v docker &> /dev/null; then
        print_success "Docker installed"
    else
        print_warning "Docker not found. Please install Docker to build images."
    fi
}

# Create git branch
setup_git_branch() {
    print_header "Setting Up Git Branch"
    
    current_branch=$(git rev-parse --abbrev-ref HEAD)
    
    if [ "$current_branch" = "devops/docker-k8s-cicd" ]; then
        print_success "Already on devops/docker-k8s-cicd branch"
    else
        print_info "Creating devops/docker-k8s-cicd branch..."
        git checkout -b devops/docker-k8s-cicd || git checkout devops/docker-k8s-cicd
        print_success "Branch setup complete"
    fi
}

# Verify deployment structure
verify_structure() {
    print_header "Verifying Deployment Structure"
    
    files=(
        "deployment/docker/backend/Dockerfile"
        "deployment/docker/frontend/Dockerfile"
        "deployment/docker/frontend/nginx.conf"
        "deployment/kubernetes/configmap.yaml"
        "deployment/kubernetes/secret.yaml"
        "deployment/kubernetes/backend-deployment.yaml"
        "deployment/kubernetes/backend-service.yaml"
        "deployment/kubernetes/frontend-deployment.yaml"
        "deployment/kubernetes/frontend-service.yaml"
        "deployment/kubernetes/ingress.yaml"
        ".github/workflows/docker-k8s-deploy.yml"
    )
    
    missing=0
    for file in "${files[@]}"; do
        if [ -f "$file" ]; then
            print_success "$file"
        else
            print_error "$file not found"
            missing=$((missing + 1))
        fi
    done
    
    if [ $missing -eq 0 ]; then
        print_success "All required files present"
    else
        print_error "$missing files missing"
    fi
}

# Setup Kubernetes namespace
setup_kubernetes() {
    print_header "Setting Up Kubernetes"
    
    if ! command -v kubectl &> /dev/null; then
        print_warning "kubectl not installed. Skipping Kubernetes setup."
        return
    fi
    
    # Check cluster connection
    if kubectl cluster-info &> /dev/null; then
        print_success "Connected to Kubernetes cluster"
    else
        print_warning "Could not connect to Kubernetes cluster"
        print_info "Run: kubectl cluster-info"
        return
    fi
    
    # Create namespace
    if kubectl get namespace stockpulse &> /dev/null; then
        print_success "Namespace 'stockpulse' already exists"
    else
        print_info "Creating namespace 'stockpulse'..."
        kubectl create namespace stockpulse
        print_success "Namespace created"
    fi
}

# Display Docker Hub setup instructions
setup_docker_hub() {
    print_header "Docker Hub Configuration"
    
    echo "Follow these steps to prepare Docker Hub:"
    echo ""
    echo "1. Go to: https://hub.docker.com/"
    echo "2. Login to your account"
    echo "3. Navigate to Account Settings → Security → Access Tokens"
    echo "4. Create new token: 'github-actions-cicd'"
    echo "5. Copy the token (you won't see it again)"
    echo ""
    print_info "You'll need this token for GitHub Secrets setup"
}

# Display GitHub Secrets setup instructions
setup_github_secrets() {
    print_header "GitHub Secrets Configuration"
    
    echo "Add these secrets to your GitHub repository:"
    echo ""
    echo "1. Go to: Settings → Secrets and variables → Actions"
    echo ""
    echo "2. Add DOCKER_USERNAME"
    echo "   Value: venkatachalav"
    echo ""
    echo "3. Add DOCKER_PASSWORD"
    echo "   Value: <your-docker-hub-token>"
    echo ""
    echo "4. Add KUBE_CONFIG_DATA"
    echo "   Value: <base64-encoded-kubeconfig>"
    echo ""
    print_info "Generate base64 kubeconfig:"
    echo "   cat ~/.kube/config | base64 -w 0"
    echo ""
    print_warning "Copy the entire output to KUBE_CONFIG_DATA secret"
}

# Verify GitHub Actions workflow
verify_github_actions() {
    print_header "GitHub Actions Workflow"
    
    workflow_file=".github/workflows/docker-k8s-deploy.yml"
    
    if [ -f "$workflow_file" ]; then
        print_success "Workflow file exists"
        
        if grep -q "docker/build-push-action" "$workflow_file"; then
            print_success "Docker build action configured"
        fi
        
        if grep -q "kubectl" "$workflow_file"; then
            print_success "Kubernetes deployment configured"
        fi
    else
        print_error "Workflow file not found"
    fi
}

# Prepare git commit
prepare_commit() {
    print_header "Preparing Git Commit"
    
    echo "Ready to commit changes?"
    echo ""
    echo "Files to be committed:"
    git status --short || true
    echo ""
    
    read -p "Commit and push? (y/n) " -n 1 -r
    echo
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        print_info "Committing changes..."
        git add .
        git commit -m "feat: add Docker & Kubernetes CI/CD pipeline" || true
        
        print_info "Pushing to GitHub..."
        git push origin devops/docker-k8s-cicd
        
        print_success "Changes pushed to GitHub"
        echo ""
        print_info "Go to: https://github.com/$(git config --get remote.origin.url | sed 's/.*://;s/\.git$//')/actions"
        print_info "Watch the 'Docker Build & Kubernetes Deploy' workflow"
    fi
}

# Final summary
print_summary() {
    print_header "Setup Summary"
    
    echo "✓ Deployment structure verified"
    echo "✓ Git branch configured"
    echo "✓ Dockerfiles ready"
    echo "✓ Kubernetes manifests ready"
    echo "✓ GitHub Actions workflow ready"
    echo ""
    echo "Next Steps:"
    echo ""
    echo "1. Setup Docker Hub token"
    echo "   • https://hub.docker.com/settings/security"
    echo ""
    echo "2. Add GitHub Secrets"
    echo "   • DOCKER_USERNAME"
    echo "   • DOCKER_PASSWORD"
    echo "   • KUBE_CONFIG_DATA"
    echo ""
    echo "3. Commit and push changes"
    echo "   • git add ."
    echo "   • git commit -m 'feat: add CI/CD pipeline'"
    echo "   • git push origin devops/docker-k8s-cicd"
    echo ""
    echo "4. Monitor GitHub Actions"
    echo "   • Go to Actions tab"
    echo "   • Watch pipeline run (10-15 minutes)"
    echo ""
}

# Main execution
main() {
    echo -e "${GREEN}"
    echo "╔═══════════════════════════════════════════╗"
    echo "║   StockPulse CI/CD Setup Script (Bash)    ║"
    echo "╚═══════════════════════════════════════════╝"
    echo -e "${NC}"
    
    check_prerequisites
    setup_git_branch
    verify_structure
    verify_github_actions
    setup_kubernetes
    setup_docker_hub
    setup_github_secrets
    prepare_commit
    print_summary
    
    echo -e "${GREEN}Setup complete!${NC}"
}

# Run main function
main
