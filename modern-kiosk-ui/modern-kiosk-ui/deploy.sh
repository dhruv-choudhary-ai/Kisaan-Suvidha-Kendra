#!/bin/bash

# Production Deployment Script
# Builds the frontend and starts production server on a single port

echo "🚀 Deploying Modern Kiosk UI for Production..."
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Check Node.js
if ! command -v node &> /dev/null; then
    echo -e "${RED}❌ Node.js not found${NC}"
    exit 1
fi

# Install frontend dependencies if needed
if [ ! -d "node_modules" ]; then
    echo -e "${YELLOW}📦 Installing frontend dependencies...${NC}"
    npm install
    if [ $? -ne 0 ]; then
        echo -e "${RED}❌ Failed to install frontend dependencies${NC}"
        exit 1
    fi
fi

# Build frontend
echo -e "${YELLOW}🔨 Building frontend for production...${NC}"
npm run build
if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Build failed${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Frontend built successfully${NC}"
echo ""

# Install production server dependencies
if [ ! -d "node_modules_prod" ]; then
    echo -e "${YELLOW}📦 Installing production server dependencies...${NC}"
    mkdir -p node_modules_prod
    cd node_modules_prod
    npm init -y > /dev/null 2>&1
    npm install express http-proxy-middleware > /dev/null 2>&1
    cd ..
fi

# Check if backend is running
echo -e "${YELLOW}🔍 Checking for backend services...${NC}"

BACKEND_RUNNING=false
AVATAR_RUNNING=false

if curl -s http://localhost:5000/health > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Backend is running on port 5000${NC}"
    BACKEND_RUNNING=true
else
    echo -e "${YELLOW}⚠️  Backend not detected on port 5000${NC}"
fi

if curl -s http://localhost:8080/ > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Avatar service is running on port 8080${NC}"
    AVATAR_RUNNING=true
else
    echo -e "${YELLOW}⚠️  Avatar service not detected on port 8080${NC}"
fi

echo ""

if [ "$BACKEND_RUNNING" = false ] || [ "$AVATAR_RUNNING" = false ]; then
    echo -e "${YELLOW}⚠️  Warning: Some backend services are not running${NC}"
    echo -e "${YELLOW}   The kiosk may not function fully until all services are started${NC}"
    echo ""
    read -p "Continue anyway? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Start production server
echo -e "${GREEN}🎉 Starting production server...${NC}"
echo ""

NODE_PATH=./node_modules_prod/node_modules node serve-production.js




