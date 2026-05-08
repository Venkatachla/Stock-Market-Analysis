# Docker Daemon Not Running - Setup Guide

## Issue
Docker is installed (version 29.2.1) but the daemon is not currently running.

Error: `failed to connect to the docker API at npipe:////./pipe/dockerDesktopLinuxEngine`

---

## ✅ Solutions

### Option 1: Start Docker Desktop (GUI)
1. Open **Windows Search** → Type "Docker Desktop"
2. Click **Docker Desktop** application
3. Wait for it to fully load (watch the taskbar icon)
4. Status will show "Engine running" in notification area
5. Re-run build command when ready

**Time to boot:** ~30-60 seconds

---

### Option 2: Start Docker via PowerShell (Admin)
```powershell
# Run as Administrator
Start-Service Docker

# Verify it's running
docker ps
```

**Note:** Service must be enabled first (see below)

---

### Option 3: Enable Docker as Windows Service

**For Docker Desktop:**
```powershell
# Run as Administrator
$DockerPath = "$env:ProgramFiles\Docker\Docker\Docker Desktop.exe"
& $DockerPath
```

---

## 🔍 Verify Docker is Running

```powershell
# Check if Docker daemon is running
docker ps

# If successful, output shows:
# CONTAINER ID   IMAGE     COMMAND   CREATED   STATUS    PORTS     NAMES

# If daemon is down, you'll get the npipe error
```

---

## 🚀 Once Docker is Running

### Build the Image
```powershell
cd "c:\Users\Venkatachala V\STCOK"
docker build -t stockpulse:latest .
```

**Expected output:**
```
[+] Building 45.2s (11/11) FINISHED
 => [internal] load build definition from Dockerfile
 => [frontend-builder] building frontend...
 => [stage-1] building backend...
 => => exporting to image
 => => naming to docker.io/library/stockpulse:latest
Successfully tagged stockpulse:latest
```

**Build time:** 3-5 minutes (first time)

---

## 🧪 Test the Built Image

```powershell
# Run container locally
docker run -p 8000:8000 stockpulse:latest

# In another PowerShell window, test health check
curl http://localhost:8000/health
```

---

## 📤 Push to Docker Hub

```powershell
# 1. Login to Docker Hub
docker login
# Enter username and password when prompted

# 2. Tag for your Docker Hub account
docker tag stockpulse:latest your-username/stockpulse:latest

# 3. Push to Docker Hub
docker push your-username/stockpulse:latest

# 4. Verify on https://hub.docker.com/repositories
```

---

## 🔧 Troubleshooting Docker Startup

### Docker Desktop Won't Start
- Ensure virtualization is enabled in BIOS (Hyper-V for Windows)
- Check if another Docker daemon is already running
- Try restarting your computer

### Service Start Failed
```powershell
# Check Docker service status
Get-Service Docker

# If stopped, start it
Start-Service Docker

# If disabled, enable it
Set-Service -Name Docker -StartupType Automatic
Start-Service Docker
```

### Port 8000 Already in Use
```powershell
# Find process using port 8000
Get-NetTCPConnection -LocalPort 8000

# Kill the process
Get-Process -Id <PID> | Stop-Process -Force

# Or use different port
docker run -p 9000:8000 stockpulse:latest
```

---

## 📊 Docker Desktop Settings to Check

1. **Open Docker Desktop** (click the Docker icon in taskbar)
2. **Settings** → **General**
   - [x] Start Docker Desktop when you log in
   - [x] Run the Docker daemon as a privileged containerized service on Hyper-V

3. **Resources** → **CPUs & Memory**
   - Ensure sufficient resources allocated (2GB+ RAM, 2+ CPUs recommended)

4. **Docker Engine**
   - Verify daemon is running: `docker ps` should work

---

## 🎯 Quick Build & Push Checklist

- [ ] Start Docker Desktop (wait 60 seconds for full startup)
- [ ] Verify daemon: `docker ps`
- [ ] Build image: `docker build -t stockpulse:latest .`
- [ ] Test locally: `docker run -p 8000:8000 stockpulse:latest`
- [ ] Verify health: `curl http://localhost:8000/health`
- [ ] Login to Hub: `docker login`
- [ ] Tag image: `docker tag stockpulse:latest username/stockpulse:latest`
- [ ] Push to Hub: `docker push username/stockpulse:latest`
- [ ] Verify on Docker Hub: https://hub.docker.com/repositories

---

## 📚 Helpful Commands

```powershell
# System Information
docker version          # Docker version and daemon info
docker info             # Detailed daemon configuration
docker stats            # Real-time resource usage

# Image Management
docker images           # List all images
docker image ls stockpulse  # Check if image exists
docker image rm stockpulse:latest  # Remove image

# Container Management
docker ps               # Running containers
docker ps -a            # All containers
docker logs <container> # View container logs

# Cleanup
docker system prune     # Remove unused resources
docker volume prune     # Remove unused volumes
```

---

## ✅ Next Steps

1. **Start Docker Desktop** (wait for full startup)
2. **Run:** `docker ps` (should work now)
3. **Build:** `docker build -t stockpulse:latest .`
4. **Push:** `docker push username/stockpulse:latest`

---

## 📞 Support

- **Docker Documentation:** https://docs.docker.com/
- **Troubleshooting:** https://docs.docker.com/troubleshoot/
- **Windows Issues:** https://docs.docker.com/desktop/troubleshoot/windows/

---

**Last Updated:** April 2026  
**Docker Version:** 29.2.1
