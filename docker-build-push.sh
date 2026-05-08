#!/bin/bash

# Docker Build and Push Script for Linux/Mac
# Usage: ./docker-build-push.sh [OPTIONS]
# Options:
#   -v, --version VERSION     Version tag (default: latest)
#   -u, --username USERNAME   Docker Hub username (default: venkatachalav)
#   -p, --push                Push to Docker Hub
#   -b, --backend-only        Build backend only
#   -f, --frontend-only       Build frontend only
#   -h, --help                Show this help message

set -e

# Default values
VERSION="latest"
DOCKER_HUB_USERNAME="venkatachalav"
IMAGE_NAME_BASE="stock-market-analyser"
PUSH=false
BACKEND_ONLY=false
FRONTEND_ONLY=false

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;36m'
NC='\033[0m' # No Color

# Functions
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
    echo -e "${BLUE}ℹ $1${NC}"
}

print_help() {
    cat << EOF
Docker Build and Push Script

Usage: $0 [OPTIONS]

Options:
    -v, --version VERSION       Version tag (default: latest)
    -u, --username USERNAME     Docker Hub username (default: venkatachalav)
    -i, --image-name NAME       Image base name (default: stock-market-analyser)
    -p, --push                  Push to Docker Hub after building
    -b, --backend-only          Build backend only
    -f, --frontend-only         Build frontend only
    -h, --help                  Show this help message

Examples:
    # Build both images with version 1.0.0
    $0 -v 1.0.0

    # Build and push to Docker Hub
    $0 -p

    # Build backend only
    $0 -b

    # Build with custom username and push
    $0 -u myusername -p
EOF
}

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -v|--version)
            VERSION="$2"
            shift 2
            ;;
        -u|--username)
            DOCKER_HUB_USERNAME="$2"
            shift 2
            ;;
        -i|--image-name)
            IMAGE_NAME_BASE="$2"
            shift 2
            ;;
        -p|--push)
            PUSH=true
            shift
            ;;
        -b|--backend-only)
            BACKEND_ONLY=true
            shift
            ;;
        -f|--frontend-only)
            FRONTEND_ONLY=true
            shift
            ;;
        -h|--help)
            print_help
            exit 0
            ;;
        *)
            print_error "Unknown option: $1"
            print_help
            exit 1
            ;;
    esac
done

echo ""
print_info "================================================"
print_info "Docker Build & Push Script"
print_info "================================================"
print_info "Docker Hub User: $DOCKER_HUB_USERNAME"
print_info "Image Base: $IMAGE_NAME_BASE"
print_info "Version Tag: $VERSION"
print_info "Push to Docker Hub: $PUSH"
print_info "================================================"
echo ""

# Check Docker installation
print_info "Checking Docker installation..."
if ! command -v docker &> /dev/null; then
    print_error "Docker is not installed or not in PATH"
    exit 1
fi

DOCKER_VERSION=$(docker --version)
print_success "Docker is installed: $DOCKER_VERSION"
echo ""

BACKEND_IMAGE="$DOCKER_HUB_USERNAME/$IMAGE_NAME_BASE-backend:$VERSION"
FRONTEND_IMAGE="$DOCKER_HUB_USERNAME/$IMAGE_NAME_BASE-frontend:$VERSION"
BACKEND_IMAGE_LATEST="$DOCKER_HUB_USERNAME/$IMAGE_NAME_BASE-backend:latest"
FRONTEND_IMAGE_LATEST="$DOCKER_HUB_USERNAME/$IMAGE_NAME_BASE-frontend:latest"

# Build Backend
if [ "$FRONTEND_ONLY" != true ]; then
    print_info "Building Backend Image: $BACKEND_IMAGE"
    docker build -f Dockerfile.backend -t "$BACKEND_IMAGE" -t "$BACKEND_IMAGE_LATEST" .
    
    if [ $? -eq 0 ]; then
        print_success "Backend image built successfully"
        echo ""
    else
        print_error "Failed to build backend image"
        exit 1
    fi
else
    print_warning "Skipping backend build"
    echo ""
fi

# Build Frontend
if [ "$BACKEND_ONLY" != true ]; then
    print_info "Building Frontend Image: $FRONTEND_IMAGE"
    docker build -f Dockerfile.frontend -t "$FRONTEND_IMAGE" -t "$FRONTEND_IMAGE_LATEST" .
    
    if [ $? -eq 0 ]; then
        print_success "Frontend image built successfully"
        echo ""
    else
        print_error "Failed to build frontend image"
        exit 1
    fi
else
    print_warning "Skipping frontend build"
    echo ""
fi

# List images
print_info "Built Images:"
docker images | grep "$DOCKER_HUB_USERNAME/$IMAGE_NAME_BASE" || true
echo ""

# Push to Docker Hub
if [ "$PUSH" = true ]; then
    echo ""
    print_info "================================================"
    print_info "Pushing to Docker Hub..."
    print_info "================================================"
    echo ""
    
    if [ "$FRONTEND_ONLY" != true ]; then
        print_info "Pushing Backend: $BACKEND_IMAGE"
        docker push "$BACKEND_IMAGE"
        docker push "$BACKEND_IMAGE_LATEST"
        
        if [ $? -eq 0 ]; then
            print_success "Backend pushed successfully"
            echo ""
        else
            print_error "Failed to push backend image"
            exit 1
        fi
    fi
    
    if [ "$BACKEND_ONLY" != true ]; then
        print_info "Pushing Frontend: $FRONTEND_IMAGE"
        docker push "$FRONTEND_IMAGE"
        docker push "$FRONTEND_IMAGE_LATEST"
        
        if [ $? -eq 0 ]; then
            print_success "Frontend pushed successfully"
            echo ""
        else
            print_error "Failed to push frontend image"
            exit 1
        fi
    fi
    
    print_success "All images pushed successfully!"
else
    echo ""
    print_warning "To push images to Docker Hub, run:"
    print_info "./docker-build-push.sh -p -v $VERSION"
fi

echo ""
print_info "================================================"
print_info "Docker Build Summary"
print_info "================================================"
print_info "Backend Image: $BACKEND_IMAGE"
print_info "Frontend Image: $FRONTEND_IMAGE"
echo ""
print_info "To run locally:"
print_info "  docker-compose up"
echo ""
print_info "To run backend only:"
print_info "  docker run -p 8000:8000 $BACKEND_IMAGE"
echo ""
print_info "To run frontend only:"
print_info "  docker run -p 80:80 $FRONTEND_IMAGE"
print_info "================================================"
echo ""
