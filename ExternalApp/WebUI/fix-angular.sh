#!/bin/bash

# ExternalApp Angular Configuration Fix Script

echo "🔧 Fixing Angular configuration issues..."

cd external-app

# Remove any existing node_modules and package-lock.json
echo "🧹 Cleaning existing installation..."
rm -rf node_modules
rm -f package-lock.json

# Install dependencies with specific versions
echo "📦 Installing compatible Angular dependencies..."
npm install

# If that fails, try installing dependencies one by one
if [ $? -ne 0 ]; then
    echo "⚠️  Standard install failed, trying alternative approach..."
    
    # Install Angular CLI first
    npm install -g @angular/cli@17
    
    # Install core dependencies
    npm install @angular/core@17.3.0 @angular/common@17.3.0 @angular/platform-browser@17.3.0
    npm install @angular/router@17.3.0 @angular/forms@17.3.0
    npm install @angular/platform-browser-dynamic@17.3.0 @angular/animations@17.3.0
    npm install @angular/compiler@17.3.0
    
    # Install dev dependencies
    npm install --save-dev @angular/cli@17.3.0
    npm install --save-dev @angular-devkit/build-angular@17.3.0
    npm install --save-dev @angular/compiler-cli@17.3.0
    npm install --save-dev typescript@5.4.0
    
    # Install other dependencies
    npm install rxjs@7.8.0 zone.js@0.14.0 tslib@2.3.0
fi

# Verify installation
if [ -d "node_modules" ]; then
    echo "✅ Dependencies installed successfully!"
    echo ""
    echo "🚀 You can now start the application:"
    echo "   npm start"
    echo ""
    echo "📱 The app will be available at: http://localhost:4202"
else
    echo "❌ Installation failed. Please try manual installation:"
    echo "   npm install --legacy-peer-deps"
fi