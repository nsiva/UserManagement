#!/bin/bash

# ExternalApp - Start All Services

echo "🚀 Starting ExternalApp (Full Stack)"
echo "======================================"
echo ""
echo "This will start both the FastAPI backend and Angular frontend"
echo "Make sure the UserManagement system is already running!"
echo ""

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "🛑 Shutting down ExternalApp..."
    # Kill all child processes
    jobs -p | xargs -r kill
    exit 0
}

# Trap SIGINT (Ctrl+C) and call cleanup
trap cleanup SIGINT

# Start API in background
echo "📡 Starting FastAPI backend (port 8002)..."
cd Api
chmod +x start.sh
./start.sh &
API_PID=$!

# Wait a moment for API to start
sleep 3

# Start Frontend in background
echo ""
echo "🌐 Starting Angular frontend (port 4202)..."
cd ../WebUI
chmod +x start.sh
./start.sh &
FRONTEND_PID=$!

echo ""
echo "✅ ExternalApp is starting up!"
echo ""
echo "🔗 Frontend: http://localhost:4202"
echo "📡 API: http://localhost:8002"
echo "📖 API Docs: http://localhost:8002/docs"
echo ""
echo "🔄 Integration Requirements:"
echo "   - UserManagement WebUI must be running on port 4201"
echo "   - UserManagement API must be running on port 8001"
echo ""
echo "Press Ctrl+C to stop all services"
echo ""

# Wait for background processes
wait