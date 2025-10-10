#!/bin/bash

# ExternalApp WebUI Setup Script

echo "🔧 Setting up ExternalApp WebUI..."

# Check if we're in the right directory
if [ ! -f "setup.sh" ]; then
    echo "❌ Please run this script from the WebUI directory:"
    echo "   cd /Users/siva/projects/UserManagement/ExternalApp/WebUI"
    echo "   ./setup.sh"
    exit 1
fi

# Check if Node.js and npm are installed
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed. Please install Node.js first."
    echo "   Visit: https://nodejs.org/"
    exit 1
fi

if ! command -v npm &> /dev/null; then
    echo "❌ npm is not installed. Please install npm first."
    exit 1
fi

echo "✅ Node.js version: $(node --version)"
echo "✅ npm version: $(npm --version)"

# Check if Angular CLI is installed globally
if ! command -v ng &> /dev/null; then
    echo "📦 Angular CLI not found. Installing globally..."
    npm install -g @angular/cli@latest
else
    echo "✅ Angular CLI version: $(ng version --version)"
fi

# Navigate to the Angular app directory
cd external-app

echo "📦 Installing npm dependencies..."
npm install

# Verify installation
if [ -d "node_modules" ]; then
    echo "✅ Dependencies installed successfully!"
else
    echo "❌ Failed to install dependencies."
    exit 1
fi

echo ""
echo "🎉 Setup complete! You can now start the ExternalApp WebUI:"
echo ""
echo "   cd external-app"
echo "   npm start"
echo ""
echo "   Or use the start script:"
echo "   ./start.sh"
echo ""