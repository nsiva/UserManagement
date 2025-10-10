#!/bin/bash

# ExternalApp API Start Script

echo "🚀 Starting ExternalApp API..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📚 Installing dependencies..."
pip install -r requirements.txt

# Start the server
echo "🌟 Starting FastAPI server on port 8002..."
echo "🔗 API will be available at: http://localhost:8002"
echo "📖 API docs will be available at: http://localhost:8002/docs"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

uvicorn main:app --host 0.0.0.0 --port 8002 --reload