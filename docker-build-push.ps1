# Docker Build and Push Script for Windows
# Usage: .\docker-build-push.ps1

param(
    [string]$Version = "latest",
    [string]$DockerHubUsername = "venkatachalav",
    [string]$ImageNameBase = "stock-market-analyser",
    [switch]$Push = $false,
    [switch]$SkipBackend = $false,
    [switch]$SkipFrontend = $false
)

# Colors for output
$Green = [System.ConsoleColor]::Green
$Red = [System.ConsoleColor]::Red
$Yellow = [System.ConsoleColor]::Yellow
$Blue = [System.ConsoleColor]::Cyan

function Write-Success { Write-Host $args[0] -ForegroundColor $Green }
function Write-Error-Custom { Write-Host $args[0] -ForegroundColor $Red }
function Write-Warning-Custom { Write-Host $args[0] -ForegroundColor $Yellow }
function Write-Info { Write-Host $args[0] -ForegroundColor $Blue }

Write-Info "================================================"
Write-Info "Docker Build & Push Script"
Write-Info "================================================"
Write-Info "Docker Hub User: $DockerHubUsername"
Write-Info "Image Base: $ImageNameBase"
Write-Info "Version Tag: $Version"
Write-Info "Push to Docker Hub: $Push"
Write-Info "================================================`n"

# Check Docker installation
Write-Info "Checking Docker installation..."
try {
    $dockerVersion = docker --version
    Write-Success "Docker is installed: $dockerVersion`n"
} catch {
    Write-Error-Custom "Docker is not installed or not in PATH"
    exit 1
}

$backendImage = "$DockerHubUsername/$ImageNameBase-backend:$Version"
$frontendImage = "$DockerHubUsername/$ImageNameBase-frontend:$Version"
$backendImageLatest = "$DockerHubUsername/$ImageNameBase-backend:latest"
$frontendImageLatest = "$DockerHubUsername/$ImageNameBase-frontend:latest"

# Build Backend
if (-not $SkipBackend) {
    Write-Info "Building Backend Image: $backendImage"
    docker build -f Dockerfile.backend -t $backendImage -t $backendImageLatest .
    
    if ($LASTEXITCODE -eq 0) {
        Write-Success "✓ Backend image built successfully`n"
    } else {
        Write-Error-Custom "✗ Failed to build backend image"
        exit 1
    }
} else {
    Write-Warning-Custom "Skipping backend build`n"
}

# Build Frontend
if (-not $SkipFrontend) {
    Write-Info "Building Frontend Image: $frontendImage"
    docker build -f Dockerfile.frontend -t $frontendImage -t $frontendImageLatest .
    
    if ($LASTEXITCODE -eq 0) {
        Write-Success "✓ Frontend image built successfully`n"
    } else {
        Write-Error-Custom "✗ Failed to build frontend image"
        exit 1
    }
} else {
    Write-Warning-Custom "Skipping frontend build`n"
}

# List images
Write-Info "`nBuilt Images:"
docker images | Select-String "$DockerHubUsername/$ImageNameBase"

# Push to Docker Hub
if ($Push) {
    Write-Info "`n================================================"
    Write-Info "Pushing to Docker Hub..."
    Write-Info "================================================`n"
    
    if (-not $SkipBackend) {
        Write-Info "Pushing Backend: $backendImage"
        docker push $backendImage
        docker push $backendImageLatest
        
        if ($LASTEXITCODE -eq 0) {
            Write-Success "✓ Backend pushed successfully`n"
        } else {
            Write-Error-Custom "✗ Failed to push backend image"
            exit 1
        }
    }
    
    if (-not $SkipFrontend) {
        Write-Info "Pushing Frontend: $frontendImage"
        docker push $frontendImage
        docker push $frontendImageLatest
        
        if ($LASTEXITCODE -eq 0) {
            Write-Success "✓ Frontend pushed successfully`n"
        } else {
            Write-Error-Custom "✗ Failed to push frontend image"
            exit 1
        }
    }
    
    Write-Success "`nAll images pushed successfully!"
} else {
    Write-Warning-Custom "`nTo push images to Docker Hub, run:"
    Write-Info ".\docker-build-push.ps1 -Push -Version $Version"
}

Write-Info "`n================================================"
Write-Info "Docker Build Summary"
Write-Info "================================================"
Write-Info "Backend Image: $backendImage"
Write-Info "Frontend Image: $frontendImage"
Write-Info ""
Write-Info "To run locally:"
Write-Info "  docker-compose up"
Write-Info ""
Write-Info "To run backend only:"
Write-Info "  docker run -p 8000:8000 $backendImage"
Write-Info ""
Write-Info "To run frontend only:"
Write-Info "  docker run -p 80:80 $frontendImage"
Write-Info "================================================"
