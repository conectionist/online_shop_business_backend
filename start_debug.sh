#!/bin/bash

echo "🚀 Starting FastAPI application in debug mode..."

# Build the containers with the latest code
echo "📦 Building containers..."
docker compose -f docker-compose.debug.yml build

# Start the debug environment
echo "🔧 Starting debug environment..."
docker compose -f docker-compose.debug.yml up -d

echo "✅ Debug environment started!"
echo "📡 API is available at: http://localhost:8002"
echo "🔧 Debugpy is listening on: localhost:5678"
echo "🗄️  MySQL is available on: localhost:3307"
echo ""
echo "To connect your debugger:"
echo "1. Open VS Code"
echo "2. Go to Run and Debug (Ctrl+Shift+D)"
echo "3. Select 'Debug FastAPI (Docker)'"
echo "4. Click the play button or press F5"
echo ""
echo "To view logs:"
echo "docker compose -f docker-compose.debug.yml logs -f api"
echo ""
echo "To stop the debug environment:"
echo "docker compose -f docker-compose.debug.yml down"
