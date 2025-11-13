# Kisaan Kiosk - Quick Start Script
# Run this to start both backend and frontend together

Write-Host "🌾 Kisaan Suvidha Kendra - Kiosk System Startup" -ForegroundColor Green
Write-Host "=================================================" -ForegroundColor Green
Write-Host ""

# Check if Python is installed
Write-Host "Checking Python installation..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version 2>&1
    Write-Host "✅ $pythonVersion found" -ForegroundColor Green
} catch {
    Write-Host "❌ Python not found. Please install Python 3.10+" -ForegroundColor Red
    exit 1
}

# Check if Node.js is installed
Write-Host "Checking Node.js installation..." -ForegroundColor Yellow
try {
    $nodeVersion = node --version 2>&1
    Write-Host "✅ Node.js $nodeVersion found" -ForegroundColor Green
} catch {
    Write-Host "❌ Node.js not found. Please install Node.js 18+" -ForegroundColor Red
    exit 1
}

# Check if pnpm is installed
Write-Host "Checking pnpm installation..." -ForegroundColor Yellow
try {
    $pnpmVersion = pnpm --version 2>&1
    Write-Host "✅ pnpm $pnpmVersion found" -ForegroundColor Green
} catch {
    Write-Host "⚠️  pnpm not found. Installing..." -ForegroundColor Yellow
    npm install -g pnpm
}

Write-Host ""
Write-Host "=================================================" -ForegroundColor Green
Write-Host "Starting services..." -ForegroundColor Cyan
Write-Host "=================================================" -ForegroundColor Green
Write-Host ""

# Function to start backend
$backendJob = Start-Job -ScriptBlock {
    Set-Location "backend"
    Write-Host "🚀 Starting Backend Server (Port 8000)..." -ForegroundColor Cyan
    python main.py
}

# Wait a bit for backend to start
Start-Sleep -Seconds 3

# Function to start frontend
$frontendJob = Start-Job -ScriptBlock {
    Set-Location "modern-kiosk-ui\modern-kiosk-ui"
    Write-Host "🎨 Starting Frontend Kiosk UI (Port 3000)..." -ForegroundColor Cyan
    pnpm dev
}

Write-Host ""
Write-Host "✅ Services Starting..." -ForegroundColor Green
Write-Host ""
Write-Host "📍 Backend API: http://localhost:8000" -ForegroundColor Cyan
Write-Host "📍 Frontend UI: http://localhost:3000" -ForegroundColor Cyan
Write-Host "📍 API Health: http://localhost:8000/health" -ForegroundColor Cyan
Write-Host ""
Write-Host "Press Ctrl+C to stop all services" -ForegroundColor Yellow
Write-Host ""

# Monitor jobs
try {
    while ($true) {
        # Check if jobs are still running
        if ($backendJob.State -ne "Running") {
            Write-Host "❌ Backend job stopped" -ForegroundColor Red
            break
        }
        if ($frontendJob.State -ne "Running") {
            Write-Host "❌ Frontend job stopped" -ForegroundColor Red
            break
        }
        
        # Show output from jobs
        Receive-Job -Job $backendJob
        Receive-Job -Job $frontendJob
        
        Start-Sleep -Seconds 1
    }
} finally {
    Write-Host ""
    Write-Host "Stopping services..." -ForegroundColor Yellow
    Stop-Job -Job $backendJob
    Stop-Job -Job $frontendJob
    Remove-Job -Job $backendJob
    Remove-Job -Job $frontendJob
    Write-Host "✅ All services stopped" -ForegroundColor Green
}
