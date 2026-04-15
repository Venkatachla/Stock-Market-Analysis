# STCOK Trading System - Windows PowerShell Startup Script
# Usage: powershell -ExecutionPolicy Bypass -File START.ps1

Write-Host "`n" + ("=" * 80) -ForegroundColor Cyan
Write-Host "  STOCKPULSE - AI Trading Dashboard" -ForegroundColor Cyan
Write-Host ("=" * 80) -ForegroundColor Cyan + "`n"

# Configuration
$backendPort = 8000
$backendHost = "127.0.0.1"
$frontendPort = 8080
$projectRoot = Get-Location

# Function to check if port is in use
function Test-Port {
    param([int]$Port)
    try {
        Test-NetConnection -ComputerName "127.0.0.1" -Port $Port -WarningAction SilentlyContinue -ErrorAction SilentlyContinue | Select-Object -ExpandProperty TcpTestSucceeded
    } catch {
        return $false
    }
}

# 1. Database Check
Write-Host "1️⃣  Checking Database..." -ForegroundColor Yellow
$dbPath = "data\platform.db"
if (Test-Path $dbPath) {
    $dbSize = (Get-Item $dbPath).Length / 1KB
    Write-Host "   ✓ Database found: $dbSize KB" -ForegroundColor Green
} else {
    Write-Host "   ⚠ Database not found - initializing..." -ForegroundColor Yellow
    python add_demo_users.py
}

# 2. Kill any existing Python processes
Write-Host "`n2️⃣  Cleaning up old processes..." -ForegroundColor Yellow
Get-Process python -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
Start-Sleep -Milliseconds 500
Write-Host "   ✓ Old processes stopped" -ForegroundColor Green

# 3. Start Backend
Write-Host "`n3️⃣  Starting Backend Server..." -ForegroundColor Yellow
if (-not (Test-Port $backendPort)) {
    $backendTitle = "StockPulse Backend"
    Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$projectRoot'; python -m uvicorn api.app:app --host $backendHost --port $backendPort --reload" -WindowStyle Normal
    Start-Sleep -Seconds 2
    Write-Host "   ✓ Backend started on $backendHost:$backendPort" -ForegroundColor Green
}

# 4. Start Frontend
Write-Host "`n4️⃣  Starting Frontend Server..." -ForegroundColor Yellow
$frontendTitle = "StockPulse Frontend"
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$projectRoot\frontend'; npm run dev" -WindowStyle Normal
Start-Sleep -Seconds 3
Write-Host "   ✓ Frontend started on localhost:$frontendPort" -ForegroundColor Green

# 5. Display Summary
Write-Host "`n" + ("=" * 80) -ForegroundColor Green
Write-Host "  ✓ SYSTEM READY" -ForegroundColor Green
Write-Host ("=" * 80) -ForegroundColor Green

Write-Host "`n📱 Web Application:" -ForegroundColor Cyan
Write-Host "   Frontend:  http://localhost:$frontendPort" -ForegroundColor White
Write-Host "   Backend:   http://$backendHost:$backendPort" -ForegroundColor White
Write-Host "   Docs:      http://$backendHost:$backendPort/docs" -ForegroundColor White

Write-Host "`n🔐 Demo Login:" -ForegroundColor Cyan
Write-Host "   Email:    admin@example.com" -ForegroundColor White
Write-Host "   Password: password123" -ForegroundColor White

Write-Host "`n📊 Database:" -ForegroundColor Cyan
Write-Host "   Location: $dbPath" -ForegroundColor White
Write-Host "   Type:     SQLite3" -ForegroundColor White

Write-Host "`n💡 Useful Commands:" -ForegroundColor Cyan
Write-Host "   View DB:  python db_viewer.py" -ForegroundColor White
Write-Host "   Clear DB: python db_viewer.py clear" -ForegroundColor White

Write-Host "`n" + ("=" * 80) -ForegroundColor Green + "`n"

# 6. Open Browser
Write-Host "Opening browser..." -ForegroundColor Yellow
Start-Process "http://localhost:$frontendPort"

Write-Host "Press any key to continue or close this window to stop all services..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
