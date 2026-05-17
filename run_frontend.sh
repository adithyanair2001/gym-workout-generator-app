#!/bin/bash

# Gym Workout RAG - Frontend Startup Script

echo "============================================"
echo "  Gym Workout RAG - Frontend Launcher"
echo "============================================"
echo ""

# Get the directory where the script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found!"
    echo "Please run: python -m venv venv && ./venv/bin/pip install -r requirements.txt"
    exit 1
fi

# Install frontend dependencies if needed
echo "📦 Checking frontend dependencies..."
./venv/bin/pip install -q Flask requests

echo ""
echo "🚀 Starting application..."
echo ""
echo "📍 Frontend will be available at: http://localhost:5000"
echo "📍 Backend API will automatically start at: http://localhost:8000"
echo ""
echo "⏳ Please wait 10-30 seconds for both servers to initialize"
echo "💡 Press Ctrl+C to stop both servers"
echo ""
echo "============================================"
echo ""

# Run the Flask app (which will auto-start FastAPI)
./venv/bin/python frontend/app.py

# Made with Bob
