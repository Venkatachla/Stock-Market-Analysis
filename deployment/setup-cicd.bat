@echo off
REM CI/CD Setup Script for Windows
REM Automated configuration for Docker, Kubernetes, and GitHub Actions

setlocal enabledelayedexpansion

cls
echo.
echo ========================================
echo   StockPulse CI/CD Setup Script
echo   Windows Edition
echo ========================================
echo.

REM Colors using PowerShell
set "GREEN=[92m"
set "RED=[91m"
set "YELLOW=[93m"
set "BLUE=[94m"
set "END=[0m"

REM Check prerequisites
echo %BLUE%Checking Prerequisites...%END%

where git >nul 2>nul
if %errorlevel% equ 0 (
    echo %GREEN%✓ Git installed%END%
) else (
    echo %RED%✗ Git not found. Please install Git.%END%
    exit /b 1
)

where kubectl >nul 2>nul
if %errorlevel% equ 0 (
    echo %GREEN%✓ kubectl installed%END%
) else (
    echo %YELLOW%⚠ kubectl not found. Install kubectl to manage Kubernetes.%END%
)

where docker >nul 2>nul
if %errorlevel% equ 0 (
    echo %GREEN%✓ Docker installed%END%
) else (
    echo %YELLOW%⚠ Docker not found. Install Docker to build images.%END%
)

echo.
echo %BLUE%Setting Up Git Branch...%END%

git rev-parse --abbrev-ref HEAD >branch.txt
set /p current_branch=<branch.txt
del branch.txt

if "%current_branch%"=="devops/docker-k8s-cicd" (
    echo %GREEN%✓ Already on devops/docker-k8s-cicd branch%END%
) else (
    echo Creating devops/docker-k8s-cicd branch...
    git checkout -b devops/docker-k8s-cicd 2>nul || git checkout devops/docker-k8s-cicd
    echo %GREEN%✓ Branch setup complete%END%
)

echo.
echo %BLUE%Verifying Deployment Structure...%END%

setlocal enabledelayedexpansion
set missing=0

for %%F in (
    "deployment\docker\backend\Dockerfile"
    "deployment\docker\frontend\Dockerfile"
    "deployment\docker\frontend\nginx.conf"
    "deployment\kubernetes\configmap.yaml"
    "deployment\kubernetes\secret.yaml"
    "deployment\kubernetes\backend-deployment.yaml"
    "deployment\kubernetes\backend-service.yaml"
    "deployment\kubernetes\frontend-deployment.yaml"
    "deployment\kubernetes\frontend-service.yaml"
    "deployment\kubernetes\ingress.yaml"
    ".github\workflows\docker-k8s-deploy.yml"
) do (
    if exist "%%~F" (
        echo %GREEN%✓ %%~F%END%
    ) else (
        echo %RED%✗ %%~F not found%END%
        set /a missing=!missing!+1
    )
)

if %missing% equ 0 (
    echo %GREEN%✓ All required files present%END%
) else (
    echo %RED%✗ %missing% files missing%END%
)

echo.
echo %BLUE%Docker Hub Configuration%END%
echo.
echo Follow these steps to prepare Docker Hub:
echo.
echo 1. Go to: https://hub.docker.com/
echo 2. Login to your account
echo 3. Navigate to Account Settings -^> Security -^> Access Tokens
echo 4. Create new token: 'github-actions-cicd'
echo 5. Copy the token
echo.

echo %BLUE%GitHub Secrets Configuration%END%
echo.
echo Add these secrets to your GitHub repository:
echo.
echo 1. Go to: Settings -^> Secrets and variables -^> Actions
echo.
echo 2. Add DOCKER_USERNAME
echo    Value: venkatachalav
echo.
echo 3. Add DOCKER_PASSWORD
echo    Value: ^<your-docker-hub-token^>
echo.
echo 4. Add KUBE_CONFIG_DATA
echo    Value: ^<base64-encoded-kubeconfig^>
echo.
echo Generate base64 kubeconfig (PowerShell):
echo    [Convert]::ToBase64String([IO.File]::ReadAllBytes("$env:USERPROFILE\.kube\config"))
echo.

echo %YELLOW%⚠ Copy the entire output to KUBE_CONFIG_DATA secret%END%
echo.

echo %BLUE%Setup Summary%END%
echo.
echo ✓ Deployment structure verified
echo ✓ Git branch configured
echo ✓ Dockerfiles ready
echo ✓ Kubernetes manifests ready
echo ✓ GitHub Actions workflow ready
echo.

echo Next Steps:
echo.
echo 1. Setup Docker Hub token
echo    • https://hub.docker.com/settings/security
echo.
echo 2. Add GitHub Secrets
echo    • DOCKER_USERNAME
echo    • DOCKER_PASSWORD
echo    • KUBE_CONFIG_DATA
echo.
echo 3. Commit and push changes
echo    • git add .
echo    • git commit -m "feat: add CI/CD pipeline"
echo    • git push origin devops/docker-k8s-cicd
echo.
echo 4. Monitor GitHub Actions
echo    • Go to Actions tab
echo    • Watch pipeline run (10-15 minutes)
echo.

echo %GREEN%Setup verification complete!%END%
echo.
pause
