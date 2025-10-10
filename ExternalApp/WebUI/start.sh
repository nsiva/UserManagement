#!/bin/bash

# ExternalApp Frontend Start Script

echo "🚀 Starting ExternalApp Frontend..."

# Navigate to the Angular app directory
cd external-app

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo "📦 Installing dependencies..."
    npm install
fi

# Start the Angular development server
echo "🌟 Starting Angular development server on port 4202..."
echo "🔗 App will be available at: http://localhost:4202"
echo "📖 Make sure the ExternalApp API is running on port 8002"
echo "📖 Make sure the UserManagement system is running on port 4201"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

npm start