#!/bin/bash

# Kisaan Kiosk - Quick Start Script (Linux/Mac)
# Run this to start both backend and frontend together

echo "🌾 Kisaan Suvidha Kendra - Kiosk System Startup"
echo "================================================="
echo ""

# Check if Python is installed
echo "Checking Python installation..."
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version)
    echo "✅ $PYTHON_VERSION found"
else
    echo "❌ Python not found. Please install Python 3.10+"
    exit 1
fi

# Check if Node.js is installed
echo "Checking Node.js installation..."
if command -v node &> /dev/null; then
    NODE_VERSION=$(node --version)
    echo "✅ Node.js $NODE_VERSION found"
else
    echo "❌ Node.js not found. Please install Node.js 18+"
    exit 1
fi

# Check if pnpm is installed
echo "Checking pnpm installation..."
if command -v pnpm &> /dev/null; then
    PNPM_VERSION=$(pnpm --version)
    echo "✅ pnpm $PNPM_VERSION found"
else
    echo "⚠️  pnpm not found. Installing..."
    npm install -g pnpm
fi

echo ""
echo "================================================="
echo "Starting services..."
echo "================================================="
echo ""

# Start backend in background
cd backend
echo "🚀 Starting Backend Server (Port 8000)..."
python3 main.py &
BACKEND_PID=$!
cd ..

# Wait for backend to start
sleep 3

# Start frontend in background
cd modern-kiosk-ui/modern-kiosk-ui
echo "🎨 Starting Frontend Kiosk UI (Port 3000)..."
pnpm dev &
FRONTEND_PID=$!
cd ../..

echo ""
echo "✅ Services Started!"
echo ""
echo "📍 Backend API: http://localhost:8000"
echo "📍 Frontend UI: http://localhost:3000"
echo "📍 API Health: http://localhost:8000/health"
echo ""
echo "Press Ctrl+C to stop all services"
echo ""

# Trap Ctrl+C to stop both services
trap "echo ''; echo 'Stopping services...'; kill $BACKEND_PID $FRONTEND_PID; echo '✅ All services stopped'; exit 0" INT

# Wait for processes
wait
