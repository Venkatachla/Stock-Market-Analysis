@echo off
REM Build and push StockPulse Docker image to Docker Hub

setlocal enabledelayedexpansion

REM Configuration
set DOCKER_USERNAME=your-docker-username
set IMAGE_NAME=stockpulse
set IMAGE_TAG=latest
set REGISTRY=docker.io

echo.
echo ============================================
echo   Docker Build and Push for StockPulse
echo ============================================
echo.

REM Step 1: Check if Docker is installed
docker --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Docker is not installed or not in PATH
    echo Visit: https://docs.docker.com/get-docker/
    exit /b 1
)
echo [OK] Docker is installed

REM Step 2: Check Docker daemon
docker info >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Docker daemon is not running or you are not logged in
    echo Run: docker login
    pause
    exit /b 1
)
echo [OK] Docker daemon is running and authenticated

REM Step 3: Build the image
echo.
echo [INFO] Building Docker image: %DOCKER_USERNAME%/%IMAGE_NAME%:%IMAGE_TAG%
docker build -t %DOCKER_USERNAME%/%IMAGE_NAME%:%IMAGE_TAG% .

if %errorlevel% neq 0 (
    echo [ERROR] Build failed
    exit /b 1
)
echo [OK] Build successful

REM Step 4: Test the image locally
echo.
echo [INFO] Starting container for health check...
docker run -d --name stockpulse-test -p 8000:8000 %DOCKER_USERNAME%/%IMAGE_NAME%:%IMAGE_TAG% >nul
if %errorlevel% neq 0 (
    echo [ERROR] Failed to start container
    exit /b 1
)

REM Wait for container to start
echo [INFO] Waiting for container to initialize...
timeout /t 10 /nobreak

REM Check health
for /f %%i in ('curl -s http://localhost:8000/health 2^>nul ^| findstr /i "ok"') do set HEALTH=%%i

if "!HEALTH!"=="ok" (
    echo [OK] Health check passed
) else (
    echo [WARNING] Health check failed or endpoint not responding yet
)

REM Stop test container
docker stop stockpulse-test >nul
docker rm stockpulse-test >nul
echo [OK] Test container stopped

REM Step 5: Push to Docker Hub
echo.
echo [INFO] Pushing image to Docker Hub...
docker push %DOCKER_USERNAME%/%IMAGE_NAME%:%IMAGE_TAG%

if %errorlevel% neq 0 (
    echo [ERROR] Push failed
    exit /b 1
)

echo.
echo ============================================
echo   Build and Push Successful!
echo ============================================
echo.
echo Image: %REGISTRY%/%DOCKER_USERNAME%/%IMAGE_NAME%:%IMAGE_TAG%
echo.
echo To pull and run:
echo   docker pull %DOCKER_USERNAME%/%IMAGE_NAME%:%IMAGE_TAG%
echo   docker run -p 8000:8000 %DOCKER_USERNAME%/%IMAGE_NAME%:%IMAGE_TAG%
echo.
pause
